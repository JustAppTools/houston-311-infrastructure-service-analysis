# Limitations

## Data Access and Scope

V2 uses one accessible City of Houston ArcGIS archive layer. The public web map's D365 map image service returned a server error during development, so it was not used for analytical outputs.

The committed outputs use an April-June 2025 extract. Findings should be read as a bounded V2 analysis, not a long-term trend or comprehensive historical performance audit.

## Classification

Infrastructure requests are selected and grouped with keyword rules. This is transparent and reproducible, but it can miss relevant categories with unexpected names or include categories that are adjacent to infrastructure operations.

## Resolution Time

Resolution time is calculated from opened and closed date fields. Records with missing, negative, or far-future closed dates are excluded from median resolution calculations. The V2 long-resolution threshold is `14` days and is an analytical screening threshold, not an official SLA.

The `Resolve_By_Time` field is retained but not used for late-case findings because far-future values appeared in the archive extract.

## Spatial Analysis

V2 uses official council-district polygons for choropleth mapping and district area estimates. However, area burden is still summarized from the source `Council_District` attribute in each 311 record rather than reassigned by point-in-polygon overlay.

V2 does not include population normalization, ACS vulnerability overlays, or official address-level repeat-request deduplication.

Repeat-location clusters use rounded coordinates and category matching. They identify candidate recurring service locations, not verified duplicate requests.

## Privacy and Interpretation

Processed outputs omit source address and narrative fields. Maps still show request coordinates from the public source data, so outputs should be interpreted as operational screening products rather than resident-level analysis.

Findings are not official City of Houston metrics and should not be used for emergency response or operational dispatch decisions.
