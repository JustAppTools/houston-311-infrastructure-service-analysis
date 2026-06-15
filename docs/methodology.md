# Methodology

## 1. Data Acquisition

`scripts/fetch_data.py` queries the City of Houston 311 archive layer in pages. The default V3 extract covers records opened from `2025-04-01` through `2025-06-30`.

`scripts/fetch_boundaries.py` downloads official council district polygons from the Harris County/COHGIS `CoH_Boundaries` service.

`scripts/fetch_demographics.py` supports 2024 ACS 5-year tract demographic retrieval through the Census API. In this environment, the API returned a key-required response. Set `CENSUS_API_KEY` and rerun the script to generate population and household rates.

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

## 4. Scoring

The V3 burden score uses a weighted percentile model:

- request rate per 10,000 residents when ACS is available, otherwise requests per square mile: `25%`
- request rate per 10,000 households when ACS is available, otherwise requests per square mile: `15%`
- median resolution time: `20%`
- unresolved share: `15%`
- long-resolution share: `10%`
- repeat-cluster share: `15%`

Scores are classified as:

- `Low`: less than 25
- `Medium`: 25 to less than 50
- `High`: 50 to less than 75
- `Very High`: 75 or higher

## 5. Outputs

The pipeline produces cleaned CSV/GeoJSON data, summary tables, category charts, point maps, repeat-cluster maps, thematic request-rate maps, and the main council-district burden choropleth.
