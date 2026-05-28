from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.helpers.service import async_register_admin_service
import voluptuous as vol

from .const import (
    CARRIERS,
    CONF_API_KEY,
    CONF_CARRIER,
    CONF_NAME,
    CONF_POSTAL_CODE,
    CONF_SCAN_INTERVAL,
    CONF_TRACKING_NUMBER,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .coordinator import MySuiviColisCoordinator

_LOGGER = logging.getLogger(__name__)

ADD_TRACKING_SCHEMA = vol.Schema({
    vol.Required(CONF_TRACKING_NUMBER): str,
    vol.Required(CONF_CARRIER): vol.In(CARRIERS),
    vol.Optional(CONF_NAME, default=""): str,
    vol.Optional(CONF_POSTAL_CODE, default=""): str,
})

REMOVE_TRACKING_SCHEMA = vol.Schema({
    vol.Required(CONF_TRACKING_NUMBER): str,
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE, title=DOMAIN, version="1.0.0")

    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored = await store.async_load()
    tracking_entries = stored if isinstance(stored, list) else []

    options_entries = entry.options.get("tracking_entries", [])
    existing_numbers = {e[CONF_TRACKING_NUMBER] for e in tracking_entries}
    for opt_entry in options_entries:
        if opt_entry[CONF_TRACKING_NUMBER] not in existing_numbers:
            tracking_entries.append(opt_entry)

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL) or entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = MySuiviColisCoordinator(
        hass,
        tracking_entries,
        scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "store": store,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    await _async_register_services(hass, entry, coordinator, store)

    www_path = hass.config.path("custom_components", DOMAIN, "www")
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(f"/{DOMAIN}", www_path, cache_headers=False)]
        )
    except Exception as exc:
        _LOGGER.warning("Static path already registered: %s", exc)

    await _async_register_card_resource(hass)

    return True


async def _async_register_card_resource(hass: HomeAssistant) -> None:
    try:
        lovelace = hass.data.get("lovelace")
        if lovelace is None:
            _LOGGER.debug("Lovelace not ready yet, skipping card auto-registration")
            return
        resources = lovelace.resources
        if resources is None:
            _LOGGER.debug("Lovelace resources not ready yet, skipping card auto-registration")
            return
        if asyncio.iscoroutinefunction(resources.async_items):
            items = await resources.async_items()
        else:
            items = resources.async_items() if callable(resources.async_items) else resources
        url = f"/{DOMAIN}/my-suivi-colis-card.js"
        if any(r.get("url") == url for r in items):
            _LOGGER.debug("Card resource already registered")
            return
        await resources.async_create_item({
            "res_type": "module",
            "url": url,
        })
        _LOGGER.info("Card resource auto-registered in Lovelace")
    except Exception as exc:
        _LOGGER.warning("Could not auto-register card resource: %s", exc)


async def _async_register_services(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: MySuiviColisCoordinator,
    store: Store,
) -> None:
    async def handle_add_tracking(call: ServiceCall) -> None:
        number = call.data[CONF_TRACKING_NUMBER]
        carrier = call.data[CONF_CARRIER]
        name = call.data.get(CONF_NAME, "")

        if any(e[CONF_TRACKING_NUMBER] == number for e in coordinator.tracking_entries):
            raise HomeAssistantError(f"Le numéro {number} est déjà suivi.")

        postal_code = call.data.get(CONF_POSTAL_CODE, "")
        new_entry = {
            CONF_TRACKING_NUMBER: number,
            CONF_CARRIER: carrier,
            CONF_NAME: name,
            CONF_POSTAL_CODE: postal_code,
        }
        entries = list(coordinator.tracking_entries)
        entries.append(new_entry)
        coordinator.tracking_entries = entries
        await store.async_save(entries)
        await hass.config_entries.async_reload(entry.entry_id)

    async def handle_remove_tracking(call: ServiceCall) -> None:
        number = call.data[CONF_TRACKING_NUMBER]
        entries = [
            e for e in coordinator.tracking_entries
            if e[CONF_TRACKING_NUMBER] != number
        ]
        if len(entries) == len(coordinator.tracking_entries):
            raise HomeAssistantError(f"Le numéro {number} n'est pas suivi.")
        coordinator.tracking_entries = entries
        await store.async_save(entries)
        await hass.config_entries.async_reload(entry.entry_id)

    async def handle_refresh(call: ServiceCall) -> None:
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN, "add_tracking", handle_add_tracking,
        schema=ADD_TRACKING_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, "remove_tracking", handle_remove_tracking,
        schema=REMOVE_TRACKING_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, "refresh", handle_refresh,
        schema=vol.Schema({}),
    )


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.services.async_remove(DOMAIN, "add_tracking")
        hass.services.async_remove(DOMAIN, "remove_tracking")
        hass.services.async_remove(DOMAIN, "refresh")
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Migrating from version %s", entry.version)
    if entry.version == 1:
        entry.version = 1
    return True
