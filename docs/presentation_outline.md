# Presentation Outline

## 1. Question

Which Houston council districts show the highest observed infrastructure-service burden in 311 request data?

## 2. Data

- City of Houston 311 archive records
- April-June 2025 extract
- Official council district polygons
- H-GAC road and river context layers
- Optional ACS demographic normalization

## 3. Method

- Standardize infrastructure categories
- Clean dates, status fields, coordinates, and quality flags
- Assign request points to official council districts
- Detect approximate repeat-location clusters
- Score districts using weighted percentile metrics

## 4. Main Visual

Use `outputs/maps/council_district_service_burden_choropleth.png`.

## 5. Findings

- District C and District H rank Very High.
- Solid Waste / Recycling dominates the request mix.
- Repeat-location patterns are substantial and should be treated as candidate recurring service locations.

## 6. Limitations

- 311 data reflects reported issues, not all infrastructure need.
- ACS normalization awaits a valid Census API key.
- The score is analytical, not official.

## 7. Next Steps

- Add ACS-normalized rates.
- Extend the time window.
- Add category-specific score views.
- Publish the GitHub Pages showcase.
