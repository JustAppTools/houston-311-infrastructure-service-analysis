# Houston 311 Infrastructure Service Burden Brief

## Purpose

This project screens Houston 311 infrastructure-related service requests to identify council districts with heavier observed request burden during April-June 2025.

## Main Output

The primary showcase output is `outputs/maps/council_district_service_burden_choropleth.png`, supported by an interactive static site at `index.html`.

## Key Findings

- 82,743 infrastructure-related 311 records were processed.
- Solid Waste / Recycling is the largest standardized request category.
- District C ranks highest under the current V3 service-burden score, followed closely by District H.
- Repeat-location screening detected 7,945 approximate coordinate/category clusters.

## Interpretation

The score is an analytical index built from request rate, resolution time, unresolved share, long-resolution share, and repeat-cluster share. It is not an official City of Houston metric.

ACS population and household normalization is supported, but the supplied Census key was rejected. The committed outputs therefore use requests per square mile as the documented rate fallback.

## Recommended Next Step

Run the pipeline with a valid `CENSUS_API_KEY` and compare the ACS-normalized rankings with the current area-density fallback.
