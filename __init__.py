"""The Chore Tracker integration."""

from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

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

    async def async_handle_complete_chore(call):
        entity_id = call.data.get("entity_id")
        entity = hass.data[DOMAIN].get(entity_id)
        if entity:
            _LOGGER.debug("Completing chore for entity_id=%s", entity_id)
            await entity.async_complete()
        else:
            _LOGGER.warning("No chore entity found for entity_id=%s", entity_id)

    hass.services.async_register(
        DOMAIN,
        "complete_chore",
        async_handle_complete_chore,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Chore Tracker config entry."""
    _LOGGER.debug("Unloading Chore Tracker entry_id=%s", entry.entry_id)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(DOMAIN, None)
    return unload_ok
