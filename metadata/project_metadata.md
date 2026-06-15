# Project Metadata

## Title

Houston 311 Infrastructure Service Request Analysis

## Abstract

This project analyzes reported infrastructure-related Houston 311 service requests for April-June 2025. It produces static GIS maps, tables, figures, a formal map plate, and documentation describing a council-district screening index. The output is not an official City performance measure or verified infrastructure-condition map.

## Spatial Extent

City of Houston council districts, with request coordinates screened to the broader Houston area.

## Temporal Extent

April 1, 2025 through June 30, 2025.

## Coordinate Reference Notes

311 request coordinates are stored as latitude/longitude. Council district polygons are fetched from the COHGIS / Harris County ArcGIS service and stored as GeoJSON for processing. District area values used for requests-per-square-mile calculations come from source boundary geometry attributes.

## Primary Outputs

- `deliverables/map_plates/houston_311_service_burden_map_plate.png`
- `deliverables/map_plates/houston_311_service_burden_map_plate_grayscale.png`
- `deliverables/map_plates/houston_311_service_burden_map_plate_thumbnail.png`
- `deliverables/map_plates/score_component_small_multiples.png`
- `deliverables/map_plates/non_solid_waste_screening_map_plate.png`
- `deliverables/map_plates/category_balanced_density_map_plate.png`
- `deliverables/map_plates/district_assignment_qa_map_plate.png`
- `deliverables/houston_311_static_gis_atlas.pdf`
- `deliverables/executive_brief.png`
- `deliverables/static_gis_report.md`
- `deliverables/map_atlas.md`
- `outputs/maps/council_district_service_burden_choropleth.png`
- `outputs/tables/council_district_service_burden.csv`
- `outputs/tables/score_sensitivity_rankings.csv`
- `outputs/tables/source_spatial_assignment_matrix.csv`
- `outputs/gis/council_district_screening_index.geojson`
- `outputs/gis/district_assignment_qa_flags.geojson`

## Access And Use Constraints

This is an analytical portfolio project built from public data. It is not an official City of Houston performance product.
