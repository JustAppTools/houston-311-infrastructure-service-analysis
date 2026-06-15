# Technical Memo: Houston 311 Infrastructure Service Request Analysis

## Purpose

This V2 analysis identifies Houston infrastructure-service burden using public 311 request records and official council-district boundary context. The work emphasizes reproducible data acquisition, cleaning, QA/QC, resolution-time analysis, repeat-location screening, static map and chart production, and public-sector interpretation.

## Data

The project uses the City of Houston `Houston311_Archives` ArcGIS REST layer:

https://mycity2.houstontx.gov/gisweb01/rest/services/311/Houston311_Archives/MapServer/0

The V2 extract covers records opened from `2025-04-01` through `2025-06-30`. The pipeline downloaded `82,743` infrastructure-related records from the source query.

V2 also uses official `COH_Council_Districts` polygons from the Harris County/COHGIS boundary service:

https://www.gis.hctx.net/arcgis/rest/services/CoH/CoH_Boundaries/MapServer/0

## Methods

The pipeline filters 311 records by infrastructure-related request-type keywords, cleans core fields, standardizes categories, calculates resolution time in days, flags unresolved cases, flags long-resolution cases over `14` days, screens approximate repeat-location clusters, and writes summary outputs.

Council-district service burden is scored with a weighted percentile model:

- request density per square mile: `30%`
- median resolution time: `25%`
- unresolved share: `20%`
- long-resolution share: `15%`
- repeat-cluster share: `10%`

The score is classified as `Low`, `Medium`, `High`, or `Very High`.

## Key Findings

The April-June 2025 extract contains `82,743` cleaned infrastructure-related records. Coordinate completeness is `100%` after basic source-field screening.

`Solid Waste / Recycling` is the largest category with `43,194` requests. Its leading request types include missed recycling pickup, missed garbage pickup, missed heavy-trash pickup, container replacement, and related collection issues.

The overall median resolution time among records with usable closed dates is about `3.8` days. `Solid Waste / Recycling` has the highest median among major standardized categories at about `8.1` days.

The overall unresolved share is about `15.5%`. Among multi-record categories, `Drainage / Flooding` has the highest unresolved share at about `20.0%`, followed by `Solid Waste / Recycling` at about `18.8%`.

The V2 council-district burden score ranks district `H` highest with a score of `80.9`, classified as `Very High`. Districts `C`, `B`, `D`, `A`, and `K` classify as `High`.

Repeat-location screening detected `7,945` approximate coordinate/category clusters with at least three requests. These clusters are candidates for recurring-service review, not verified duplicate incidents.

## Recommended Interpretation

These findings should be treated as a public-data screening analysis for a bounded three-month period. They are useful for identifying candidate categories and areas for deeper review, not for official performance reporting.

High scores can reflect high request density, longer median resolution times, larger unresolved shares, larger long-resolution shares, or larger repeat-cluster shares. A high score does not by itself prove service failure or causal inequity.

## Limitations

The V2 analysis uses official district boundary polygons for display and area-normalized density, but council-district summaries still rely on district attributes in the source 311 records. It does not include population denominators.

The `Resolve_By_Time` field showed far-future values in the archive extract, so late/SLA findings are not reported. V2 uses a transparent `14` day long-resolution flag instead.

Request classification is keyword based. It is intentionally auditable but should be refined with a reviewed service-type crosswalk.

## Next Steps

- Build a reviewed service-request category crosswalk.
- Add official super-neighborhood polygons.
- Normalize request counts by population or households where appropriate.
- Add ACS vulnerability overlays.
- Compare multiple months or years to separate seasonal effects from persistent burden.
- Produce a polished PDF report or lightweight public web presentation.
