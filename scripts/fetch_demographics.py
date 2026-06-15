import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

from project_config import DATA_CONTEXT, ensure_directories
from spatial_utils import assign_point_to_district, load_geojson


ACS_YEAR = "2024"
ACS_DATASET = "acs/acs5"
TRACT_LAYER_URL = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/7"
BOUNDARY_FILE = DATA_CONTEXT / "council_district_boundaries.geojson"
TRACT_POINTS_FILE = DATA_CONTEXT / "acs_tract_points.csv"
DISTRICT_DEMOGRAPHICS_FILE = DATA_CONTEXT / "council_district_demographics.csv"
DEMOGRAPHICS_METADATA = DATA_CONTEXT / "demographics_metadata.json"

DEFAULT_COUNTIES = ["201", "157", "339"]

ACS_VARIABLES = {
    "B01003_001E": "population",
    "B11001_001E": "households",
    "B19013_001E": "median_household_income",
    "B17001_001E": "poverty_universe",
    "B17001_002E": "poverty_count",
    "B25044_001E": "vehicle_universe",
    "B25044_003E": "owner_no_vehicle",
    "B25044_010E": "renter_no_vehicle",
}


def get_json(url: str, params: dict | None = None):
    full_url = url if params is None else f"{url}?{urlencode(params)}"
    with urlopen(full_url, timeout=120) as response:
        text = response.read().decode("utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(text[:500].strip()) from exc


def fetch_acs_for_county(county: str, api_key: str | None) -> pd.DataFrame:
    variables = ["NAME", *ACS_VARIABLES.keys()]
    url = f"https://api.census.gov/data/{ACS_YEAR}/{ACS_DATASET}"
    params = {
        "get": ",".join(variables),
        "for": "tract:*",
        "in": f"state:48 county:{county}",
    }
    if api_key:
        params["key"] = api_key
    payload = get_json(url, params)
    header, rows = payload[0], payload[1:]
    df = pd.DataFrame(rows, columns=header)
    df["GEOID"] = df["state"] + df["county"] + df["tract"]
    df = df.rename(columns=ACS_VARIABLES)
    for col in ACS_VARIABLES.values():
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def fetch_tract_points(counties: list[str]) -> pd.DataFrame:
    where = "STATE = '48' AND COUNTY IN ({})".format(
        ",".join(f"'{county}'" for county in counties)
    )
    payload = get_json(
        f"{TRACT_LAYER_URL}/query",
        {
            "where": where,
            "outFields": "GEOID,NAME,STATE,COUNTY,TRACT,INTPTLAT,INTPTLON,AREALAND",
            "returnGeometry": "false",
            "resultRecordCount": "100000",
            "f": "json",
        },
    )
    rows = [feature.get("attributes", {}) for feature in payload.get("features", [])]
    df = pd.DataFrame(rows)
    df["INTPTLAT"] = pd.to_numeric(df["INTPTLAT"], errors="coerce")
    df["INTPTLON"] = pd.to_numeric(df["INTPTLON"], errors="coerce")
    return df


def weighted_average(values: pd.Series, weights: pd.Series) -> float | None:
    valid = values.notna() & weights.notna() & (weights > 0)
    if not valid.any():
        return None
    return float((values[valid] * weights[valid]).sum() / weights[valid].sum())


def aggregate_to_districts(tracts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for district, subset in tracts.dropna(subset=["assigned_council_district"]).groupby(
        "assigned_council_district"
    ):
        population = subset["population"].sum()
        households = subset["households"].sum()
        poverty_universe = subset["poverty_universe"].sum()
        vehicle_universe = subset["vehicle_universe"].sum()
        no_vehicle = subset["owner_no_vehicle"].sum() + subset["renter_no_vehicle"].sum()
        rows.append(
            {
                "council_district": district,
                "tract_centroid_count": int(len(subset)),
                "estimated_population": int(population),
                "estimated_households": int(households),
                "poverty_count": int(subset["poverty_count"].sum()),
                "poverty_universe": int(poverty_universe),
                "poverty_rate": float(subset["poverty_count"].sum() / poverty_universe)
                if poverty_universe
                else None,
                "vehicle_universe": int(vehicle_universe),
                "no_vehicle_households": int(no_vehicle),
                "no_vehicle_household_share": float(no_vehicle / vehicle_universe)
                if vehicle_universe
                else None,
                "median_household_income_weighted": weighted_average(
                    subset["median_household_income"], subset["households"]
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("council_district")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch ACS tract demographics for V3.")
    parser.add_argument("--counties", nargs="+", default=DEFAULT_COUNTIES)
    parser.add_argument("--census-api-key", default=os.getenv("CENSUS_API_KEY"))
    args = parser.parse_args()

    ensure_directories()
    boundaries = load_geojson(BOUNDARY_FILE)
    if boundaries is None:
        raise SystemExit("Missing council district boundaries. Run scripts/fetch_boundaries.py first.")

    access_error = None
    try:
        acs = pd.concat(
            [fetch_acs_for_county(county, args.census_api_key) for county in args.counties],
            ignore_index=True,
        )
        tracts = fetch_tract_points(args.counties)
        merged = tracts.merge(acs, on="GEOID", how="left")
        merged["assigned_council_district"] = [
            assign_point_to_district(lon, lat, boundaries)
            for lon, lat in zip(merged["INTPTLON"], merged["INTPTLAT"])
        ]
        merged.to_csv(TRACT_POINTS_FILE, index=False)

        district = aggregate_to_districts(merged)
        district.to_csv(DISTRICT_DEMOGRAPHICS_FILE, index=False)
    except Exception as exc:
        access_error = str(exc)
        merged = pd.DataFrame()
        district = pd.DataFrame(
            columns=[
                "council_district",
                "tract_centroid_count",
                "estimated_population",
                "estimated_households",
                "poverty_count",
                "poverty_universe",
                "poverty_rate",
                "vehicle_universe",
                "no_vehicle_households",
                "no_vehicle_household_share",
                "median_household_income_weighted",
            ]
        )
        district.to_csv(DISTRICT_DEMOGRAPHICS_FILE, index=False)

    metadata = {
        "acs_year": ACS_YEAR,
        "acs_dataset": ACS_DATASET,
        "acs_variables": ACS_VARIABLES,
        "census_api_url": f"https://api.census.gov/data/{ACS_YEAR}/{ACS_DATASET}",
        "tract_layer_url": TRACT_LAYER_URL,
        "counties": args.counties,
        "tracts_downloaded": int(len(merged)),
        "tract_centroids_assigned_to_council_districts": int(
            merged["assigned_council_district"].notna().sum()
        )
        if not merged.empty
        else 0,
        "district_rows_written": int(len(district)),
        "used_api_key": bool(args.census_api_key),
        "access_error": access_error,
        "access_limitation": (
            "The Census API returned a non-JSON response in this environment. Set CENSUS_API_KEY and rerun scripts/fetch_demographics.py to enable ACS population and household rates."
            if access_error
            else None
        ),
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "method_note": "District demographics are approximated by assigning ACS tract internal points to official council district polygons. This is not areal interpolation.",
    }
    DEMOGRAPHICS_METADATA.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    if access_error:
        print(f"Demographic fetch skipped: {access_error[:140]}")
    else:
        print(f"Wrote demographics for {len(district)} council districts.")


if __name__ == "__main__":
    main()
