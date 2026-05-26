from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CARRIER,
    ATTR_DESTINATION,
    ATTR_ESTIMATED_DELIVERY,
    ATTR_HISTORY,
    ATTR_LAST_UPDATE,
    ATTR_LATITUDE,
    ATTR_LOCATION,
    ATTR_LONGITUDE,
    ATTR_ORIGIN,
    ATTR_SENDER,
    ATTR_STATUS,
    ATTR_TIMESTAMP,
    ATTR_TRACKING_NUMBER,
    ATTR_WEIGHT,
    CARRIERS,
    DOMAIN,
    STATUS_FRIENDLY,
    STATUS_ICONS,
)
from .coordinator import MySuiviColisCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MySuiviColisCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities = []
    for entry in coordinator.tracking_entries:
        entities.append(
            SuiviColisSensor(
                coordinator,
                entry["tracking_number"],
                entry["carrier"],
                entry.get("name", entry["tracking_number"]),
            )
        )

    async_add_entities(entities)


class SuiviColisSensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator: MySuiviColisCoordinator,
        tracking_number: str,
        carrier: str,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._tracking_number = tracking_number
        self._carrier = carrier
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{tracking_number}"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._carrier_name = CARRIERS.get(carrier, carrier)

    @property
    def native_value(self) -> str | None:
        data = self.coordinator.data.get(self._tracking_number)
        if data is None:
            return None
        status = data.get("status")
        return STATUS_FRIENDLY.get(status, status)

    @property
    def icon(self) -> str:
        data = self.coordinator.data.get(self._tracking_number)
        if data is None:
            return "mdi:package-variant-closed"
        status = data.get("status")
        return STATUS_ICONS.get(status, "mdi:package-variant-closed")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data.get(self._tracking_number, {})
        attrs = {
            ATTR_TRACKING_NUMBER: self._tracking_number,
            ATTR_CARRIER: self._carrier_name,
            ATTR_STATUS: data.get("status"),
            ATTR_LOCATION: data.get("location"),
            ATTR_LATITUDE: data.get("latitude"),
            ATTR_LONGITUDE: data.get("longitude"),
            ATTR_TIMESTAMP: data.get("timestamp"),
            ATTR_LAST_UPDATE: data.get("last_update"),
            ATTR_ESTIMATED_DELIVERY: data.get("estimated_delivery"),
            ATTR_ORIGIN: data.get("origin"),
            ATTR_DESTINATION: data.get("destination"),
            ATTR_WEIGHT: data.get("weight"),
            ATTR_SENDER: data.get("sender"),
            ATTR_HISTORY: data.get("history", []),
        }
        return {k: v for k, v in attrs.items() if v is not None and v != []}

    @property
    def capabilities(self) -> dict[str, Any]:
        return {
            "tracking_number": self._tracking_number,
            "carrier": self._carrier_name,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data.get(self._tracking_number)
        if data and data.get("status_changed"):
            status = data.get("status")
            friendly = STATUS_FRIENDLY.get(status, status)
            self.hass.bus.fire(f"{DOMAIN}_status_changed", {
                "tracking_number": self._tracking_number,
                "carrier": self._carrier_name,
                "status": status,
                "status_friendly": friendly,
                "location": data.get("location"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
            })
        super()._handle_coordinator_update()
