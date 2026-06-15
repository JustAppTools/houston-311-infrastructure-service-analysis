# Output Index

## Main Showcase Visual

- `deliverables/map_plates/houston_311_service_burden_map_plate.png` - formal static GIS map plate for the project.
- `deliverables/map_plates/houston_311_service_burden_map_plate_grayscale.png` - grayscale/print-safety variant of the primary plate.
- `deliverables/map_plates/houston_311_service_burden_map_plate_thumbnail.png` - smaller preview version for README and web previews.
- `deliverables/map_plates/score_component_small_multiples.png` - four-panel score component sheet.
- `deliverables/map_plates/non_solid_waste_screening_map_plate.png` - sensitivity plate excluding Solid Waste / Recycling requests.
- `deliverables/map_plates/category_balanced_density_map_plate.png` - equal-category density comparison plate.
- `deliverables/map_plates/district_assignment_qa_map_plate.png` - spatial assignment QA plate.
- `deliverables/houston_311_static_gis_atlas.pdf` - static PDF atlas assembled from map plates.
- `deliverables/executive_brief.png` - one-page static GIS executive brief.
- `outputs/maps/council_district_service_burden_choropleth.png` - supporting choropleth map. It ranks council districts by the V3 reported-request screening score.
- `deliverables/static_gis_report.md` - static GIS report.
- `deliverables/map_atlas.md` - atlas index for map and figure outputs.
- `index.html` - optional viewer that uses the main map, supporting maps, and district tables.

## Supporting Maps

- `outputs/maps/repeat_location_clusters.png` - approximate 100-meter same-category repeat request clusters.
- `outputs/maps/overall_infrastructure_request_points.png` - sampled point distribution for all valid infrastructure coordinates.
- `outputs/maps/open_or_long_resolution_requests.png` - point distribution for unresolved or long-resolution requests.
- `outputs/maps/drainage_water_sewer_requests.png` - drainage, water, and sewer request points.
- `outputs/maps/road_sidewalk_signal_requests.png` - road, sidewalk, signal, and lighting request points.
- `outputs/maps/solid_waste_recycling_burden.png` - thematic district rate map.
- `outputs/maps/water_sewer_drainage_burden.png` - thematic district rate map.
- `outputs/maps/roads_signals_sidewalks_burden.png` - thematic district rate map.
- `outputs/maps/request_density_component.png` - score component map.
- `outputs/maps/unresolved_share_component.png` - score component map.
- `outputs/maps/long_resolution_share_component.png` - score component map.
- `outputs/maps/repeat_cluster_share_component.png` - score component map.
- `outputs/maps/non_solid_waste_screening_score.png` - sensitivity map excluding Solid Waste / Recycling requests.
- `outputs/maps/category_balanced_density_score.png` - equal-category density comparison map.
- `outputs/maps/district_assignment_qa_flags.png` - spatial assignment QA map.

## Figures

- `outputs/figures/request_count_by_category.png`
- `outputs/figures/median_resolution_time_by_category.png`
- `outputs/figures/open_unresolved_share_by_category.png`
- `outputs/figures/monthly_request_volume.png`

## Tables

- `outputs/tables/council_district_service_burden.csv` - primary ranked district table.
- `outputs/tables/district_burden_drivers.csv` - top district driver summary.
- `outputs/tables/repeat_location_clusters.csv` - detected repeat-location clusters.
- `outputs/tables/thematic_district_burden.csv` - district metrics for thematic maps.
- `outputs/tables/district_data_quality.csv` - district-level coordinate and spatial-assignment quality checks.
- `outputs/tables/score_components.csv` - score component percentiles and weighted points by district.
- `outputs/tables/score_sensitivity_rankings.csv` - baseline, equal-weight, non-solid-waste, and category-balanced rank comparison.
- `outputs/tables/council_district_non_solid_waste_screening.csv` - weighted score recomputed without Solid Waste / Recycling requests.
- `outputs/tables/category_balanced_district_density.csv` - district density score with equal category influence.
- `outputs/tables/category_balanced_density_components.csv` - category-by-district density percentiles used for category-balanced scoring.
- `outputs/tables/source_spatial_assignment_matrix.csv` - source district vs point-in-polygon assignment cross-tab.
- `outputs/tables/unscored_request_diagnostics.csv` - records outside the A-K district score total summarized by reason and category.
- Other table outputs summarize categories, resolution, unresolved share, long-resolution share, and monthly volume.

## GIS Layers

- `outputs/gis/council_district_screening_index.geojson` - council district polygons with baseline score, QA fields, and alternate score fields.
- `outputs/gis/district_assignment_qa_flags.geojson` - district polygons with spatial assignment share below 90 percent.
- `outputs/gis/repeat_location_clusters.geojson` - approximate repeat-location clusters as point features.
- `outputs/gis/request_points_sample.geojson` - sampled request-point layer for GIS inspection.
