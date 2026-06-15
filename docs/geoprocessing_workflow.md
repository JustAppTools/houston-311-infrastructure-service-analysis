# Geoprocessing Workflow

```mermaid
flowchart LR
  A["Houston 311 Archive<br/>service request records"] --> B["Infrastructure request filter<br/>keyword and type screening"]
  B --> C["Cleaning and QA/QC<br/>dates, status, coordinates, categories"]
  C --> D["Official council district polygons<br/>COHGIS / Harris County"]
  D --> E["Point-in-polygon assignment"]
  C --> E
  E --> F["District aggregation<br/>counts, rates, resolution, open share"]
  E --> G["Repeat-location screening<br/>100-meter coordinate bins"]
  F --> H["Service-burden score<br/>weighted percentile model"]
  G --> H
  H --> I["Static GIS outputs<br/>map plates, atlas, figures, tables"]
```

## Notes

- The committed V3.2 output uses requests per square mile as the rate component because ACS API access was not successful with the supplied key.
- ACS resident and household rate fields are supported by the pipeline and can be regenerated when a valid Census API key is available.
- The workflow produces static GIS outputs. The optional `index.html` file is a viewer for committed artifacts, not the analytical product itself.
