# Static GIS Report: Reported Houston 311 Infrastructure Requests

## Research Question

Which Houston council districts rank highest in a reported-311-request screening index for infrastructure-related requests?

## Study Period And Data

- Study period: April 1, 2025 through June 30, 2025
- Cleaned infrastructure records: 82,743
- Records included in council-district scoring: 82,418
- Records not included in council-district scoring: 325
- Boundary unit: City Council district
- Main committed rate method: requests per square mile; ACS population/household normalization is not used in this version

## Main Map Plate

![Main map plate](map_plates/houston_311_service_burden_map_plate.png)

## Principal Findings

- Top-scoring district: C (80, Very High)
- Overall open/unclosed share as of data pull: 15.5%
- Overall long-resolution share: 20.2%
- Overall repeat-cluster share: 42.0%
- Largest standardized category: Solid Waste / Recycling (52.2%)

## Method Summary

The pipeline filters 311 records to infrastructure-related request types, cleans date and coordinate fields, assigns request points to official council district polygons, screens approximate repeat-location clusters, and aggregates district metrics. The screening score combines area-density fallback, median resolution days, open/unclosed share, long-resolution share, and repeat-cluster share. It is not an official City performance measure or a verified infrastructure-condition measure.

## Data Quality Flags

- District E: spatial assignment share 37.4%

## Static GIS Deliverables

- `deliverables/map_plates/houston_311_service_burden_map_plate.png`
- `deliverables/map_plates/houston_311_service_burden_map_plate_grayscale.png`
- `deliverables/map_plates/houston_311_service_burden_map_plate_thumbnail.png`
- `deliverables/map_plates/repeat_location_cluster_map_plate.png`
- `deliverables/map_plates/score_component_small_multiples.png`
- `deliverables/map_plates/non_solid_waste_screening_map_plate.png`
- `deliverables/map_plates/category_balanced_density_map_plate.png`
- `deliverables/map_plates/district_assignment_qa_map_plate.png`
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

## Sensitivity And QA Outputs

The project also exports alternate score and QA diagnostics:

- `outputs/tables/source_spatial_assignment_matrix.csv`
- `outputs/tables/unscored_request_diagnostics.csv`
- `outputs/tables/score_sensitivity_rankings.csv`
- `outputs/tables/council_district_non_solid_waste_screening.csv`
- `outputs/tables/category_balanced_district_density.csv`
- `outputs/gis/*.geojson`

## Limitations

The output is a public-data screening analysis. It is not an official City of Houston performance measure, not a causal model, and not a complete inventory of infrastructure need. 311 requests reflect reporting behavior as well as conditions. ACS population and household normalization is not used in this committed version; it awaits a valid Census API key. The primary map omits a scale bar until a projected CRS workflow is added.
