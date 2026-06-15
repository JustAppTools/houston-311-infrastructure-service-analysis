from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
CONFIG_FILE = CONFIG_DIR / "analysis_config.json"
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
HGAC_MAJOR_ROADS_URL = "https://gis.h-gac.com/arcgis/rest/services/Open_Data/Transportation/MapServer/9"
HGAC_MAJOR_RIVERS_URL = "https://gis.h-gac.com/arcgis/rest/services/Open_Data/Environment/MapServer/1"

def load_analysis_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


ANALYSIS_CONFIG = load_analysis_config()

DEFAULT_START_DATE = ANALYSIS_CONFIG.get("date_range", {}).get("start_date", "2025-04-01")
DEFAULT_END_DATE = ANALYSIS_CONFIG.get("date_range", {}).get("end_date_exclusive", "2025-07-01")
DEFAULT_MAX_RECORDS = int(ANALYSIS_CONFIG.get("data_fetch", {}).get("max_records", 100000))
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

LONG_RESOLUTION_DAYS = int(ANALYSIS_CONFIG.get("quality_thresholds", {}).get("long_resolution_days", 14))
REPEAT_CLUSTER_MIN_COUNT = int(ANALYSIS_CONFIG.get("quality_thresholds", {}).get("repeat_cluster_min_count", 3))
SCORE_WEIGHTS = {
    "resident_request_rate": 0.25,
    "household_request_rate": 0.15,
    "median_resolution_days": 0.20,
    "unresolved_share": 0.15,
    "long_resolution_share": 0.10,
    "repeat_cluster_share": 0.15,
}
SCORE_WEIGHTS.update(ANALYSIS_CONFIG.get("score_weights", {}))

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
    for path in [CONFIG_DIR, DATA_RAW, DATA_PROCESSED, DATA_CONTEXT, TABLES, FIGURES, MAPS, DOCS]:
        path.mkdir(parents=True, exist_ok=True)
