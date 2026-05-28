from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import aiohttp

from .const import (
    STATUS_AVAILABLE_FOR_PICKUP,
    STATUS_DELIVERED,
    STATUS_EXCEPTION,
    STATUS_IN_TRANSIT,
    STATUS_OUT_FOR_DELIVERY,
    STATUS_PENDING,
    STATUS_PICKED_UP,
)

_LOGGER = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


async def geocode_city(city: str) -> tuple[float | None, float | None]:
    if not city:
        return None, None
    try:
        params = {
            "q": city,
            "format": "json",
            "limit": 1,
        }
        headers = {
            "User-Agent": "HomeAssistant-MySuiviColis/1.0",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                NOMINATIM_URL, params=params, headers=headers, timeout=5
            ) as resp:
                if resp.status != 200:
                    return None, None
                data = await resp.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        _LOGGER.debug("Geocode failed for %s", city)
    return None, None


class BaseCarrierTracker(ABC):
    @abstractmethod
    async def track(self, tracking_number: str, entry: dict[str, Any] | None = None) -> dict[str, Any]:
        pass

    @property
    @abstractmethod
    def carrier_key(self) -> str:
        pass


class ColissimoTracker(BaseCarrierTracker):
    BASE_URL = "https://www.laposte.fr/ssu/api/colis/suivi"

    @property
    def carrier_key(self) -> str:
        return "colissimo"

    async def track(self, tracking_number: str, entry: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.BASE_URL}/{tracking_number}"
        _LOGGER.debug("Colissimo URL: %s", url)
        headers = {
            "Accept": "application/json",
            "User-Agent": "HomeAssistant/1.0",
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status != 200:
                        return self._error_result(f"HTTP {resp.status}")
                    data = await resp.json()
                    return await self._parse_response(data)
            except Exception as err:
                return self._error_result(str(err))

    async def _parse_response(self, data: dict) -> dict[str, Any]:
        result = {
            "status": STATUS_PENDING,
            "raw_status": "pending",
            "location": None,
            "latitude": None,
            "longitude": None,
            "timestamp": datetime.now().isoformat(),
            "estimated_delivery": None,
            "history": [],
            "origin": None,
            "destination": None,
            "weight": None,
        }
        try:
            timeline = data.get("timeline", [])
            if not timeline:
                return result

            last = timeline[-1]
            code = last.get("code", "")
            result["raw_status"] = code
            result["status"] = self._map_status(code)
            result["timestamp"] = last.get("date", datetime.now().isoformat())

            loc = last.get("location", {})
            if isinstance(loc, dict):
                city = loc.get("city") or loc.get("label")
                result["location"] = city
            else:
                result["location"] = str(loc) if loc else None

            for entry in timeline:
                e_loc = entry.get("location", {})
                e_city = e_loc.get("city") if isinstance(e_loc, dict) else str(e_loc) if e_loc else None
                result["history"].append({
                    "status": entry.get("label", ""),
                    "location": e_city,
                    "date": entry.get("date"),
                })

            estimated = data.get("estimatedDeliveryDate")
            if estimated:
                result["estimated_delivery"] = estimated

            origin = data.get("origin", {})
            if isinstance(origin, dict):
                result["origin"] = origin.get("city") or origin.get("label")
            dest = data.get("destination", {})
            if isinstance(dest, dict):
                result["destination"] = dest.get("city") or dest.get("label")

            if result["location"] and not result.get("latitude"):
                lat, lng = await geocode_city(result["location"])
                result["latitude"] = lat
                result["longitude"] = lng

        except Exception as err:
            _LOGGER.error("Error parsing Colissimo response: %s", err)
        return result

    def _map_status(self, code: str) -> str:
        mapping = {
            "PRIS_EN_CHARGE": STATUS_PICKED_UP,
            "EN_TRANSIT": STATUS_IN_TRANSIT,
            "EN_COURS_ACHEMINEMENT": STATUS_IN_TRANSIT,
            "EN_COURS_LIVRAISON": STATUS_OUT_FOR_DELIVERY,
            "DISTRIBUE": STATUS_DELIVERED,
            "A_RETIRER": STATUS_PICKED_UP,
            "RETOUR": STATUS_EXCEPTION,
            "ANOMALIE": STATUS_EXCEPTION,
        }
        return mapping.get(code, STATUS_IN_TRANSIT)

    def _error_result(self, error: str) -> dict[str, Any]:
        return {
            "status": STATUS_EXCEPTION,
            "raw_status": "error",
            "location": None,
            "latitude": None,
            "longitude": None,
            "timestamp": datetime.now().isoformat(),
            "estimated_delivery": None,
            "history": [],
            "error": error,
        }


class LaposteTracker(ColissimoTracker):
    @property
    def carrier_key(self) -> str:
        return "laposte"


class ChronopostTracker(BaseCarrierTracker):
    BASE_URL = "https://www.chronopost.fr/tracking/ws-rf/shippingCase"

    @property
    def carrier_key(self) -> str:
        return "chronopost"

    async def track(self, tracking_number: str, entry: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.BASE_URL}/{tracking_number}"
        _LOGGER.debug("Chronopost URL: %s", url)
        headers = {
            "Accept": "application/json",
            "User-Agent": "HomeAssistant/1.0",
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status != 200:
                        return self._error_result(f"HTTP {resp.status}")
                    data = await resp.json()
                    return await self._parse_response(data)
            except Exception as err:
                return self._error_result(str(err))

    async def _parse_response(self, data: dict) -> dict[str, Any]:
        result = {
            "status": STATUS_PENDING,
            "raw_status": "pending",
            "location": None,
            "latitude": None,
            "longitude": None,
            "timestamp": datetime.now().isoformat(),
            "estimated_delivery": None,
            "history": [],
            "origin": None,
            "destination": None,
            "weight": None,
        }
        try:
            events = data.get("events", [])
            if not events:
                return result

            last = events[-1]
            code = last.get("code", "")
            result["raw_status"] = code
            result["status"] = self._map_status(code)
            result["location"] = last.get("location")
            result["timestamp"] = last.get("date", datetime.now().isoformat())

            for ev in events:
                result["history"].append({
                    "status": ev.get("label", ""),
                    "location": ev.get("location"),
                    "date": ev.get("date"),
                })

            estimated = data.get("estimatedDeliveryDate")
            if estimated:
                result["estimated_delivery"] = estimated

            if result["location"]:
                lat, lng = await geocode_city(result["location"])
                result["latitude"] = lat
                result["longitude"] = lng

        except Exception as err:
            _LOGGER.error("Error parsing Chronopost response: %s", err)
        return result

    def _map_status(self, code: str) -> str:
        mapping = {
            "PICKUP": STATUS_PICKED_UP,
            "IN_TRANSIT": STATUS_IN_TRANSIT,
            "DELIVERY": STATUS_OUT_FOR_DELIVERY,
            "DELIVERED": STATUS_DELIVERED,
            "EXCEPTION": STATUS_EXCEPTION,
        }
        return mapping.get(code, STATUS_IN_TRANSIT)

    def _error_result(self, error: str) -> dict[str, Any]:
        return {
            "status": STATUS_EXCEPTION,
            "raw_status": "error",
            "location": None,
            "latitude": None,
            "longitude": None,
            "timestamp": datetime.now().isoformat(),
            "estimated_delivery": None,
            "history": [],
            "error": error,
        }


class MondialRelayTracker(BaseCarrierTracker):
    TRACKING_URL = "https://www.mondialrelay.fr/suivi-de-colis/"

    @property
    def carrier_key(self) -> str:
        return "mondial_relay"

    async def track(self, tracking_number: str, entry: dict[str, Any] | None = None) -> dict[str, Any]:
        import re
        from html.parser import HTMLParser

        result = {
            "status": STATUS_PENDING,
            "raw_status": "pending",
            "location": None,
            "latitude": None,
            "longitude": None,
            "timestamp": datetime.now().isoformat(),
            "estimated_delivery": None,
            "history": [],
            "origin": None,
            "destination": None,
            "weight": None,
        }
        try:
            postal_code = (entry or {}).get("postal_code", "")
            params = {"numero": tracking_number}
            if postal_code:
                params["codePostal"] = postal_code
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 14) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.6099.144 Mobile Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            }
            async with aiohttp.ClientSession() as session:
                _LOGGER.debug("Mondial Relay URL: %s?%s", self.TRACKING_URL, "&".join(f"{k}={v}" for k, v in params.items()))
                async with session.get(
                    self.TRACKING_URL, params=params, headers=headers, timeout=15,
                    allow_redirects=True,
                ) as resp:
                    if resp.status != 200:
                        result["note"] = f"Site MR inaccessible (HTTP {resp.status})"
                        return result
                    html = await resp.text()

            class MRParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.in_timeline = False
                    self.events = []
                    self.current_event = {}
                    self.current_tag = None
                    self.in_timeline_container = False
                    self.timeline_depth = 0
                    self.status_text = None
                    self.location_text = None
                    self.date_text = None
                    self.capture_text = False
                    self.label_map = {
                        "Préparation": "Préparation chez l'expéditeur",
                        "Transit": "Colis en transit",
                        "Livraison": "Colis en cours de livraison",
                        "Disponible": "Colis disponible en point relais",
                        "Distribué": "Colis livré",
                        "Retour": "Retour à l'expéditeur",
                    }

                def handle_starttag(self, tag, attrs):
                    attrs_dict = dict(attrs)
                    if tag == "div":
                        cls = attrs_dict.get("class", "")
                        if "timeline" in cls.lower() or "event-list" in cls.lower() or "steps" in cls.lower():
                            self.in_timeline = True
                        if self.in_timeline and ("event" in cls.lower() or "step" in cls.lower() or "item" in cls.lower()):
                            self.current_event = {}
                            self.timeline_depth += 1

                def handle_endtag(self, tag):
                    if tag == "div" and self.in_timeline and self.current_event:
                        if self.current_event.get("label"):
                            self.events.append(self.current_event)
                        self.current_event = {}
                    if tag == "div" and self.in_timeline and self.timeline_depth > 0:
                        self.timeline_depth -= 1

                def handle_data(self, data):
                    text = data.strip()
                    if not text:
                        return
                    lower = text.lower()
                    for key in ["livré", "distribué", "remis"]:
                        if key in lower:
                            self.current_event["label"] = text
                            self.current_event["status"] = "delivered"
                    for key in ["transit", "acheminement"]:
                        if key in lower:
                            self.current_event.setdefault("label", text)
                            self.current_event["status"] = "in_transit"
                    if "disponible" in lower or "retrait" in lower:
                        self.current_event.setdefault("label", text)
                        self.current_event["status"] = "available_for_pickup"
                    if "livraison" in lower and "cours" in lower:
                        self.current_event.setdefault("label", text)
                        self.current_event["status"] = "out_for_delivery"
                    if "préparation" in lower or "pris en charge" in lower:
                        self.current_event.setdefault("label", text)
                        self.current_event["status"] = "picked_up"
                    if "retour" in lower or "refus" in lower:
                        self.current_event.setdefault("label", text)
                        self.current_event["status"] = "exception"
                    if re.match(r"\d{2}/\d{2}/\d{4}", text):
                        self.current_event["date"] = text
                    if re.match(r"\d{2}h\d{2}", text):
                        self.current_event["time"] = text

            parser = MRParser()
            parser.feed(html)

            if parser.events:
                last = parser.events[-1]
                status_map = {
                    "delivered": STATUS_DELIVERED,
                    "in_transit": STATUS_IN_TRANSIT,
                    "out_for_delivery": STATUS_OUT_FOR_DELIVERY,
                    "picked_up": STATUS_PICKED_UP,
                    "exception": STATUS_EXCEPTION,
                    "available_for_pickup": STATUS_AVAILABLE_FOR_PICKUP,
                }
                result["status"] = status_map.get(last.get("status"), STATUS_IN_TRANSIT)
                result["raw_status"] = last.get("label", "") or last.get("status", "")
                result["location"] = None
                result["timestamp"] = f"{last.get('date', '')} {last.get('time', '')}".strip() or datetime.now().isoformat()

                for ev in parser.events:
                    dt = f"{ev.get('date', '')} {ev.get('time', '')}".strip()
                    result["history"].append({
                        "status": ev.get("label", ""),
                        "location": None,
                        "date": dt or None,
                    })
            else:
                result["note"] = "Aucune information de suivi trouvée. Vérifiez le numéro."

        except Exception as err:
            _LOGGER.error("Error tracking Mondial Relay %s: %s", tracking_number, err)
            result["status"] = STATUS_EXCEPTION
            result["error"] = str(err)

        return result


class GenericTracker(BaseCarrierTracker):
    @property
    def carrier_key(self) -> str:
        return "other"

    async def track(self, tracking_number: str, entry: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "status": STATUS_PENDING,
            "raw_status": "pending",
            "location": None,
            "latitude": None,
            "longitude": None,
            "timestamp": datetime.now().isoformat(),
            "estimated_delivery": None,
            "history": [],
            "note": "Tracking non disponible pour ce transporteur. "
                    "Configurez une clé API externe pour le suivi.",
        }


TRACKER_MAP: dict[str, type[BaseCarrierTracker]] = {
    "laposte": LaposteTracker,
    "colissimo": ColissimoTracker,
    "chronopost": ChronopostTracker,
    "dhl": GenericTracker,
    "fedex": GenericTracker,
    "ups": GenericTracker,
    "tnt": GenericTracker,
    "gls": GenericTracker,
    "mondial_relay": MondialRelayTracker,
    "amazon": GenericTracker,
    "dpd": GenericTracker,
    "relais_colis": GenericTracker,
    "other": GenericTracker,
}


def get_tracker(carrier: str) -> BaseCarrierTracker:
    tracker_cls = TRACKER_MAP.get(carrier, GenericTracker)
    return tracker_cls()
