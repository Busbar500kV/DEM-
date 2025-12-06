import rasterio
import numpy as np
from rasterio.warp import calculate_default_transform, reproject, Resampling

ELEV_THRESHOLD_M = 1524.0  # 5000 ft in metres
SRC_DEM = "data/dem/srilanka_dem.tif"
DEM_UTM = "data/dem/srilanka_dem_utm.tif"

dst_crs = "EPSG:32644"  # UTM zone covering Sri Lanka

print("Reprojecting DEM to UTM 44N...")

with rasterio.open(SRC_DEM) as src:
    transform, width, height = calculate_default_transform(
        src.crs, dst_crs, src.width, src.height, *src.bounds
    )
    kwargs = src.meta.copy()
    kwargs.update({
        "crs": dst_crs,
        "transform": transform,
        "width": width,
        "height": height
    })

    with rasterio.open(DEM_UTM, "w", **kwargs) as dst:
        reproject(
            source=rasterio.band(src, 1),
            destination=rasterio.band(dst, 1),
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=dst_crs,
            resampling=Resampling.bilinear,
        )

print("Computing area above 5000 ft...")

with rasterio.open(DEM_UTM) as src:
    dem = src.read(1)
    nodata = src.nodata

    if nodata is not None:
        valid = dem != nodata
    else:
        valid = np.isfinite(dem)

    high = (dem >= ELEV_THRESHOLD_M) & valid

    px_area_m2 = abs(src.transform.a * src.transform.e)
    area_km2 = high.sum() * px_area_m2 / 1e6

TOTAL_SL_KM2 = 65610.0  # approx land area
percent = area_km2 / TOTAL_SL_KM2 * 100.0

print(f"Area above 5000 ft: {area_km2:.2f} km²")
print(f"Percent of Sri Lanka: {percent:.3f} %")
