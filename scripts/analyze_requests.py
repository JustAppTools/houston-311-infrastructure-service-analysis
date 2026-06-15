import json

import numpy as np
import pandas as pd

from project_config import DATA_CONTEXT, DATA_PROCESSED, SCORE_WEIGHTS, TABLES, ensure_directories


CLEAN_FILE = DATA_PROCESSED / "houston_311_infrastructure_requests_cleaned.csv"
SUMMARY_FILE = DATA_PROCESSED / "analysis_summary.json"
BOUNDARY_FILE = DATA_CONTEXT / "council_district_boundaries.geojson"
DEMOGRAPHICS_FILE = DATA_CONTEXT / "council_district_demographics.csv"
SQFT_PER_SQMI = 27_878_400
THEME_GROUPS = {
    "solid_waste_recycling": ["Solid Waste / Recycling"],
    "water_sewer_drainage": ["Water", "Sewer / Wastewater", "Drainage / Flooding"],
    "roads_signals_sidewalks": [
        "Road / Pothole / Bridge",
        "Traffic Signals / Lighting",
        "Sidewalk / Bike Lane",
    ],
}


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


def demographic_table() -> pd.DataFrame:
    columns = [
        "council_district",
        "estimated_population",
        "estimated_households",
        "poverty_rate",
        "no_vehicle_household_share",
        "median_household_income_weighted",
    ]
    if not DEMOGRAPHICS_FILE.exists():
        return pd.DataFrame(columns=columns)
    df = pd.read_csv(DEMOGRAPHICS_FILE)
    for col in columns:
        if col not in df.columns:
            df[col] = np.nan
    return df


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


def rate_per_10k(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return np.where(denominator.fillna(0) > 0, numerator / denominator * 10000, np.nan)


def normalized_district_label(series: pd.Series, missing_label: str = "UNASSIGNED") -> pd.Series:
    return (
        series.fillna(missing_label)
        .astype(str)
        .str.strip()
        .replace({"": missing_label, "nan": missing_label, "None": missing_label})
    )


def json_safe(value):
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


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

    quality = (
        df.groupby("council_district", dropna=False)
        .agg(
            request_count=("case_number", "count"),
            records_with_coordinates=("latitude", "count"),
            spatially_assigned_records=("spatial_council_district", "count"),
        )
        .reset_index()
    )
    quality = quality[quality["council_district"].astype(str).str.match(r"^[A-K]$")].copy()
    quality["coordinate_completeness"] = quality["records_with_coordinates"] / quality["request_count"]
    quality["spatial_assignment_share"] = quality["spatially_assigned_records"] / quality["request_count"]
    if {"source_council_district", "spatial_council_district"}.issubset(df.columns):
        comparable = df.dropna(subset=["source_council_district", "spatial_council_district"]).copy()
        comparable["source_council_district"] = comparable["source_council_district"].astype(str).str.strip()
        comparable["spatial_council_district"] = comparable["spatial_council_district"].astype(str).str.strip()
        comparable["source_spatial_match"] = (
            comparable["source_council_district"] == comparable["spatial_council_district"]
        )
        agreement = (
            comparable.groupby("council_district")["source_spatial_match"]
            .mean()
            .reset_index(name="source_spatial_district_agreement")
        )
        quality = quality.merge(agreement, on="council_district", how="left")
    else:
        quality["source_spatial_district_agreement"] = np.nan
    quality.sort_values("council_district").to_csv(TABLES / "district_data_quality.csv", index=False)

    assignment_diag = df.copy()
    assignment_diag["source_district_label"] = normalized_district_label(
        assignment_diag["source_council_district"]
    )
    assignment_diag["spatial_district_label"] = normalized_district_label(
        assignment_diag["spatial_council_district"]
    )
    source_totals = (
        assignment_diag.groupby("source_district_label")
        .size()
        .reset_index(name="source_district_total")
    )
    assignment_matrix = (
        assignment_diag.groupby(["source_district_label", "spatial_district_label"])
        .size()
        .reset_index(name="request_count")
        .merge(source_totals, on="source_district_label", how="left")
    )
    assignment_matrix["share_of_source_district"] = (
        assignment_matrix["request_count"] / assignment_matrix["source_district_total"]
    )
    assignment_matrix.sort_values(
        ["source_district_label", "request_count"], ascending=[True, False]
    ).to_csv(TABLES / "source_spatial_assignment_matrix.csv", index=False)

    scored_district_mask = df["council_district"].astype(str).str.strip().str.match(r"^[A-K]$", na=False)
    unscored = df[~scored_district_mask].copy()
    if not unscored.empty:
        unscored["source_district_label"] = normalized_district_label(
            unscored["source_council_district"]
        )
        unscored["spatial_district_label"] = normalized_district_label(
            unscored["spatial_council_district"]
        )
        unscored["unscored_reason"] = np.where(
            unscored["source_district_label"].str.match(r"^[A-K]$"),
            "standard_source_district_not_spatially_assigned",
            "nonstandard_or_missing_source_district",
        )
        unscored_diag = (
            unscored.groupby(
                [
                    "unscored_reason",
                    "source_district_label",
                    "spatial_district_label",
                    "standardized_category",
                    "quality_flags",
                ],
                dropna=False,
            )
            .size()
            .reset_index(name="request_count")
            .sort_values("request_count", ascending=False)
        )
    else:
        unscored_diag = pd.DataFrame(
            columns=[
                "unscored_reason",
                "source_district_label",
                "spatial_district_label",
                "standardized_category",
                "quality_flags",
                "request_count",
            ]
        )
    unscored_diag.to_csv(TABLES / "unscored_request_diagnostics.csv", index=False)

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
    area = area.merge(demographic_table(), on="council_district", how="left")
    area["unresolved_share"] = area["unresolved_count"] / area["request_count"]
    area["long_resolution_share"] = area["long_resolution_count"] / area["request_count"]
    area["repeat_cluster_share"] = area["repeat_clustered_count"] / area["request_count"]
    area["requests_per_sq_mile"] = area["request_count"] / area["district_area_sq_mi"]
    area["requests_per_10k_residents"] = rate_per_10k(
        area["request_count"],
        area.get("estimated_population", pd.Series(np.nan, index=area.index)),
    )
    area["requests_per_10k_households"] = rate_per_10k(
        area["request_count"],
        area.get("estimated_households", pd.Series(np.nan, index=area.index)),
    )
    area["resident_rate_percentile"] = percentile_rank(
        area["requests_per_10k_residents"].fillna(area["requests_per_sq_mile"])
    )
    area["household_rate_percentile"] = percentile_rank(
        area["requests_per_10k_households"].fillna(area["requests_per_sq_mile"])
    )
    area["median_resolution_percentile"] = percentile_rank(area["median_resolution_days"])
    area["unresolved_share_percentile"] = percentile_rank(area["unresolved_share"])
    area["long_resolution_share_percentile"] = percentile_rank(area["long_resolution_share"])
    area["repeat_cluster_share_percentile"] = percentile_rank(area["repeat_cluster_share"])
    component_specs = [
        ("resident_request_rate", "resident_rate_percentile"),
        ("household_request_rate", "household_rate_percentile"),
        ("median_resolution_days", "median_resolution_percentile"),
        ("unresolved_share", "unresolved_share_percentile"),
        ("long_resolution_share", "long_resolution_share_percentile"),
        ("repeat_cluster_share", "repeat_cluster_share_percentile"),
    ]
    for component, percentile_col in component_specs:
        area[f"{component}_component"] = area[percentile_col] * SCORE_WEIGHTS[component]
    area["service_burden_score"] = sum(
        area[f"{component}_component"] for component, _ in component_specs
    )
    area["service_burden_class"] = area["service_burden_score"].apply(burden_class)
    area_sorted = area.sort_values("service_burden_score", ascending=False)
    area_sorted.to_csv(
        TABLES / "council_district_service_burden.csv", index=False
    )
    component_rows = []
    component_labels = {
        "resident_request_rate": "Resident request rate or density fallback",
        "household_request_rate": "Household request rate or density fallback",
        "median_resolution_days": "Median resolution days",
        "unresolved_share": "Unresolved share",
        "long_resolution_share": "Long-resolution share",
        "repeat_cluster_share": "Repeat-cluster share",
    }
    for _, row in area_sorted.iterrows():
        for component, percentile_col in component_specs:
            component_rows.append(
                {
                    "council_district": row["council_district"],
                    "component": component,
                    "component_label": component_labels[component],
                    "weight": SCORE_WEIGHTS[component],
                    "percentile": row[percentile_col],
                    "weighted_points": row[f"{component}_component"],
                    "service_burden_score": row["service_burden_score"],
                    "service_burden_class": row["service_burden_class"],
                }
            )
    pd.DataFrame(component_rows).to_csv(TABLES / "score_components.csv", index=False)

    district_base = area[
        [
            "council_district",
            "district_area_sq_mi",
            "estimated_population",
            "estimated_households",
        ]
    ].copy()

    def build_subset_score(source_df: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
        grouped = (
            source_df[source_df["council_district"].isin(area["council_district"])]
            .groupby("council_district")
            .agg(
                request_count=("case_number", "count"),
                unresolved_count=("is_open", "sum"),
                long_resolution_count=("is_long_resolution", "sum"),
                repeat_clustered_count=("is_repeat_cluster", "sum"),
                median_resolution_days=("resolution_days", "median"),
            )
            .reset_index()
        )
        subset_area = district_base.merge(grouped, on="council_district", how="left")
        for col in ["request_count", "unresolved_count", "long_resolution_count", "repeat_clustered_count"]:
            subset_area[col] = subset_area[col].fillna(0)
        subset_area["unresolved_share"] = np.where(
            subset_area["request_count"] > 0,
            subset_area["unresolved_count"] / subset_area["request_count"],
            0,
        )
        subset_area["long_resolution_share"] = np.where(
            subset_area["request_count"] > 0,
            subset_area["long_resolution_count"] / subset_area["request_count"],
            0,
        )
        subset_area["repeat_cluster_share"] = np.where(
            subset_area["request_count"] > 0,
            subset_area["repeat_clustered_count"] / subset_area["request_count"],
            0,
        )
        subset_area["requests_per_sq_mile"] = subset_area["request_count"] / subset_area["district_area_sq_mi"]
        subset_area["requests_per_10k_residents"] = rate_per_10k(
            subset_area["request_count"],
            subset_area.get("estimated_population", pd.Series(np.nan, index=subset_area.index)),
        )
        subset_area["requests_per_10k_households"] = rate_per_10k(
            subset_area["request_count"],
            subset_area.get("estimated_households", pd.Series(np.nan, index=subset_area.index)),
        )
        subset_area["resident_rate_percentile"] = percentile_rank(
            subset_area["requests_per_10k_residents"].fillna(subset_area["requests_per_sq_mile"])
        )
        subset_area["household_rate_percentile"] = percentile_rank(
            subset_area["requests_per_10k_households"].fillna(subset_area["requests_per_sq_mile"])
        )
        subset_area["median_resolution_percentile"] = percentile_rank(
            subset_area["median_resolution_days"].fillna(0)
        )
        subset_area["unresolved_share_percentile"] = percentile_rank(subset_area["unresolved_share"])
        subset_area["long_resolution_share_percentile"] = percentile_rank(subset_area["long_resolution_share"])
        subset_area["repeat_cluster_share_percentile"] = percentile_rank(subset_area["repeat_cluster_share"])
        for component, percentile_col in component_specs:
            subset_area[f"{component}_component"] = subset_area[percentile_col] * weights[component]
        subset_area["screening_score"] = sum(
            subset_area[f"{component}_component"] for component, _ in component_specs
        )
        subset_area["screening_class"] = subset_area["screening_score"].apply(burden_class)
        return subset_area.sort_values("screening_score", ascending=False)

    equal_weights = {component: 1 / len(component_specs) for component, _ in component_specs}
    non_solid = df[df["standardized_category"] != "Solid Waste / Recycling"].copy()
    non_solid_score = build_subset_score(non_solid, SCORE_WEIGHTS)
    non_solid_score.to_csv(TABLES / "council_district_non_solid_waste_screening.csv", index=False)
    equal_weight_score = build_subset_score(df, equal_weights)
    equal_weight_score.to_csv(TABLES / "council_district_equal_weight_sensitivity.csv", index=False)
    non_solid_equal_score = build_subset_score(non_solid, equal_weights)

    category_density_rows = []
    valid_districts = area["council_district"].tolist()
    for category, category_df in df[df["council_district"].isin(valid_districts)].groupby("standardized_category"):
        counts = (
            category_df.groupby("council_district")
            .size()
            .reindex(valid_districts, fill_value=0)
            .rename("request_count")
            .reset_index()
        )
        counts["standardized_category"] = category
        counts = counts.merge(
            district_base[["council_district", "district_area_sq_mi"]],
            on="council_district",
            how="left",
        )
        counts["requests_per_sq_mile"] = counts["request_count"] / counts["district_area_sq_mi"]
        counts["category_density_percentile"] = percentile_rank(counts["requests_per_sq_mile"])
        category_density_rows.append(counts)
    category_components = pd.concat(category_density_rows, ignore_index=True)
    category_components.to_csv(TABLES / "category_balanced_density_components.csv", index=False)
    category_balanced = (
        category_components.groupby("council_district")
        .agg(
            category_balanced_density_score=("category_density_percentile", "mean"),
            categories_used=("standardized_category", "nunique"),
        )
        .reset_index()
        .merge(
            area_sorted[
                [
                    "council_district",
                    "service_burden_score",
                    "service_burden_class",
                    "request_count",
                    "requests_per_sq_mile",
                ]
            ],
            on="council_district",
            how="left",
        )
        .sort_values("category_balanced_density_score", ascending=False)
    )
    category_balanced["category_balanced_class"] = category_balanced[
        "category_balanced_density_score"
    ].apply(burden_class)
    category_balanced.to_csv(TABLES / "category_balanced_district_density.csv", index=False)

    baseline_rank = area_sorted[["council_district"]].reset_index(drop=True)
    baseline_rank["baseline_rank"] = baseline_rank.index + 1

    def scenario_rows(name: str, score_df: pd.DataFrame, score_col: str = "screening_score") -> pd.DataFrame:
        rows = score_df[["council_district", score_col]].copy()
        rows = rows.rename(columns={score_col: "score"}).sort_values("score", ascending=False)
        rows["scenario"] = name
        rows["rank"] = range(1, len(rows) + 1)
        rows = rows.merge(baseline_rank, on="council_district", how="left")
        rows["rank_delta_from_baseline"] = rows["rank"] - rows["baseline_rank"]
        return rows[["scenario", "council_district", "rank", "baseline_rank", "rank_delta_from_baseline", "score"]]

    sensitivity = pd.concat(
        [
            scenario_rows("baseline_area_density_fallback", area_sorted.rename(columns={"service_burden_score": "screening_score"})),
            scenario_rows("equal_component_weights", equal_weight_score),
            scenario_rows("non_solid_waste_current_weights", non_solid_score),
            scenario_rows("non_solid_waste_equal_weights", non_solid_equal_score),
            scenario_rows("category_balanced_density_only", category_balanced, "category_balanced_density_score"),
        ],
        ignore_index=True,
    )
    sensitivity.to_csv(TABLES / "score_sensitivity_rankings.csv", index=False)

    thematic_rows = []
    for theme, categories in THEME_GROUPS.items():
        subset = df[df["standardized_category"].isin(categories)]
        if subset.empty:
            continue
        theme_area = (
            subset[subset["council_district"].isin(area["council_district"])]
            .groupby("council_district")
            .agg(
                request_count=("case_number", "count"),
                unresolved_count=("is_open", "sum"),
                long_resolution_count=("is_long_resolution", "sum"),
                repeat_clustered_count=("is_repeat_cluster", "sum"),
                median_resolution_days=("resolution_days", "median"),
            )
            .reset_index()
        )
        theme_area = area[["council_district", "district_area_sq_mi", "estimated_population", "estimated_households"]].merge(
            theme_area, on="council_district", how="left"
        )
        for col in ["request_count", "unresolved_count", "long_resolution_count", "repeat_clustered_count"]:
            theme_area[col] = theme_area[col].fillna(0)
        theme_area["theme"] = theme
        theme_area["requests_per_sq_mile"] = theme_area["request_count"] / theme_area["district_area_sq_mi"]
        theme_area["requests_per_10k_residents"] = rate_per_10k(
            theme_area["request_count"],
            theme_area.get("estimated_population", pd.Series(np.nan, index=theme_area.index)),
        )
        theme_area["unresolved_share"] = np.where(
            theme_area["request_count"] > 0,
            theme_area["unresolved_count"] / theme_area["request_count"],
            np.nan,
        )
        theme_area["long_resolution_share"] = np.where(
            theme_area["request_count"] > 0,
            theme_area["long_resolution_count"] / theme_area["request_count"],
            np.nan,
        )
        thematic_rows.append(theme_area)
    if thematic_rows:
        pd.concat(thematic_rows, ignore_index=True).sort_values(
            ["theme", "requests_per_10k_residents"], ascending=[True, False]
        ).to_csv(TABLES / "thematic_district_burden.csv", index=False)

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
    district_score_request_count = int(area_sorted["request_count"].sum()) if not area_sorted.empty else 0
    records_not_in_district_score = int(len(df) - district_score_request_count)
    top_category_record = top_category.iloc[0].to_dict() if not top_category.empty else None
    if top_category_record:
        top_category_record["share"] = float(top_category_record["count"] / len(df))
    quality_alerts = (
        quality[quality["spatial_assignment_share"] < 0.9]
        .sort_values("spatial_assignment_share")
        .to_dict(orient="records")
    )
    summary = {
        "record_count": int(len(df)),
        "district_score_request_count": district_score_request_count,
        "records_not_in_district_score": records_not_in_district_score,
        "date_min": str(df["opened_date"].min()),
        "date_max": str(df["opened_date"].max()),
        "coordinate_completeness": float(df[["latitude", "longitude"]].notna().all(axis=1).mean()),
        "top_standardized_category": top_category_record,
        "median_resolution_days_overall": float(resolved["resolution_days"].median())
        if not resolved.empty
        else None,
        "unresolved_share_overall": float(df["is_open"].mean()),
        "long_resolution_share_overall": float(df["is_long_resolution"].mean()),
        "repeat_cluster_share_overall": float(df["is_repeat_cluster"].mean()),
        "top_burden_council_district": area_sorted.iloc[0].to_dict() if not area_sorted.empty else None,
        "top_non_solid_waste_council_district": non_solid_score.iloc[0].to_dict() if not non_solid_score.empty else None,
        "top_category_balanced_council_district": category_balanced.iloc[0].to_dict() if not category_balanced.empty else None,
        "district_quality_alerts": quality_alerts,
        "tables": [
            "top_infrastructure_request_categories.csv",
            "median_resolution_time_by_category.csv",
            "unresolved_open_requests_by_category.csv",
            "long_resolution_categories.csv",
            "monthly_request_volume.csv",
            "council_district_service_burden.csv",
            "district_burden_drivers.csv",
            "repeat_location_clusters.csv",
            "thematic_district_burden.csv",
            "district_data_quality.csv",
            "source_spatial_assignment_matrix.csv",
            "unscored_request_diagnostics.csv",
            "score_components.csv",
            "council_district_non_solid_waste_screening.csv",
            "council_district_equal_weight_sensitivity.csv",
            "category_balanced_density_components.csv",
            "category_balanced_district_density.csv",
            "score_sensitivity_rankings.csv",
        ],
    }
    SUMMARY_FILE.write_text(json.dumps(json_safe(summary), indent=2), encoding="utf-8")
    print(f"Wrote summary tables and {SUMMARY_FILE.name}.")


if __name__ == "__main__":
    main()
