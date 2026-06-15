# Data Sources

## City of Houston 311 Archive

- Source name: City of Houston `Houston311_Archives`
- Source type: ArcGIS REST MapServer feature layer
- Layer URL: https://mycity2.houstontx.gov/gisweb01/rest/services/311/Houston311_Archives/MapServer/0
- Service description: Houston 311 service requests archive
- V1 query window: `2025-06-01` through `2025-07-01` exclusive
- V1 downloaded records: `33,172`

The pipeline queries the ArcGIS REST endpoint directly using `scripts/fetch_data.py`. The raw CSV extract is generated locally in `data/raw/` and ignored by git. The query metadata is committed in `data/raw/fetch_metadata.json`.

## Related City GIS Services Reviewed

- Houston 311 Service Request Map web map: https://www.arcgis.com/home/item.html?id=101c92d355b848ca93321e621a6b5133
- City REST folder for 311 services: https://mycity2.houstontx.gov/gisweb01/rest/services/311
- Recent 311 service request FeatureServer: https://mycity2.houstontx.gov/gisweb01/rest/services/311/HOUSTON311_RECENT_SR_SNOW/FeatureServer/0

The current D365 service referenced by the public web map returned a server-side access/startup error during V1 development, so the project uses the accessible archive service instead.

## Boundary and Context Data

V1 does not download separate council-district or super-neighborhood boundary polygons. Area screening uses the council-district and super-neighborhood attributes already present in the 311 archive records. This avoids fabricating spatial joins and keeps the V1 output reproducible with the accessible data.
