import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from project_config import (
    ARCHIVE_LAYER_URL,
    DATA_RAW,
    DEFAULT_END_DATE,
    DEFAULT_MAX_RECORDS,
    DEFAULT_START_DATE,
    INFRASTRUCTURE_TERMS,
    OUT_FIELDS,
    PAGE_SIZE,
    ensure_directories,
)


def arcgis_get(endpoint: str, params: dict, timeout: int = 90) -> dict:
    url = f"{endpoint}/query?{urlencode(params)}"
    with urlopen(url, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if "error" in payload:
        raise RuntimeError(f"ArcGIS error: {payload['error']}")
    return payload


def build_where(start_date: str, end_date: str) -> str:
    terms = " OR ".join(
        f"Incident_Case_Type LIKE '%{term.replace(chr(39), chr(39) + chr(39))}%'"
        for term in INFRASTRUCTURE_TERMS
    )
    return (
        f"Created_Date_Local >= DATE '{start_date}' "
        f"AND Created_Date_Local < DATE '{end_date}' "
        f"AND ({terms})"
    )


def count_records(where: str) -> int:
    payload = arcgis_get(
        ARCHIVE_LAYER_URL,
        {"where": where, "returnCountOnly": "true", "f": "json"},
        timeout=120,
    )
    return int(payload.get("count", 0))


def fetch_features(where: str, max_records: int) -> list[dict]:
    features: list[dict] = []
    offset = 0
    while offset < max_records:
        record_count = min(PAGE_SIZE, max_records - offset)
        params = {
            "where": where,
            "outFields": ",".join(OUT_FIELDS),
            "returnGeometry": "true",
            "outSR": "4326",
            "resultOffset": offset,
            "resultRecordCount": record_count,
            "orderByFields": "OBJECTID",
            "f": "json",
        }
        payload = arcgis_get(ARCHIVE_LAYER_URL, params)
        batch = payload.get("features", [])
        if not batch:
            break
        features.extend(batch)
        offset += len(batch)
        if len(batch) < record_count:
            break
        time.sleep(0.1)
    return features


def flatten_features(features: list[dict]) -> list[dict]:
    rows = []
    for feature in features:
        row = dict(feature.get("attributes", {}))
        geom = feature.get("geometry") or {}
        row["geometry_x"] = geom.get("x")
        row["geometry_y"] = geom.get("y")
        rows.append(row)
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    fieldnames = list(rows[0].keys()) if rows else OUT_FIELDS + ["geometry_x", "geometry_y"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Houston 311 infrastructure records.")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--max-records", type=int, default=DEFAULT_MAX_RECORDS)
    args = parser.parse_args()

    ensure_directories()
    where = build_where(args.start_date, args.end_date)
    source_count = None
    access_error = None
    rows: list[dict] = []

    try:
        source_count = count_records(where)
        features = fetch_features(where, min(args.max_records, source_count))
        rows = flatten_features(features)
        write_csv(rows, DATA_RAW / "houston_311_archive_infrastructure_extract.csv")
    except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
        access_error = str(exc)

    metadata = {
        "source_name": "City of Houston Houston311_Archives ArcGIS MapServer layer",
        "source_url": ARCHIVE_LAYER_URL,
        "query_where": where,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "max_records_requested": args.max_records,
        "source_count_for_query": source_count,
        "records_downloaded": len(rows),
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "access_error": access_error,
        "note": "Raw CSV is generated locally and ignored by git to avoid committing bulky source extracts.",
    }
    (DATA_RAW / "fetch_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    if access_error:
        raise SystemExit(f"Data fetch failed: {access_error}")

    print(f"Downloaded {len(rows):,} records from {source_count:,} matching source records.")


if __name__ == "__main__":
    main()
