# Release Notes V3.4

## Robust Static GIS Screening Update

V3.4 strengthens the project's analytical transparency. The primary map plate now frames the output as a reported-request screening index, not a verified infrastructure-condition or official performance measure.

## Added

- Source-vs-spatial council district assignment matrix.
- Unscored-request diagnostics for records outside the A-K district score total.
- Non-solid-waste weighted screening score.
- Equal-weight score sensitivity table.
- Category-balanced density score and component table.
- Score sensitivity ranking table.
- GIS-ready GeoJSON layers in `outputs/gis/`.
- Formal sensitivity and QA map plates.
- Known limitations documentation.

## Updated

- Main map plate language, caveats, QA note, and all-district ranking.
- Static GIS report and map atlas.
- README output inventory.
- Cartographic methodology and technical memo.
- Unit tests for GIS and sensitivity outputs.

## Still Pending

- Valid Census API key for ACS population and household normalization.
- Projected CRS workflow for defensible scale bars and distance calculations.
- Investigation of the District E source-vs-spatial assignment issue against authoritative source-system definitions.
- Finer spatial units such as super neighborhoods or Census tracts.
