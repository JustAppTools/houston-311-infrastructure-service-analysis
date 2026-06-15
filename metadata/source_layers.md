# Source Layers

## Houston 311 Archive

- URL: https://mycity2.houstontx.gov/gisweb01/rest/services/311/Houston311_Archives/MapServer/0
- Role: source service request records
- Fields used: case number, request type, opened date, closed date, status, state, latitude, longitude, council district, department/division context

## Council District Boundaries

- URL: https://www.gis.hctx.net/arcgis/rest/services/CoH/CoH_Boundaries/MapServer/0
- Role: official polygon boundaries for point-in-polygon assignment and choropleth mapping

## H-GAC Major Roads

- URL: https://gis.h-gac.com/arcgis/rest/services/Open_Data/Transportation/MapServer/9
- Role: muted cartographic context only

## H-GAC Major Rivers

- URL: https://gis.h-gac.com/arcgis/rest/services/Open_Data/Environment/MapServer/1
- Role: muted cartographic context only

## ACS / TIGERweb

- Census API URL: https://api.census.gov/data/2024/acs/acs5
- TIGERweb tract layer: https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/7
- Role: optional demographic normalization
- Current status: not populated in committed outputs because the supplied Census API key was rejected
