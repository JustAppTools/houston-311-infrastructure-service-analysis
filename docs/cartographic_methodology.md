# Cartographic Methodology

## Map Purpose

The primary map communicates relative Houston 311 infrastructure service burden by council district for April-June 2025. It is intended as a static GIS screening product rather than a live operational dashboard.

## Classification

The main choropleth classifies the service-burden score into four fixed classes:

- `Low`: less than 25
- `Medium`: 25 to less than 50
- `High`: 50 to less than 75
- `Very High`: 75 or higher

Thematic maps use quartiles within each theme. This supports comparison across districts inside a theme, but thematic map classes should not be compared directly across different themes.

## Symbolization

- Council districts are filled by burden class.
- District labels use single-letter council district identifiers.
- Major roads and major rivers/bayous are included as muted context layers.
- Point maps are sampled when record counts are high to preserve readability and repository size.

## Marginalia

Formal map plates include title, subtitle, source note, classification note, CRS/projection note, analytical caveat, and approximate scale. The scale bar is approximate because the static map renderer draws from longitude/latitude coordinates into a fixed image frame rather than a fully projected cartographic layout.

## Interpretation Limits

Map classes describe patterns visible in the 311 extract. They do not prove infrastructure condition, service failure, resident satisfaction, or causal inequity.

## Atlas Products

The static atlas includes a primary burden plate, thematic plates, repeat-location plate, and score-component small multiples. The component sheet uses separate quartiles for each metric, so color classes should be read within each panel rather than compared directly across panels.
