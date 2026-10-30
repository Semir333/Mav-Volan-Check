"""Constants for the BKK & MÁV Transit Sync integration."""

DOMAIN = "bkk_mav_sync"

# Configuration options
CONF_TRANSPORT_TYPE = "transport_type"
CONF_STOP_ID = "stop_id"
CONF_DIRECTION_FILTER = "direction_filter"
CONF_API_KEY = "api_key"
CONF_SCAN_INTERVAL = "scan_interval"

TRANSPORT_TYPE_TRAIN = "train"
TRANSPORT_TYPE_BUS = "bus"

DEFAULT_SCAN_INTERVAL = 60
DEFAULT_BKK_KEY = "web-54feeb28-a942-48ae-89a5-9955879ebb2c"

# Vonat hivatalos megálló eltolódások (másodpercben, Erdőkerteshez képest)
TRAIN_OFFSETS = {
    "vác": 1680, "vac": 1680,
    "vác-alsóváros": 1500, "vac-alsovaros": 1500,
    "máriaudvar": 1320, "mariaudvar": 1320,
    "csörög": 1140, "csorog": 1140,
    "vácrátót": 900, "vacratot": 900,
    "váchartyán": 660, "vachartyan": 660,
    "rudnaykert": 480, "rudnaykert": 480,
    "őrbottyán": 300, "orbottyan": 300,
    "vicziántelep": 120, "vicziantelep": 120,
    "erdőkertes": 0, "erdokertes": 0
}