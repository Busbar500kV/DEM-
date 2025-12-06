import rasterio
import numpy as np
import matplotlib.pyplot as plt

DEM_UTM = "data/dem/srilanka_dem_utm.tif"
ELEV_THRESHOLD_M = 1524.0  # 5000 ft

with rasterio.open(DEM_UTM) as src:
    dem = src.read(1)
    bounds = src.bounds

    # mask where DEM is >= 5000 ft and positive (avoid ocean 0 m noise)
    high = (dem >= ELEV_THRESHOLD_M) & (dem > 0)

    # Build extent in map coordinates (UTM metres)
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

plt.figure(figsize=(8, 10))
plt.imshow(high, origin="upper", extent=extent, cmap="Greens")

plt.title("Sri Lanka – Area Above 5000 ft (1524 m)")
plt.xlabel("Easting (m, UTM Zone 44N)")
plt.ylabel("Northing (m, UTM Zone 44N)")

# simple outline: semi-transparent background for context
plt.imshow(np.where(high, np.nan, 0), origin="upper", extent=extent,
           alpha=0.1, cmap="Greys")

plt.tight_layout()
plt.savefig("figs/above_5000ft_2d.png", dpi=300)
plt.close()

print("Saved 2D map to figs/above_5000ft_2d.png")
