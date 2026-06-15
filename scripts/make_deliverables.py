import json
import textwrap
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont, JpegImagePlugin  # noqa: F401

from project_config import DELIVERABLES, MAPS, MAP_PLATES, TABLES, ensure_directories


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_FILE = ROOT / "data" / "processed" / "analysis_summary.json"
MAIN_MAP = MAPS / "council_district_service_burden_map_body.png"
MAIN_MAP_FALLBACK = MAPS / "council_district_service_burden_choropleth.png"
PLATE_FILE = MAP_PLATES / "houston_311_service_burden_map_plate.png"
GRAYSCALE_PLATE_FILE = MAP_PLATES / "houston_311_service_burden_map_plate_grayscale.png"
THUMBNAIL_FILE = MAP_PLATES / "houston_311_service_burden_map_plate_thumbnail.png"
PDF_ATLAS = DELIVERABLES / "houston_311_static_gis_atlas.pdf"
DRIVERS_FILE = TABLES / "district_burden_drivers.csv"
DISTRICT_FILE = TABLES / "council_district_service_burden.csv"
COMPONENT_FILE = TABLES / "score_components.csv"
BOUNDARY_FILE = ROOT / "data" / "processed" / "context" / "council_district_boundaries.geojson"


PAGE = {
    "width": 3300,
    "height": 2550,
    "background": (248, 249, 247),
    "ink": (35, 38, 42),
    "muted": (91, 101, 107),
    "line": (190, 197, 194),
    "panel": (255, 255, 252),
    "accent": (31, 111, 125),
    "berry": (148, 49, 73),
}


SCORE_COLORS = {
    "Low": (137, 171, 112),
    "Medium": (220, 185, 101),
    "High": (210, 121, 84),
    "Very High": (148, 49, 73),
}

SCORE_LABELS = {
    "Low": "Low (<25)",
    "Medium": "Medium (25-49)",
    "High": "High (50-74)",
    "Very High": "Very High (75+)",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    width_chars: int,
    fill: tuple[int, int, int],
    text_font: ImageFont.ImageFont,
    line_gap: int = 10,
) -> int:
    x, y = xy
    line_height = text_font.size + line_gap if hasattr(text_font, "size") else 28
    for paragraph in text.split("\n"):
        for line in textwrap.wrap(paragraph, width=width_chars) or [""]:
            draw.text((x, y), line, fill=fill, font=text_font)
            y += line_height
    return y


def draw_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    title_size: int = 29,
) -> tuple[int, int]:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=8, fill=PAGE["panel"], outline=PAGE["line"], width=2)
    draw.text((x1 + 28, y1 + 24), title, fill=PAGE["ink"], font=font(title_size, True))
    return x1 + 28, y1 + 76


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def draw_title_block(draw: ImageDraw.ImageDraw, title: str, subtitle: str, summary: dict | None = None) -> None:
    draw.text(
        (130, 86),
        title,
        fill=PAGE["ink"],
        font=font(76, True),
    )
    draw.text(
        (132, 176),
        subtitle,
        fill=PAGE["muted"],
        font=font(36),
    )
    if not summary:
        return
    top = summary.get("top_burden_council_district") or {}
    callout = (
        f"{summary.get('record_count', 0):,} 311 requests | "
        f"Top district: {top.get('council_district', 'n/a')} "
        f"({top.get('service_burden_score', 0):.0f}) | "
        f"Overall open/unclosed: {fmt_pct(summary.get('unresolved_share_overall'))}"
    )
    draw.rounded_rectangle((2060, 82, 3170, 205), radius=8, fill=PAGE["panel"], outline=PAGE["line"], width=2)
    draw.text((2100, 122), callout, fill=PAGE["ink"], font=font(30, True))


def draw_info_panel(draw: ImageDraw.ImageDraw, summary: dict, x: int, y: int, w: int, h: int) -> None:
    draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=PAGE["panel"], outline=PAGE["line"], width=2)
    draw.text((x + 36, y + 34), "Map Interpretation", fill=PAGE["ink"], font=font(36, True))
    body = (
        "The service-burden score combines request-rate density, median resolution time, "
        "unresolved share, long-resolution share, and repeat-location share. ACS resident "
        "and household rates are supported when a valid Census API key is available; this "
        "committed map uses requests per square mile as the documented rate fallback."
    )
    y2 = draw_wrapped(draw, body, (x + 36, y + 92), 48, PAGE["muted"], font(25), 8)

    draw.text((x + 36, y2 + 28), "Key Findings", fill=PAGE["ink"], font=font(32, True))
    findings = [
        f"{summary.get('record_count', 0):,} cleaned infrastructure-related records.",
        f"Median resolution time: {summary.get('median_resolution_days_overall', 0):.1f} days.",
        f"Unresolved share: {fmt_pct(summary.get('unresolved_share_overall'))}.",
        f"Repeat-cluster share: {fmt_pct(summary.get('repeat_cluster_share_overall'))}.",
    ]
    yy = y2 + 82
    for finding in findings:
        draw.ellipse((x + 38, yy + 9, x + 52, yy + 23), fill=PAGE["accent"])
        yy = draw_wrapped(draw, finding, (x + 70, yy), 44, PAGE["ink"], font(24), 8) + 4

    draw.text((x + 36, y + h - 260), "Data Quality Note", fill=PAGE["ink"], font=font(32, True))
    quality_note = (
        "District assignments use point-in-polygon against official council district boundaries. "
        "The data-quality table reports coordinate completeness and source-vs-spatial district agreement."
    )
    draw_wrapped(draw, quality_note, (x + 36, y + h - 205), 48, PAGE["muted"], font(24), 8)


def draw_at_a_glance(draw: ImageDraw.ImageDraw, summary: dict, box: tuple[int, int, int, int]) -> None:
    x, y = draw_card(draw, box, "At a Glance")
    top = summary.get("top_burden_council_district") or {}
    top_district = top.get("council_district", "n/a")
    if top_district != "n/a":
        top_district = f"District {top_district}"
    scored = summary.get("district_score_request_count")
    if scored is None and DISTRICT_FILE.exists():
        scored = int(pd.read_csv(DISTRICT_FILE)["request_count"].sum())
    metrics = [
        (f"{summary.get('record_count', 0):,}", "total requests"),
        (f"{int(scored or 0):,}", "scored requests"),
        (str(top_district), "top score"),
        (fmt_pct(summary.get("unresolved_share_overall")), "overall open/unclosed"),
    ]
    card_w = 190
    gap = 17
    for i, (value, label) in enumerate(metrics):
        xx = x + i * (card_w + gap)
        draw.rounded_rectangle((xx, y, xx + card_w, y + 128), radius=6, fill=(248, 249, 247), outline=(217, 222, 219), width=1)
        value_font = font(31 if len(value) <= 8 else 27, True)
        draw.text((xx + 16, y + 20), value, fill=PAGE["ink"], font=value_font)
        draw_wrapped(draw, label, (xx + 16, y + 72), 16, PAGE["muted"], font(18), 4)


def draw_score_method(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x, y = draw_card(draw, box, "Screening Index")
    draw.text(
        (x, y),
        "Reported requests, not verified infrastructure condition.",
        fill=PAGE["ink"],
        font=font(23, True),
    )
    body = (
        "ACS normalization is not used in this version; the score uses area-density fallback. "
        "Weights: density 40%, median resolution 20%, open/unclosed 15%, long-resolution 10%, repeat clusters 15%. "
        "Repeat means approximate coordinate/category clusters."
    )
    draw_wrapped(draw, body, (x, y + 42), 58, PAGE["muted"], font(19), 6)


def draw_plate_legend(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x, y = draw_card(draw, box, "Legend")
    draw.text((x, y), "Internal 0-100 score classes, not official thresholds", fill=PAGE["muted"], font=font(19))
    y += 32
    for i, (label, fill) in enumerate(SCORE_COLORS.items()):
        yy = y + i * 36
        draw.rectangle((x, yy + 2, x + 28, yy + 30), fill=fill, outline=(120, 126, 123))
        draw.text((x + 44, yy), SCORE_LABELS[label], fill=PAGE["ink"], font=font(23))
    note_y = y + 145
    draw.line((x, note_y + 9, x + 44, note_y + 9), fill=(75, 82, 82), width=4)
    draw.text((x + 60, note_y), "Very High district outline", fill=PAGE["muted"], font=font(18))


def draw_top_drivers(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x, y = draw_card(draw, box, "Highest-Scoring Districts")
    if not DRIVERS_FILE.exists() or not DISTRICT_FILE.exists():
        draw.text((x, y), "Driver tables are unavailable.", fill=PAGE["muted"], font=font(23))
        return
    drivers = pd.read_csv(DRIVERS_FILE).head(4)
    districts = pd.read_csv(DISTRICT_FILE).set_index("council_district")
    bar_x = x + 330
    bar_w = 390
    for rank, (_, row) in enumerate(drivers.iterrows(), start=1):
        district = row["council_district"]
        metrics = districts.loc[district] if district in districts.index else {}
        density = metrics.get("requests_per_sq_mile", 0)
        unresolved = metrics.get("unresolved_share", 0) * 100
        long_resolution = metrics.get("long_resolution_share", 0) * 100
        repeat = metrics.get("repeat_cluster_share", 0) * 100
        service_class = metrics.get("service_burden_class", "")
        score = float(row["service_burden_score"])
        fill = SCORE_COLORS.get(service_class, PAGE["accent"])
        top_cat = str(row["top_category"]).replace("Solid Waste / Recycling", "Solid Waste").replace("Traffic Signals / Lighting", "Signals").replace("Road / Pothole / Bridge", "Roads").replace(" / ", "/")
        top_share = float(row.get("top_category_share", 0)) * 100
        draw.ellipse((x, y + 2, x + 34, y + 36), fill=fill, outline=(90, 96, 94), width=1)
        draw.text((x + 11, y + 7), str(rank), fill=(255, 255, 255), font=font(18, True))
        draw.text((x + 48, y), f"District {district}", fill=PAGE["ink"], font=font(23, True))
        draw.text((x + 48, y + 31), f"{density:,.0f} req/sq mi | {unresolved:.0f}% open | {long_resolution:.0f}% >14d", fill=PAGE["muted"], font=font(17))
        draw.rounded_rectangle((bar_x, y + 4, bar_x + bar_w, y + 28), radius=4, fill=(235, 238, 235), outline=(217, 222, 219), width=1)
        draw.rounded_rectangle((bar_x, y + 4, bar_x + int(bar_w * score / 100), y + 28), radius=4, fill=fill)
        draw.text((bar_x + bar_w + 16, y + 1), f"{score:.0f}", fill=PAGE["ink"], font=font(21, True))
        draw.text((x + 48, y + 58), f"{repeat:.0f}% repeat clusters | {top_cat[:24]}: {top_share:.0f}%", fill=PAGE["muted"], font=font(17))
        y += 92
    draw.text((x, box[3] - 34), "Bars show rounded internal index scores across 11 districts.", fill=PAGE["muted"], font=font(17))


def draw_quality_note(draw: ImageDraw.ImageDraw, summary: dict, box: tuple[int, int, int, int]) -> None:
    x, y = draw_card(draw, box, "Data Quality Note")
    alerts = summary.get("district_quality_alerts") or []
    e_alert = next((alert for alert in alerts if str(alert.get("council_district")) == "E"), None)
    unscored = summary.get("records_not_in_district_score")
    y = draw_wrapped(
        draw,
        "Point-in-polygon district assignment; requests reflect reporting behavior as well as conditions.",
        (x, y),
        58,
        PAGE["muted"],
        font(18),
        5,
    )
    if e_alert:
        share = float(e_alert.get("spatial_assignment_share", 0)) * 100
        y = draw_wrapped(draw, f"QA flag: District E spatial assignment share is {share:.1f}%; interpret E cautiously.", (x, y + 6), 58, PAGE["berry"], font(18, True), 5)
    if unscored is not None:
        draw_wrapped(draw, f"{int(unscored):,} cleaned requests are outside the district-score total.", (x, y + 6), 58, PAGE["muted"], font(18), 5)


def draw_screening_badge(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=8, fill=(255, 255, 252), outline=PAGE["berry"], width=2)
    draw.text((x1 + 24, y1 + 22), "SCREENING ANALYSIS", fill=PAGE["berry"], font=font(25, True))
    draw_wrapped(
        draw,
        "Reported 311 requests; not official City performance or verified infrastructure condition.",
        (x1 + 24, y1 + 64),
        54,
        PAGE["ink"],
        font(20),
        5,
    )


def draw_rank_table(draw: ImageDraw.ImageDraw, summary: dict, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=8, fill=PAGE["panel"], outline=PAGE["line"], width=2)
    draw.text((x1 + 24, y1 + 20), "All-District Rank", fill=PAGE["ink"], font=font(25, True))
    scored = summary.get("district_score_request_count", 0)
    total = summary.get("record_count", 0)
    draw.text((x1 + 330, y1 + 25), f"{scored:,} of {total:,} requests included in district scores", fill=PAGE["muted"], font=font(18))
    if not DISTRICT_FILE.exists():
        draw.text((x1 + 24, y1 + 72), "District score table unavailable.", fill=PAGE["muted"], font=font(20))
        return
    data = pd.read_csv(DISTRICT_FILE).sort_values("service_burden_score", ascending=False).reset_index(drop=True)
    header_y = y1 + 66
    draw.text((x1 + 24, header_y), "Rank", fill=PAGE["muted"], font=font(15, True))
    draw.text((x1 + 110, header_y), "Dist.", fill=PAGE["muted"], font=font(15, True))
    draw.text((x1 + 210, header_y), "Score", fill=PAGE["muted"], font=font(15, True))
    draw.text((x1 + 315, header_y), "Class", fill=PAGE["muted"], font=font(15, True))
    draw.text((x1 + 560, header_y), "Requests", fill=PAGE["muted"], font=font(15, True))
    draw.text((x1 + 735, header_y), "Density", fill=PAGE["muted"], font=font(15, True))
    y = header_y + 25
    for rank, row in data.iterrows():
        yy = y + rank * 19
        district = str(row["council_district"])
        if district == "E":
            district = "E*"
        klass = str(row["service_burden_class"])
        fill = SCORE_COLORS.get(klass, PAGE["muted"])
        row_font = font(15)
        draw.text((x1 + 24, yy), str(rank + 1), fill=PAGE["ink"], font=row_font)
        draw.text((x1 + 110, yy), district, fill=PAGE["ink"], font=font(15, True))
        draw.text((x1 + 210, yy), f"{row['service_burden_score']:.0f}", fill=PAGE["ink"], font=row_font)
        draw.rectangle((x1 + 315, yy + 2, x1 + 337, yy + 17), fill=fill, outline=(120, 126, 123))
        draw.text((x1 + 350, yy), klass, fill=PAGE["ink"], font=row_font)
        draw.text((x1 + 560, yy), f"{int(row['request_count']):,}", fill=PAGE["ink"], font=row_font)
        draw.text((x1 + 735, yy), f"{row['requests_per_sq_mile']:.0f}/sq mi", fill=PAGE["ink"], font=row_font)
    footnote_y = y2 - 28
    draw.line((x1 + 24, footnote_y - 8, x2 - 24, footnote_y - 8), fill=(230, 233, 230), width=1)
    draw.text((x1 + 24, footnote_y), "*District E has a spatial-assignment QA flag.", fill=PAGE["berry"], font=font(15, True))


def draw_component_breakdown(draw: ImageDraw.ImageDraw, summary: dict, box: tuple[int, int, int, int]) -> None:
    x, y = draw_card(draw, box, "Top District Components", title_size=26)
    top = summary.get("top_burden_council_district") or {}
    district = str(top.get("council_district", ""))
    if not district or not COMPONENT_FILE.exists():
        draw.text((x, y), "Component table unavailable.", fill=PAGE["muted"], font=font(19))
        return
    components = pd.read_csv(COMPONENT_FILE)
    top_components = components[components["council_district"].astype(str) == district]
    if top_components.empty:
        draw.text((x, y), "Component table unavailable.", fill=PAGE["muted"], font=font(19))
        return
    points = {
        "Density fallback": top_components[top_components["component"].isin(["resident_request_rate", "household_request_rate"])]["weighted_points"].sum(),
        "Median resolution": top_components[top_components["component"] == "median_resolution_days"]["weighted_points"].sum(),
        "Open/unclosed": top_components[top_components["component"] == "unresolved_share"]["weighted_points"].sum(),
        "Long-resolution": top_components[top_components["component"] == "long_resolution_share"]["weighted_points"].sum(),
        "Repeat clusters": top_components[top_components["component"] == "repeat_cluster_share"]["weighted_points"].sum(),
    }
    draw.text((x, y), f"District {district}; rounded point contribution to index score", fill=PAGE["muted"], font=font(17))
    y += 30
    bar_x = x + 250
    bar_w = 480
    max_points = max(points.values()) or 1
    for label, value in points.items():
        draw.text((x, y + 2), label, fill=PAGE["ink"], font=font(17))
        draw.rounded_rectangle((bar_x, y + 4, bar_x + bar_w, y + 20), radius=3, fill=(235, 238, 235))
        draw.rounded_rectangle((bar_x, y + 4, bar_x + int(bar_w * value / max_points), y + 20), radius=3, fill=SCORE_COLORS["Very High"])
        draw.text((bar_x + bar_w + 14, y), f"{value:.0f}", fill=PAGE["ink"], font=font(17, True))
        y += 25


def draw_scale_bar(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    segment = 130
    draw.text((x, y - 42), "Scale (approx.)", fill=PAGE["ink"], font=font(23, True))
    for i in range(4):
        fill = PAGE["ink"] if i % 2 == 0 else PAGE["panel"]
        draw.rectangle((x + i * segment, y, x + (i + 1) * segment, y + 24), fill=fill, outline=PAGE["ink"], width=2)
    for i, label in enumerate(["0", "5", "10", "15", "20 mi"]):
        xx = x + i * segment
        draw.line((xx, y, xx, y + 34), fill=PAGE["ink"], width=2)
        draw.text((xx - 10, y + 42), label, fill=PAGE["ink"], font=font(19))
    draw.text((x, y + 80), "Approximate because this plate uses a static image frame.", fill=PAGE["muted"], font=font(18))


def draw_locator_inset(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=8, fill=PAGE["panel"], outline=PAGE["line"], width=2)
    draw.text((x1 + 24, y1 + 22), "Regional Locator", fill=PAGE["ink"], font=font(25, True))
    if not BOUNDARY_FILE.exists():
        draw.text((x1 + 24, y1 + 70), "Council boundary file unavailable.", fill=PAGE["muted"], font=font(19))
        return
    geojson = json.loads(BOUNDARY_FILE.read_text(encoding="utf-8"))
    rings = []
    xs, ys = [], []
    for feature in geojson.get("features", []):
        geom = feature.get("geometry", {})
        coords = geom.get("coordinates", [])
        polygons = coords if geom.get("type") == "MultiPolygon" else [coords]
        for polygon in polygons:
            for ring in polygon[:1]:
                rings.append(ring)
                for lon, lat in ring:
                    xs.append(lon)
                    ys.append(lat)
    if not xs:
        return
    lon_min, lon_max = min(xs) - 0.35, max(xs) + 0.35
    lat_min, lat_max = min(ys) - 0.25, max(ys) + 0.25
    map_box = (x1 + 30, y1 + 70, x2 - 275, y2 - 28)
    def project(lon: float, lat: float) -> tuple[float, float]:
        left, top, right, bottom = map_box
        x = left + (lon - lon_min) / (lon_max - lon_min) * (right - left)
        y = bottom - (lat - lat_min) / (lat_max - lat_min) * (bottom - top)
        return x, y
    draw.rounded_rectangle(map_box, radius=4, fill=(244, 246, 244), outline=(197, 203, 200), width=1)
    # Schematic regional context; the highlighted shape is the actual council-district study area.
    for label, lon, lat in [
        ("Harris County area", -95.42, 29.86),
        ("Galveston Bay", -94.95, 29.58),
        ("Fort Bend", -95.72, 29.55),
    ]:
        px, py = project(lon, lat)
        draw.text((px, py), label, fill=(142, 150, 146), font=font(15))
    for ring in rings:
        pts = [project(lon, lat) for lon, lat in ring]
        if len(pts) >= 3:
            draw.polygon(pts, fill=(213, 222, 214), outline=(77, 86, 82))
    draw.text((x2 - 240, y1 + 76), "Houston", fill=PAGE["ink"], font=font(22, True))
    draw_wrapped(
        draw,
        "Study area shown in regional Gulf Coast context. Locator is schematic except for the highlighted council-district geometry.",
        (x2 - 240, y1 + 114),
        28,
        PAGE["muted"],
        font(18),
        5,
    )


def save_accessibility_exports() -> None:
    if not PLATE_FILE.exists():
        return
    plate = Image.open(PLATE_FILE).convert("RGB")
    grayscale = plate.convert("L").convert("RGB")
    grayscale.save(GRAYSCALE_PLATE_FILE)
    thumbnail = plate.copy()
    thumbnail.thumbnail((1400, 1082), Image.Resampling.LANCZOS)
    thumbnail.save(THUMBNAIL_FILE)


def paste_map_image(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    source: Path,
    box: tuple[int, int, int, int],
    crop: tuple[int, int, int, int] | None = None,
) -> None:
    map_img = Image.open(source).convert("RGB")
    if crop:
        map_img = map_img.crop(crop)
    if source.name != "council_district_service_burden_map_body.png":
        map_img = map_img.crop((40, 28, map_img.width - 40, map_img.height - 28))
    max_w = box[2] - box[0]
    max_h = box[3] - box[1]
    scale = min(max_w / map_img.width, max_h / map_img.height)
    map_img = map_img.resize((int(map_img.width * scale), int(map_img.height * scale)), Image.Resampling.LANCZOS)
    map_x = box[0] + ((box[2] - box[0]) - map_img.width) // 2
    map_y = box[1] + ((box[3] - box[1]) - map_img.height) // 2
    img.paste(map_img, (map_x, map_y))


def make_main_plate() -> None:
    ensure_directories()
    main_source = MAIN_MAP if MAIN_MAP.exists() else MAIN_MAP_FALLBACK
    if not main_source.exists():
        raise SystemExit(f"Missing main map: {main_source}")
    summary = json.loads(SUMMARY_FILE.read_text(encoding="utf-8")) if SUMMARY_FILE.exists() else {}

    img = Image.new("RGB", (PAGE["width"], PAGE["height"]), PAGE["background"])
    draw = ImageDraw.Draw(img)
    draw_title_block(
        draw,
        "Reported Houston 311 Infrastructure Requests",
        "Council-district screening index | Apr-Jun 2025 bounded sample | ACS not used; area-density fallback",
    )
    draw_screening_badge(draw, (2280, 82, 3170, 205))

    paste_map_image(img, draw, main_source, (75, 238, 2245, 1660), crop=(92, 52, 1314, 848))
    draw_locator_inset(draw, (75, 1710, 1085, 2075))
    draw_rank_table(draw, summary, (1125, 1710, 2245, 2075))

    draw_at_a_glance(draw, summary, (2280, 248, 3170, 480))
    draw_score_method(draw, (2280, 510, 3170, 790))
    draw_plate_legend(draw, (2280, 820, 3170, 1095))
    draw_top_drivers(draw, (2280, 1125, 3170, 1608))
    draw_quality_note(draw, summary, (2280, 1638, 3170, 1865))
    draw_component_breakdown(draw, summary, (2280, 1895, 3170, 2145))

    sources = (
        "City of Houston 311 Archive; COHGIS / Harris County council district polygons; "
        "H-GAC major roads and rivers. ACS normalization is not used in this committed output."
    )
    limitations = (
        "Source request coordinates are WGS84 latitude/longitude. Council district area values use "
        "source boundary geometry attributes. Scale bar omitted until a projected CRS workflow is added."
    )
    draw.rounded_rectangle((130, 2170, 3170, 2380), radius=8, fill=PAGE["panel"], outline=PAGE["line"], width=2)
    draw.text((170, 2202), "Sources", fill=PAGE["ink"], font=font(28, True))
    draw_wrapped(draw, sources, (170, 2255), 72, PAGE["muted"], font(20), 5)
    draw.text((1585, 2202), "Limitations", fill=PAGE["ink"], font=font(28, True))
    draw_wrapped(draw, limitations, (1585, 2255), 76, PAGE["muted"], font(20), 5)
    draw.text((170, 2340), "Analytical screening product; not an official City of Houston performance measure.", fill=PAGE["berry"], font=font(20, True))

    img.save(PLATE_FILE)
    print(f"Wrote {PLATE_FILE}")


def make_standard_plate(
    source: Path,
    output: Path,
    title: str,
    subtitle: str,
    interpretation: str,
) -> None:
    if not source.exists():
        return
    img = Image.new("RGB", (PAGE["width"], PAGE["height"]), PAGE["background"])
    draw = ImageDraw.Draw(img)
    draw_title_block(draw, title, subtitle)
    draw.rounded_rectangle((100, 250, 2220, 1885), radius=8, fill=(240, 243, 240), outline=PAGE["line"], width=3)
    paste_map_image(img, draw, source, (130, 280, 2190, 1840))
    draw.rounded_rectangle((2280, 250, 3170, 1380), radius=8, fill=PAGE["panel"], outline=PAGE["line"], width=2)
    draw.text((2320, 292), "How To Read This Map", fill=PAGE["ink"], font=font(36, True))
    draw_wrapped(draw, interpretation, (2320, 360), 48, PAGE["muted"], font(25), 8)
    draw_scale_bar(draw, 2320, 1500)
    draw.rounded_rectangle((130, 2050, 3170, 2388), radius=8, fill=PAGE["panel"], outline=PAGE["line"], width=2)
    draw.text((170, 2090), "Sources and Notes", fill=PAGE["ink"], font=font(34, True))
    draw_wrapped(
        draw,
        "Sources: City of Houston 311 Archive; COHGIS / Harris County council district polygons; H-GAC map context layers. Static analytical output; not an official City of Houston metric.",
        (170, 2150),
        150,
        PAGE["muted"],
        font(24),
        8,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output)


def make_component_sheet() -> Path:
    component_sources = [
        (MAPS / "request_density_component.png", "Request density"),
        (MAPS / "unresolved_share_component.png", "Unresolved share"),
        (MAPS / "long_resolution_share_component.png", "Long-resolution share"),
        (MAPS / "repeat_cluster_share_component.png", "Repeat-cluster share"),
    ]
    output = MAP_PLATES / "score_component_small_multiples.png"
    img = Image.new("RGB", (PAGE["width"], PAGE["height"]), PAGE["background"])
    draw = ImageDraw.Draw(img)
    draw_title_block(
        draw,
        "Score Component Map Series",
        "Council district component maps | April-June 2025 | Static GIS small multiples",
    )
    boxes = [(110, 280, 1600, 1160), (1700, 280, 3190, 1160), (110, 1270, 1600, 2150), (1700, 1270, 3190, 2150)]
    for (source, label), box in zip(component_sources, boxes):
        draw.rounded_rectangle((box[0] - 20, box[1] - 20, box[2] + 20, box[3] + 60), radius=8, fill=(240, 243, 240), outline=PAGE["line"], width=2)
        draw.text((box[0], box[3] + 20), label, fill=PAGE["ink"], font=font(28, True))
        if source.exists():
            paste_map_image(img, draw, source, box)
    draw.text((130, 2360), "Component maps explain which inputs drive the composite burden score. Quartiles are classified separately by component.", fill=PAGE["muted"], font=font(26))
    img.save(output)
    return output


def make_executive_brief(summary: dict) -> Path:
    output = DELIVERABLES / "executive_brief.png"
    top = summary.get("top_burden_council_district") or {}
    img = Image.new("RGB", (2550, 3300), PAGE["background"])
    draw = ImageDraw.Draw(img)
    draw.text((110, 95), "Reported Houston 311 Infrastructure Requests", fill=PAGE["ink"], font=font(58, True))
    draw.text((112, 170), "One-page static GIS screening brief | April-June 2025", fill=PAGE["muted"], font=font(32))
    source = MAIN_MAP if MAIN_MAP.exists() else MAIN_MAP_FALLBACK
    paste_map_image(img, draw, source, (110, 260, 2440, 1760))
    draw.text((110, 1880), "Key Findings", fill=PAGE["ink"], font=font(42, True))
    findings = [
        f"{summary.get('record_count', 0):,} cleaned infrastructure-related 311 records.",
        f"Top-scoring district: {top.get('council_district', 'n/a')} ({top.get('service_burden_score', 0):.0f}, {top.get('service_burden_class', 'n/a')}).",
        f"Overall open/unclosed share as of pull: {fmt_pct(summary.get('unresolved_share_overall'))}.",
        f"Overall repeat-cluster share: {fmt_pct(summary.get('repeat_cluster_share_overall'))}.",
    ]
    y = 1950
    for finding in findings:
        draw.ellipse((120, y + 14, 140, y + 34), fill=PAGE["accent"])
        y = draw_wrapped(draw, finding, (165, y), 92, PAGE["ink"], font(30), 10) + 14
    draw.text((110, 2360), "Method Note", fill=PAGE["ink"], font=font(42, True))
    draw_wrapped(
        draw,
        "The score is a screening index. ACS normalization is not used in this committed output; request rates use area-density fallback.",
        (110, 2430),
        92,
        PAGE["muted"],
        font(30),
        10,
    )
    draw.text((110, 2940), "Limitations", fill=PAGE["ink"], font=font(42, True))
    draw_wrapped(
        draw,
        "This is a public-data screening analysis, not an official City of Houston performance metric or a complete measure of infrastructure need.",
        (110, 3010),
        92,
        PAGE["muted"],
        font(30),
        10,
    )
    img.save(output)
    return output


def write_static_report() -> None:
    summary = json.loads(SUMMARY_FILE.read_text(encoding="utf-8")) if SUMMARY_FILE.exists() else {}
    top = summary.get("top_burden_council_district") or {}
    scored = summary.get("district_score_request_count", 0)
    unscored = summary.get("records_not_in_district_score", 0)
    quality_alerts = summary.get("district_quality_alerts") or []
    report = f"""# Static GIS Report: Reported Houston 311 Infrastructure Requests

## Research Question

Which Houston council districts rank highest in a reported-311-request screening index for infrastructure-related requests?

## Study Period And Data

- Study period: April 1, 2025 through June 30, 2025
- Cleaned infrastructure records: {summary.get("record_count", 0):,}
- Records included in council-district scoring: {scored:,}
- Records not included in council-district scoring: {unscored:,}
- Boundary unit: City Council district
- Main committed rate method: requests per square mile; ACS population/household normalization is not used in this version

## Main Map Plate

![Main map plate](map_plates/houston_311_service_burden_map_plate.png)

## Principal Findings

- Top-scoring district: {top.get("council_district", "n/a")} ({top.get("service_burden_score", 0):.0f}, {top.get("service_burden_class", "n/a")})
- Overall open/unclosed share as of data pull: {fmt_pct(summary.get("unresolved_share_overall"))}
- Overall long-resolution share: {fmt_pct(summary.get("long_resolution_share_overall"))}
- Overall repeat-cluster share: {fmt_pct(summary.get("repeat_cluster_share_overall"))}
- Largest standardized category: {summary.get("top_standardized_category", {}).get("category", "n/a")} ({fmt_pct(summary.get("top_standardized_category", {}).get("share"))})

## Method Summary

The pipeline filters 311 records to infrastructure-related request types, cleans date and coordinate fields, assigns request points to official council district polygons, screens approximate repeat-location clusters, and aggregates district metrics. The screening score combines area-density fallback, median resolution days, open/unclosed share, long-resolution share, and repeat-cluster share. It is not an official City performance measure or a verified infrastructure-condition measure.

## Data Quality Flags

{chr(10).join(f"- District {alert.get('council_district')}: spatial assignment share {fmt_pct(alert.get('spatial_assignment_share'))}" for alert in quality_alerts) if quality_alerts else "- No district spatial-assignment alerts below the configured review threshold."}

## Static GIS Deliverables

- `deliverables/map_plates/houston_311_service_burden_map_plate.png`
- `deliverables/map_plates/houston_311_service_burden_map_plate_grayscale.png`
- `deliverables/map_plates/houston_311_service_burden_map_plate_thumbnail.png`
- `deliverables/map_plates/repeat_location_cluster_map_plate.png`
- `deliverables/map_plates/score_component_small_multiples.png`
- `deliverables/map_plates/non_solid_waste_screening_map_plate.png`
- `deliverables/map_plates/category_balanced_density_map_plate.png`
- `deliverables/map_plates/district_assignment_qa_map_plate.png`
- `deliverables/houston_311_static_gis_atlas.pdf`
- `deliverables/executive_brief.png`
- `deliverables/map_atlas.md`
- `outputs/maps/*.png`
- `outputs/figures/*.png`
- `outputs/tables/*.csv`

## Score Components

The composite score is supported by `outputs/tables/score_components.csv` and four static component maps:

- request density
- unresolved request share
- long-resolution request share
- repeat-cluster request share

These outputs help explain whether a high burden score is driven mainly by request density, slow resolution, open cases, or recurring locations.

## Sensitivity And QA Outputs

The project also exports alternate score and QA diagnostics:

- `outputs/tables/source_spatial_assignment_matrix.csv`
- `outputs/tables/unscored_request_diagnostics.csv`
- `outputs/tables/score_sensitivity_rankings.csv`
- `outputs/tables/council_district_non_solid_waste_screening.csv`
- `outputs/tables/category_balanced_district_density.csv`
- `outputs/gis/*.geojson`

## Limitations

The output is a public-data screening analysis. It is not an official City of Houston performance measure, not a causal model, and not a complete inventory of infrastructure need. 311 requests reflect reporting behavior as well as conditions. ACS population and household normalization is not used in this committed version; it awaits a valid Census API key. The primary map omits a scale bar until a projected CRS workflow is added.
"""
    (DELIVERABLES / "static_gis_report.md").write_text(report, encoding="utf-8")


def write_map_atlas() -> None:
    atlas = """# Static GIS Map Atlas

## Primary Plate

- `map_plates/houston_311_service_burden_map_plate.png` - formal static GIS plate for the council-district 311 request screening index.
- `map_plates/houston_311_service_burden_map_plate_grayscale.png` - grayscale/print-safety variant of the primary plate.
- `map_plates/houston_311_service_burden_map_plate_thumbnail.png` - smaller preview version for README and web previews.
- `map_plates/repeat_location_cluster_map_plate.png` - formal plate for repeat-location clusters.
- `map_plates/solid_waste_recycling_map_plate.png` - formal thematic plate.
- `map_plates/water_sewer_drainage_map_plate.png` - formal thematic plate.
- `map_plates/roads_signals_sidewalks_map_plate.png` - formal thematic plate.
- `map_plates/score_component_small_multiples.png` - four-panel component map sheet.
- `map_plates/non_solid_waste_screening_map_plate.png` - sensitivity plate excluding Solid Waste / Recycling requests.
- `map_plates/category_balanced_density_map_plate.png` - equal-category density comparison plate.
- `map_plates/district_assignment_qa_map_plate.png` - spatial assignment QA plate.

## Core Maps

- `../outputs/maps/council_district_service_burden_choropleth.png` - main analytical choropleth.
- `../outputs/maps/repeat_location_clusters.png` - repeat-location cluster screening map.
- `../outputs/maps/overall_infrastructure_request_points.png` - point distribution map.
- `../outputs/maps/open_or_long_resolution_requests.png` - unresolved or long-resolution point distribution.
- `../outputs/maps/request_density_component.png` - score component map.
- `../outputs/maps/unresolved_share_component.png` - score component map.
- `../outputs/maps/long_resolution_share_component.png` - score component map.
- `../outputs/maps/repeat_cluster_share_component.png` - score component map.
- `../outputs/maps/non_solid_waste_screening_score.png` - sensitivity score map.
- `../outputs/maps/category_balanced_density_score.png` - category-balanced density comparison map.
- `../outputs/maps/district_assignment_qa_flags.png` - district assignment QA map.

## Thematic Map Series

- `../outputs/maps/solid_waste_recycling_burden.png`
- `../outputs/maps/water_sewer_drainage_burden.png`
- `../outputs/maps/roads_signals_sidewalks_burden.png`

## Supporting Figures

- `../outputs/figures/request_count_by_category.png`
- `../outputs/figures/median_resolution_time_by_category.png`
- `../outputs/figures/open_unresolved_share_by_category.png`
- `../outputs/figures/monthly_request_volume.png`
"""
    (DELIVERABLES / "map_atlas.md").write_text(atlas, encoding="utf-8")


def make_pdf_atlas(images: list[Path]) -> None:
    pages = []
    for path in images:
        if path.exists():
            pages.append(Image.open(path).convert("RGB"))
    if pages:
        pages[0].save(PDF_ATLAS, save_all=True, append_images=pages[1:])


def make_all_plates(summary: dict) -> list[Path]:
    make_main_plate()
    save_accessibility_exports()
    plate_specs = [
        (
            MAPS / "repeat_location_clusters.png",
            MAP_PLATES / "repeat_location_cluster_map_plate.png",
            "Repeat-Location Infrastructure Clusters",
            "Approximate recurring 311 infrastructure request locations",
            "Bubble symbols show approximate coordinate/category bins with three or more requests. This is a screening map for recurring service locations, not address-level deduplication.",
        ),
        (
            MAPS / "solid_waste_recycling_burden.png",
            MAP_PLATES / "solid_waste_recycling_map_plate.png",
            "Solid Waste and Recycling Request Rate",
            "Council district thematic map | April-June 2025",
            "Districts are shaded by within-theme request rate quartiles. This map highlights the dominant request category in the extract.",
        ),
        (
            MAPS / "water_sewer_drainage_burden.png",
            MAP_PLATES / "water_sewer_drainage_map_plate.png",
            "Water, Sewer, and Drainage Request Rate",
            "Council district thematic map | April-June 2025",
            "Districts are shaded by within-theme request rate quartiles for water, sewer, and drainage-related request categories.",
        ),
        (
            MAPS / "roads_signals_sidewalks_burden.png",
            MAP_PLATES / "roads_signals_sidewalks_map_plate.png",
            "Road, Signal, and Sidewalk Request Rate",
            "Council district thematic map | April-June 2025",
            "Districts are shaded by within-theme request rate quartiles for road, signal, lighting, sidewalk, and bike-lane request categories.",
        ),
        (
            MAPS / "non_solid_waste_screening_score.png",
            MAP_PLATES / "non_solid_waste_screening_map_plate.png",
            "Non-Solid-Waste Screening Score",
            "Sensitivity map excluding Solid Waste / Recycling requests",
            "This plate tests whether district rankings are driven mainly by the dominant Solid Waste / Recycling category. It uses the current score weights on non-solid-waste request categories only.",
        ),
        (
            MAPS / "category_balanced_density_score.png",
            MAP_PLATES / "category_balanced_density_map_plate.png",
            "Category-Balanced Request Density",
            "Equal-category density comparison | April-June 2025",
            "This plate averages district density percentiles across request categories so no single high-volume category dominates the density comparison.",
        ),
        (
            MAPS / "district_assignment_qa_flags.png",
            MAP_PLATES / "district_assignment_qa_map_plate.png",
            "Council District Assignment QA",
            "Spatial assignment share by source council district",
            "This plate highlights districts where source-labeled records do not consistently spatially assign to the current council-district polygons. It is a QA layer, not part of the score.",
        ),
    ]
    outputs = [PLATE_FILE, GRAYSCALE_PLATE_FILE]
    for source, output, title, subtitle, interpretation in plate_specs:
        make_standard_plate(source, output, title, subtitle, interpretation)
        outputs.append(output)
    outputs.append(make_component_sheet())
    outputs.append(make_executive_brief(summary))
    return outputs


def main() -> None:
    summary = json.loads(SUMMARY_FILE.read_text(encoding="utf-8")) if SUMMARY_FILE.exists() else {}
    plates = make_all_plates(summary)
    write_static_report()
    write_map_atlas()
    make_pdf_atlas(plates)
    print("Wrote static GIS deliverables.")


if __name__ == "__main__":
    main()
