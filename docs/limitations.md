# Limitations

## Scope

The committed outputs use an April-June 2025 extract. Findings should be read as a bounded public-data screening analysis, not a long-term trend or official performance audit.

## Classification

Infrastructure requests are selected and grouped with keyword rules. This is transparent and reproducible, but a reviewed source-type crosswalk would be stronger.

## Spatial Assignment

V3 assigns request points to official council district polygons with a lightweight point-in-polygon implementation. This improves on using the source district field, but it is still dependent on source coordinate quality.

## Demographics

The project supports ACS population and household normalization, but the Census API rejected the supplied key in this environment. The committed score therefore falls back to area-normalized request density. Set a valid `CENSUS_API_KEY` and rerun the pipeline to generate ACS-normalized rates.

## Repeat Clusters

Repeat-location clusters use rounded coordinates and category matching. They identify candidate recurring service locations, not verified duplicate requests.

## Interpretation

Findings are not official City of Houston metrics and should not be used for emergency response or operational dispatch decisions.

H-GAC roads and rivers are map context only. They do not affect district scores.

## Publication

The interactive showcase is a static GitHub Pages artifact. It reads committed CSV outputs and images; it is not a live dashboard and does not automatically refresh unless the pipeline is rerun and outputs are recommitted.
