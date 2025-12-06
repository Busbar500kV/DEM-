import rasterio
import numpy as np
import matplotlib.pyplot as plt
from pyproj import Transformer

DEM_UTM = "data/dem/srilanka_dem_utm.tif"
FIG_OUT = "figs/above_5000ft_with_towns_zoomed.png"
THRESH_M = 1524.0  # 5000 ft in metres

# Towns (lat, lon)
towns = [
    ("Nuwara Eliya", 6.97078, 80.78286),
    ("Pattipola",    6.85570, 80.83070),
    ("Ohiya",        6.81901, 80.84470),
    ("Ambewela",     6.87866, 80.81382),
]

with rasterio.open(DEM_UTM) as src:
    dem = src.read(1)
    transform = src.transform

# High-elevation mask
high = (dem >= THRESH_M) & (dem > 0)

# --- AUTO ZOOM TO RED ZONE ---
rows, cols = np.where(high)
rmin, rmax = rows.min(), rows.max()
cmin, cmax = cols.min(), cols.max()

# Expand bounds slightly for visual margin
pad = 50
rmin = max(0, rmin - pad)
rmax = min(dem.shape[0], rmax + pad)
cmin = max(0, cmin - pad)
cmax = min(dem.shape[1], cmax + pad)

high_zoom = high[rmin:rmax, cmin:cmax]

# Convert pixel bounds to real UTM coordinates
x_min, y_max = rasterio.transform.xy(transform, rmin, cmin)
x_max, y_min = rasterio.transform.xy(transform, rmax, cmax)

extent = [x_min, x_max, y_min, y_max]

# Coordinate transform for towns
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)
lons = [lon for (_, lat, lon) in towns]
lats = [lat for (_, lat, lon) in towns]
xs, ys = transformer.transform(lons, lats)

# Plot
plt.figure(figsize=(9, 10))
plt.imshow(high_zoom, extent=extent, origin="upper", cmap="Reds")

plt.scatter(xs, ys, c="white", edgecolor="black", s=50, zorder=3)

for (name, lat, lon), x, y in zip(towns, xs, ys):
    plt.text(
        x + 1200, y + 1200,
        name,
        fontsize=9,
        color="black",
        bbox=dict(facecolor="white", alpha=0.75, edgecolor="none"),
        zorder=4
    )

plt.title("Sri Lanka – Terrain Above 5000 ft (1524 m)\nZoomed with Highland Towns")
plt.xlabel("Easting (m, UTM 44N)")
plt.ylabel("Northing (m, UTM 44N)")
plt.tight_layout()
plt.savefig(FIG_OUT, dpi=300)
plt.close()

print(f"Saved zoomed map to {FIG_OUT}")