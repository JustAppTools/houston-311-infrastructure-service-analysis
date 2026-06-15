# Executive Summary

This V3 project analyzes Houston 311 infrastructure-related requests opened from April through June 2025. It uses real City of Houston 311 archive records, official council district boundaries, point-in-polygon district assignment, repeat-location screening, and static public-sector GIS outputs.

The extract contains `82,743` cleaned records. `Solid Waste / Recycling` is the largest category with `43,194` requests. The overall median resolution time is about `3.8` days, and the unresolved share is about `15.5%`.

The V3 burden score ranks council district `C` as `Very High`, followed closely by district `H`. The score combines request rate, median resolution time, unresolved share, long-resolution share, and repeat-cluster share. In this environment, Census ACS population/household normalization was blocked by a key-required API response, so the committed score uses area-normalized request density as the available rate component.

The main showcase output is:

`outputs/maps/council_district_service_burden_choropleth.png`

The analysis should be interpreted as a bounded public-data screening product, not an official City performance metric or emergency response tool.
