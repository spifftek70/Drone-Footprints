#  Copyright (c) 2024
#  Author: Dean Hand
#  License: AGPL
#  Version: 1.0

import rasterio
from rasterio.windows import Window
from rasterio.transform import from_gcps
from rasterio.control import GroundControlPoint
from rasterio.mask import mask as rio_mask
from rasterio.crs import CRS
import numpy as np
from shapely.geometry import Polygon
import geopandas as gpd


def create_geotiffs(raster_path, temp_output_path, output_geotiff_path, corner_coords):
    """
    Creates geotiffs from a raster image, applying scaling and warping based on specified ground control points.

    Parameters:
    - raster_path: Path to the input raster file.
    - temp_output_path: Path for saving the temporary scaled raster before warping.
    - output_geotiff_path: Path for the final output GeoTIFF file.
    - corner_coords: List of tuples with the corner coordinates for ground control points in the order of [top-left,
        top-right, bottom-right, bottom-left].
    """
    # Open the input raster to read metadata and dimensions
    with rasterio.open(raster_path) as src:
        orig_width, orig_height = src.width, src.height
        meta = src.meta.copy()

        # Scale dimensions for output raster and adjust transform accordingly
        meta["width"], meta["height"] = orig_width * 2, orig_height * 2
        scale_transform = src.transform * src.transform.scale(
            orig_width / meta["width"], orig_height / meta["height"]
        )
        meta.update({"transform": scale_transform, "nodata": src.nodata or 255})

        # Create a temporary scaled raster
        with rasterio.open(temp_output_path, "w", **meta) as dst:
            for band_index in range(1, src.count + 1):
                empty_band = np.full(
                    (meta["height"], meta["width"]), meta["nodata"], dtype=src.dtypes[0]
                )
                dst.write(empty_band, band_index)

            # Center the original image in the scaled raster
            col_offset, row_offset = (meta["width"] - orig_width) // 2, (meta["height"] - orig_height) // 2
            for band_index in range(1, src.count + 1):
                band_data = src.read(band_index)
                dst.write(band_data, band_index, window=Window(col_offset, row_offset, orig_width, orig_height))

    # Warp the scaled image using provided ground control points
    warp_image_with_gcp(temp_output_path, output_geotiff_path, corner_coords)


def warp_image_with_gcp(input_raster_path, output_raster_path, gcp_coords):
    """
    Warps an image using specified ground control points and saves the result as a GeoTIFF.

    Parameters:
    - input_raster_path: Path to the input raster file to be warped.
    - output_raster_path: Path for saving the warped GeoTIFF.
    - gcp_coords: List of tuples with the coordinates for ground control points in the order of [top-left, top-right,
        bottom-right, bottom-left].
    """
    with rasterio.open(input_raster_path, "r+") as src:
        src.crs = CRS.from_epsg(4326)  # Set the coordinate reference system to WGS84
        nodata = src.nodatavals[0]

        # Apply mask based on nodata values to identify data extent
        data = src.read()
        data_mask = np.any(data != nodata, axis=0) if nodata is not None else np.any(data > 0, axis=0)
        rows, cols = np.where(data_mask)
        extent = np.min(rows), np.min(cols), np.max(rows), np.max(cols)

        # Compute spatial coordinates for the extent corners
        minx, maxy = src.transform * (extent[1], extent[0])
        maxx, miny = src.transform * (extent[3] + 1, extent[2] + 1)

        # Create GroundControlPoint objects for each corner using the provided coordinates
        gcps = [GroundControlPoint(col=col, row=row, x=x, y=y) for (col, row), (x, y) in
                zip([(extent[1], extent[0]), (extent[3], extent[0]), (extent[3], extent[2]), (extent[1], extent[2])],
                    gcp_coords)]

        # Apply the GCPs to compute a new transform for the raster
        src.transform = from_gcps(gcps)
        polygon = Polygon(gcp_coords)
        gdf = gpd.GeoDataFrame([{"geometry": polygon}], crs="EPSG:4326")

        # Mask the raster with the polygon and update metadata
        out_image, out_transform = rio_mask(src, [mapping(gdf.geometry.iloc[0])], nodata=255, crop=True)
        out_meta = src.meta.copy()
        out_meta.update(
            {"driver": "GTiff", "height": out_image.shape[1], "width": out_image.shape[2], "transform": out_transform})

        # Save the warped image as a GeoTIFF
        with rasterio.open(output_raster_path, "w", **out_meta) as dst:
            dst.crs = CRS.from_epsg(4326)
            dst.write(out_image)
