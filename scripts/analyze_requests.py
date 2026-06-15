import json

import numpy as np
import pandas as pd

from project_config import DATA_CONTEXT, DATA_PROCESSED, TABLES, ensure_directories


CLEAN_FILE = DATA_PROCESSED / "houston_311_infrastructure_requests_cleaned.csv"
SUMMARY_FILE = DATA_PROCESSED / "analysis_summary.json"
BOUNDARY_FILE = DATA_CONTEXT / "council_district_boundaries.geojson"
SQFT_PER_SQMI = 27_878_400


def district_area_table() -> pd.DataFrame:
    if not BOUNDARY_FILE.exists():
        return pd.DataFrame(columns=["council_district", "district_area_sq_mi", "district_member"])
    geojson = json.loads(BOUNDARY_FILE.read_text(encoding="utf-8"))
    rows = []
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        district = str(props.get("DISTRICT") or "").strip()
        area_sqft = props.get("Shape.STArea()") or props.get("Shape_STAr")
        rows.append(
            {
                "council_district": district,
                "district_area_sq_mi": float(area_sqft) / SQFT_PER_SQMI if area_sqft else np.nan,
                "district_member": props.get("MEMBER"),
            }
        )
    return pd.DataFrame(rows)


def burden_class(score: float) -> str:
    if score >= 75:
        return "Very High"
    if score >= 50:
        return "High"
    if score >= 25:
        return "Medium"
    return "Low"


def percentile_rank(series: pd.Series) -> pd.Series:
    if series.nunique(dropna=True) <= 1:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return series.rank(pct=True).fillna(0) * 100


def to_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def main() -> None:
    ensure_directories()
    if not CLEAN_FILE.exists():
        raise SystemExit(f"Missing cleaned data: {CLEAN_FILE}")

    df = pd.read_csv(CLEAN_FILE, parse_dates=["opened_date", "closed_date"])
    for field in ["is_open", "is_long_resolution", "is_repeat_cluster"]:
        if field in df.columns:
            df[field] = to_bool(df[field])
    resolved = df[df["resolution_days"].notna()].copy()

    category_counts = (
        df.groupby(["standardized_category", "request_type"], dropna=False)
        .size()
        .reset_index(name="request_count")
        .sort_values("request_count", ascending=False)
    )
    category_counts.to_csv(TABLES / "top_infrastructure_request_categories.csv", index=False)

    median_resolution = (
        resolved.groupby("standardized_category", dropna=False)["resolution_days"]
        .median()
        .reset_index(name="median_resolution_days")
        .sort_values("median_resolution_days", ascending=False)
    )
    median_resolution.to_csv(TABLES / "median_resolution_time_by_category.csv", index=False)

    open_summary = (
        df.groupby("standardized_category", dropna=False)
        .agg(request_count=("case_number", "count"), unresolved_count=("is_open", "sum"))
        .reset_index()
    )
    open_summary["unresolved_share"] = open_summary["unresolved_count"] / open_summary["request_count"]
    open_summary.sort_values(["unresolved_share", "request_count"], ascending=False).to_csv(
        TABLES / "unresolved_open_requests_by_category.csv", index=False
    )

    long_summary = (
        df.groupby("standardized_category", dropna=False)
        .agg(
            request_count=("case_number", "count"),
            long_resolution_count=("is_long_resolution", "sum"),
            median_resolution_days=("resolution_days", "median"),
        )
        .reset_index()
    )
    long_summary["long_resolution_share"] = (
        long_summary["long_resolution_count"] / long_summary["request_count"]
    )
    long_summary.sort_values(["long_resolution_share", "request_count"], ascending=False).to_csv(
        TABLES / "long_resolution_categories.csv", index=False
    )

    repeat_clusters = (
        df[df["is_repeat_cluster"].astype(bool)]
        .groupby(
            [
                "council_district",
                "standardized_category",
                "lat_bin_approx_100m",
                "lon_bin_approx_100m",
            ],
            dropna=False,
        )
        .agg(
            cluster_request_count=("case_number", "count"),
            open_cluster_count=("is_open", "sum"),
            long_resolution_cluster_count=("is_long_resolution", "sum"),
            median_resolution_days=("resolution_days", "median"),
        )
        .reset_index()
        .sort_values("cluster_request_count", ascending=False)
    )
    repeat_clusters.to_csv(TABLES / "repeat_location_clusters.csv", index=False)

    monthly = (
        df.groupby(["month", "standardized_category"], dropna=False)
        .size()
        .reset_index(name="request_count")
        .sort_values(["month", "request_count"], ascending=[True, False])
    )
    monthly.to_csv(TABLES / "monthly_request_volume.csv", index=False)

    area = (
        df[df["council_district"].notna() & (df["council_district"].astype(str).str.strip() != "")]
        .groupby("council_district")
        .agg(
            request_count=("case_number", "count"),
            unresolved_count=("is_open", "sum"),
            long_resolution_count=("is_long_resolution", "sum"),
            repeat_clustered_count=("is_repeat_cluster", "sum"),
            median_resolution_days=("resolution_days", "median"),
            records_with_coordinates=("latitude", "count"),
        )
        .reset_index()
    )
    area = area[area["council_district"].astype(str).str.match(r"^[A-K]$")].copy()
    area = area.merge(district_area_table(), on="council_district", how="left")
    area["unresolved_share"] = area["unresolved_count"] / area["request_count"]
    area["long_resolution_share"] = area["long_resolution_count"] / area["request_count"]
    area["repeat_cluster_share"] = area["repeat_clustered_count"] / area["request_count"]
    area["requests_per_sq_mile"] = area["request_count"] / area["district_area_sq_mi"]
    area["service_burden_score"] = (
        percentile_rank(area["requests_per_sq_mile"].fillna(area["request_count"])) * 0.30
        + percentile_rank(area["median_resolution_days"]) * 0.25
        + percentile_rank(area["unresolved_share"]) * 0.20
        + percentile_rank(area["long_resolution_share"]) * 0.15
        + percentile_rank(area["repeat_cluster_share"]) * 0.10
    )
    area["service_burden_class"] = area["service_burden_score"].apply(burden_class)
    area_sorted = area.sort_values("service_burden_score", ascending=False)
    area_sorted.to_csv(
        TABLES / "council_district_service_burden.csv", index=False
    )

    drivers = []
    for district, subset in df[df["council_district"].isin(area["council_district"])].groupby("council_district"):
        category_counts_for_district = subset["standardized_category"].value_counts()
        top_category = category_counts_for_district.index[0]
        drivers.append(
            {
                "council_district": district,
                "top_category": top_category,
                "top_category_request_count": int(category_counts_for_district.iloc[0]),
                "top_category_share": float(category_counts_for_district.iloc[0] / len(subset)),
                "request_count": int(len(subset)),
                "unresolved_share": float(subset["is_open"].mean()),
                "long_resolution_share": float(subset["is_long_resolution"].mean()),
                "repeat_cluster_share": float(subset["is_repeat_cluster"].mean()),
                "median_resolution_days": float(subset["resolution_days"].median()),
            }
        )
    pd.DataFrame(drivers).merge(
        area_sorted[["council_district", "service_burden_score", "service_burden_class"]],
        on="council_district",
        how="left",
    ).sort_values("service_burden_score", ascending=False).to_csv(
        TABLES / "district_burden_drivers.csv", index=False
    )

    top_category = (
        df["standardized_category"].value_counts().rename_axis("category").reset_index(name="count")
    )
    summary = {
        "record_count": int(len(df)),
        "date_min": str(df["opened_date"].min()),
        "date_max": str(df["opened_date"].max()),
        "coordinate_completeness": float(df[["latitude", "longitude"]].notna().all(axis=1).mean()),
        "top_standardized_category": top_category.iloc[0].to_dict() if not top_category.empty else None,
        "median_resolution_days_overall": float(resolved["resolution_days"].median())
        if not resolved.empty
        else None,
        "unresolved_share_overall": float(df["is_open"].mean()),
        "long_resolution_share_overall": float(df["is_long_resolution"].mean()),
        "top_burden_council_district": area_sorted.iloc[0].to_dict() if not area_sorted.empty else None,
        "tables": [
            "top_infrastructure_request_categories.csv",
            "median_resolution_time_by_category.csv",
            "unresolved_open_requests_by_category.csv",
            "long_resolution_categories.csv",
            "monthly_request_volume.csv",
            "council_district_service_burden.csv",
            "district_burden_drivers.csv",
            "repeat_location_clusters.csv",
        ],
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote summary tables and {SUMMARY_FILE.name}.")


if __name__ == "__main__":
    main()
