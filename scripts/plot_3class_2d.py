import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

DEM_UTM = "data/dem/srilanka_dem_utm.tif"
FIG_OUT = "figs/srilanka_3class_0_5000ft.png"
THRESH = 1524.0  # 5000 ft in metres

with rasterio.open(DEM_UTM) as src:
    dem = src.read(1)
    bounds = src.bounds

# Classification:
# 0 = <= 0 m (blue)
# 1 = 0–5000 ft (green)
# 2 = > 5000 ft (red)
cls = np.zeros_like(dem, dtype=np.uint8)
cls[(dem > 0) & (dem < THRESH)] = 1
cls[dem >= THRESH] = 2

# Custom colormap: blue, green, red
cmap = ListedColormap(["#1f4fff", "#2ecc71", "#e74c3c"])

extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

plt.figure(figsize=(8, 10))
plt.imshow(cls, origin="upper", extent=extent, cmap=cmap)

plt.title("Sri Lanka Elevation Classes\nBlue ≤ 0 m | Green 0–5000 ft | Red > 5000 ft")
plt.xlabel("Easting (m, UTM Zone 44N)")
plt.ylabel("Northing (m, UTM Zone 44N)")

# Legend (manual)
import matplotlib.patches as mpatches
blue_patch = mpatches.Patch(color="#1f4fff", label="≤ 0 m")
green_patch = mpatches.Patch(color="#2ecc71", label="0–5000 ft (0–1524 m)")
red_patch = mpatches.Patch(color="#e74c3c", label="> 5000 ft (> 1524 m)")
plt.legend(handles=[blue_patch, green_patch, red_patch],
           loc="lower right", framealpha=0.9)

plt.tight_layout()
plt.savefig(FIG_OUT, dpi=300)
plt.close()

print(f"Saved 3-class 2D map to {FIG_OUT}")
