import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen

from project_config import (
    DATA_CONTEXT,
    HGAC_MAJOR_RIVERS_URL,
    HGAC_MAJOR_ROADS_URL,
    ensure_directories,
)


CONTEXT_LAYERS = [
    {
        "name": "major_roads",
        "source_name": "H-GAC Major Roads",
        "url": HGAC_MAJOR_ROADS_URL,
        "output": DATA_CONTEXT / "major_roads.geojson",
    },
    {
        "name": "major_rivers",
        "source_name": "H-GAC Major Rivers",
        "url": HGAC_MAJOR_RIVERS_URL,
        "output": DATA_CONTEXT / "major_rivers.geojson",
    },
]
METADATA_FILE = DATA_CONTEXT / "map_context_metadata.json"


def fetch_geojson(layer_url: str) -> dict:
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "resultRecordCount": "100000",
        "f": "geojson",
    }
    with urlopen(f"{layer_url}/query?{urlencode(params)}", timeout=120) as response:
        text = response.read().decode("utf-8")
    payload = json.loads(text)
    if "features" not in payload:
        raise RuntimeError(payload.get("error", payload))
    return payload


def main() -> None:
    ensure_directories()
    metadata = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "layers": [],
    }
    for layer in CONTEXT_LAYERS:
        status = {
            "name": layer["name"],
            "source_name": layer["source_name"],
            "source_url": layer["url"],
            "output_file": layer["output"].name,
            "feature_count": 0,
            "error": None,
        }
        try:
            geojson = fetch_geojson(layer["url"])
            layer["output"].write_text(json.dumps(geojson), encoding="utf-8")
            status["feature_count"] = len(geojson.get("features", []))
        except Exception as exc:
            status["error"] = str(exc)[:500]
        metadata["layers"].append(status)
    METADATA_FILE.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print("Wrote optional map context metadata.")


if __name__ == "__main__":
    main()
