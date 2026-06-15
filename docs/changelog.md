# Changelog

## V3.2

- Reframed the project around static GIS analysis and map production.
- Added `deliverables/` with a formal map plate, static GIS report, and map atlas.
- Added multiple formal map plates, a score-component small-multiple sheet, a one-page executive brief, and a static PDF atlas.
- Added score-component table and component choropleth maps.
- Added V3.3 release notes for the static atlas expansion.
- Added `metadata/` with project metadata, source-layer notes, and processing lineage.
- Added cartographic methodology and geoprocessing workflow documentation.
- Added `scripts/make_deliverables.py` and wired it into the reproducible pipeline.

## V3.1

- Added a root `index.html` interactive static showcase for GitHub Pages.
- Added GitHub Actions CI for unit tests and Python compile checks.
- Added a GitHub Pages deployment workflow.
- Added `outputs/tables/district_data_quality.csv` with coordinate and spatial-assignment quality metrics.
- Added strict JSON-safe analysis summary output.
- Added pinned dependency versions in `requirements.txt`.
- Added project brief, presentation outline, and future-work documents.
- Updated README and output index for the interactive/public showcase.

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
