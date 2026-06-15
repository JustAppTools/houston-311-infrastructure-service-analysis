# Methodology

## 1. Data Acquisition

`scripts/fetch_data.py` queries the City of Houston ArcGIS REST archive layer in pages. The default V2 extract covers records opened from `2025-04-01` through `2025-06-30`.

The source query filters for infrastructure-related request types using a transparent keyword screen:

- water
- sewer
- drainage and flooding
- potholes, streets, bridges, and sidewalks
- traffic signals and lighting
- dumping, trash, garbage, recycling, debris, and containers

`scripts/fetch_boundaries.py` downloads official council district polygons from the Harris County/COHGIS `CoH_Boundaries` service. Boundary geometry is saved in `data/processed/context/`.

## 2. Cleaning and QA/QC

`scripts/clean_311_requests.py` creates the processed analytical dataset. It:

- converts ArcGIS epoch-millisecond date fields to timestamps
- standardizes request categories with keyword rules in `scripts/project_config.py`
- calculates `resolution_days` for records with usable opened and closed dates
- flags open/unresolved records using status, state, and closed-date availability
- flags long-resolution records where `resolution_days > 14`
- screens for missing dates, missing coordinates, low-confidence categories, and far-future closed dates
- excludes source address and narrative fields from the processed output

Far-future closed dates are treated as invalid and excluded from resolution-time calculations because they can distort median resolution times.

## 3. Repeat-Location Screening

V2 adds approximate repeat-location screening. Coordinates are rounded to three decimals, roughly a 100-meter grid in Houston. Records are flagged as repeat-clustered when at least three same-category records share a council district and rounded coordinate bin.

This is a screening method, not address-level deduplication.

## 4. Tables and Scoring

`scripts/analyze_requests.py` generates summary tables for:

- top request categories by count
- median resolution time by category
- unresolved/open count and share by category
- long-resolution count and share by category
- monthly request volume
- council-district service burden
- district burden drivers
- repeat-location clusters

The V2 service-burden score is a percentile-based screen using:

- request density per square mile, weight `30%`
- median resolution time, weight `25%`
- unresolved share, weight `20%`
- long-resolution share, weight `15%`
- repeat-cluster share, weight `10%`

Scores are classified as:

- `Low`: less than 25
- `Medium`: 25 to less than 50
- `High`: 50 to less than 75
- `Very High`: 75 or higher

## 5. Figures and Maps

`scripts/make_maps.py` uses Pillow to generate static PNG charts and maps without requiring heavyweight local GIS libraries.

Maps are coordinate plots from the source latitude/longitude fields with official council-district boundary context where feasible. The flagship burden map is an official council-district polygon choropleth with driver callouts.
