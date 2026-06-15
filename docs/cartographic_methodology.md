# Cartographic Methodology

## Map Purpose

The primary map communicates a reported Houston 311 infrastructure-request screening index by council district for April-June 2025. It is intended as a static GIS screening product rather than a live operational dashboard, official City performance product, or verified infrastructure-condition map.

## Classification

The main choropleth classifies the internal screening score into four fixed classes:

- `Low`: less than 25
- `Medium`: 25 to less than 50
- `High`: 50 to less than 75
- `Very High`: 75 or higher

Thematic maps use quartiles within each theme. This supports comparison across districts inside a theme, but thematic map classes should not be compared directly across different themes.

## Symbolization

- Council districts are filled by burden class.
- `Very High` districts receive a stronger outline so the highest-burden geography remains legible in the full plate.
- District labels use single-letter council district identifiers.
- Major roads and major rivers/bayous are included as muted context layers, with selected reference labels for orientation.
- Point maps are sampled when record counts are high to preserve readability and repository size.

## Marginalia

Formal map plates include title, subtitle, source note, classification note, score caveat, CRS/projection note, analytical caveat, and locator inset. Supporting atlas plates may include an approximate scale note, but the primary plate omits the scale bar because the static renderer draws from longitude/latitude coordinates into a fixed image frame rather than a fully projected cartographic layout.

The committed primary plate uses area-normalized request density because ACS population normalization awaits a valid Census API key. The primary plate omits a scale bar until a projected CRS workflow is added. A grayscale/print-safety variant and a smaller thumbnail preview are generated alongside the primary plate.

The primary plate discloses the District E spatial-assignment QA flag and the difference between cleaned requests and records included in the council-district score total.

## Interpretation Limits

Map classes describe patterns visible in the 311 extract. They do not prove infrastructure condition, service failure, resident satisfaction, government performance, or causal inequity. Reported 311 requests are affected by reporting access, civic engagement, land use, activity density, duplicate reporting, and service closure timing.

## Atlas Products

The static atlas includes a primary burden plate, thematic plates, repeat-location plate, and score-component small multiples. The component sheet uses separate quartiles for each metric, so color classes should be read within each panel rather than compared directly across panels.

The atlas also includes sensitivity and QA plates:

- a non-solid-waste screening map to test whether rankings are driven by the dominant Solid Waste / Recycling category
- a category-balanced density map that gives each request category equal influence in the density comparison
- a district assignment QA map that highlights spatial assignment review flags
