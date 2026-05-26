from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

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
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class MySuiviColisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title="My Suivi Colis",
                data=user_input,
                options={},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional(CONF_API_KEY, default=""): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=DEFAULT_SCAN_INTERVAL,
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            action = user_input.get("action")
            if action == "add":
                return await self.async_step_add_tracking()
            if action == "remove":
                return await self.async_step_remove_tracking()
            return await self.async_step_interval()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("action", default="interval"): vol.In({
                    "interval": "Modifier l'intervalle de mise à jour",
                    "add": "Ajouter un colis",
                    "remove": "Supprimer un colis",
                }),
            }),
        )

    async def async_step_interval(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL]},
            )

        return self.async_show_form(
            step_id="interval",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.data.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
            }),
        )

    async def async_step_add_tracking(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            entries = self.config_entry.options.get("tracking_entries", [])
            entries.append({
                CONF_TRACKING_NUMBER: user_input[CONF_TRACKING_NUMBER],
                CONF_CARRIER: user_input[CONF_CARRIER],
                CONF_NAME: user_input.get(CONF_NAME, ""),
                CONF_POSTAL_CODE: user_input.get(CONF_POSTAL_CODE, ""),
            })
            return self.async_create_entry(
                title="",
                data={**self.config_entry.options, "tracking_entries": entries},
            )

        return self.async_show_form(
            step_id="add_tracking",
            data_schema=vol.Schema({
                vol.Optional(CONF_NAME, default=""): str,
                vol.Required(CONF_TRACKING_NUMBER): str,
                vol.Required(CONF_CARRIER): vol.In(CARRIERS),
                vol.Optional(CONF_POSTAL_CODE, default=""): str,
            }),
        )

    async def async_step_remove_tracking(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        entries = self.config_entry.options.get("tracking_entries", [])

        if user_input is not None:
            indices = user_input.get("remove", [])
            entries = [
                e for i, e in enumerate(entries) if i not in indices
            ]
            return self.async_create_entry(
                title="",
                data={**self.config_entry.options, "tracking_entries": entries},
            )

        if not entries:
            return self.async_abort(reason="no_entries_to_remove")

        options_map = {
            str(i): f"{e.get(CONF_NAME, e[CONF_TRACKING_NUMBER])} ({CARRIERS.get(e[CONF_CARRIER], e[CONF_CARRIER])})"
            for i, e in enumerate(entries)
        }

        return self.async_show_form(
            step_id="remove_tracking",
            data_schema=vol.Schema({
                vol.Optional("remove"): cv.multi_select(options_map),
            }),
        )
