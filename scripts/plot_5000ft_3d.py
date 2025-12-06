import rasterio
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

DEM_UTM = "data/dem/srilanka_dem_utm.tif"
ELEV_THRESHOLD_M = 1524.0  # 5000 ft

with rasterio.open(DEM_UTM) as src:
    dem = src.read(1)
    transform = src.transform
    height, width = dem.shape

    # Only keep elevations >= 5000 ft and >0
    high = (dem >= ELEV_THRESHOLD_M) & (dem > 0)
    dem_masked = np.where(high, dem, np.nan)

    # Downsample for 3D plotting
    step = 20  # adjust if you want more/less detail
    dem_ds = dem_masked[::step, ::step]

    h_ds, w_ds = dem_ds.shape

    # Build coordinate grids in UTM metres
    xs = np.arange(0, w_ds) * transform.a * step + transform.c
    ys = np.arange(0, h_ds) * transform.e * step + transform.f
    X, Y = np.meshgrid(xs, ys)

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection="3d")

# Note: dem_ds has NaNs where elevation < 5000 ft
surf = ax.plot_surface(X, Y, dem_ds,
                       linewidth=0, antialiased=False)

ax.set_title("Sri Lanka – 3D View of Terrain Above 5000 ft (1524 m)")
ax.set_xlabel("Easting (m, UTM 44N)")
ax.set_ylabel("Northing (m, UTM 44N)")
ax.set_zlabel("Elevation (m)")

# A slightly tilted view
ax.view_init(elev=45, azim=235)

plt.tight_layout()
plt.savefig("figs/above_5000ft_3d.png", dpi=300)
plt.close()

print("Saved 3D map to figs/above_5000ft_3d.png")
