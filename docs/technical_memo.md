# Technical Memo: Houston 311 Infrastructure Service Request Analysis

## Purpose

This V1 analysis identifies Houston infrastructure-service burden using public 311 request records. The work emphasizes reproducible data acquisition, cleaning, QA/QC, resolution-time analysis, static map and chart production, and public-sector interpretation.

## Data

The project uses the City of Houston `Houston311_Archives` ArcGIS REST layer:

https://mycity2.houstontx.gov/gisweb01/rest/services/311/Houston311_Archives/MapServer/0

The V1 extract covers records opened from `2025-06-01` through `2025-06-30`. The pipeline downloaded `33,172` infrastructure-related records from the source query.

## Methods

The pipeline filters 311 records by infrastructure-related request-type keywords, cleans core fields, standardizes categories, calculates resolution time in days, flags unresolved cases, flags long-resolution cases over `14` days, and writes summary outputs.

Council-district service burden is scored with a weighted percentile model:

- request volume: `35%`
- median resolution time: `25%`
- unresolved share: `20%`
- long-resolution share: `20%`

The score is classified as `Low`, `Medium`, `High`, or `Very High`.

## Key Findings

The June 2025 extract contains `33,172` cleaned infrastructure-related records. Coordinate completeness is `100%` after basic source-field screening.

`Solid Waste / Recycling` is the largest category with `19,707` requests. Its leading request types include missed recycling pickup, missed garbage pickup, missed heavy-trash pickup, container replacement, and related collection issues.

The overall median resolution time among records with usable closed dates is about `6.8` days. `Solid Waste / Recycling` has the highest median among major standardized categories at about `13.2` days.

The overall unresolved share is about `14.1%`. Among multi-record categories, `Drainage / Flooding` has the highest unresolved share at about `22.3%`, followed by `Solid Waste / Recycling` at about `17.1%`.

The V1 council-district burden screen ranks district `C` highest with a score of `84.6`, classified as `Very High`. District `B` also falls in the `Very High` class. Districts `D`, `A`, `H`, `E`, and `I` classify as `High` in the V1 screen.

## Recommended Interpretation

These findings should be treated as a public-data screening analysis for a bounded month. They are useful for identifying candidate categories and areas for deeper review, not for official performance reporting.

High scores can reflect high request volume, longer median resolution times, larger unresolved shares, or larger long-resolution shares. A high score does not by itself prove service failure or causal inequity.

## Limitations

The V1 analysis does not use official district boundary polygons or population denominators. Council-district summaries rely on district attributes in the source 311 records.

The `Resolve_By_Time` field showed far-future values in the archive extract, so late/SLA findings are not reported. V1 uses a transparent `14` day long-resolution flag instead.

Request classification is keyword based. It is intentionally auditable but should be refined in V2 with a reviewed service-type crosswalk.

## Next Steps for V2

- Build a reviewed service-request category crosswalk.
- Add official council district and super-neighborhood polygons.
- Normalize request counts by population or households where appropriate.
- Add ACS vulnerability overlays.
- Add repeat-request clustering near shared locations.
- Compare multiple months or years to separate seasonal effects from persistent burden.
- Produce a polished PDF report or lightweight public web presentation.
