# Data Sources

## City of Houston 311 Archive

- Source name: City of Houston `Houston311_Archives`
- Source type: ArcGIS REST MapServer feature layer
- Layer URL: https://mycity2.houstontx.gov/gisweb01/rest/services/311/Houston311_Archives/MapServer/0
- V3 query window: `2025-04-01` through `2025-07-01` exclusive
- V3 downloaded records: `82,743`

## City Council District Boundaries

- Source name: `COH_Council_Districts`
- Source type: ArcGIS REST MapServer feature layer
- Layer URL: https://www.gis.hctx.net/arcgis/rest/services/CoH/CoH_Boundaries/MapServer/0
- Source attribution: COHGIS / Harris County GIS service
- Records downloaded: `11`

## ACS / Census Demographic Context

- Source name: 2024 ACS 5-year
- Census API URL: https://api.census.gov/data/2024/acs/acs5
- TIGERweb tract layer: https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/7
- Intended variables: population, households, median household income, poverty count/universe, and no-vehicle household inputs

In this environment, the Census API returned a key-required response. The project records that limitation in `data/processed/context/demographics_metadata.json`. Set `CENSUS_API_KEY` and rerun `scripts/fetch_demographics.py` to enable ACS-normalized outputs.
