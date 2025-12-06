import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from pyproj import Transformer

DEM_UTM = "data/dem/srilanka_dem_utm.tif"
FIG_OUT = "figs/above_5000ft_with_towns.png"
THRESH_M = 1524.0  # 5000 ft in metres

# Towns/villages near or above 5000 ft
# (lat, lon) in degrees, WGS84
towns = [
    ("Nuwara Eliya", 6.97078, 80.78286),
    ("Pattipola",    6.85570, 80.83070),
    ("Ohiya",        6.81901, 80.84470),
    ("Ambewela",     6.87866, 80.81382),
]

# Load DEM in UTM 44N
with rasterio.open(DEM_UTM) as src:
    dem = src.read(1)
    bounds = src.bounds

# Mask for > 5000 ft and positive elevation (avoid ocean)
high = (dem >= THRESH_M) & (dem > 0)

extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

# Simple 2-color colormap: transparent for non-high, red for high
cmap = ListedColormap(["none", "#e74c3c"])

# Prepare high mask as 0/1
high_int = np.zeros_like(dem, dtype=np.uint8)
high_int[high] = 1

# Transform town coordinates from lon/lat (EPSG:4326) to UTM 44N (EPSG:32644)
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)

lons = [lon for (_, lat, lon) in towns]
lats = [lat for (_, lat, lon) in towns]
xs, ys = transformer.transform(lons, lats)

plt.figure(figsize=(8, 10))

# Draw high-elevation mask
plt.imshow(high_int, origin="upper", extent=extent, cmap=cmap)

# Plot town locations
plt.scatter(xs, ys, marker="o", s=40, facecolor="white", edgecolor="black", zorder=3)

# Labels slightly offset
for (name, lat, lon), x, y in zip(towns, xs, ys):
    plt.text(
        x + 2000, y + 2000,  # offset in metres
        name,
        fontsize=8,
        color="black",
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none", pad=1.5),
        zorder=4,
    )

plt.title("Sri Lanka – Terrain Above 5000 ft (1524 m)\nwith Selected Highland Towns and Villages")
plt.xlabel("Easting (m, UTM Zone 44N)")
plt.ylabel("Northing (m, UTM Zone 44N)")

plt.tight_layout()
plt.savefig(FIG_OUT, dpi=300)
plt.close()

print(f"Saved map with towns to {FIG_OUT}")
