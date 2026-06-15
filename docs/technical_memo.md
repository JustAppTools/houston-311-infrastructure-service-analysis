# Technical Memo: Houston 311 Infrastructure Service Request Analysis

## Purpose

This V3 analysis identifies Houston infrastructure-service burden using public 311 request records, official council district polygons, spatial district assignment, repeat-location screening, and static GIS outputs.

## Data

The V3 extract covers records opened from `2025-04-01` through `2025-06-30`. The pipeline downloaded `82,743` infrastructure-related records from the City of Houston 311 archive.

Official council district polygons come from the Harris County/COHGIS `CoH_Boundaries` service.

The pipeline also supports 2024 ACS 5-year demographic normalization. In this environment, the Census API returned a key-required response, so ACS rates were not committed. The score falls back to requests per square mile where population and household rates are unavailable.

## Methods

The pipeline filters infrastructure-related 311 records, standardizes categories, calculates resolution time, flags unresolved and long-resolution records, assigns council districts with point-in-polygon logic, screens approximate repeat-location clusters, and generates static outputs.

The burden score combines request-rate, median resolution, unresolved share, long-resolution share, and repeat-cluster share. If ACS data is available, the rate components use residents and households. If ACS data is unavailable, area density is used as the rate fallback.

## Key Findings

The April-June 2025 extract contains `82,743` cleaned infrastructure-related records. Coordinate completeness is `100%` after basic source-field screening.

`Solid Waste / Recycling` is the largest category with `43,194` requests. Overall median resolution time is about `3.8` days. Overall unresolved share is about `15.5%`.

The V3 council-district burden score ranks district `C` highest with a score of `80.5`, classified as `Very High`. District `H` also classifies as `Very High`.

Repeat-location screening detected `7,945` approximate coordinate/category clusters with at least three requests.

## Recommended Interpretation

These findings should be treated as a public-data screening analysis for a bounded three-month period. They are useful for identifying candidate categories and areas for deeper review, not for official performance reporting.

High scores can reflect high request rate, longer median resolution times, larger unresolved shares, larger long-resolution shares, or larger repeat-cluster shares. A high score does not by itself prove service failure or causal inequity.

## Next Steps

- Rerun with `CENSUS_API_KEY` to generate ACS-normalized resident and household rates.
- Add official super-neighborhood polygons.
- Build a reviewed request-type crosswalk.
- Add ACS vulnerability overlays once Census access is available.
- Compare multiple years to distinguish seasonal spikes from persistent burden.
