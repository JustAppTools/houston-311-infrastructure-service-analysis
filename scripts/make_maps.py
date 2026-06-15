import math
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from project_config import CANVAS, FIGURES, MAPS, TABLES, ensure_directories


CLEAN_FILE = Path(__file__).resolve().parents[1] / "data" / "processed" / "houston_311_infrastructure_requests_cleaned.csv"


PALETTE = [
    (31, 111, 125),
    (192, 94, 72),
    (92, 137, 76),
    (126, 90, 138),
    (185, 139, 56),
    (73, 100, 150),
    (131, 91, 65),
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
    draw.text((CANVAS["margin"], 38), title, fill=CANVAS["ink"], font=font(34, True))
    if subtitle:
        draw.text((CANVAS["margin"], 82), subtitle, fill=CANVAS["muted"], font=font(20))
    return img, draw


def save_bar_chart(data: pd.DataFrame, label_col: str, value_col: str, title: str, path: Path, suffix: str = "") -> None:
    data = data.head(10).iloc[::-1]
    img, draw = canvas(title, "City of Houston 311 archive extract; V1 infrastructure categories")
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
    img, draw = canvas("Monthly Request Volume", "Shown when the extract spans more than one month")
    left, top, right, bottom = 140, 170, CANVAS["width"] - 110, CANVAS["height"] - 120
    if len(monthly) < 2:
        draw.text((left, top), "The default V1 extract covers one month, so a trend line is not interpreted.", fill=CANVAS["ink"], font=font(24, True))
        draw.text((left, top + 48), f"{monthly.iloc[0]['month']}: {int(monthly.iloc[0]['request_count']):,} infrastructure records", fill=CANVAS["muted"], font=font(23))
        img.save(path)
        return
    max_y = max(monthly["request_count"].max(), 1)
    points = []
    for i, row in monthly.reset_index(drop=True).iterrows():
        x = left + i * (right - left) / (len(monthly) - 1)
        y = bottom - row["request_count"] * (bottom - top) / max_y
        points.append((x, y))
    for grid_i in range(5):
        y = top + grid_i * (bottom - top) / 4
        draw.line((left, y, right, y), fill=CANVAS["grid"], width=1)
    draw.line(points, fill=CANVAS["accent"], width=5)
    for x, y in points:
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=CANVAS["accent2"])
    for i, row in monthly.reset_index(drop=True).iterrows():
        x = points[i][0]
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
    if geo.empty:
        draw.text((left + 40, top + 40), "No valid coordinates in this extract.", fill=CANVAS["ink"], font=font(24, True))
        img.save(path)
        return
    lon_min, lon_max = geo["longitude"].quantile([0.01, 0.99])
    lat_min, lat_max = geo["latitude"].quantile([0.01, 0.99])
    lon_pad = max((lon_max - lon_min) * 0.08, 0.02)
    lat_pad = max((lat_max - lat_min) * 0.08, 0.02)
    lon_min, lon_max = lon_min - lon_pad, lon_max + lon_pad
    lat_min, lat_max = lat_min - lat_pad, lat_max + lat_pad
    sample = geo.sample(n=min(len(geo), 12000), random_state=42)
    for _, row in sample.iterrows():
        x = left + (row["longitude"] - lon_min) / (lon_max - lon_min) * (right - left)
        y = bottom - (row["latitude"] - lat_min) / (lat_max - lat_min) * (bottom - top)
        if left <= x <= right and top <= y <= bottom:
            draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=color)
    draw.text((left, bottom + 22), f"{len(geo):,} valid coordinate records; random sample drawn when over 12,000 points.", fill=CANVAS["muted"], font=font(18))
    img.save(path)


def draw_burden_map(df: pd.DataFrame, path: Path) -> None:
    area_path = TABLES / "council_district_service_burden.csv"
    img, draw = canvas("Council District Service-Burden Screen", "Symbols are district centroids from request coordinates, not official boundaries")
    left, top, right, bottom = 100, 140, CANVAS["width"] - 90, CANVAS["height"] - 90
    draw.rectangle((left, top, right, bottom), outline=(185, 191, 191), width=2, fill=(241, 243, 240))
    geo = valid_geo(df)
    if geo.empty or not area_path.exists():
        draw.text((left + 40, top + 40), "No valid coordinate or council-district data in this extract.", fill=CANVAS["ink"], font=font(24, True))
        img.save(path)
        return
    area = pd.read_csv(area_path)
    centers = geo.groupby("council_district").agg(latitude=("latitude", "median"), longitude=("longitude", "median")).reset_index()
    plot = centers.merge(area, on="council_district", how="inner")
    lon_min, lon_max = geo["longitude"].quantile([0.01, 0.99])
    lat_min, lat_max = geo["latitude"].quantile([0.01, 0.99])
    lon_pad = max((lon_max - lon_min) * 0.08, 0.02)
    lat_pad = max((lat_max - lat_min) * 0.08, 0.02)
    lon_min, lon_max = lon_min - lon_pad, lon_max + lon_pad
    lat_min, lat_max = lat_min - lat_pad, lat_max + lat_pad
    colors = {"Low": (116, 152, 96), "Medium": (207, 169, 82), "High": (204, 112, 77), "Very High": (159, 67, 85)}
    for _, row in plot.iterrows():
        x = left + (row["longitude"] - lon_min) / (lon_max - lon_min) * (right - left)
        y = bottom - (row["latitude"] - lat_min) / (lat_max - lat_min) * (bottom - top)
        radius = 12 + math.sqrt(max(row["request_count"], 1)) * 0.25
        fill = colors.get(row["service_burden_class"], (120, 120, 120))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill, outline=(255, 255, 255), width=2)
        draw.text((x - 6, y - 10), str(row["council_district"]), fill=(255, 255, 255), font=font(18, True))
    legend_x = right - 270
    for i, (label, fill) in enumerate(colors.items()):
        y = top + 24 + i * 34
        draw.rectangle((legend_x, y, legend_x + 22, y + 22), fill=fill)
        draw.text((legend_x + 34, y - 1), label, fill=CANVAS["ink"], font=font(18))
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
    draw_burden_map(df, MAPS / "council_district_service_burden_screen.png")
    print("Wrote static figures and maps.")


if __name__ == "__main__":
    main()
