# Static GIS Report: Houston 311 Infrastructure Service Burden

## Research Question

Which Houston council districts show the highest observed infrastructure-service burden in 311 request data?

## Study Period And Data

- Study period: April 1, 2025 through June 30, 2025
- Cleaned infrastructure records: 82,743
- Boundary unit: City Council district
- Main rate fallback in committed output: requests per square mile

## Main Map Plate

![Main map plate](map_plates/houston_311_service_burden_map_plate.png)

## Principal Findings

- Top burden district: C (80.5, Very High)
- Overall unresolved share: 15.5%
- Overall long-resolution share: 20.2%
- Overall repeat-cluster share: 42.0%
- Largest standardized category: Solid Waste / Recycling

## Method Summary

The pipeline filters 311 records to infrastructure-related request types, cleans date and coordinate fields, assigns request points to official council district polygons, screens approximate repeat-location clusters, and aggregates district metrics. The service-burden score combines request-rate density, median resolution days, unresolved share, long-resolution share, and repeat-cluster share.

## Static GIS Deliverables

- `deliverables/map_plates/houston_311_service_burden_map_plate.png`
- `deliverables/map_plates/repeat_location_cluster_map_plate.png`
- `deliverables/map_plates/score_component_small_multiples.png`
- `deliverables/houston_311_static_gis_atlas.pdf`
- `deliverables/executive_brief.png`
- `deliverables/map_atlas.md`
- `outputs/maps/*.png`
- `outputs/figures/*.png`
- `outputs/tables/*.csv`

## Score Components

The composite score is supported by `outputs/tables/score_components.csv` and four static component maps:

- request density
- unresolved request share
- long-resolution request share
- repeat-cluster request share

These outputs help explain whether a high burden score is driven mainly by request density, slow resolution, open cases, or recurring locations.

## Limitations

The output is a public-data screening analysis. It is not an official City of Houston performance measure, not a causal model, and not a complete inventory of infrastructure need. ACS population and household normalization is supported but awaits a valid Census API key.
