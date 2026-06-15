# Changelog

## V3

- Added point-in-polygon council district assignment for 311 request coordinates.
- Added optional 2024 ACS 5-year demographic fetch with `CENSUS_API_KEY` support.
- Added documented ACS access-limitation fallback when the Census API rejects or requires a key.
- Added H-GAC major roads and major rivers/bayous as optional visual context layers.
- Added configurable analysis settings in `config/analysis_config.json`.
- Added an output index for generated showcase artifacts.
- Added thematic district burden maps for solid waste, water/sewer/drainage, and roads/signals/sidewalks.
- Added repeat-location cluster tests and core logic tests.
- Added `Makefile` task shortcuts.
- Added executive summary and static portfolio page.
- Updated the hero map with score ranges, date range, driver details, and clearer source notes.

## V2

- Added official council district polygons.
- Replaced the V1 centroid screen with a polygon choropleth.
- Expanded the analysis window to April-June 2025.
- Added repeat-location cluster screening.
- Added district burden-driver and thematic table outputs.

## V1

- Built the first reproducible Houston 311 infrastructure analysis pipeline.
- Downloaded and cleaned real City of Houston 311 records.
- Generated initial tables, charts, maps, data dictionary, README, and technical memo.
