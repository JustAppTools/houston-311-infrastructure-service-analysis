# Known Limitations

This project is a static GIS screening analysis of reported Houston 311 requests. It is not an official City of Houston performance measure, causal model, or verified infrastructure-condition inventory.

## Current Scoring Limits

- The committed score uses requests per square mile because ACS population and household normalization did not run with a valid Census API key.
- Reported 311 requests reflect reporting behavior as well as infrastructure conditions.
- The study period is a bounded three-month sample: April 1, 2025 through June 30, 2025.
- Solid Waste / Recycling is the dominant request category, so baseline rankings should be compared with the non-solid-waste and category-balanced sensitivity outputs.
- Scores are internal percentile-style screening values across 11 council districts, not official thresholds.

## Data Quality Limits

- District E has a spatial-assignment QA flag: many source-labeled District E records do not spatially assign to the current council-district polygons.
- The district score table includes 82,418 of 82,743 cleaned requests. Records outside the A-K district score total are summarized in `outputs/tables/unscored_request_diagnostics.csv`.
- Open/unclosed status is based on source status fields and closure dates as of the data pull.
- Repeat clusters use rounded coordinate/category bins and are not address-level duplicate detection.

## Cartographic Limits

- The primary plate omits a scale bar until a projected CRS workflow is added.
- Road and water layers are visual context only and are not score inputs.
- Council districts are large reporting units and hide within-district variation.
