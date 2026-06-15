import json
from pathlib import Path

import numpy as np
import pandas as pd

from project_config import DATA_CONTEXT, DATA_PROCESSED, GIS, TABLES, ensure_directories


BOUNDARY_FILE = DATA_CONTEXT / "council_district_boundaries.geojson"
CLEAN_FILE = DATA_PROCESSED / "houston_311_infrastructure_requests_cleaned.csv"


def clean_value(value):
    if isinstance(value, np.generic):
        value = value.item()
    if pd.isna(value):
        return None
    return value


def clean_properties(props: dict) -> dict:
    return {str(key): clean_value(value) for key, value in props.items()}


def write_geojson(path: Path, features: list[dict], metadata: dict | None = None) -> None:
    collection = {"type": "FeatureCollection", "features": features}
    if metadata:
        collection["metadata"] = metadata
    path.write_text(json.dumps(collection, indent=2), encoding="utf-8")


def load_table(name: str) -> pd.DataFrame:
    path = TABLES / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def export_district_layers() -> None:
    if not BOUNDARY_FILE.exists():
        return
    boundaries = json.loads(BOUNDARY_FILE.read_text(encoding="utf-8"))
    burden = load_table("council_district_service_burden.csv")
    quality = load_table("district_data_quality.csv")
    non_solid = load_table("council_district_non_solid_waste_screening.csv")
    balanced = load_table("category_balanced_district_density.csv")

    if not burden.empty:
        burden = burden.add_prefix("baseline_").rename(columns={"baseline_council_district": "council_district"})
    if not quality.empty:
        quality = quality.add_prefix("qa_").rename(columns={"qa_council_district": "council_district"})
    if not non_solid.empty:
        non_solid = non_solid[
            ["council_district", "screening_score", "screening_class", "request_count"]
        ].rename(
            columns={
                "screening_score": "non_solid_waste_score",
                "screening_class": "non_solid_waste_class",
                "request_count": "non_solid_waste_request_count",
            }
        )
    if not balanced.empty:
        balanced = balanced[
            ["council_district", "category_balanced_density_score", "category_balanced_class"]
        ]

    merged = burden
    for table in [quality, non_solid, balanced]:
        if not table.empty:
            merged = merged.merge(table, on="council_district", how="left") if not merged.empty else table
    metrics = {
        str(row["council_district"]): clean_properties(row.to_dict())
        for _, row in merged.iterrows()
    } if not merged.empty else {}

    features = []
    qa_features = []
    for feature in boundaries.get("features", []):
        props = feature.get("properties", {}).copy()
        district = str(props.get("DISTRICT") or "").strip()
        merged_props = {
            "council_district": district,
            "district_member": props.get("MEMBER"),
            **metrics.get(district, {}),
        }
        out_feature = {
            "type": "Feature",
            "geometry": feature.get("geometry"),
            "properties": clean_properties(merged_props),
        }
        features.append(out_feature)
        qa_share = merged_props.get("qa_spatial_assignment_share")
        if qa_share is not None and qa_share < 0.9:
            qa_features.append(out_feature)

    write_geojson(
        GIS / "council_district_screening_index.geojson",
        features,
        {
            "description": "Council district polygons with baseline screening score, QA fields, and alternate score fields.",
            "crs_note": "Source geometries are stored in WGS84 GeoJSON coordinates.",
        },
    )
    write_geojson(
        GIS / "district_assignment_qa_flags.geojson",
        qa_features,
        {
            "description": "Council district polygons with spatial assignment share below 90 percent.",
            "review_threshold": 0.9,
        },
    )


def export_repeat_clusters() -> None:
    clusters = load_table("repeat_location_clusters.csv")
    if clusters.empty:
        return
    features = []
    for _, row in clusters.iterrows():
        lon = row.get("lon_bin_approx_100m")
        lat = row.get("lat_bin_approx_100m")
        if pd.isna(lon) or pd.isna(lat):
            continue
        props = clean_properties(row.drop(["lon_bin_approx_100m", "lat_bin_approx_100m"]).to_dict())
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                "properties": props,
            }
        )
    write_geojson(
        GIS / "repeat_location_clusters.geojson",
        features,
        {
            "description": "Approximate same-category repeat-request clusters using rounded coordinate bins.",
            "coordinate_precision_note": "Coordinates are rounded to roughly 100-meter bins; this is not address-level deduplication.",
        },
    )


def export_request_sample(max_features: int = 10000) -> None:
    if not CLEAN_FILE.exists():
        return
    df = pd.read_csv(CLEAN_FILE, parse_dates=["opened_date", "closed_date"])
    geo = df.dropna(subset=["longitude", "latitude"]).copy()
    source_count = len(geo)
    if len(geo) > max_features:
        geo = geo.sample(n=max_features, random_state=42).sort_values("source_objectid")
    keep = [
        "case_number",
        "standardized_category",
        "opened_date",
        "closed_date",
        "is_open",
        "is_long_resolution",
        "is_repeat_cluster",
        "council_district",
        "source_council_district",
        "spatial_council_district",
        "quality_flags",
    ]
    features = []
    for _, row in geo.iterrows():
        props = {}
        for field in keep:
            value = row.get(field)
            if hasattr(value, "isoformat") and pd.notna(value):
                value = value.isoformat()
            props[field] = clean_value(value)
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(row["longitude"]), float(row["latitude"])]},
                "properties": props,
            }
        )
    write_geojson(
        GIS / "request_points_sample.geojson",
        features,
        {
            "sampled": source_count > len(features),
            "feature_count": len(features),
            "source_coordinate_record_count": source_count,
        },
    )


def main() -> None:
    ensure_directories()
    export_district_layers()
    export_repeat_clusters()
    export_request_sample()
    print("Wrote GIS-ready GeoJSON layers.")


if __name__ == "__main__":
    main()
