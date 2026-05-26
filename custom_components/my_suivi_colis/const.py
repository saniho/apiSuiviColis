DOMAIN = "my_suivi_colis"
PLATFORMS = ["sensor"]

STORAGE_KEY = f"{DOMAIN}.tracking_entries"
STORAGE_VERSION = 1

CONF_API_KEY = "api_key"
CONF_TRACKING_NUMBER = "tracking_number"
CONF_CARRIER = "carrier"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_NAME = "name"
CONF_POSTAL_CODE = "postal_code"

DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 5

CARRIERS = {
    "laposte": "La Poste",
    "colissimo": "Colissimo",
    "chronopost": "Chronopost",
    "dhl": "DHL",
    "fedex": "FedEx",
    "ups": "UPS",
    "tnt": "TNT",
    "gls": "GLS",
    "mondial_relay": "Mondial Relay",
    "amazon": "Amazon Logistics",
    "dpd": "DPD",
    "relais_colis": "Relais Colis",
    "other": "Autre transporteur",
}

ATTR_STATUS = "status"
ATTR_LOCATION = "location"
ATTR_LATITUDE = "latitude"
ATTR_LONGITUDE = "longitude"
ATTR_TIMESTAMP = "timestamp"
ATTR_ESTIMATED_DELIVERY = "estimated_delivery"
ATTR_LAST_UPDATE = "last_update"
ATTR_CARRIER = "carrier"
ATTR_TRACKING_NUMBER = "tracking_number"
ATTR_HISTORY = "history"
ATTR_ORIGIN = "origin"
ATTR_DESTINATION = "destination"
ATTR_WEIGHT = "weight"
ATTR_SENDER = "sender"

STATUS_DELIVERED = "delivered"
STATUS_IN_TRANSIT = "in_transit"
STATUS_OUT_FOR_DELIVERY = "out_for_delivery"
STATUS_PICKED_UP = "picked_up"
STATUS_EXCEPTION = "exception"
STATUS_PENDING = "pending"
STATUS_DELAYED = "delayed"
STATUS_AVAILABLE_FOR_PICKUP = "available_for_pickup"

STATUS_ICONS = {
    STATUS_DELIVERED: "mdi:package-variant-closed-check",
    STATUS_IN_TRANSIT: "mdi:truck-delivery",
    STATUS_OUT_FOR_DELIVERY: "mdi:truck-fast",
    STATUS_PICKED_UP: "mdi:package-up",
    STATUS_EXCEPTION: "mdi:alert-circle",
    STATUS_PENDING: "mdi:clock-outline",
    STATUS_DELAYED: "mdi:clock-alert",
    STATUS_AVAILABLE_FOR_PICKUP: "mdi:package-variant-closed",
}

STATUS_FRIENDLY = {
    STATUS_DELIVERED: "Livré",
    STATUS_IN_TRANSIT: "En transit",
    STATUS_OUT_FOR_DELIVERY: "En cours de livraison",
    STATUS_PICKED_UP: "Pris en charge",
    STATUS_EXCEPTION: "Exception",
    STATUS_PENDING: "En attente",
    STATUS_DELAYED: "Retardé",
    STATUS_AVAILABLE_FOR_PICKUP: "Disponible en point relais",
}

STARTUP_MESSAGE = """
-------------------------------------------------------------------
{title}
Version: {version}
This is a custom integration for Home Assistant.
-------------------------------------------------------------------
"""
