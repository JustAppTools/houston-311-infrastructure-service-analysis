# Data Sources

## City of Houston 311 Archive

- Source name: City of Houston `Houston311_Archives`
- Source type: ArcGIS REST MapServer feature layer
- Layer URL: https://mycity2.houstontx.gov/gisweb01/rest/services/311/Houston311_Archives/MapServer/0
- Service description: Houston 311 service requests archive
- V2 query window: `2025-04-01` through `2025-07-01` exclusive
- V2 downloaded records: `82,743`

The pipeline queries the ArcGIS REST endpoint directly using `scripts/fetch_data.py`. The raw CSV extract is generated locally in `data/raw/` and ignored by git. The query metadata is committed in `data/raw/fetch_metadata.json`.

## City Council District Boundaries

- Source name: `COH_Council_Districts`
- Source type: ArcGIS REST MapServer feature layer
- Layer URL: https://www.gis.hctx.net/arcgis/rest/services/CoH/CoH_Boundaries/MapServer/0
- Source attribution: COHGIS / Harris County GIS service
- Records downloaded: `11`

V2 uses these official polygons for the flagship choropleth map, district labels, member names, and area-normalized request density. Boundary metadata is saved in `data/processed/context/boundary_metadata.json`.

## Related City GIS Services Reviewed

- Houston 311 Service Request Map web map: https://www.arcgis.com/home/item.html?id=101c92d355b848ca93321e621a6b5133
- City REST folder for 311 services: https://mycity2.houstontx.gov/gisweb01/rest/services/311
- Recent 311 service request FeatureServer: https://mycity2.houstontx.gov/gisweb01/rest/services/311/HOUSTON311_RECENT_SR_SNOW/FeatureServer/0

The current D365 service referenced by the public web map returned a server-side access/startup error during initial development, so the project uses the accessible archive service instead.

## Context Not Yet Included

V2 does not include ACS population, household, or vulnerability denominators. Those overlays require a separate tract/block-group workflow and are recommended for a future version.
