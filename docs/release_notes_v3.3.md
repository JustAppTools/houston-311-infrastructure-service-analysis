# Release Notes: V3.3 Static GIS Atlas Expansion

## Added

- Score component table: `outputs/tables/score_components.csv`
- Score component maps:
  - `outputs/maps/request_density_component.png`
  - `outputs/maps/unresolved_share_component.png`
  - `outputs/maps/long_resolution_share_component.png`
  - `outputs/maps/repeat_cluster_share_component.png`
- Titleless map body for plate composition: `outputs/maps/council_district_service_burden_map_body.png`
- Additional formal map plates:
  - repeat-location clusters
  - solid waste/recycling
  - water/sewer/drainage
  - roads/signals/sidewalks
  - score component small multiples
- One-page executive brief: `deliverables/executive_brief.png`
- Static PDF atlas: `deliverables/houston_311_static_gis_atlas.pdf`

## Improved

- Formal map plate composition now uses a titleless map body to avoid duplicated title text.
- Static report and map atlas reference the expanded plate set.
- Tests now verify required static GIS outputs and score-component schema.

## Still Blocked

- ACS-normalized rates and equity/context maps require a valid Census API key.
