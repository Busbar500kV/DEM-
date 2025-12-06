import rasterio
import numpy as np
import matplotlib.pyplot as plt
from pyproj import Transformer

DEM_UTM = "data/dem/srilanka_dem_utm.tif"
FIG_OUT = "figs/above_5000ft_with_towns_zoomed.png"
THRESH_M = 1524.0  # 5000 ft in metres

# Extended list of highland towns / villages (lat, lon)
towns = [
    ("Nuwara Eliya",  6.97078, 80.78286),
    ("Kandapola",     6.99170, 80.81940),
    ("Ragala",        7.01117, 80.85561),
    ("Ambewela",      6.87872, 80.81356),
    ("Pattipola",     6.85850, 80.83086),
    ("Ohiya",         6.81901, 80.84470),
    ("Idalgashinna",  6.78330, 80.90000),
    ("Haputale",      6.76566, 80.95100),
    ("Diyatalawa",    6.80964, 80.95746),
    ("Meemure",       7.43265, 80.84608),
]

with rasterio.open(DEM_UTM) as src:
    dem = src.read(1)
    transform = src.transform

# High-elevation mask
high = (dem >= THRESH_M) & (dem > 0)

# Auto-zoom to area with high-elevation pixels
rows, cols = np.where(high)
rmin, rmax = rows.min(), rows.max()
cmin, cmax = cols.min(), cols.max()

pad = 50
rmin = max(0, rmin - pad)
rmax = min(dem.shape[0], rmax + pad)
cmin = max(0, cmin - pad)
cmax = min(dem.shape[1], cmax + pad)

high_zoom = high[rmin:rmax, cmin:cmax]

# Convert pixel bounds to UTM coordinates
x_min, y_max = rasterio.transform.xy(transform, rmin, cmin)
x_max, y_min = rasterio.transform.xy(transform, rmax, cmax)
extent = [x_min, x_max, y_min, y_max]

# Transform town coordinates (lon/lat -> UTM 44N)
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)
lons = [lon for (_, lat, lon) in towns]
lats = [lat for (_, lat, lon) in towns]
xs, ys = transformer.transform(lons, lats)

plt.figure(figsize=(9, 10))
plt.imshow(high_zoom, extent=extent, origin="upper", cmap="Reds")

# Plot towns
plt.scatter(xs, ys, c="white", edgecolor="black", s=40, zorder=3)

# Label towns (small font, light background)
for (name, lat, lon), x, y in zip(towns, xs, ys):
    plt.text(
        x + 1200,
        y + 1200,
        name,
        fontsize=7.5,
        color="black",
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=1.5),
        zorder=4,
    )

plt.title("Sri Lanka – Terrain Above 5000 ft (1524 m)\nZoomed with Highland Towns and Villages")
plt.xlabel("Easting (m, UTM 44N)")
plt.ylabel("Northing (m, UTM 44N)")
plt.tight_layout()
plt.savefig(FIG_OUT, dpi=300)
plt.close()

print(f"Saved zoomed map to {FIG_OUT}")