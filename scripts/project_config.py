from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_CONTEXT = DATA_PROCESSED / "context"
OUTPUTS = ROOT / "outputs"
TABLES = OUTPUTS / "tables"
FIGURES = OUTPUTS / "figures"
MAPS = OUTPUTS / "maps"
DOCS = ROOT / "docs"

ARCHIVE_LAYER_URL = (
    "https://mycity2.houstontx.gov/gisweb01/rest/services/311/"
    "Houston311_Archives/MapServer/0"
)
RECENT_LAYER_URL = (
    "https://mycity2.houstontx.gov/gisweb01/rest/services/311/"
    "HOUSTON311_RECENT_SR_SNOW/FeatureServer/0"
)
COUNCIL_DISTRICTS_URL = (
    "https://www.gis.hctx.net/arcgis/rest/services/CoH/"
    "CoH_Boundaries/MapServer/0"
)

DEFAULT_START_DATE = "2025-04-01"
DEFAULT_END_DATE = "2025-07-01"
DEFAULT_MAX_RECORDS = 100000
PAGE_SIZE = 1000

OUT_FIELDS = [
    "OBJECTID",
    "Case_Number",
    "Created_Date_Local",
    "Closed_Date",
    "Status",
    "State_Code_Name",
    "Incident_Case_Type",
    "Title",
    "Latitude",
    "Longitude",
    "Council_District",
    "Customer_SuperNeighborhood",
    "Department",
    "Division",
    "Service_Area",
    "SLA_Name",
    "Resolve_By_Time",
]

INFRASTRUCTURE_TERMS = [
    "Water",
    "Sewer",
    "Drainage",
    "Flood",
    "Pothole",
    "Sidewalk",
    "Traffic",
    "Signal",
    "Light",
    "Dump",
    "Trash",
    "Recycling",
    "Garbage",
    "Bridge",
    "Street",
    "Debris",
    "Container",
]

CATEGORY_RULES = [
    ("Drainage / Flooding", ["drainage", "flood"]),
    ("Sewer / Wastewater", ["sewer", "wastewater"]),
    ("Water", ["water", "hydrant", "meter"]),
    ("Road / Pothole / Bridge", ["pothole", "bridge", "street", "road", "barricade"]),
    ("Sidewalk / Bike Lane", ["sidewalk", "bike lane", "trail"]),
    ("Traffic Signals / Lighting", ["traffic", "signal", "lighting", "light", "beacon"]),
    ("Solid Waste / Recycling", ["trash", "recycling", "garbage", "container", "debris", "dump", "pickup"]),
]

LONG_RESOLUTION_DAYS = 14
REPEAT_CLUSTER_MIN_COUNT = 3

CANVAS = {
    "width": 1400,
    "height": 900,
    "margin": 86,
    "background": (248, 249, 247),
    "ink": (35, 38, 42),
    "muted": (97, 105, 112),
    "grid": (220, 224, 225),
    "accent": (31, 111, 125),
    "accent2": (192, 94, 72),
}


def ensure_directories() -> None:
    for path in [DATA_RAW, DATA_PROCESSED, DATA_CONTEXT, TABLES, FIGURES, MAPS, DOCS]:
        path.mkdir(parents=True, exist_ok=True)
