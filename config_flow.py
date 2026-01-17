"""Config flow for Chore Tracker integration with recurrence wizard."""

from __future__ import annotations

from datetime import date

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

DOMAIN = "chore_tracker"

CONF_NAME = "name"
CONF_ICON = "icon"
CONF_PERSON_ENTITY = "person_entity"
CONF_RECURRENCE_TYPE = "recurrence_type"
CONF_INTERVAL = "interval"
CONF_DAY_OF_MONTH = "day_of_month"
CONF_MONTH = "month"
CONF_START_DATE = "start_date"


class ChoreTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._base_data: dict = {}

    async def async_step_user(self, user_input=None):
        """Page 1: Basic info + recurrence type."""
        if user_input is not None:
            recurrence_type = user_input[CONF_RECURRENCE_TYPE]
            self._base_data = {
                CONF_NAME: user_input[CONF_NAME],
                CONF_ICON: user_input[CONF_ICON],
                CONF_PERSON_ENTITY: user_input.get(CONF_PERSON_ENTITY),
                CONF_RECURRENCE_TYPE: recurrence_type,
            }

            if recurrence_type == "manual":
                # Finish immediately with manual defaults
                data = {
                    **self._base_data,
                    CONF_START_DATE: date.today().isoformat(),
                    "due_days": 9999,
                }
                return self.async_create_entry(title=data[CONF_NAME], data=data)

            # Otherwise go to recurrence details page
            return await self.async_step_recurrence()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Optional(CONF_ICON, default="mdi:broom"): selector.IconSelector(),
                vol.Optional(CONF_PERSON_ENTITY): selector.EntitySelector(
                    {"domain": "person"}
                ),
                vol.Required(CONF_RECURRENCE_TYPE, default="daily"): vol.In(
                    {
                        "manual": "Manual",
                        "daily": "Daily",
                        "weekly": "Weekly",
                        "monthly_date": "Monthly - date of month",
                        "monthly_weekday": "Monthly - day of week",
                        "yearly": "Yearly",
                    }
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_recurrence(self, user_input=None):
        """Page 2: Recurrence pattern options."""
        if user_input is not None:
            recurrence_type = self._base_data[CONF_RECURRENCE_TYPE]

            # Convert checkboxes to lists for weekly pattern
            if recurrence_type == "weekly" and "weekdays" in user_input:
                # Strip numbered prefixes from weekdays
                user_input["weekdays"] = [
                    day.split("_", 1)[1] if "_" in day else day
                    for day in user_input.get("weekdays", [])
                ]

            # Convert checkboxes to lists for monthly_weekday pattern
            if recurrence_type == "monthly_weekday":
                monthly_weekdays = []
                if user_input.get("monday_monthly"):
                    monthly_weekdays.append("Monday")
                if user_input.get("tuesday_monthly"):
                    monthly_weekdays.append("Tuesday")
                if user_input.get("wednesday_monthly"):
                    monthly_weekdays.append("Wednesday")
                if user_input.get("thursday_monthly"):
                    monthly_weekdays.append("Thursday")
                if user_input.get("friday_monthly"):
                    monthly_weekdays.append("Friday")
                if user_input.get("saturday_monthly"):
                    monthly_weekdays.append("Saturday")
                if user_input.get("sunday_monthly"):
                    monthly_weekdays.append("Sunday")

                user_input["monthly_weekdays"] = monthly_weekdays

                # Remove the checkbox keys
                for key in [
                    "monday_monthly",
                    "tuesday_monthly",
                    "wednesday_monthly",
                    "thursday_monthly",
                    "friday_monthly",
                    "saturday_monthly",
                    "sunday_monthly",
                ]:
                    user_input.pop(key, None)

            data = {**self._base_data, **user_input}
            return self.async_create_entry(title=data[CONF_NAME], data=data)

        recurrence_type = self._base_data[CONF_RECURRENCE_TYPE]
        schema_dict: dict = {}

        if recurrence_type == "daily":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "days",
                        "mode": "box",
                        "translation_key": "occur_every_days",
                    }
                )
            )

        elif recurrence_type == "weekly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "weeks",
                        "mode": "box",
                        "translation_key": "occur_every_weeks",
                    }
                )
            )
            schema_dict[vol.Optional("weekdays", default=[])] = selector.SelectSelector(
                {
                    "options": [
                        "1_Monday",
                        "2_Tuesday",
                        "3_Wednesday",
                        "4_Thursday",
                        "5_Friday",
                        "6_Saturday",
                        "7_Sunday",
                    ],
                    "multiple": True,
                }
            )

        elif recurrence_type == "monthly_date":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "months",
                        "mode": "box",
                        "translation_key": "occur_every_months",
                    }
                )
            )
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

        elif recurrence_type == "monthly_weekday":
            # Weekday checkboxes section - "Reoccur every"
            schema_dict[vol.Optional("monday_monthly", default=False)] = bool
            schema_dict[vol.Optional("tuesday_monthly", default=False)] = bool
            schema_dict[vol.Optional("wednesday_monthly", default=False)] = bool
            schema_dict[vol.Optional("thursday_monthly", default=False)] = bool
            schema_dict[vol.Optional("friday_monthly", default=False)] = bool
            schema_dict[vol.Optional("saturday_monthly", default=False)] = bool
            schema_dict[vol.Optional("sunday_monthly", default=False)] = bool

            # Week selector - "Of the"
            schema_dict[vol.Optional("monthly_weeks", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "1st",
                            "2nd",
                            "3rd",
                            "4th",
                            "Last",
                        ],
                        "multiple": True,
                    }
                )
            )

            # Interval - "Occur every X months"
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "months",
                        "mode": "box",
                        "translation_key": "occur_every_months",
                    }
                )
            )

        elif recurrence_type == "yearly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "years",
                        "mode": "box",
                        "translation_key": "occur_every_years",
                    }
                )
            )
            schema_dict[vol.Required(CONF_MONTH, default=1)] = selector.SelectSelector(
                {
                    "options": [
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December",
                    ],
                }
            )
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

        # Always put start date last
        schema_dict[vol.Required(CONF_START_DATE, default=date.today().isoformat())] = (
            selector.DateSelector()
        )

        return self.async_show_form(
            step_id="recurrence", data_schema=vol.Schema(schema_dict)
        )

    async def async_step_monthly(self, user_input=None):
        """Page 3: Monthly recurrence type (day vs weekday)."""
        if user_input is not None:
            monthly_type = user_input.get("monthly_type", "day_of_month")

            if monthly_type == "day_of_month":
                # Use day of month
                data = {
                    **self._base_data,
                    CONF_DAY_OF_MONTH: user_input.get(CONF_DAY_OF_MONTH, 1),
                    CONF_START_DATE: user_input.get(
                        CONF_START_DATE, date.today().isoformat()
                    ),
                }
            else:
                # Use weekday of month
                data = {
                    **self._base_data,
                    "monthly_weekdays": user_input.get("monthly_weekdays", []),
                    "monthly_weeks": user_input.get("monthly_weeks", []),
                    CONF_START_DATE: user_input.get(
                        CONF_START_DATE, date.today().isoformat()
                    ),
                }

            return self.async_create_entry(title=data[CONF_NAME], data=data)

        schema_dict: dict = {}

        schema_dict[vol.Required("monthly_type", default="day_of_month")] = vol.In(
            {
                "day_of_month": "Day of month",
                "weekday": "Specific weekday",
            }
        )

        schema_dict[vol.Optional(CONF_DAY_OF_MONTH, default=1)] = (
            selector.NumberSelector(
                {
                    "min": 1,
                    "max": 31,
                    "mode": "box",
                    "translation_key": "day_of_month",
                }
            )
        )

        schema_dict[vol.Optional("monthly_weekdays", default=[])] = (
            selector.SelectSelector(
                {
                    "options": [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday",
                    ],
                    "multiple": True,
                }
            )
        )

        schema_dict[vol.Optional("monthly_weeks", default=[])] = (
            selector.SelectSelector(
                {
                    "options": [
                        "1st",
                        "2nd",
                        "3rd",
                        "4th",
                        "Last",
                    ],
                    "multiple": True,
                }
            )
        )

        schema_dict[vol.Required(CONF_START_DATE, default=date.today().isoformat())] = (
            selector.DateSelector()
        )

        return self.async_show_form(
            step_id="monthly", data_schema=vol.Schema(schema_dict)
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return ChoreTrackerOptionsFlowHandler(config_entry)


class ChoreTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle editing options after a chore has been created."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry
        self._base_options: dict = {}

    async def async_step_init(self, user_input=None):
        """Page 1: Basic options."""
        if user_input is not None:
            recurrence_type = user_input[CONF_RECURRENCE_TYPE]
            self._base_options = {
                CONF_RECURRENCE_TYPE: recurrence_type,
                CONF_ICON: user_input.get(CONF_ICON, "mdi:broom"),
                CONF_PERSON_ENTITY: user_input.get(CONF_PERSON_ENTITY),
            }

            if recurrence_type == "manual":
                data = {
                    **self._base_options,
                    CONF_START_DATE: date.today().isoformat(),
                    "due_days": 9999,
                }
                return self.async_create_entry(title="", data=data)

            return await self.async_step_recurrence()

        options = self._entry.options or {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_RECURRENCE_TYPE,
                    default=options.get(CONF_RECURRENCE_TYPE, "daily"),
                ): vol.In(
                    {
                        "manual": "Manual",
                        "daily": "Daily",
                        "weekly": "Weekly",
                        "monthly_date": "Monthly - date of month",
                        "monthly_weekday": "Monthly - day of week",
                        "yearly": "Yearly",
                    }
                ),
                vol.Optional(
                    CONF_ICON, default=options.get(CONF_ICON, "mdi:broom")
                ): selector.IconSelector(),
                vol.Optional(
                    CONF_PERSON_ENTITY, default=options.get(CONF_PERSON_ENTITY)
                ): selector.EntitySelector({"domain": "person"}),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_recurrence(self, user_input=None):
        """Page 2: Recurrence pattern options."""
        if user_input is not None:
            # Convert checkbox booleans to weekdays list
            if (
                user_input.get(CONF_RECURRENCE_TYPE) == "weekly"
                or self._base_options.get(CONF_RECURRENCE_TYPE) == "weekly"
            ):
                weekdays = []
                if user_input.get("monday"):
                    weekdays.append("Monday")
                if user_input.get("tuesday"):
                    weekdays.append("Tuesday")
                if user_input.get("wednesday"):
                    weekdays.append("Wednesday")
                if user_input.get("thursday"):
                    weekdays.append("Thursday")
                if user_input.get("friday"):
                    weekdays.append("Friday")
                if user_input.get("saturday"):
                    weekdays.append("Saturday")
                if user_input.get("sunday"):
                    weekdays.append("Sunday")

                # Remove checkbox keys and add weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                    ]
                }
                if weekdays:
                    user_input["weekdays"] = weekdays

            # Convert monthly_weekday checkboxes to list
            if self._base_options.get(CONF_RECURRENCE_TYPE) == "monthly_weekday":
                monthly_weekdays = []
                if user_input.get("monday_monthly"):
                    monthly_weekdays.append("Monday")
                if user_input.get("tuesday_monthly"):
                    monthly_weekdays.append("Tuesday")
                if user_input.get("wednesday_monthly"):
                    monthly_weekdays.append("Wednesday")
                if user_input.get("thursday_monthly"):
                    monthly_weekdays.append("Thursday")
                if user_input.get("friday_monthly"):
                    monthly_weekdays.append("Friday")
                if user_input.get("saturday_monthly"):
                    monthly_weekdays.append("Saturday")
                if user_input.get("sunday_monthly"):
                    monthly_weekdays.append("Sunday")

                # Remove checkbox keys and add monthly_weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday_monthly",
                        "tuesday_monthly",
                        "wednesday_monthly",
                        "thursday_monthly",
                        "friday_monthly",
                        "saturday_monthly",
                        "sunday_monthly",
                    ]
                }
                if monthly_weekdays:
                    user_input["monthly_weekdays"] = monthly_weekdays

            data = {**self._base_options, **user_input}
            return self.async_create_entry(title="", data=data)

        recurrence_type = self._base_options[CONF_RECURRENCE_TYPE]
        schema_dict: dict = {}

        if recurrence_type == "daily":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "days",
                        "mode": "box",
                        "translation_key": "occur_every_days",
                    }
                )
            )

        elif recurrence_type == "weekly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "weeks",
                        "mode": "box",
                        "translation_key": "occur_every_weeks",
                    }
                )
            )
            schema_dict[vol.Optional("monday", default=False)] = bool
            schema_dict[vol.Optional("tuesday", default=False)] = bool
            schema_dict[vol.Optional("wednesday", default=False)] = bool
            schema_dict[vol.Optional("thursday", default=False)] = bool
            schema_dict[vol.Optional("friday", default=False)] = bool
            schema_dict[vol.Optional("saturday", default=False)] = bool
            schema_dict[vol.Optional("sunday", default=False)] = bool

        elif recurrence_type == "monthly":
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weekdays", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                            "Sunday",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weeks", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "1st",
                            "2nd",
                            "3rd",
                            "4th",
                            "Last",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "months",
                        "mode": "box",
                        "translation_key": "occur_every_months",
                    }
                )
            )

        elif recurrence_type == "yearly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "years",
                        "mode": "box",
                        "translation_key": "occur_every_years",
                    }
                )
            )
            schema_dict[vol.Required(CONF_MONTH, default=1)] = selector.SelectSelector(
                {
                    "options": [
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December",
                    ],
                }
            )
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

        # Always put start date last
        schema_dict[vol.Required(CONF_START_DATE, default=date.today().isoformat())] = (
            selector.DateSelector()
        )

        return self.async_show_form(
            step_id="recurrence", data_schema=vol.Schema(schema_dict)
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return ChoreTrackerOptionsFlowHandler(config_entry)


class ChoreTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle editing options after a chore has been created."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry
        self._base_options: dict = {}

    async def async_step_init(self, user_input=None):
        """Page 1: Basic options."""
        if user_input is not None:
            recurrence_type = user_input[CONF_RECURRENCE_TYPE]
            self._base_options = {
                CONF_RECURRENCE_TYPE: recurrence_type,
                CONF_ICON: user_input.get(CONF_ICON, "mdi:broom"),
                CONF_PERSON_ENTITY: user_input.get(CONF_PERSON_ENTITY),
            }

            if recurrence_type == "manual":
                data = {
                    **self._base_options,
                    CONF_START_DATE: date.today().isoformat(),
                    "due_days": 9999,
                }
                return self.async_create_entry(title="", data=data)

            return await self.async_step_recurrence()

        options = self._entry.options or {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_RECURRENCE_TYPE,
                    default=options.get(CONF_RECURRENCE_TYPE, "daily"),
                ): vol.In(
                    {
                        "manual": "Manual",
                        "daily": "Daily",
                        "weekly": "Weekly",
                        "monthly_date": "Monthly - date of month",
                        "monthly_weekday": "Monthly - day of week",
                        "yearly": "Yearly",
                    }
                ),
                vol.Optional(
                    CONF_ICON, default=options.get(CONF_ICON, "mdi:broom")
                ): selector.IconSelector(),
                vol.Optional(
                    CONF_PERSON_ENTITY, default=options.get(CONF_PERSON_ENTITY)
                ): selector.EntitySelector({"domain": "person"}),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_recurrence(self, user_input=None):
        """Page 2: Recurrence pattern options."""
        if user_input is not None:
            # Convert checkbox booleans to weekdays list
            if (
                user_input.get(CONF_RECURRENCE_TYPE) == "weekly"
                or self._base_options.get(CONF_RECURRENCE_TYPE) == "weekly"
            ):
                weekdays = []
                if user_input.get("monday"):
                    weekdays.append("Monday")
                if user_input.get("tuesday"):
                    weekdays.append("Tuesday")
                if user_input.get("wednesday"):
                    weekdays.append("Wednesday")
                if user_input.get("thursday"):
                    weekdays.append("Thursday")
                if user_input.get("friday"):
                    weekdays.append("Friday")
                if user_input.get("saturday"):
                    weekdays.append("Saturday")
                if user_input.get("sunday"):
                    weekdays.append("Sunday")

                # Remove checkbox keys and add weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                    ]
                }
                if weekdays:
                    user_input["weekdays"] = weekdays

            # Convert monthly_weekday checkboxes to list
            if self._base_options.get(CONF_RECURRENCE_TYPE) == "monthly_weekday":
                monthly_weekdays = []
                if user_input.get("monday_monthly"):
                    monthly_weekdays.append("Monday")
                if user_input.get("tuesday_monthly"):
                    monthly_weekdays.append("Tuesday")
                if user_input.get("wednesday_monthly"):
                    monthly_weekdays.append("Wednesday")
                if user_input.get("thursday_monthly"):
                    monthly_weekdays.append("Thursday")
                if user_input.get("friday_monthly"):
                    monthly_weekdays.append("Friday")
                if user_input.get("saturday_monthly"):
                    monthly_weekdays.append("Saturday")
                if user_input.get("sunday_monthly"):
                    monthly_weekdays.append("Sunday")

                # Remove checkbox keys and add monthly_weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday_monthly",
                        "tuesday_monthly",
                        "wednesday_monthly",
                        "thursday_monthly",
                        "friday_monthly",
                        "saturday_monthly",
                        "sunday_monthly",
                    ]
                }
                if monthly_weekdays:
                    user_input["monthly_weekdays"] = monthly_weekdays

            data = {**self._base_options, **user_input}
            return self.async_create_entry(title="", data=data)

        recurrence_type = self._base_options[CONF_RECURRENCE_TYPE]
        schema_dict: dict = {}

        if recurrence_type == "daily":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "days",
                        "mode": "box",
                        "translation_key": "occur_every_days",
                    }
                )
            )

        elif recurrence_type == "weekly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "weeks",
                        "mode": "box",
                        "translation_key": "occur_every_weeks",
                    }
                )
            )
            schema_dict[vol.Optional("monday", default=False)] = bool
            schema_dict[vol.Optional("tuesday", default=False)] = bool
            schema_dict[vol.Optional("wednesday", default=False)] = bool
            schema_dict[vol.Optional("thursday", default=False)] = bool
            schema_dict[vol.Optional("friday", default=False)] = bool
            schema_dict[vol.Optional("saturday", default=False)] = bool
            schema_dict[vol.Optional("sunday", default=False)] = bool

        elif recurrence_type == "monthly":
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weekdays", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                            "Sunday",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weeks", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "1st",
                            "2nd",
                            "3rd",
                            "4th",
                            "Last",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "months",
                        "mode": "box",
                        "translation_key": "occur_every_months",
                    }
                )
            )

        elif recurrence_type == "yearly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "years",
                        "mode": "box",
                        "translation_key": "occur_every_years",
                    }
                )
            )
            schema_dict[vol.Required(CONF_MONTH, default=1)] = selector.SelectSelector(
                {
                    "options": [
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December",
                    ],
                }
            )
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

        # Always put start date last
        schema_dict[vol.Required(CONF_START_DATE, default=date.today().isoformat())] = (
            selector.DateSelector()
        )

        return self.async_show_form(
            step_id="recurrence", data_schema=vol.Schema(schema_dict)
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return ChoreTrackerOptionsFlowHandler(config_entry)


class ChoreTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle editing options after a chore has been created."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry
        self._base_options: dict = {}

    async def async_step_init(self, user_input=None):
        """Page 1: Basic options."""
        if user_input is not None:
            recurrence_type = user_input[CONF_RECURRENCE_TYPE]
            self._base_options = {
                CONF_RECURRENCE_TYPE: recurrence_type,
                CONF_ICON: user_input.get(CONF_ICON, "mdi:broom"),
                CONF_PERSON_ENTITY: user_input.get(CONF_PERSON_ENTITY),
            }

            if recurrence_type == "manual":
                data = {
                    **self._base_options,
                    CONF_START_DATE: date.today().isoformat(),
                    "due_days": 9999,
                }
                return self.async_create_entry(title="", data=data)

            return await self.async_step_recurrence()

        options = self._entry.options or {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_RECURRENCE_TYPE,
                    default=options.get(CONF_RECURRENCE_TYPE, "daily"),
                ): vol.In(
                    {
                        "manual": "Manual",
                        "daily": "Daily",
                        "weekly": "Weekly",
                        "monthly_date": "Monthly - date of month",
                        "monthly_weekday": "Monthly - day of week",
                        "yearly": "Yearly",
                    }
                ),
                vol.Optional(
                    CONF_ICON, default=options.get(CONF_ICON, "mdi:broom")
                ): selector.IconSelector(),
                vol.Optional(
                    CONF_PERSON_ENTITY, default=options.get(CONF_PERSON_ENTITY)
                ): selector.EntitySelector({"domain": "person"}),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_recurrence(self, user_input=None):
        """Page 2: Recurrence pattern options."""
        if user_input is not None:
            # Convert checkbox booleans to weekdays list
            if (
                user_input.get(CONF_RECURRENCE_TYPE) == "weekly"
                or self._base_options.get(CONF_RECURRENCE_TYPE) == "weekly"
            ):
                weekdays = []
                if user_input.get("monday"):
                    weekdays.append("Monday")
                if user_input.get("tuesday"):
                    weekdays.append("Tuesday")
                if user_input.get("wednesday"):
                    weekdays.append("Wednesday")
                if user_input.get("thursday"):
                    weekdays.append("Thursday")
                if user_input.get("friday"):
                    weekdays.append("Friday")
                if user_input.get("saturday"):
                    weekdays.append("Saturday")
                if user_input.get("sunday"):
                    weekdays.append("Sunday")

                # Remove checkbox keys and add weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                    ]
                }
                if weekdays:
                    user_input["weekdays"] = weekdays

            # Convert monthly_weekday checkboxes to list
            if self._base_options.get(CONF_RECURRENCE_TYPE) == "monthly_weekday":
                monthly_weekdays = []
                if user_input.get("monday_monthly"):
                    monthly_weekdays.append("Monday")
                if user_input.get("tuesday_monthly"):
                    monthly_weekdays.append("Tuesday")
                if user_input.get("wednesday_monthly"):
                    monthly_weekdays.append("Wednesday")
                if user_input.get("thursday_monthly"):
                    monthly_weekdays.append("Thursday")
                if user_input.get("friday_monthly"):
                    monthly_weekdays.append("Friday")
                if user_input.get("saturday_monthly"):
                    monthly_weekdays.append("Saturday")
                if user_input.get("sunday_monthly"):
                    monthly_weekdays.append("Sunday")

                # Remove checkbox keys and add monthly_weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday_monthly",
                        "tuesday_monthly",
                        "wednesday_monthly",
                        "thursday_monthly",
                        "friday_monthly",
                        "saturday_monthly",
                        "sunday_monthly",
                    ]
                }
                if monthly_weekdays:
                    user_input["monthly_weekdays"] = monthly_weekdays

            data = {**self._base_options, **user_input}
            return self.async_create_entry(title="", data=data)

        recurrence_type = self._base_options[CONF_RECURRENCE_TYPE]
        schema_dict: dict = {}

        if recurrence_type == "daily":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "days",
                        "mode": "box",
                        "translation_key": "occur_every_days",
                    }
                )
            )

        elif recurrence_type == "weekly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "weeks",
                        "mode": "box",
                        "translation_key": "occur_every_weeks",
                    }
                )
            )
            schema_dict[vol.Optional("monday", default=False)] = bool
            schema_dict[vol.Optional("tuesday", default=False)] = bool
            schema_dict[vol.Optional("wednesday", default=False)] = bool
            schema_dict[vol.Optional("thursday", default=False)] = bool
            schema_dict[vol.Optional("friday", default=False)] = bool
            schema_dict[vol.Optional("saturday", default=False)] = bool
            schema_dict[vol.Optional("sunday", default=False)] = bool

        elif recurrence_type == "monthly":
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weekdays", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                            "Sunday",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weeks", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "1st",
                            "2nd",
                            "3rd",
                            "4th",
                            "Last",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "months",
                        "mode": "box",
                        "translation_key": "occur_every_months",
                    }
                )
            )

        elif recurrence_type == "yearly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "years",
                        "mode": "box",
                        "translation_key": "occur_every_years",
                    }
                )
            )
            schema_dict[vol.Required(CONF_MONTH, default=1)] = selector.SelectSelector(
                {
                    "options": [
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December",
                    ],
                }
            )
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

        # Always put start date last
        schema_dict[vol.Required(CONF_START_DATE, default=date.today().isoformat())] = (
            selector.DateSelector()
        )

        return self.async_show_form(
            step_id="recurrence", data_schema=vol.Schema(schema_dict)
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return ChoreTrackerOptionsFlowHandler(config_entry)


class ChoreTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle editing options after a chore has been created."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry
        self._base_options: dict = {}

    async def async_step_init(self, user_input=None):
        """Page 1: Basic options."""
        if user_input is not None:
            recurrence_type = user_input[CONF_RECURRENCE_TYPE]
            self._base_options = {
                CONF_RECURRENCE_TYPE: recurrence_type,
                CONF_ICON: user_input.get(CONF_ICON, "mdi:broom"),
                CONF_PERSON_ENTITY: user_input.get(CONF_PERSON_ENTITY),
            }

            if recurrence_type == "manual":
                data = {
                    **self._base_options,
                    CONF_START_DATE: date.today().isoformat(),
                    "due_days": 9999,
                }
                return self.async_create_entry(title="", data=data)

            return await self.async_step_recurrence()

        options = self._entry.options or {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_RECURRENCE_TYPE,
                    default=options.get(CONF_RECURRENCE_TYPE, "daily"),
                ): vol.In(
                    {
                        "manual": "Manual",
                        "daily": "Daily",
                        "weekly": "Weekly",
                        "monthly_date": "Monthly - date of month",
                        "monthly_weekday": "Monthly - day of week",
                        "yearly": "Yearly",
                    }
                ),
                vol.Optional(
                    CONF_ICON, default=options.get(CONF_ICON, "mdi:broom")
                ): selector.IconSelector(),
                vol.Optional(
                    CONF_PERSON_ENTITY, default=options.get(CONF_PERSON_ENTITY)
                ): selector.EntitySelector({"domain": "person"}),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_recurrence(self, user_input=None):
        """Page 2: Recurrence pattern options."""
        if user_input is not None:
            # Convert checkbox booleans to weekdays list
            if (
                user_input.get(CONF_RECURRENCE_TYPE) == "weekly"
                or self._base_options.get(CONF_RECURRENCE_TYPE) == "weekly"
            ):
                weekdays = []
                if user_input.get("monday"):
                    weekdays.append("Monday")
                if user_input.get("tuesday"):
                    weekdays.append("Tuesday")
                if user_input.get("wednesday"):
                    weekdays.append("Wednesday")
                if user_input.get("thursday"):
                    weekdays.append("Thursday")
                if user_input.get("friday"):
                    weekdays.append("Friday")
                if user_input.get("saturday"):
                    weekdays.append("Saturday")
                if user_input.get("sunday"):
                    weekdays.append("Sunday")

                # Remove checkbox keys and add weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                    ]
                }
                if weekdays:
                    user_input["weekdays"] = weekdays

            # Convert monthly_weekday checkboxes to list
            if self._base_options.get(CONF_RECURRENCE_TYPE) == "monthly_weekday":
                monthly_weekdays = []
                if user_input.get("monday_monthly"):
                    monthly_weekdays.append("Monday")
                if user_input.get("tuesday_monthly"):
                    monthly_weekdays.append("Tuesday")
                if user_input.get("wednesday_monthly"):
                    monthly_weekdays.append("Wednesday")
                if user_input.get("thursday_monthly"):
                    monthly_weekdays.append("Thursday")
                if user_input.get("friday_monthly"):
                    monthly_weekdays.append("Friday")
                if user_input.get("saturday_monthly"):
                    monthly_weekdays.append("Saturday")
                if user_input.get("sunday_monthly"):
                    monthly_weekdays.append("Sunday")

                # Remove checkbox keys and add monthly_weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday_monthly",
                        "tuesday_monthly",
                        "wednesday_monthly",
                        "thursday_monthly",
                        "friday_monthly",
                        "saturday_monthly",
                        "sunday_monthly",
                    ]
                }
                if monthly_weekdays:
                    user_input["monthly_weekdays"] = monthly_weekdays

            data = {**self._base_options, **user_input}
            return self.async_create_entry(title="", data=data)

        recurrence_type = self._base_options[CONF_RECURRENCE_TYPE]
        schema_dict: dict = {}

        if recurrence_type == "daily":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "days",
                        "mode": "box",
                        "translation_key": "occur_every_days",
                    }
                )
            )

        elif recurrence_type == "weekly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "weeks",
                        "mode": "box",
                        "translation_key": "occur_every_weeks",
                    }
                )
            )
            schema_dict[vol.Optional("monday", default=False)] = bool
            schema_dict[vol.Optional("tuesday", default=False)] = bool
            schema_dict[vol.Optional("wednesday", default=False)] = bool
            schema_dict[vol.Optional("thursday", default=False)] = bool
            schema_dict[vol.Optional("friday", default=False)] = bool
            schema_dict[vol.Optional("saturday", default=False)] = bool
            schema_dict[vol.Optional("sunday", default=False)] = bool

        elif recurrence_type == "monthly":
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weekdays", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                            "Sunday",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weeks", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "1st",
                            "2nd",
                            "3rd",
                            "4th",
                            "Last",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "months",
                        "mode": "box",
                        "translation_key": "occur_every_months",
                    }
                )
            )

        elif recurrence_type == "yearly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "years",
                        "mode": "box",
                        "translation_key": "occur_every_years",
                    }
                )
            )
            schema_dict[vol.Required(CONF_MONTH, default=1)] = selector.SelectSelector(
                {
                    "options": [
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December",
                    ],
                }
            )
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

        # Always put start date last
        schema_dict[vol.Required(CONF_START_DATE, default=date.today().isoformat())] = (
            selector.DateSelector()
        )

        return self.async_show_form(
            step_id="recurrence", data_schema=vol.Schema(schema_dict)
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return ChoreTrackerOptionsFlowHandler(config_entry)


class ChoreTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle editing options after a chore has been created."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry
        self._base_options: dict = {}

    async def async_step_init(self, user_input=None):
        """Page 1: Basic options."""
        if user_input is not None:
            recurrence_type = user_input[CONF_RECURRENCE_TYPE]
            self._base_options = {
                CONF_RECURRENCE_TYPE: recurrence_type,
                CONF_ICON: user_input.get(CONF_ICON, "mdi:broom"),
                CONF_PERSON_ENTITY: user_input.get(CONF_PERSON_ENTITY),
            }

            if recurrence_type == "manual":
                data = {
                    **self._base_options,
                    CONF_START_DATE: date.today().isoformat(),
                    "due_days": 9999,
                }
                return self.async_create_entry(title="", data=data)

            return await self.async_step_recurrence()

        options = self._entry.options or {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_RECURRENCE_TYPE,
                    default=options.get(CONF_RECURRENCE_TYPE, "daily"),
                ): vol.In(
                    {
                        "manual": "Manual",
                        "daily": "Daily",
                        "weekly": "Weekly",
                        "monthly_date": "Monthly - date of month",
                        "monthly_weekday": "Monthly - day of week",
                        "yearly": "Yearly",
                    }
                ),
                vol.Optional(
                    CONF_ICON, default=options.get(CONF_ICON, "mdi:broom")
                ): selector.IconSelector(),
                vol.Optional(
                    CONF_PERSON_ENTITY, default=options.get(CONF_PERSON_ENTITY)
                ): selector.EntitySelector({"domain": "person"}),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_recurrence(self, user_input=None):
        """Page 2: Recurrence pattern options."""
        if user_input is not None:
            # Convert checkbox booleans to weekdays list
            if (
                user_input.get(CONF_RECURRENCE_TYPE) == "weekly"
                or self._base_options.get(CONF_RECURRENCE_TYPE) == "weekly"
            ):
                weekdays = []
                if user_input.get("monday"):
                    weekdays.append("Monday")
                if user_input.get("tuesday"):
                    weekdays.append("Tuesday")
                if user_input.get("wednesday"):
                    weekdays.append("Wednesday")
                if user_input.get("thursday"):
                    weekdays.append("Thursday")
                if user_input.get("friday"):
                    weekdays.append("Friday")
                if user_input.get("saturday"):
                    weekdays.append("Saturday")
                if user_input.get("sunday"):
                    weekdays.append("Sunday")

                # Remove checkbox keys and add weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                    ]
                }
                if weekdays:
                    user_input["weekdays"] = weekdays

            # Convert monthly_weekday checkboxes to list
            if self._base_options.get(CONF_RECURRENCE_TYPE) == "monthly_weekday":
                monthly_weekdays = []
                if user_input.get("monday_monthly"):
                    monthly_weekdays.append("Monday")
                if user_input.get("tuesday_monthly"):
                    monthly_weekdays.append("Tuesday")
                if user_input.get("wednesday_monthly"):
                    monthly_weekdays.append("Wednesday")
                if user_input.get("thursday_monthly"):
                    monthly_weekdays.append("Thursday")
                if user_input.get("friday_monthly"):
                    monthly_weekdays.append("Friday")
                if user_input.get("saturday_monthly"):
                    monthly_weekdays.append("Saturday")
                if user_input.get("sunday_monthly"):
                    monthly_weekdays.append("Sunday")

                # Remove checkbox keys and add monthly_weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday_monthly",
                        "tuesday_monthly",
                        "wednesday_monthly",
                        "thursday_monthly",
                        "friday_monthly",
                        "saturday_monthly",
                        "sunday_monthly",
                    ]
                }
                if monthly_weekdays:
                    user_input["monthly_weekdays"] = monthly_weekdays

            data = {**self._base_options, **user_input}
            return self.async_create_entry(title="", data=data)

        recurrence_type = self._base_options[CONF_RECURRENCE_TYPE]
        schema_dict: dict = {}

        if recurrence_type == "daily":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "days",
                        "mode": "box",
                        "translation_key": "occur_every_days",
                    }
                )
            )

        elif recurrence_type == "weekly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "weeks",
                        "mode": "box",
                        "translation_key": "occur_every_weeks",
                    }
                )
            )
            schema_dict[vol.Optional("monday", default=False)] = bool
            schema_dict[vol.Optional("tuesday", default=False)] = bool
            schema_dict[vol.Optional("wednesday", default=False)] = bool
            schema_dict[vol.Optional("thursday", default=False)] = bool
            schema_dict[vol.Optional("friday", default=False)] = bool
            schema_dict[vol.Optional("saturday", default=False)] = bool
            schema_dict[vol.Optional("sunday", default=False)] = bool

        elif recurrence_type == "monthly":
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weekdays", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                            "Sunday",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weeks", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "1st",
                            "2nd",
                            "3rd",
                            "4th",
                            "Last",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "months",
                        "mode": "box",
                        "translation_key": "occur_every_months",
                    }
                )
            )

        elif recurrence_type == "yearly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "years",
                        "mode": "box",
                        "translation_key": "occur_every_years",
                    }
                )
            )
            schema_dict[vol.Required(CONF_MONTH, default=1)] = selector.SelectSelector(
                {
                    "options": [
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December",
                    ],
                }
            )
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

        # Always put start date last
        schema_dict[vol.Required(CONF_START_DATE, default=date.today().isoformat())] = (
            selector.DateSelector()
        )

        return self.async_show_form(
            step_id="recurrence", data_schema=vol.Schema(schema_dict)
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return ChoreTrackerOptionsFlowHandler(config_entry)


class ChoreTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle editing options after a chore has been created."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry
        self._base_options: dict = {}

    async def async_step_init(self, user_input=None):
        """Page 1: Basic options."""
        if user_input is not None:
            recurrence_type = user_input[CONF_RECURRENCE_TYPE]
            self._base_options = {
                CONF_RECURRENCE_TYPE: recurrence_type,
                CONF_ICON: user_input.get(CONF_ICON, "mdi:broom"),
                CONF_PERSON_ENTITY: user_input.get(CONF_PERSON_ENTITY),
            }

            if recurrence_type == "manual":
                data = {
                    **self._base_options,
                    CONF_START_DATE: date.today().isoformat(),
                    "due_days": 9999,
                }
                return self.async_create_entry(title="", data=data)

            return await self.async_step_recurrence()

        options = self._entry.options or {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_RECURRENCE_TYPE,
                    default=options.get(CONF_RECURRENCE_TYPE, "daily"),
                ): vol.In(
                    {
                        "manual": "Manual",
                        "daily": "Daily",
                        "weekly": "Weekly",
                        "monthly_date": "Monthly - date of month",
                        "monthly_weekday": "Monthly - day of week",
                        "yearly": "Yearly",
                    }
                ),
                vol.Optional(
                    CONF_ICON, default=options.get(CONF_ICON, "mdi:broom")
                ): selector.IconSelector(),
                vol.Optional(
                    CONF_PERSON_ENTITY, default=options.get(CONF_PERSON_ENTITY)
                ): selector.EntitySelector({"domain": "person"}),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_recurrence(self, user_input=None):
        """Page 2: Recurrence pattern options."""
        if user_input is not None:
            # Convert checkbox booleans to weekdays list
            if (
                user_input.get(CONF_RECURRENCE_TYPE) == "weekly"
                or self._base_options.get(CONF_RECURRENCE_TYPE) == "weekly"
            ):
                weekdays = []
                if user_input.get("monday"):
                    weekdays.append("Monday")
                if user_input.get("tuesday"):
                    weekdays.append("Tuesday")
                if user_input.get("wednesday"):
                    weekdays.append("Wednesday")
                if user_input.get("thursday"):
                    weekdays.append("Thursday")
                if user_input.get("friday"):
                    weekdays.append("Friday")
                if user_input.get("saturday"):
                    weekdays.append("Saturday")
                if user_input.get("sunday"):
                    weekdays.append("Sunday")

                # Remove checkbox keys and add weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                    ]
                }
                if weekdays:
                    user_input["weekdays"] = weekdays

            # Convert monthly_weekday checkboxes to list
            if self._base_options.get(CONF_RECURRENCE_TYPE) == "monthly_weekday":
                monthly_weekdays = []
                if user_input.get("monday_monthly"):
                    monthly_weekdays.append("Monday")
                if user_input.get("tuesday_monthly"):
                    monthly_weekdays.append("Tuesday")
                if user_input.get("wednesday_monthly"):
                    monthly_weekdays.append("Wednesday")
                if user_input.get("thursday_monthly"):
                    monthly_weekdays.append("Thursday")
                if user_input.get("friday_monthly"):
                    monthly_weekdays.append("Friday")
                if user_input.get("saturday_monthly"):
                    monthly_weekdays.append("Saturday")
                if user_input.get("sunday_monthly"):
                    monthly_weekdays.append("Sunday")

                # Remove checkbox keys and add monthly_weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday_monthly",
                        "tuesday_monthly",
                        "wednesday_monthly",
                        "thursday_monthly",
                        "friday_monthly",
                        "saturday_monthly",
                        "sunday_monthly",
                    ]
                }
                if monthly_weekdays:
                    user_input["monthly_weekdays"] = monthly_weekdays

            data = {**self._base_options, **user_input}
            return self.async_create_entry(title="", data=data)

        recurrence_type = self._base_options[CONF_RECURRENCE_TYPE]
        schema_dict: dict = {}

        if recurrence_type == "daily":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "days",
                        "mode": "box",
                        "translation_key": "occur_every_days",
                    }
                )
            )

        elif recurrence_type == "weekly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "weeks",
                        "mode": "box",
                        "translation_key": "occur_every_weeks",
                    }
                )
            )
            schema_dict[vol.Optional("monday", default=False)] = bool
            schema_dict[vol.Optional("tuesday", default=False)] = bool
            schema_dict[vol.Optional("wednesday", default=False)] = bool
            schema_dict[vol.Optional("thursday", default=False)] = bool
            schema_dict[vol.Optional("friday", default=False)] = bool
            schema_dict[vol.Optional("saturday", default=False)] = bool
            schema_dict[vol.Optional("sunday", default=False)] = bool

        elif recurrence_type == "monthly":
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weekdays", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                            "Sunday",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weeks", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "1st",
                            "2nd",
                            "3rd",
                            "4th",
                            "Last",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "months",
                        "mode": "box",
                        "translation_key": "occur_every_months",
                    }
                )
            )

        elif recurrence_type == "yearly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "years",
                        "mode": "box",
                        "translation_key": "occur_every_years",
                    }
                )
            )
            schema_dict[vol.Required(CONF_MONTH, default=1)] = selector.SelectSelector(
                {
                    "options": [
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December",
                    ],
                }
            )
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

        # Always put start date last
        schema_dict[vol.Required(CONF_START_DATE, default=date.today().isoformat())] = (
            selector.DateSelector()
        )

        return self.async_show_form(
            step_id="recurrence", data_schema=vol.Schema(schema_dict)
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return ChoreTrackerOptionsFlowHandler(config_entry)


class ChoreTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle editing options after a chore has been created."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry
        self._base_options: dict = {}

    async def async_step_init(self, user_input=None):
        """Page 1: Basic options."""
        if user_input is not None:
            recurrence_type = user_input[CONF_RECURRENCE_TYPE]
            self._base_options = {
                CONF_RECURRENCE_TYPE: recurrence_type,
                CONF_ICON: user_input.get(CONF_ICON, "mdi:broom"),
                CONF_PERSON_ENTITY: user_input.get(CONF_PERSON_ENTITY),
            }

            if recurrence_type == "manual":
                data = {
                    **self._base_options,
                    CONF_START_DATE: date.today().isoformat(),
                    "due_days": 9999,
                }
                return self.async_create_entry(title="", data=data)

            return await self.async_step_recurrence()

        options = self._entry.options or {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_RECURRENCE_TYPE,
                    default=options.get(CONF_RECURRENCE_TYPE, "daily"),
                ): vol.In(
                    {
                        "manual": "Manual",
                        "daily": "Daily",
                        "weekly": "Weekly",
                        "monthly_date": "Monthly - date of month",
                        "monthly_weekday": "Monthly - day of week",
                        "yearly": "Yearly",
                    }
                ),
                vol.Optional(
                    CONF_ICON, default=options.get(CONF_ICON, "mdi:broom")
                ): selector.IconSelector(),
                vol.Optional(
                    CONF_PERSON_ENTITY, default=options.get(CONF_PERSON_ENTITY)
                ): selector.EntitySelector({"domain": "person"}),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_recurrence(self, user_input=None):
        """Page 2: Recurrence pattern options."""
        if user_input is not None:
            # Convert checkbox booleans to weekdays list
            if (
                user_input.get(CONF_RECURRENCE_TYPE) == "weekly"
                or self._base_options.get(CONF_RECURRENCE_TYPE) == "weekly"
            ):
                weekdays = []
                if user_input.get("monday"):
                    weekdays.append("Monday")
                if user_input.get("tuesday"):
                    weekdays.append("Tuesday")
                if user_input.get("wednesday"):
                    weekdays.append("Wednesday")
                if user_input.get("thursday"):
                    weekdays.append("Thursday")
                if user_input.get("friday"):
                    weekdays.append("Friday")
                if user_input.get("saturday"):
                    weekdays.append("Saturday")
                if user_input.get("sunday"):
                    weekdays.append("Sunday")

                # Remove checkbox keys and add weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                    ]
                }
                if weekdays:
                    user_input["weekdays"] = weekdays

            # Convert monthly_weekday checkboxes to list
            if self._base_options.get(CONF_RECURRENCE_TYPE) == "monthly_weekday":
                monthly_weekdays = []
                if user_input.get("monday_monthly"):
                    monthly_weekdays.append("Monday")
                if user_input.get("tuesday_monthly"):
                    monthly_weekdays.append("Tuesday")
                if user_input.get("wednesday_monthly"):
                    monthly_weekdays.append("Wednesday")
                if user_input.get("thursday_monthly"):
                    monthly_weekdays.append("Thursday")
                if user_input.get("friday_monthly"):
                    monthly_weekdays.append("Friday")
                if user_input.get("saturday_monthly"):
                    monthly_weekdays.append("Saturday")
                if user_input.get("sunday_monthly"):
                    monthly_weekdays.append("Sunday")

                # Remove checkbox keys and add monthly_weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday_monthly",
                        "tuesday_monthly",
                        "wednesday_monthly",
                        "thursday_monthly",
                        "friday_monthly",
                        "saturday_monthly",
                        "sunday_monthly",
                    ]
                }
                if monthly_weekdays:
                    user_input["monthly_weekdays"] = monthly_weekdays

            data = {**self._base_options, **user_input}
            return self.async_create_entry(title="", data=data)

        recurrence_type = self._base_options[CONF_RECURRENCE_TYPE]
        schema_dict: dict = {}

        if recurrence_type == "daily":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "days",
                        "mode": "box",
                        "translation_key": "occur_every_days",
                    }
                )
            )

        elif recurrence_type == "weekly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "weeks",
                        "mode": "box",
                        "translation_key": "occur_every_weeks",
                    }
                )
            )
            schema_dict[vol.Optional("monday", default=False)] = bool
            schema_dict[vol.Optional("tuesday", default=False)] = bool
            schema_dict[vol.Optional("wednesday", default=False)] = bool
            schema_dict[vol.Optional("thursday", default=False)] = bool
            schema_dict[vol.Optional("friday", default=False)] = bool
            schema_dict[vol.Optional("saturday", default=False)] = bool
            schema_dict[vol.Optional("sunday", default=False)] = bool

        elif recurrence_type == "monthly":
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weekdays", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                            "Sunday",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weeks", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "1st",
                            "2nd",
                            "3rd",
                            "4th",
                            "Last",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "months",
                        "mode": "box",
                        "translation_key": "occur_every_months",
                    }
                )
            )

        elif recurrence_type == "yearly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "years",
                        "mode": "box",
                        "translation_key": "occur_every_years",
                    }
                )
            )
            schema_dict[vol.Required(CONF_MONTH, default=1)] = selector.SelectSelector(
                {
                    "options": [
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December",
                    ],
                }
            )
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

        # Always put start date last
        schema_dict[vol.Required(CONF_START_DATE, default=date.today().isoformat())] = (
            selector.DateSelector()
        )

        return self.async_show_form(
            step_id="recurrence", data_schema=vol.Schema(schema_dict)
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return ChoreTrackerOptionsFlowHandler(config_entry)


class ChoreTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle editing options after a chore has been created."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry
        self._base_options: dict = {}

    async def async_step_init(self, user_input=None):
        """Page 1: Basic options."""
        if user_input is not None:
            recurrence_type = user_input[CONF_RECURRENCE_TYPE]
            self._base_options = {
                CONF_RECURRENCE_TYPE: recurrence_type,
                CONF_ICON: user_input.get(CONF_ICON, "mdi:broom"),
                CONF_PERSON_ENTITY: user_input.get(CONF_PERSON_ENTITY),
            }

            if recurrence_type == "manual":
                data = {
                    **self._base_options,
                    CONF_START_DATE: date.today().isoformat(),
                    "due_days": 9999,
                }
                return self.async_create_entry(title="", data=data)

            return await self.async_step_recurrence()

        options = self._entry.options or {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_RECURRENCE_TYPE,
                    default=options.get(CONF_RECURRENCE_TYPE, "daily"),
                ): vol.In(
                    {
                        "manual": "Manual",
                        "daily": "Daily",
                        "weekly": "Weekly",
                        "monthly_date": "Monthly - date of month",
                        "monthly_weekday": "Monthly - day of week",
                        "yearly": "Yearly",
                    }
                ),
                vol.Optional(
                    CONF_ICON, default=options.get(CONF_ICON, "mdi:broom")
                ): selector.IconSelector(),
                vol.Optional(
                    CONF_PERSON_ENTITY, default=options.get(CONF_PERSON_ENTITY)
                ): selector.EntitySelector({"domain": "person"}),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_recurrence(self, user_input=None):
        """Page 2: Recurrence pattern options."""
        if user_input is not None:
            # Convert checkbox booleans to weekdays list
            if (
                user_input.get(CONF_RECURRENCE_TYPE) == "weekly"
                or self._base_options.get(CONF_RECURRENCE_TYPE) == "weekly"
            ):
                weekdays = []
                if user_input.get("monday"):
                    weekdays.append("Monday")
                if user_input.get("tuesday"):
                    weekdays.append("Tuesday")
                if user_input.get("wednesday"):
                    weekdays.append("Wednesday")
                if user_input.get("thursday"):
                    weekdays.append("Thursday")
                if user_input.get("friday"):
                    weekdays.append("Friday")
                if user_input.get("saturday"):
                    weekdays.append("Saturday")
                if user_input.get("sunday"):
                    weekdays.append("Sunday")

                # Remove checkbox keys and add weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                    ]
                }
                if weekdays:
                    user_input["weekdays"] = weekdays

            # Convert monthly_weekday checkboxes to list
            if self._base_options.get(CONF_RECURRENCE_TYPE) == "monthly_weekday":
                monthly_weekdays = []
                if user_input.get("monday_monthly"):
                    monthly_weekdays.append("Monday")
                if user_input.get("tuesday_monthly"):
                    monthly_weekdays.append("Tuesday")
                if user_input.get("wednesday_monthly"):
                    monthly_weekdays.append("Wednesday")
                if user_input.get("thursday_monthly"):
                    monthly_weekdays.append("Thursday")
                if user_input.get("friday_monthly"):
                    monthly_weekdays.append("Friday")
                if user_input.get("saturday_monthly"):
                    monthly_weekdays.append("Saturday")
                if user_input.get("sunday_monthly"):
                    monthly_weekdays.append("Sunday")

                # Remove checkbox keys and add monthly_weekdays list
                user_input = {
                    k: v
                    for k, v in user_input.items()
                    if k
                    not in [
                        "monday_monthly",
                        "tuesday_monthly",
                        "wednesday_monthly",
                        "thursday_monthly",
                        "friday_monthly",
                        "saturday_monthly",
                        "sunday_monthly",
                    ]
                }
                if monthly_weekdays:
                    user_input["monthly_weekdays"] = monthly_weekdays

            data = {**self._base_options, **user_input}
            return self.async_create_entry(title="", data=data)

        recurrence_type = self._base_options[CONF_RECURRENCE_TYPE]
        schema_dict: dict = {}

        if recurrence_type == "daily":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "days",
                        "mode": "box",
                        "translation_key": "occur_every_days",
                    }
                )
            )

        elif recurrence_type == "weekly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "weeks",
                        "mode": "box",
                        "translation_key": "occur_every_weeks",
                    }
                )
            )
            schema_dict[vol.Optional("monday", default=False)] = bool
            schema_dict[vol.Optional("tuesday", default=False)] = bool
            schema_dict[vol.Optional("wednesday", default=False)] = bool
            schema_dict[vol.Optional("thursday", default=False)] = bool
            schema_dict[vol.Optional("friday", default=False)] = bool
            schema_dict[vol.Optional("saturday", default=False)] = bool
            schema_dict[vol.Optional("sunday", default=False)] = bool

        elif recurrence_type == "monthly":
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weekdays", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                            "Sunday",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Optional("monthly_weeks", default=[])] = (
                selector.SelectSelector(
                    {
                        "options": [
                            "1st",
                            "2nd",
                            "3rd",
                            "4th",
                            "Last",
                        ],
                        "multiple": True,
                    }
                )
            )

            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "months",
                        "mode": "box",
                        "translation_key": "occur_every_months",
                    }
                )
            )

        elif recurrence_type == "yearly":
            schema_dict[vol.Required(CONF_INTERVAL, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "step": 1,
                        "unit_of_measurement": "years",
                        "mode": "box",
                        "translation_key": "occur_every_years",
                    }
                )
            )
            schema_dict[vol.Required(CONF_MONTH, default=1)] = selector.SelectSelector(
                {
                    "options": [
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December",
                    ],
                }
            )
            schema_dict[vol.Required(CONF_DAY_OF_MONTH, default=1)] = (
                selector.NumberSelector(
                    {
                        "min": 1,
                        "max": 31,
                        "mode": "box",
                        "translation_key": "day_of_month",
                    }
                )
            )

        # Always put start date last
        schema_dict[vol.Required(CONF_START_DATE, default=date.today().isoformat())] = (
            selector.DateSelector()
        )

        return self.async_show_form(
            step_id="recurrence", data_schema=vol.Schema(schema_dict)
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return ChoreTrackerOptionsFlowHandler(config_entry)
