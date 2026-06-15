import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen

from project_config import COUNCIL_DISTRICTS_URL, DATA_CONTEXT, ensure_directories


BOUNDARY_FILE = DATA_CONTEXT / "council_district_boundaries.geojson"
BOUNDARY_METADATA = DATA_CONTEXT / "boundary_metadata.json"


def main() -> None:
    ensure_directories()
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "geometryPrecision": 5,
        "maxAllowableOffset": 0.0005,
        "f": "geojson",
    }
    url = f"{COUNCIL_DISTRICTS_URL}/query?{urlencode(params)}"
    with urlopen(url, timeout=120) as response:
        geojson = json.loads(response.read().decode("utf-8"))
    if geojson.get("type") != "FeatureCollection" or not geojson.get("features"):
        raise RuntimeError("Council district boundary service returned no GeoJSON features.")

    BOUNDARY_FILE.write_text(json.dumps(geojson, indent=2), encoding="utf-8")
    metadata = {
        "source_name": "COH_Council_Districts",
        "source_url": COUNCIL_DISTRICTS_URL,
        "records_downloaded": len(geojson["features"]),
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "note": "Official council district polygons are used for V2 choropleth mapping and area-normalized request density.",
    }
    BOUNDARY_METADATA.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Wrote {len(geojson['features'])} council district boundary features.")


if __name__ == "__main__":
    main()
