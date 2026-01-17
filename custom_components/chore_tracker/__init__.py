"""The Chore Tracker integration."""

from __future__ import annotations

import logging
from datetime import datetime
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import Platform
from homeassistant.exceptions import ServiceValidationError
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

DOMAIN = "chore_tracker"
PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config) -> bool:
    """Set up the Chore Tracker integration (YAML not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Chore Tracker from a config entry."""
    _LOGGER.debug("Setting up Chore Tracker entry_id=%s", entry.entry_id)

    hass.data.setdefault(DOMAIN, {})

    # Forward setup to sensor.py
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def async_handle_complete_chore(call: ServiceCall) -> None:
        """Handle the complete_chore service call."""
        entity_id = call.data.get("entity_id")
        entity = hass.data[DOMAIN].get(entity_id)
        if entity:
            _LOGGER.debug("Completing chore for entity_id=%s", entity_id)
            await entity.async_complete()
        else:
            _LOGGER.warning("No chore entity found for entity_id=%s", entity_id)
            raise ServiceValidationError(
                f"Entity {entity_id} not found",
                translation_domain=DOMAIN,
                translation_key="entity_not_found",
            )

    async def async_handle_set_due_date(call: ServiceCall) -> None:
        """Handle the set_due_date service call."""
        entity_id = call.data.get("entity_id")
        due_date_input = call.data.get("due_date")

        entity = hass.data[DOMAIN].get(entity_id)
        if not entity:
            _LOGGER.warning("No chore entity found for entity_id=%s", entity_id)
            raise ServiceValidationError(
                f"Entity {entity_id} not found",
                translation_domain=DOMAIN,
                translation_key="entity_not_found",
            )

        try:
            # Handle different input types
            if isinstance(due_date_input, str):
                # Parse string to date
                due_date = datetime.fromisoformat(due_date_input).date()
            elif isinstance(due_date_input, datetime):
                # Extract date from datetime
                due_date = due_date_input.date()
            else:
                # Assume it's already a date object
                due_date = due_date_input

            _LOGGER.debug(
                "Setting due date for entity_id=%s to %s", entity_id, due_date
            )
            await entity.async_set_due_date(due_date)
        except (ValueError, TypeError, AttributeError) as err:
            _LOGGER.error("Invalid date format: %s", due_date_input)
            raise ServiceValidationError(
                f"Invalid date format: {due_date_input}",
                translation_domain=DOMAIN,
                translation_key="invalid_date_format",
            ) from err

    hass.services.async_register(
        DOMAIN,
        "complete_chore",
        async_handle_complete_chore,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_id,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        "set_due_date",
        async_handle_set_due_date,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_id,
                vol.Required("due_date"): cv.date,
            }
        ),
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Chore Tracker config entry."""
    _LOGGER.debug("Unloading Chore Tracker entry_id=%s", entry.entry_id)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(DOMAIN, None)
    return unload_ok
