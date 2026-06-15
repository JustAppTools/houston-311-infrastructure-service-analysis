import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pandas as pd

from project_config import CATEGORY_RULES, DATA_PROCESSED, DATA_RAW, LONG_RESOLUTION_DAYS, ensure_directories


RAW_FILE = DATA_RAW / "houston_311_archive_infrastructure_extract.csv"
CLEAN_FILE = DATA_PROCESSED / "houston_311_infrastructure_requests_cleaned.csv"
GEOJSON_FILE = DATA_PROCESSED / "houston_311_infrastructure_requests_cleaned.geojson"


def parse_arcgis_datetime(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return pd.to_datetime(numeric, unit="ms", utc=True, errors="coerce").dt.tz_convert(None)


def classify_category(value: object) -> str:
    text = str(value or "").lower()
    for label, needles in CATEGORY_RULES:
        if any(needle in text for needle in needles):
            return label
    return "Other Infrastructure"


def is_open_status(status: object, state: object, closed_date) -> bool:
    combined = f"{status or ''} {state or ''}".lower()
    if pd.notna(closed_date) or "resolved" in combined or "completed" in combined:
        return False
    if "cancel" in combined or "merged" in combined:
        return False
    return True


def build_quality_flags(row: pd.Series) -> str:
    flags = []
    if pd.isna(row["opened_date"]):
        flags.append("missing_opened_date")
    if row.get("invalid_future_closed_date", False):
        flags.append("invalid_future_closed_date")
    if pd.isna(row["closed_date"]) and not row["is_open"]:
        flags.append("missing_closed_date_for_non_open")
    lat = row["latitude"]
    lon = row["longitude"]
    if pd.isna(lat) or pd.isna(lon):
        flags.append("missing_coordinates")
    elif not (29.0 <= float(lat) <= 30.2 and -96.2 <= float(lon) <= -94.6):
        flags.append("coordinate_outside_houston_screen")
    if row["standardized_category"] == "Other Infrastructure":
        flags.append("low_confidence_category")
    return "|".join(flags) if flags else "ok"


def write_geojson(df: pd.DataFrame, path: Path, max_features: int = 5000) -> None:
    features = []
    keep_fields = [
        "case_number",
        "standardized_category",
        "request_type",
        "opened_date",
        "closed_date",
        "status",
        "state_code_name",
        "resolution_days",
        "is_open",
        "is_long_resolution",
        "council_district",
        "super_neighborhood",
        "quality_flags",
    ]
    geo = df[df["quality_flags"].str.contains("missing_coordinates") == False].copy()
    source_feature_count = len(geo)
    if len(geo) > max_features:
        geo = geo.sample(n=max_features, random_state=42).sort_values("source_objectid")
    for _, row in geo.iterrows():
        props = {}
        for field in keep_fields:
            value = row.get(field)
            if pd.isna(value):
                value = None
            elif hasattr(value, "isoformat"):
                value = value.isoformat()
            props[field] = value
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row["longitude"]), float(row["latitude"])],
                },
                "properties": props,
            }
        )
    geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "sampled": source_feature_count > len(features),
            "feature_count": len(features),
            "source_coordinate_record_count": source_feature_count,
            "note": "The full cleaned analytical extract is stored in the processed CSV; GeoJSON is sampled for repository size.",
        },
        "features": features,
    }
    path.write_text(json.dumps(geojson, indent=2), encoding="utf-8")


def main() -> None:
    ensure_directories()
    if not RAW_FILE.exists():
        raise SystemExit(f"Missing raw extract: {RAW_FILE}. Run scripts/fetch_data.py first.")

    raw = pd.read_csv(RAW_FILE)
    df = pd.DataFrame(
        {
            "source_objectid": raw.get("OBJECTID"),
            "case_number": raw.get("Case_Number"),
            "request_type": raw.get("Incident_Case_Type"),
            "standardized_category": raw.get("Incident_Case_Type").apply(classify_category),
            "opened_date": parse_arcgis_datetime(raw.get("Created_Date_Local")),
            "closed_date": parse_arcgis_datetime(raw.get("Closed_Date")),
            "status": raw.get("Status"),
            "state_code_name": raw.get("State_Code_Name"),
            "department": raw.get("Department"),
            "division": raw.get("Division"),
            "service_area": raw.get("Service_Area"),
            "sla_name": raw.get("SLA_Name"),
            "resolve_by_time": parse_arcgis_datetime(raw.get("Resolve_By_Time")),
            "latitude": pd.to_numeric(raw.get("Latitude").fillna(raw.get("geometry_y")), errors="coerce"),
            "longitude": pd.to_numeric(raw.get("Longitude").fillna(raw.get("geometry_x")), errors="coerce"),
            "council_district": raw.get("Council_District"),
            "super_neighborhood": raw.get("Customer_SuperNeighborhood"),
        }
    )
    max_reasonable_closed = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)
    df["invalid_future_closed_date"] = df["closed_date"] > max_reasonable_closed
    df.loc[df["invalid_future_closed_date"], "closed_date"] = pd.NaT
    df["resolution_days"] = (df["closed_date"] - df["opened_date"]).dt.total_seconds() / 86400
    df.loc[df["resolution_days"] < 0, "resolution_days"] = pd.NA
    df["is_open"] = [
        is_open_status(status, state, closed)
        for status, state, closed in zip(df["status"], df["state_code_name"], df["closed_date"])
    ]
    df["is_long_resolution"] = df["resolution_days"].fillna(0) > LONG_RESOLUTION_DAYS
    df["month"] = df["opened_date"].dt.to_period("M").astype(str)
    df["quality_flags"] = df.apply(build_quality_flags, axis=1)

    df.to_csv(CLEAN_FILE, index=False)
    write_geojson(df, GEOJSON_FILE)
    print(f"Wrote {len(df):,} cleaned records.")


if __name__ == "__main__":
    main()
