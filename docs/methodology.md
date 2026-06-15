# Methodology

## 1. Data Acquisition

`scripts/fetch_data.py` queries the City of Houston 311 archive layer in pages. The default V3 extract covers records opened from `2025-04-01` through `2025-06-30`.

`scripts/fetch_boundaries.py` downloads official council district polygons from the Harris County/COHGIS `CoH_Boundaries` service.

`scripts/fetch_context.py` downloads optional H-GAC major road and major river/bayou linework for visual orientation in the maps.

`scripts/fetch_demographics.py` supports 2024 ACS 5-year tract demographic retrieval through the Census API. In this environment, the API rejected the supplied key. Set a valid `CENSUS_API_KEY` and rerun the script to generate population and household rates.

## 2. Cleaning and QA/QC

`scripts/clean_311_requests.py`:

- converts ArcGIS date fields
- standardizes infrastructure categories
- calculates resolution days
- flags unresolved and long-resolution records
- flags missing or invalid dates and coordinates
- assigns council districts by point-in-polygon against official district polygons
- keeps the source council district field for audit comparison
- excludes address and narrative fields from processed outputs

## 3. Repeat-Location Screening

Coordinates are rounded to three decimals, roughly a 100-meter grid in Houston. Records are flagged as repeat-clustered when at least three same-category records share a council district and rounded coordinate bin. This is a screening method, not address-level deduplication.

## 4. Screening Score

The V3 screening score uses a weighted percentile model:

- request rate per 10,000 residents when ACS is available, otherwise requests per square mile: `25%`
- request rate per 10,000 households when ACS is available, otherwise requests per square mile: `15%`
- median resolution time: `20%`
- unresolved share: `15%`
- long-resolution share: `10%`
- repeat-cluster share: `15%`

These settings are exposed in `config/analysis_config.json`.

Scores are classified as:

- `Low`: less than 25
- `Medium`: 25 to less than 50
- `High`: 50 to less than 75
- `Very High`: 75 or higher

The committed output uses area-density fallback because ACS normalization did not run with a valid Census API key in this environment. `outputs/tables/score_sensitivity_rankings.csv` compares the baseline score with equal-weight, non-solid-waste, and category-balanced scenarios.

## 5. Sensitivity and Alternate Scores

The pipeline produces several diagnostics for score robustness:

- `council_district_non_solid_waste_screening.csv` excludes `Solid Waste / Recycling` and recomputes the weighted score.
- `category_balanced_district_density.csv` averages district density percentiles across request categories so no single high-volume category dominates the density comparison.
- `council_district_equal_weight_sensitivity.csv` recomputes the score with equal component weights.
- `score_sensitivity_rankings.csv` compares ranks across baseline and sensitivity scenarios.

## 6. Outputs

The pipeline produces cleaned CSV/GeoJSON data, summary tables, GIS-ready GeoJSON layers, category charts, point maps, repeat-cluster maps, thematic request-rate maps, sensitivity maps, QA maps, and the main council-district screening choropleth.

The V3.1 public showcase adds a static `index.html` page that reads generated CSV tables and displays district metrics alongside the map outputs. The page is designed for GitHub Pages and does not require a backend.

## 7. Data Quality Outputs

`outputs/tables/district_data_quality.csv` summarizes coordinate completeness, spatial assignment share, and source-vs-spatial council district agreement by district. These metrics are audit aids and are not part of the service-burden score.

`outputs/tables/source_spatial_assignment_matrix.csv` cross-tabulates source council district labels against point-in-polygon district assignments. `outputs/tables/unscored_request_diagnostics.csv` summarizes records not included in the council-district score total.
