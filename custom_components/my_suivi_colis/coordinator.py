from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .helpers import get_tracker

_LOGGER = logging.getLogger(__name__)


class MySuiviColisCoordinator(DataUpdateCoordinator):
    def __init__(
        self,
        hass: HomeAssistant,
        tracking_entries: list[dict[str, str]],
        scan_interval: int = 30,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval),
        )
        self.tracking_entries = tracking_entries
        self.data: dict[str, dict[str, Any]] = {}

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for entry in self.tracking_entries:
            number = entry["tracking_number"]
            carrier = entry["carrier"]
            try:
                tracker = get_tracker(carrier)
                data = await tracker.track(number, entry=entry)
                old_data = self.data.get(number, {})
                old_status = old_data.get("status")
                new_status = data.get("status")
                data["previous_status"] = old_status
                data["status_changed"] = old_status != new_status
                result[number] = data
            except Exception as err:
                _LOGGER.error("Error tracking %s (%s): %s", number, carrier, err)
                result[number] = {
                    "status": "exception",
                    "location": None,
                    "latitude": None,
                    "longitude": None,
                    "timestamp": None,
                    "estimated_delivery": None,
                    "history": [],
                    "error": str(err),
                    "status_changed": False,
                }
        return result
