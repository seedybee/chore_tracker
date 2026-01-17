from __future__ import annotations
from datetime import datetime, timedelta, date
from homeassistant.components.sensor import SensorEntity, RestoreEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

DOMAIN = "chore_tracker"

# Constants (make sure these match your config_flow.py)
CONF_NAME = "name"
CONF_ICON = "icon"
CONF_RECURRENCE_TYPE = "recurrence_type"
CONF_INTERVAL = "interval"
CONF_DAY_OF_MONTH = "day_of_month"
CONF_MONTH = "month"
CONF_START_DATE = "start_date"
CONF_PERSON_ENTITY = "person_entity"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Chore Tracker sensor from a config entry."""
    data = entry.data
    entity = ChoreTrackerSensorEntity(
        hass=hass,
        entry=entry,
        unique_id=entry.entry_id,
        name=data.get(CONF_NAME),
        recurrence_type=data.get(CONF_RECURRENCE_TYPE),
        interval=data.get(CONF_INTERVAL, 1),
        day_of_month=data.get(CONF_DAY_OF_MONTH),
        month=data.get(CONF_MONTH),
        start_date=datetime.fromisoformat(data.get(CONF_START_DATE)).date(),
        icon=data.get(CONF_ICON),
        person_entity=data.get(CONF_PERSON_ENTITY),
        weekdays=data.get("weekdays"),
        monthly_weekdays=data.get("monthly_weekdays"),
        monthly_weeks=data.get("monthly_weeks"),
    )

    # Register entity in hass.data for service access
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entity.entity_id] = entity

    async_add_entities([entity])


class ChoreTrackerSensorEntity(RestoreEntity, SensorEntity):
    """Sensor entity representing a chore recurrence."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        unique_id: str,
        name: str,
        recurrence_type: str,
        interval: int,
        day_of_month: int | None,
        month: int | None,
        start_date: date,
        icon: str | None,
        person_entity: str | None,
        weekdays: list[str] | None = None,
        monthly_weekdays: list[str] | None = None,
        monthly_weeks: list[str] | None = None,
    ):
        self._hass = hass
        self._entry = entry
        self._unique_id = unique_id
        self._name = name
        self._recurrence_type = recurrence_type
        self._interval = int(interval) if interval else 1
        self._day_of_month = int(day_of_month) if day_of_month else None
        self._month = int(month) if month else None
        self._start_date = start_date
        self._icon = icon
        self._person_entity = person_entity
        self._weekdays = weekdays
        self._monthly_weekdays = monthly_weekdays
        self._monthly_weeks = monthly_weeks
        self._last_completed_date: date | None = None

        # Calculate first due date
        self._due_date: datetime | None = self._calculate_next_due(self._start_date)

    async def async_added_to_hass(self) -> None:
        """Restore last completed date when entity is added."""
        await super().async_added_to_hass()

        # Restore previous state
        last_state = await self.async_get_last_state()
        if last_state and last_state.attributes.get("last_completed_date"):
            try:
                self._last_completed_date = datetime.fromisoformat(
                    last_state.attributes["last_completed_date"]
                ).date()
            except (ValueError, TypeError):
                self._last_completed_date = None

        # Register in hass.data
        self._hass.data.setdefault(DOMAIN, {})
        self._hass.data[DOMAIN][self.entity_id] = self

    async def async_will_remove_from_hass(self) -> None:
        """Clean up when entity is removed."""
        await super().async_will_remove_from_hass()

        # Unregister from hass.data
        if self.entity_id in self._hass.data.get(DOMAIN, {}):
            self._hass.data[DOMAIN].pop(self.entity_id)

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def icon(self) -> str | None:
        return self._icon

    @property
    def state(self) -> str | None:
        """Return the chore status as the sensor state."""
        if self._due_date is None:
            return "Unscheduled"
        days = (self._due_date.date() - date.today()).days
        if days > 0:
            return "Upcoming"
        elif days == 0:
            return "Due today"
        else:
            return "Overdue"

    @property
    def extra_state_attributes(self) -> dict:
        """Expose chore details as attributes."""
        # Calculate days for "Days until due" (unclamped)
        days_until_due = None
        if self._due_date is not None:
            days_until_due = (self._due_date.date() - date.today()).days

        # Get assigned person's first name
        assigned_to = None
        if self._person_entity:
            person_state = self.hass.states.get(self._person_entity)
            if person_state and person_state.attributes.get("friendly_name"):
                full_name = person_state.attributes["friendly_name"]
                assigned_to = full_name.split()[0] if full_name else self._person_entity
            else:
                assigned_to = self._person_entity  # Fallback to entity ID

        # Build attributes dict in the requested order
        attrs = {
            "chore_due_date": self._due_date.date().isoformat()
            if self._due_date
            else None,
            "days_until_due": days_until_due,
        }
        if assigned_to:
            attrs["assigned_to"] = assigned_to
        attrs.update(
            {
                "recurrence_type": self._recurrence_type,
                "interval": self._interval,
                "last_completed_date": self._last_completed_date.isoformat()
                if self._last_completed_date
                else None,
            }
        )
        # Add conditional attributes at the end
        if self._weekdays:
            attrs["weekdays"] = self._weekdays
        if self._day_of_month:
            attrs["day_of_month"] = self._day_of_month
        if self._month:
            attrs["month"] = self._month
        if self._monthly_weekdays:
            attrs["monthly_weekdays"] = self._monthly_weekdays
        if self._monthly_weeks:
            attrs["monthly_weeks"] = self._monthly_weeks
        return attrs

    async def async_complete(self) -> None:
        """Mark chore as completed and calculate next due date."""
        # Set last completed date to today
        self._last_completed_date = date.today()

        # Calculate next due date from current due date (or today if overdue)
        if self._due_date:
            # Use the current due date as the base for calculation
            base_date = self._due_date.date()
        else:
            base_date = date.today()

        # Calculate next occurrence
        self._due_date = self._calculate_next_due(base_date)

        # Update Home Assistant state
        self.async_write_ha_state()

    async def async_set_due_date(self, new_due_date: date) -> None:
        """Set a custom due date for the chore."""
        # Convert date to datetime
        self._due_date = datetime.combine(new_due_date, datetime.min.time())

        # Update Home Assistant state
        self.async_write_ha_state()

    def _calculate_next_due(self, start_date: date) -> datetime | None:
        """Calculate the next due date based on recurrence type and interval."""
        recurrence_type = self._recurrence_type
        interval = int(self._interval) if self._interval else 1

        year = int(start_date.year)
        month = int(start_date.month)
        day = int(start_date.day)

        if recurrence_type == "daily":
            return datetime(year, month, day) + timedelta(days=interval)

        elif recurrence_type == "weekly":
            if self._weekdays:
                weekday_map = {
                    "Monday": 0,
                    "Tuesday": 1,
                    "Wednesday": 2,
                    "Thursday": 3,
                    "Friday": 4,
                    "Saturday": 5,
                    "Sunday": 6,
                }
                selected_days = [
                    weekday_map[day] for day in self._weekdays if day in weekday_map
                ]
                if selected_days:
                    current_weekday = start_date.weekday()
                    # Find next occurrence (skip today, start from tomorrow)
                    for offset in range(1, 8):
                        check_weekday = (current_weekday + offset) % 7
                        if check_weekday in selected_days:
                            return datetime.combine(
                                start_date + timedelta(days=offset), datetime.min.time()
                            )
            # Fall back to simple weekly
            return datetime(year, month, day) + timedelta(weeks=interval)

        elif recurrence_type in ("monthly", "monthly_date"):
            # Day-of-month pattern
            new_month = month + interval
            new_year = year
            while new_month > 12:
                new_month -= 12
                new_year += 1

            max_day = [
                31,
                29 if new_year % 4 == 0 else 28,
                31,
                30,
                31,
                30,
                31,
                31,
                30,
                31,
                30,
                31,
            ][new_month - 1]
            new_day = min(int(self._day_of_month or day), max_day)

            return datetime(new_year, new_month, new_day)

        elif recurrence_type == "monthly_weekday":
            # Weekday-of-month pattern (e.g., 2nd Monday)
            if self._monthly_weekdays and self._monthly_weeks:
                return self._calculate_monthly_weekday(start_date, interval)
            return None

        elif recurrence_type == "yearly":
            new_year = year + interval
            new_month = int(self._month or month)
            new_day = int(self._day_of_month or day)

            max_day = [
                31,
                29 if new_year % 4 == 0 else 28,
                31,
                30,
                31,
                30,
                31,
                31,
                30,
                31,
                30,
                31,
            ][new_month - 1]
            new_day = min(new_day, max_day)

            return datetime(new_year, new_month, new_day)

        return None

    def _calculate_monthly_weekday(
        self, start_date: date, interval: int
    ) -> datetime | None:
        """Calculate next due date for monthly weekday pattern (e.g., 2nd Monday)."""
        weekday_map = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }
        week_map = {"1st": 1, "2nd": 2, "3rd": 3, "4th": 4, "Last": 5}

        # Get selected weekdays and weeks
        selected_weekdays = [
            weekday_map[day] for day in self._monthly_weekdays if day in weekday_map
        ]
        selected_weeks = [
            week_map.get(week, week_map.get(week.lower()))
            for week in self._monthly_weeks
            if week in week_map or week.lower() in week_map
        ]
        selected_weeks = [w for w in selected_weeks if w is not None]

        if not selected_weekdays or not selected_weeks:
            return None

        # Start from next month
        current_date = start_date
        target_month = current_date.month + interval
        target_year = current_date.year

        while target_month > 12:
            target_month -= 12
            target_year += 1

        # Find the first matching weekday in the selected weeks
        for week_num in selected_weeks:
            for weekday in selected_weekdays:
                candidate_date = self._find_weekday_in_week(
                    target_year, target_month, weekday, week_num
                )
                if candidate_date:
                    return datetime.combine(candidate_date, datetime.min.time())

        return None

    def _find_weekday_in_week(
        self, year: int, month: int, target_weekday: int, week_num: int
    ) -> date | None:
        """Find a specific weekday in a specific week of a month."""
        # Get first day of month
        first_day = date(year, month, 1)
        first_weekday = first_day.weekday()

        # Calculate offset to first occurrence of target weekday
        offset = (target_weekday - first_weekday) % 7
        first_occurrence = first_day + timedelta(days=offset)

        if week_num == 5:  # "Last" week
            # Find last occurrence
            candidate = first_occurrence + timedelta(weeks=3)
            if candidate.month != month:
                candidate = first_occurrence + timedelta(weeks=2)
            return candidate
        else:
            # Find nth occurrence
            candidate = first_occurrence + timedelta(weeks=(week_num - 1))
            if candidate.month == month:
                return candidate

        return None
