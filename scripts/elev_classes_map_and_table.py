#!/usr/bin/env python3
"""
Make a 2D elevation-class map of Sri Lanka and compute area statistics.

Classes (using DEM in metres, UTM Zone 44N):

0.  elevation <= 0 m                        -> blue
1.  0 m < elevation <= 3000 ft  (914.4 m)   -> green
2.  3000–4000 ft (914.4–1219.2 m)           -> yellow
3.  4000–5000 ft (1219.2–1524.0 m)          -> orange
4.  5000–6000 ft (1524.0–1828.8 m)          -> light red
5.  elevation > 6000 ft  (>1828.8 m)        -> dark red

It also prints & saves a markdown table with the land area
(and % of land) above 3000, 4000, 5000 and 6000 ft.

Assumes that:
    data/dem/srilanka_dem_utm44n.tif
already exists (created from your Copernicus DEM).
"""

from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DEM_UTM_PATH = Path("data/dem/srilanka_dem_utm44n.tif")
OUT_FIG = Path("figs/srilanka_elev_6classes_towns.png")
OUT_TABLE = Path("results/area_above_3000_4000_5000_6000ft.md")


# ---------------------------------------------------------------------------
# Towns / villages: lat, lon, approx elevation (for documentation)
# Coordinates are WGS84 decimal degrees from topo / coordinate sources.
# Elevations are from topo / elevation references (Wikipedia, topographic maps).
# ---------------------------------------------------------------------------

HIGHLAND_TOWNS = [
    # Central highlands core
    {"name": "Nuwara Eliya", "lat": 6.97078, "lon": 80.78286, "elev_m": 1868},
    {"name": "Ambewela",     "lat": 6.87866, "lon": 80.81382, "elev_m": 1837},
    {"name": "Pattipola",    "lat": 6.85850, "lon": 80.83086, "elev_m": 1892},
    {"name": "Ohiya",        "lat": 6.81901, "lon": 80.84470, "elev_m": 1774},

    # Uva highlands
    {"name": "Haputale",     "lat": 6.76566, "lon": 80.95104, "elev_m": 1431},
    {"name": "Bandarawela",  "lat": 6.82451, "lon": 80.98587, "elev_m": 1226},
    {"name": "Diyatalawa",   "lat": 6.81100, "lon": 80.95500, "elev_m": 1281},
    {"name": "Ella",         "lat": 6.87560, "lon": 81.04630, "elev_m": 1041},

    # Knuckles / eastern highlands
    {"name": "Meemure",      "lat": 7.43333, "lon": 80.83333, "elev_m": 936},

    # Hill-country cities
    {"name": "Hatton",       "lat": 6.88730, "lon": 80.59856, "elev_m": 1271},
    {"name": "Kandy",        "lat": 7.29057, "lon": 80.63373, "elev_m": 514},
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def load_dem(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"DEM not found: {path}")
    src = rasterio.open(path)
    dem = src.read(1, masked=True)  # masked array (nodata -> mask)
    transform = src.transform
    bounds = src.bounds
    return src, dem, transform, bounds


def compute_area_stats(dem, transform):
    """
    dem: masked array (metres), in UTM 44N.
    Returns:
      total_land_km2, stats list[(ft, m, area_km2, pct)]
    """
    # Pixel area in m² (north-up assumption holds for UTM warp)
    pixel_area_m2 = abs(transform.a * transform.e)

    # Strict land mask: elevation > 0m and valid (not nodata)
    landmask = (~dem.mask) & (dem > 0)

    total_land_km2 = landmask.sum() * pixel_area_m2 / 1e6

    ft_to_m = 0.3048
    thresholds_ft = [3000, 4000, 5000, 6000]
    thresholds_m = {ft: ft * ft_to_m for ft in thresholds_ft}

    stats = []
    for ft in thresholds_ft:
        th_m = thresholds_m[ft]
        mask = landmask & (dem >= th_m)
        area_km2 = mask.sum() * pixel_area_m2 / 1e6
        pct = (area_km2 / total_land_km2 * 100.0) if total_land_km2 > 0 else np.nan
        stats.append((ft, th_m, area_km2, pct))

    return total_land_km2, stats


def save_markdown_table(total_land_km2, stats, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("### Land area above elevation thresholds\n")
    lines.append(f"Total land area from DEM (> 0 m): **{total_land_km2:,.2f} km²**\n")
    lines.append("| Threshold (ft) | Threshold (m) | Area ≥ threshold (km²) | % of land |")
    lines.append("|--------------:|-------------:|------------------------:|----------:|")
    for ft, th_m, area_km2, pct in stats:
        lines.append(
            f"| {ft:>6} | {th_m:>11.1f} | {area_km2:>22.2f} | {pct:>9.3f} |"
        )
    text = "\n".join(lines) + "\n"

    print("\n" + text)  # to terminal
    with out_path.open("w", encoding="utf-8") as f:
        f.write(text)
    print(f"Markdown table written to: {out_path}")


def make_class_map(dem):
    """
    Build a 2D array of integer classes 0..5 using the ranges specified.
    Returns: classes (int8 array), thresholds_m dict
    """
    ft_to_m = 0.3048
    thresholds_m = {
        3000: 3000 * ft_to_m,
        4000: 4000 * ft_to_m,
        5000: 5000 * ft_to_m,
        6000: 6000 * ft_to_m,
    }

    classes = np.full(dem.shape, -1, dtype=np.int8)
    valid = ~dem.mask

    sea = valid & (dem <= 0)
    c1 = valid & (dem > 0) & (dem <= thresholds_m[3000])
    c2 = valid & (dem > thresholds_m[3000]) & (dem <= thresholds_m[4000])
    c3 = valid & (dem > thresholds_m[4000]) & (dem <= thresholds_m[5000])
    c4 = valid & (dem > thresholds_m[5000]) & (dem <= thresholds_m[6000])
    c5 = valid & (dem > thresholds_m[6000])

    classes[sea] = 0
    classes[c1] = 1
    classes[c2] = 2
    classes[c3] = 3
    classes[c4] = 4
    classes[c5] = 5

    return classes, thresholds_m


def plot_map(src, classes, bounds, towns, out_fig: Path):
    out_fig.parent.mkdir(parents=True, exist_ok=True)

    cmap = ListedColormap([
        "#0000ff",  # 0: sea / <= 0 m (blue)
        "#00aa00",  # 1: 0–3000 ft (green)
        "#ffff00",  # 2: 3000–4000 ft (yellow)
        "#ffcc00",  # 3: 4000–5000 ft (orange)
        "#ff9999",  # 4: 5000–6000 ft (light red)
        "#990000",  # 5: > 6000 ft (dark red)
    ])
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5], cmap.N)

    fig, ax = plt.subplots(figsize=(8, 11))

    im = ax.imshow(
        classes,
        cmap=cmap,
        norm=norm,
        extent=(bounds.left, bounds.right, bounds.bottom, bounds.top),
        origin="upper",
    )

    ax.set_xlabel("Easting (m, UTM Zone 44N)")
    ax.set_ylabel("Northing (m, UTM Zone 44N)")
    ax.set_title(
        "Sri Lanka – Elevation Classes\n"
        "Blue ≤0 m; Green 0–3000 ft; Yellow 3000–4000 ft; "
        "Orange 4000–5000 ft; Light red 5000–6000 ft; Dark red >6000 ft",
        fontsize=10,
    )

    cbar = fig.colorbar(
        im, ax=ax, fraction=0.046, pad=0.04, ticks=[0, 1, 2, 3, 4, 5]
    )
    cbar.ax.set_yticklabels(
        ["≤0 m", "0–3000 ft", "3000–4000 ft",
         "4000–5000 ft", "5000–6000 ft", ">6000 ft"]
    )

    # Overlay towns (transform to UTM 44N)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)
    for t in towns:
        e, n = transformer.transform(t["lon"], t["lat"])
        ax.scatter(
            e, n,
            s=20,
            edgecolor="black",
            facecolor="white",
            linewidth=0.5,
            zorder=3,
        )
        ax.text(
            e + 1000, n + 1000,
            t["name"],
            fontsize=6,
            ha="left",
            va="bottom",
            bbox=dict(
                boxstyle="round,pad=0.2",
                facecolor="white",
                alpha=0.7,
                edgecolor="none",
            ),
            zorder=4,
        )

    fig.tight_layout()
    fig.savefig(out_fig, dpi=300)
    plt.close(fig)
    print(f"Map saved to: {out_fig}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    src, dem, transform, bounds = load_dem(DEM_UTM_PATH)

    # Area statistics and markdown table
    total_land_km2, stats = compute_area_stats(dem, transform)
    save_markdown_table(total_land_km2, stats, OUT_TABLE)

    # Class map + 2D figure
    classes, _ = make_class_map(dem)
    plot_map(src, classes, bounds, HIGHLAND_TOWNS, OUT_FIG)

    src.close()


if __name__ == "__main__":
    main()