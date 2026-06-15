# Processing Lineage

## 1. Fetch

`scripts/fetch_data.py` downloads Houston 311 archive records for the configured date window. `scripts/fetch_boundaries.py` downloads council district polygons. `scripts/fetch_context.py` downloads optional roads and rivers context layers.

## 2. Clean

`scripts/clean_311_requests.py` standardizes request categories, converts dates, flags open and long-resolution cases, screens coordinates, assigns points to council districts, and writes cleaned CSV/GeoJSON outputs.

## 3. Analyze

`scripts/analyze_requests.py` creates category summaries, resolution summaries, repeat-location clusters, district burden tables, thematic tables, data-quality tables, and strict JSON summary metadata.

## 4. Map

`scripts/make_maps.py` creates static maps and figures from the cleaned data and analysis tables.

## 5. Deliver

`scripts/make_deliverables.py` creates the formal map plate, static GIS report, and map atlas files in `deliverables/`.

## Reproducible Command

```bash
python scripts/run_all.py --skip-fetch --skip-context
```

Use the full command without skip flags to refetch source data and context files.
