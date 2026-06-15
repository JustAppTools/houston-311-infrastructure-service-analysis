import json
import math
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from project_config import CANVAS, DATA_CONTEXT, FIGURES, MAPS, TABLES, ensure_directories


CLEAN_FILE = Path(__file__).resolve().parents[1] / "data" / "processed" / "houston_311_infrastructure_requests_cleaned.csv"
BOUNDARY_FILE = DATA_CONTEXT / "council_district_boundaries.geojson"
MAJOR_ROADS_FILE = DATA_CONTEXT / "major_roads.geojson"
MAJOR_RIVERS_FILE = DATA_CONTEXT / "major_rivers.geojson"


PALETTE = [
    (31, 111, 125),
    (192, 94, 72),
    (92, 137, 76),
    (126, 90, 138),
    (185, 139, 56),
    (73, 100, 150),
    (131, 91, 65),
]


BURDEN_COLORS = {
    "Low": (137, 171, 112),
    "Medium": (220, 185, 101),
    "High": (210, 121, 84),
    "Very High": (148, 49, 73),
}


REFERENCE_LABELS = [
    ("Downtown", -95.3698, 29.7604, (12, -22)),
    ("IH 610", -95.405, 29.818, (12, -14)),
    ("Buffalo Bayou", -95.48, 29.765, (10, -18)),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def canvas(title: str, subtitle: str = "") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (CANVAS["width"], CANVAS["height"]), CANVAS["background"])
    draw = ImageDraw.Draw(img)
    if title:
        draw.text((CANVAS["margin"], 38), title, fill=CANVAS["ink"], font=font(34, True))
    if subtitle:
        draw.text((CANVAS["margin"], 82), subtitle, fill=CANVAS["muted"], font=font(20))
    return img, draw


def score_class(score: float) -> str:
    if score >= 75:
        return "Very High"
    if score >= 50:
        return "High"
    if score >= 25:
        return "Medium"
    return "Low"


def load_boundaries() -> dict | None:
    if not BOUNDARY_FILE.exists():
        return None
    return json.loads(BOUNDARY_FILE.read_text(encoding="utf-8"))


def load_geojson(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def iter_rings(geometry: dict):
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if geom_type == "Polygon":
        for ring in coords:
            yield ring
    elif geom_type == "MultiPolygon":
        for polygon in coords:
            for ring in polygon:
                yield ring


def iter_lines(geometry: dict):
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if geom_type == "LineString":
        yield coords
    elif geom_type == "MultiLineString":
        for line in coords:
            yield line


def clip_segment(
    p1: tuple[float, float],
    p2: tuple[float, float],
    box: tuple[int, int, int, int],
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    left, top, right, bottom = box
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    p = [-dx, dx, -dy, dy]
    q = [x1 - left, right - x1, y1 - top, bottom - y1]
    u1, u2 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if pi == 0:
            if qi < 0:
                return None
        else:
            u = qi / pi
            if pi < 0:
                u1 = max(u1, u)
            else:
                u2 = min(u2, u)
    if u1 > u2:
        return None
    return ((x1 + u1 * dx, y1 + u1 * dy), (x1 + u2 * dx, y1 + u2 * dy))


def draw_context_lines(
    draw: ImageDraw.ImageDraw,
    project,
    clip_box: tuple[int, int, int, int],
) -> None:
    layers = [
        (load_geojson(MAJOR_RIVERS_FILE), (138, 180, 191), 1),
        (load_geojson(MAJOR_ROADS_FILE), (214, 218, 215), 1),
    ]
    for geojson, color, width in layers:
        if not geojson:
            continue
        for feature in geojson.get("features", []):
            for line in iter_lines(feature.get("geometry", {})):
                pts = [project(lon, lat) for lon, lat in line]
                for p1, p2 in zip(pts, pts[1:]):
                    clipped = clip_segment(p1, p2, clip_box)
                    if clipped:
                        draw.line(clipped, fill=color, width=width)


def draw_reference_labels(draw: ImageDraw.ImageDraw, project, clip_box: tuple[int, int, int, int]) -> None:
    left, top, right, bottom = clip_box
    for label, lon, lat, offset in REFERENCE_LABELS:
        x, y = project(lon, lat)
        if not (left <= x <= right and top <= y <= bottom):
            continue
        dx, dy = offset
        label_font = font(14, True)
        tx, ty = x + dx, y + dy
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]:
            draw.text((tx + ox, ty + oy), label, fill=(255, 255, 252), font=label_font)
        draw.text((tx, ty), label, fill=(72, 79, 80), font=label_font)


LABEL_OFFSETS = {
    "C": (-8, 8),
    "G": (-10, -10),
    "H": (8, -8),
    "I": (10, 4),
    "J": (0, 12),
}


def draw_district_labels(draw: ImageDraw.ImageDraw, boundaries: dict, project, size: int = 19) -> None:
    for feature in boundaries.get("features", []):
        district = str(feature.get("properties", {}).get("DISTRICT", "")).strip()
        lon, lat = feature_label_point(feature)
        x, y = project(lon, lat)
        dx, dy = LABEL_OFFSETS.get(district, (0, 0))
        x += dx
        y += dy
        radius = max(15, size - 3)
        draw.ellipse((x - radius - 2, y - radius - 2, x + radius + 2, y + radius + 2), fill=(255, 255, 255))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(255, 255, 255), outline=(67, 73, 73), width=2)
        bbox = draw.textbbox((0, 0), district, font=font(size, True))
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text((x - text_w / 2, y - text_h / 2 - 1), district, fill=CANVAS["ink"], font=font(size, True))


def draw_north_arrow(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.line((x, y + 62, x, y + 12), fill=CANVAS["ink"], width=3)
    draw.polygon([(x, y), (x - 15, y + 34), (x, y + 25), (x + 15, y + 34)], fill=CANVAS["ink"])
    label_font = font(18, True)
    bbox = draw.textbbox((0, 0), "N", font=label_font)
    label_w = bbox[2] - bbox[0]
    draw.text((x - label_w / 2, y + 72), "N", fill=CANVAS["ink"], font=label_font)


def boundary_extent(boundaries: dict | None, fallback_df: pd.DataFrame) -> tuple[float, float, float, float]:
    xs, ys = [], []
    if boundaries:
        for feature in boundaries.get("features", []):
            for ring in iter_rings(feature.get("geometry", {})):
                for lon, lat in ring:
                    xs.append(lon)
                    ys.append(lat)
    if not xs:
        geo = valid_geo(fallback_df)
        xs = geo["longitude"].tolist()
        ys = geo["latitude"].tolist()
    lon_min, lon_max = min(xs), max(xs)
    lat_min, lat_max = min(ys), max(ys)
    lon_pad = max((lon_max - lon_min) * 0.05, 0.02)
    lat_pad = max((lat_max - lat_min) * 0.05, 0.02)
    return lon_min - lon_pad, lon_max + lon_pad, lat_min - lat_pad, lat_max + lat_pad


def make_projector(extent: tuple[float, float, float, float], box: tuple[int, int, int, int]):
    lon_min, lon_max, lat_min, lat_max = extent
    left, top, right, bottom = box

    def project(lon: float, lat: float) -> tuple[float, float]:
        x = left + (lon - lon_min) / (lon_max - lon_min) * (right - left)
        y = bottom - (lat - lat_min) / (lat_max - lat_min) * (bottom - top)
        return x, y

    return project


def draw_boundary_backdrop(
    draw: ImageDraw.ImageDraw,
    boundaries: dict | None,
    project,
    fill: tuple[int, int, int] | None = None,
    outline: tuple[int, int, int] = (172, 178, 178),
    width: int = 2,
) -> None:
    if not boundaries:
        return
    for feature in boundaries.get("features", []):
        for i, ring in enumerate(iter_rings(feature.get("geometry", {}))):
            pts = [project(lon, lat) for lon, lat in ring]
            if len(pts) >= 3:
                draw.polygon(pts, fill=fill if i == 0 else None, outline=outline)
                if width > 1:
                    draw.line(pts + [pts[0]], fill=outline, width=width)


def feature_label_point(feature: dict) -> tuple[float, float]:
    xs, ys = [], []
    for ring in iter_rings(feature.get("geometry", {})):
        for lon, lat in ring:
            xs.append(lon)
            ys.append(lat)
    return (sum(xs) / len(xs), sum(ys) / len(ys)) if xs else (0, 0)


def save_bar_chart(data: pd.DataFrame, label_col: str, value_col: str, title: str, path: Path, suffix: str = "") -> None:
    data = data.head(10).iloc[::-1]
    img, draw = canvas(title, "City of Houston 311 archive extract; V3 infrastructure categories")
    left, top, right, bottom = 410, 145, CANVAS["width"] - 120, CANVAS["height"] - 90
    max_value = max(float(data[value_col].max()), 1)
    bar_h = max(28, (bottom - top) // max(len(data), 1) - 12)
    for i, (_, row) in enumerate(data.iterrows()):
        y = top + i * ((bottom - top) / max(len(data), 1))
        value = float(row[value_col])
        width = int((right - left) * value / max_value)
        color = PALETTE[i % len(PALETTE)]
        label = str(row[label_col])
        draw.text((CANVAS["margin"], y + 3), label[:38], fill=CANVAS["ink"], font=font(19))
        draw.rounded_rectangle((left, y, left + width, y + bar_h), radius=3, fill=color)
        text = f"{value:,.1f}{suffix}" if suffix else f"{value:,.0f}"
        draw.text((left + width + 10, y + 2), text, fill=CANVAS["ink"], font=font(18, True))
    draw.line((left, top - 10, left, bottom), fill=CANVAS["grid"], width=2)
    img.save(path)


def save_share_chart(data: pd.DataFrame, title: str, path: Path) -> None:
    display = data.sort_values("unresolved_share", ascending=False).head(10).iloc[::-1]
    display = display.assign(unresolved_pct=display["unresolved_share"] * 100)
    save_bar_chart(display, "standardized_category", "unresolved_pct", title, path, suffix="%")


def save_month_chart(df: pd.DataFrame, path: Path) -> None:
    monthly = df.groupby("month").size().reset_index(name="request_count").sort_values("month")
    img, draw = canvas("Monthly Request Volume", "Infrastructure-related Houston 311 requests in the V3 extract")
    left, top, right, bottom = 140, 170, CANVAS["width"] - 110, CANVAS["height"] - 120
    if len(monthly) < 2:
        draw.text((left, top), "The extract covers one month, so a trend line is not interpreted.", fill=CANVAS["ink"], font=font(24, True))
        draw.text((left, top + 48), f"{monthly.iloc[0]['month']}: {int(monthly.iloc[0]['request_count']):,} infrastructure records", fill=CANVAS["muted"], font=font(23))
        img.save(path)
        return
    max_y = max(monthly["request_count"].max(), 1)
    min_y = min(monthly["request_count"].min(), 0)
    points = []
    for i, row in monthly.reset_index(drop=True).iterrows():
        x = left + i * (right - left) / (len(monthly) - 1)
        y = bottom - (row["request_count"] - min_y) * (bottom - top) / (max_y - min_y)
        points.append((x, y))
    for grid_i in range(5):
        y = top + grid_i * (bottom - top) / 4
        value = max_y - grid_i * (max_y - min_y) / 4
        draw.line((left, y, right, y), fill=CANVAS["grid"], width=1)
        draw.text((left - 92, y - 10), f"{value:,.0f}", fill=CANVAS["muted"], font=font(16))
    draw.line((left, top, left, bottom), fill=CANVAS["grid"], width=2)
    draw.line((left, bottom, right, bottom), fill=CANVAS["grid"], width=2)
    draw.line(points, fill=CANVAS["accent"], width=5)
    for x, y in points:
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=CANVAS["accent2"])
    for i, row in monthly.reset_index(drop=True).iterrows():
        x, y = points[i]
        value = int(row["request_count"])
        draw.text((x - 35, y - 36), f"{value:,}", fill=CANVAS["ink"], font=font(18, True))
        draw.text((x - 35, bottom + 18), str(row["month"]), fill=CANVAS["ink"], font=font(17))
    img.save(path)


def valid_geo(df: pd.DataFrame) -> pd.DataFrame:
    geo = df.dropna(subset=["latitude", "longitude"]).copy()
    return geo[(geo["latitude"].between(29.0, 30.2)) & (geo["longitude"].between(-96.2, -94.6))]


def draw_map(df: pd.DataFrame, title: str, path: Path, color: tuple[int, int, int] = (31, 111, 125)) -> None:
    geo = valid_geo(df)
    img, draw = canvas(title, "Point positions from City of Houston 311 latitude/longitude fields")
    left, top, right, bottom = 100, 140, CANVAS["width"] - 90, CANVAS["height"] - 90
    draw.rectangle((left, top, right, bottom), outline=(185, 191, 191), width=2, fill=(241, 243, 240))
    boundaries = load_boundaries()
    if geo.empty:
        draw.text((left + 40, top + 40), "No valid coordinates in this extract.", fill=CANVAS["ink"], font=font(24, True))
        img.save(path)
        return
    extent = boundary_extent(boundaries, geo)
    project = make_projector(extent, (left, top, right, bottom))
    draw_boundary_backdrop(draw, boundaries, project, fill=(235, 238, 235), outline=(198, 203, 201), width=1)
    draw_context_lines(draw, project, (left, top, right, bottom))
    sample = geo.sample(n=min(len(geo), 12000), random_state=42)
    for _, row in sample.iterrows():
        x, y = project(row["longitude"], row["latitude"])
        if left <= x <= right and top <= y <= bottom:
            draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=color)
    draw.text((left, bottom + 22), f"{len(geo):,} valid coordinate records; random sample drawn when over 12,000 points.", fill=CANVAS["muted"], font=font(18))
    img.save(path)


def draw_burden_map(df: pd.DataFrame, path: Path, show_header: bool = True, show_side_info: bool = True) -> None:
    area_path = TABLES / "council_district_service_burden.csv"
    driver_path = TABLES / "district_burden_drivers.csv"
    img, draw = canvas(
        "Houston 311 Infrastructure Burden by Council District" if show_header else "",
        "April-June 2025; score uses ACS rates when available, otherwise area density, plus resolution/open/repeat metrics" if show_header else "",
    )
    top_offset = 140 if show_header else 58
    bottom_offset = CANVAS["height"] - 90 if show_header else CANVAS["height"] - 56
    left, top, right, bottom = 100, top_offset, CANVAS["width"] - 90, bottom_offset
    draw.rectangle((left, top, right, bottom), outline=(185, 191, 191), width=2, fill=(241, 243, 240))
    geo = valid_geo(df)
    boundaries = load_boundaries()
    if geo.empty or not area_path.exists() or not boundaries:
        draw.text((left + 40, top + 40), "No valid coordinate, boundary, or council-district data in this extract.", fill=CANVAS["ink"], font=font(24, True))
        img.save(path)
        return
    area = pd.read_csv(area_path)
    area_by_district = {str(row["council_district"]): row for _, row in area.iterrows()}
    extent = boundary_extent(boundaries, geo)
    map_right = right - 330 if show_side_info else right
    project = make_projector(extent, (left, top, map_right, bottom))
    legend_labels = {
        "Low": "Low (<25)",
        "Medium": "Medium (25-49)",
        "High": "High (50-74)",
        "Very High": "Very High (75+)",
    }
    for feature in boundaries.get("features", []):
        district = str(feature.get("properties", {}).get("DISTRICT", "")).strip()
        row = area_by_district.get(district)
        burden_class = row["service_burden_class"] if row is not None else ""
        fill = BURDEN_COLORS.get(burden_class, (224, 226, 222))
        for ring in iter_rings(feature.get("geometry", {})):
            pts = [project(lon, lat) for lon, lat in ring]
            if len(pts) >= 3:
                draw.polygon(pts, fill=fill, outline=(255, 255, 255))
                outline = (75, 82, 82)
                width = 4 if burden_class == "Very High" else 2
                draw.line(pts + [pts[0]], fill=outline, width=width)
    draw_context_lines(draw, project, (left, top, map_right, bottom))
    draw_reference_labels(draw, project, (left, top, map_right, bottom))
    draw_district_labels(draw, boundaries, project, size=19)
    if show_side_info:
        legend_x = right - 280
        for i, (label, fill) in enumerate(BURDEN_COLORS.items()):
            y = top + 24 + i * 34
            draw.rectangle((legend_x, y, legend_x + 22, y + 22), fill=fill)
            draw.text((legend_x + 34, y - 1), legend_labels[label], fill=CANVAS["ink"], font=font(18))
        draw.text((legend_x, top + 180), "Top Drivers", fill=CANVAS["ink"], font=font(22, True))
        if driver_path.exists():
            drivers = pd.read_csv(driver_path).head(5)
            y = top + 214
            for _, row in drivers.iterrows():
                district = row["council_district"]
                score = row["service_burden_score"]
                district_metrics = area_by_district[str(district)]
                resident_rate = district_metrics.get("requests_per_10k_residents")
                density = district_metrics.get("requests_per_sq_mile")
                unresolved = district_metrics.get("unresolved_share", 0) * 100
                repeat = district_metrics.get("repeat_cluster_share", 0) * 100
                top_cat = str(row["top_category"]).replace("Solid Waste / Recycling", "Solid Waste").replace("Traffic Signals / Lighting", "Signals").replace("Road / Pothole / Bridge", "Roads").replace(" / ", "/")
                line1 = f"{district}: {score:.1f} score"
                if pd.notna(resident_rate):
                    line2 = f"{resident_rate:,.0f}/10k res; {unresolved:.0f}% open"
                else:
                    line2 = f"{density:,.0f}/sq mi; {unresolved:.0f}% open"
                line3 = f"{repeat:.0f}% repeat; {top_cat[:16]}"
                draw.text((legend_x, y), line1, fill=CANVAS["ink"], font=font(18, True))
                draw.text((legend_x, y + 24), line2, fill=CANVAS["muted"], font=font(15))
                draw.text((legend_x, y + 44), line3, fill=CANVAS["muted"], font=font(15))
                y += 78
    draw_north_arrow(draw, left + 34, bottom - 96)
    if show_header:
        draw.text(
            (left, bottom + 22),
            "Sources: City of Houston 311 Archive; COHGIS council districts; 2024 ACS if accessible. Analytical score, not an official City metric.",
            fill=CANVAS["muted"],
            font=font(15),
        )
    img.save(path)


def draw_district_metric_choropleth(
    value_field: str,
    title: str,
    path: Path,
    unit_label: str,
    percent: bool = False,
) -> None:
    table_path = TABLES / "council_district_service_burden.csv"
    if not table_path.exists():
        return
    data = pd.read_csv(table_path)
    boundaries = load_boundaries()
    img, draw = canvas(title, f"{unit_label} by council district; April-June 2025")
    left, top, right, bottom = 100, 140, CANVAS["width"] - 90, CANVAS["height"] - 90
    draw.rectangle((left, top, right, bottom), outline=(185, 191, 191), width=2, fill=(241, 243, 240))
    if not boundaries or value_field not in data.columns:
        draw.text((left + 40, top + 40), "No boundary or metric data available.", fill=CANVAS["ink"], font=font(24, True))
        img.save(path)
        return
    extent = boundary_extent(boundaries, pd.DataFrame({"longitude": [-95.8], "latitude": [29.8]}))
    project = make_projector(extent, (left, top, right - 310, bottom))
    values = data[value_field].fillna(0)
    q1, q2, q3 = values.quantile([0.25, 0.5, 0.75])
    ramp = [(226, 232, 221), (182, 204, 181), (220, 173, 96), (147, 64, 79)]

    def color_for(value: float):
        if value <= q1:
            return ramp[0]
        if value <= q2:
            return ramp[1]
        if value <= q3:
            return ramp[2]
        return ramp[3]

    by_district = {str(row["council_district"]): row for _, row in data.iterrows()}
    for feature in boundaries.get("features", []):
        district = str(feature.get("properties", {}).get("DISTRICT", "")).strip()
        row = by_district.get(district)
        value = float(row[value_field]) if row is not None and pd.notna(row[value_field]) else 0
        for ring in iter_rings(feature.get("geometry", {})):
            pts = [project(lon, lat) for lon, lat in ring]
            if len(pts) >= 3:
                draw.polygon(pts, fill=color_for(value), outline=(255, 255, 255))
                draw.line(pts + [pts[0]], fill=(75, 82, 82), width=2)
    draw_context_lines(draw, project, (left, top, right - 310, bottom))
    draw_district_labels(draw, boundaries, project, size=17)

    def fmt(value: float) -> str:
        if percent:
            return f"{value * 100:.1f}%"
        return f"{value:,.1f}"

    legend_x = right - 275
    draw.text((legend_x, top + 24), "Quartiles", fill=CANVAS["ink"], font=font(21, True))
    labels = [f"<= {fmt(q1)}", f"{fmt(q1)}-{fmt(q2)}", f"{fmt(q2)}-{fmt(q3)}", f"> {fmt(q3)}"]
    for i, (fill, label) in enumerate(zip(ramp, labels)):
        y = top + 64 + i * 34
        draw.rectangle((legend_x, y, legend_x + 22, y + 22), fill=fill)
        draw.text((legend_x + 34, y - 1), label, fill=CANVAS["ink"], font=font(18))
    top_rows = data.sort_values(value_field, ascending=False).head(5)
    draw.text((legend_x, top + 230), "Highest Values", fill=CANVAS["ink"], font=font(21, True))
    y = top + 268
    for _, row in top_rows.iterrows():
        draw.text((legend_x, y), f"{row['council_district']}: {fmt(row[value_field])}", fill=CANVAS["ink"], font=font(17, True))
        y += 32
    draw.text(
        (left, bottom + 22),
        "Component map for score interpretation; analytical screening output, not an official City metric.",
        fill=CANVAS["muted"],
        font=font(15),
    )
    img.save(path)


def draw_alternate_score_choropleth(
    table_name: str,
    score_field: str,
    title: str,
    path: Path,
    class_field: str | None = None,
) -> None:
    table_path = TABLES / table_name
    if not table_path.exists():
        return
    data = pd.read_csv(table_path)
    boundaries = load_boundaries()
    img, draw = canvas(title, "Council district screening comparison; April-June 2025")
    left, top, right, bottom = 100, 140, CANVAS["width"] - 90, CANVAS["height"] - 90
    draw.rectangle((left, top, right, bottom), outline=(185, 191, 191), width=2, fill=(241, 243, 240))
    if not boundaries or score_field not in data.columns:
        draw.text((left + 40, top + 40), "No boundary or score data available.", fill=CANVAS["ink"], font=font(24, True))
        img.save(path)
        return
    extent = boundary_extent(boundaries, pd.DataFrame({"longitude": [-95.8], "latitude": [29.8]}))
    project = make_projector(extent, (left, top, right - 300, bottom))
    by_district = {str(row["council_district"]): row for _, row in data.iterrows()}
    for feature in boundaries.get("features", []):
        district = str(feature.get("properties", {}).get("DISTRICT", "")).strip()
        row = by_district.get(district)
        score = float(row[score_field]) if row is not None and pd.notna(row[score_field]) else 0
        klass = str(row[class_field]) if row is not None and class_field and class_field in row else score_class(score)
        fill = BURDEN_COLORS.get(klass, (224, 226, 222))
        for ring in iter_rings(feature.get("geometry", {})):
            pts = [project(lon, lat) for lon, lat in ring]
            if len(pts) >= 3:
                draw.polygon(pts, fill=fill, outline=(255, 255, 255))
                draw.line(pts + [pts[0]], fill=(75, 82, 82), width=3 if klass == "Very High" else 2)
    draw_context_lines(draw, project, (left, top, right - 300, bottom))
    draw_district_labels(draw, boundaries, project, size=17)

    legend_x = right - 265
    draw.text((legend_x, top + 24), "Score Classes", fill=CANVAS["ink"], font=font(21, True))
    for i, (label, fill) in enumerate(BURDEN_COLORS.items()):
        y = top + 64 + i * 34
        draw.rectangle((legend_x, y, legend_x + 22, y + 22), fill=fill)
        draw.text((legend_x + 34, y - 1), label, fill=CANVAS["ink"], font=font(18))
    top_rows = data.sort_values(score_field, ascending=False).head(5)
    draw.text((legend_x, top + 230), "Top Ranked", fill=CANVAS["ink"], font=font(21, True))
    y = top + 268
    for _, row in top_rows.iterrows():
        draw.text((legend_x, y), f"{row['council_district']}: {row[score_field]:.0f}", fill=CANVAS["ink"], font=font(17, True))
        y += 32
    draw.text((left, bottom + 22), "Sensitivity map; reported-request screening output, not an official City metric.", fill=CANVAS["muted"], font=font(15))
    img.save(path)


def draw_assignment_qa_map(path: Path) -> None:
    table_path = TABLES / "district_data_quality.csv"
    if not table_path.exists():
        return
    data = pd.read_csv(table_path)
    boundaries = load_boundaries()
    img, draw = canvas("Council District Assignment QA", "Spatial assignment share by source council district; April-June 2025")
    left, top, right, bottom = 100, 140, CANVAS["width"] - 90, CANVAS["height"] - 90
    draw.rectangle((left, top, right, bottom), outline=(185, 191, 191), width=2, fill=(241, 243, 240))
    if not boundaries:
        draw.text((left + 40, top + 40), "No boundary data available.", fill=CANVAS["ink"], font=font(24, True))
        img.save(path)
        return
    extent = boundary_extent(boundaries, pd.DataFrame({"longitude": [-95.8], "latitude": [29.8]}))
    project = make_projector(extent, (left, top, right - 300, bottom))
    by_district = {str(row["council_district"]): row for _, row in data.iterrows()}

    def fill_for(value: float) -> tuple[int, int, int]:
        if value < 0.5:
            return (148, 49, 73)
        if value < 0.9:
            return (210, 121, 84)
        if value < 0.98:
            return (220, 185, 101)
        return (137, 171, 112)

    for feature in boundaries.get("features", []):
        district = str(feature.get("properties", {}).get("DISTRICT", "")).strip()
        row = by_district.get(district)
        value = float(row["spatial_assignment_share"]) if row is not None and pd.notna(row["spatial_assignment_share"]) else 0
        for ring in iter_rings(feature.get("geometry", {})):
            pts = [project(lon, lat) for lon, lat in ring]
            if len(pts) >= 3:
                draw.polygon(pts, fill=fill_for(value), outline=(255, 255, 255))
                draw.line(pts + [pts[0]], fill=(75, 82, 82), width=2)
    draw_context_lines(draw, project, (left, top, right - 300, bottom))
    draw_district_labels(draw, boundaries, project, size=17)
    legend_x = right - 265
    draw.text((legend_x, top + 24), "Assignment Share", fill=CANVAS["ink"], font=font(21, True))
    legend = [
        ("<50%", (148, 49, 73)),
        ("50-89%", (210, 121, 84)),
        ("90-97%", (220, 185, 101)),
        ("98%+", (137, 171, 112)),
    ]
    for i, (label, fill) in enumerate(legend):
        y = top + 64 + i * 34
        draw.rectangle((legend_x, y, legend_x + 22, y + 22), fill=fill)
        draw.text((legend_x + 34, y - 1), label, fill=CANVAS["ink"], font=font(18))
    draw.text((legend_x, top + 230), "Review Flag", fill=CANVAS["ink"], font=font(21, True))
    flagged = data[data["spatial_assignment_share"] < 0.9].sort_values("spatial_assignment_share")
    y = top + 268
    for _, row in flagged.iterrows():
        draw.text((legend_x, y), f"{row['council_district']}: {row['spatial_assignment_share'] * 100:.1f}%", fill=CANVAS["ink"], font=font(17, True))
        y += 32
    draw.text((left, bottom + 22), "QA map identifies district assignment risks; it is not part of the screening score.", fill=CANVAS["muted"], font=font(15))
    img.save(path)


def draw_repeat_cluster_map(df: pd.DataFrame, path: Path) -> None:
    clusters_path = TABLES / "repeat_location_clusters.csv"
    img, draw = canvas("Repeat-Location Infrastructure Clusters", "Approximate 100-meter coordinate bins with 3+ same-category requests")
    left, top, right, bottom = 100, 140, CANVAS["width"] - 90, CANVAS["height"] - 90
    draw.rectangle((left, top, right, bottom), outline=(185, 191, 191), width=2, fill=(241, 243, 240))
    boundaries = load_boundaries()
    geo = valid_geo(df)
    if not clusters_path.exists() or geo.empty:
        draw.text((left + 40, top + 40), "No repeat clusters available.", fill=CANVAS["ink"], font=font(24, True))
        img.save(path)
        return
    clusters = pd.read_csv(clusters_path).dropna(subset=["lat_bin_approx_100m", "lon_bin_approx_100m"])
    extent = boundary_extent(boundaries, geo)
    project = make_projector(extent, (left, top, right, bottom))
    draw_boundary_backdrop(draw, boundaries, project, fill=(235, 238, 235), outline=(198, 203, 201), width=1)
    draw_context_lines(draw, project, (left, top, right, bottom))
    for _, row in clusters.head(350).iterrows():
        x, y = project(row["lon_bin_approx_100m"], row["lat_bin_approx_100m"])
        radius = min(22, 3 + math.sqrt(row["cluster_request_count"]) * 2.5)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(160, 69, 88), outline=(255, 255, 255), width=1)
    draw.text((left, bottom + 22), f"Top {min(len(clusters), 350):,} repeat clusters drawn from {len(clusters):,} detected clusters.", fill=CANVAS["muted"], font=font(18))
    img.save(path)


def draw_thematic_choropleth(theme: str, title: str, path: Path) -> None:
    table_path = TABLES / "thematic_district_burden.csv"
    if not table_path.exists():
        return
    data = pd.read_csv(table_path)
    data = data[data["theme"] == theme].copy()
    if data.empty:
        return
    boundaries = load_boundaries()
    value_field = (
        "requests_per_10k_residents"
        if data["requests_per_10k_residents"].notna().any()
        else "requests_per_sq_mile"
    )
    unit_label = "requests per 10,000 residents" if value_field == "requests_per_10k_residents" else "requests per square mile"
    img, draw = canvas(title, f"{unit_label.title()} by council district; April-June 2025")
    left, top, right, bottom = 100, 140, CANVAS["width"] - 90, CANVAS["height"] - 90
    draw.rectangle((left, top, right, bottom), outline=(185, 191, 191), width=2, fill=(241, 243, 240))
    if not boundaries:
        draw.text((left + 40, top + 40), "No boundary data available.", fill=CANVAS["ink"], font=font(24, True))
        img.save(path)
        return
    extent = boundary_extent(boundaries, pd.DataFrame({"longitude": [-95.8], "latitude": [29.8]}))
    project = make_projector(extent, (left, top, right - 300, bottom))
    values = data[value_field].fillna(0)
    q1, q2, q3 = values.quantile([0.25, 0.5, 0.75])
    ramp = [(220, 229, 213), (183, 203, 164), (213, 151, 105), (148, 49, 73)]

    def color_for(value: float):
        if value <= q1:
            return ramp[0]
        if value <= q2:
            return ramp[1]
        if value <= q3:
            return ramp[2]
        return ramp[3]

    by_district = {str(row["council_district"]): row for _, row in data.iterrows()}
    for feature in boundaries.get("features", []):
        district = str(feature.get("properties", {}).get("DISTRICT", "")).strip()
        row = by_district.get(district)
        value = float(row[value_field]) if row is not None else 0
        for ring in iter_rings(feature.get("geometry", {})):
            pts = [project(lon, lat) for lon, lat in ring]
            if len(pts) >= 3:
                draw.polygon(pts, fill=color_for(value), outline=(255, 255, 255))
                draw.line(pts + [pts[0]], fill=(75, 82, 82), width=2)
    draw_context_lines(draw, project, (left, top, right - 300, bottom))
    draw_district_labels(draw, boundaries, project, size=17)

    legend_x = right - 265
    draw.text((legend_x, top + 24), "Rate Quartiles", fill=CANVAS["ink"], font=font(21, True))
    labels = [
        f"<= {q1:,.0f}",
        f"{q1:,.0f}-{q2:,.0f}",
        f"{q2:,.0f}-{q3:,.0f}",
        f"> {q3:,.0f}",
    ]
    for i, (fill, label) in enumerate(zip(ramp, labels)):
        y = top + 64 + i * 34
        draw.rectangle((legend_x, y, legend_x + 22, y + 22), fill=fill)
        draw.text((legend_x + 34, y - 1), label, fill=CANVAS["ink"], font=font(18))
    top_rows = data.sort_values(value_field, ascending=False).head(4)
    draw.text((legend_x, top + 230), "Highest Rates", fill=CANVAS["ink"], font=font(21, True))
    y = top + 268
    for _, row in top_rows.iterrows():
        draw.text(
            (legend_x, y),
            f"{row['council_district']}: {row[value_field]:,.0f}" + ("/10k" if value_field == "requests_per_10k_residents" else "/sq mi"),
            fill=CANVAS["ink"],
            font=font(17, True),
        )
        y += 32
    img.save(path)


def main() -> None:
    ensure_directories()
    if not CLEAN_FILE.exists():
        raise SystemExit(f"Missing cleaned data: {CLEAN_FILE}")
    df = pd.read_csv(CLEAN_FILE)

    category = pd.read_csv(TABLES / "top_infrastructure_request_categories.csv")
    cat_rollup = category.groupby("standardized_category", as_index=False)["request_count"].sum().sort_values("request_count", ascending=False)
    save_bar_chart(cat_rollup, "standardized_category", "request_count", "Infrastructure Requests by Category", FIGURES / "request_count_by_category.png")

    median = pd.read_csv(TABLES / "median_resolution_time_by_category.csv")
    save_bar_chart(median.sort_values("median_resolution_days", ascending=False), "standardized_category", "median_resolution_days", "Median Resolution Time by Category", FIGURES / "median_resolution_time_by_category.png", suffix=" days")

    open_summary = pd.read_csv(TABLES / "unresolved_open_requests_by_category.csv")
    save_share_chart(open_summary, "Open / Unresolved Share by Category", FIGURES / "open_unresolved_share_by_category.png")
    save_month_chart(df, FIGURES / "monthly_request_volume.png")

    draw_map(df, "Overall Infrastructure Request Point Distribution", MAPS / "overall_infrastructure_request_points.png", PALETTE[0])
    draw_map(df[df["standardized_category"].isin(["Drainage / Flooding", "Water", "Sewer / Wastewater"])], "Drainage, Water, and Sewer Requests", MAPS / "drainage_water_sewer_requests.png", PALETTE[1])
    draw_map(df[df["standardized_category"].isin(["Road / Pothole / Bridge", "Sidewalk / Bike Lane", "Traffic Signals / Lighting"])], "Road, Sidewalk, Signal, and Lighting Requests", MAPS / "road_sidewalk_signal_requests.png", PALETTE[2])
    draw_map(df[(df["is_open"].astype(str).str.lower() == "true") | (df["is_long_resolution"].astype(str).str.lower() == "true")], "Open or Long-Resolution Requests", MAPS / "open_or_long_resolution_requests.png", PALETTE[3])
    draw_burden_map(df, MAPS / "council_district_service_burden_choropleth.png")
    draw_burden_map(df, MAPS / "council_district_service_burden_map_body.png", show_header=False, show_side_info=False)
    draw_district_metric_choropleth(
        "requests_per_sq_mile",
        "Infrastructure Request Density",
        MAPS / "request_density_component.png",
        "Requests per square mile",
    )
    draw_district_metric_choropleth(
        "unresolved_share",
        "Unresolved Request Share",
        MAPS / "unresolved_share_component.png",
        "Share of requests open/unresolved",
        percent=True,
    )
    draw_district_metric_choropleth(
        "long_resolution_share",
        "Long-Resolution Request Share",
        MAPS / "long_resolution_share_component.png",
        "Share of requests over threshold",
        percent=True,
    )
    draw_district_metric_choropleth(
        "repeat_cluster_share",
        "Repeat-Cluster Request Share",
        MAPS / "repeat_cluster_share_component.png",
        "Share of requests in repeat-location clusters",
        percent=True,
    )
    draw_alternate_score_choropleth(
        "council_district_non_solid_waste_screening.csv",
        "screening_score",
        "Non-Solid-Waste Screening Score",
        MAPS / "non_solid_waste_screening_score.png",
        class_field="screening_class",
    )
    draw_alternate_score_choropleth(
        "category_balanced_district_density.csv",
        "category_balanced_density_score",
        "Category-Balanced Request Density",
        MAPS / "category_balanced_density_score.png",
        class_field="category_balanced_class",
    )
    draw_assignment_qa_map(MAPS / "district_assignment_qa_flags.png")
    draw_repeat_cluster_map(df, MAPS / "repeat_location_clusters.png")
    draw_thematic_choropleth(
        "solid_waste_recycling",
        "Solid Waste and Recycling Request Rate",
        MAPS / "solid_waste_recycling_burden.png",
    )
    draw_thematic_choropleth(
        "water_sewer_drainage",
        "Water, Sewer, and Drainage Request Rate",
        MAPS / "water_sewer_drainage_burden.png",
    )
    draw_thematic_choropleth(
        "roads_signals_sidewalks",
        "Road, Signal, and Sidewalk Request Rate",
        MAPS / "roads_signals_sidewalks_burden.png",
    )
    print("Wrote static figures and maps.")


if __name__ == "__main__":
    main()
