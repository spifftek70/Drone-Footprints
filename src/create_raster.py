#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

import rasterio
import geopandas as gpd
from rasterio.windows import Window
from shapely.geometry import Polygon, mapping
import numpy as np
from rasterio.transform import from_gcps
from rasterio.control import GroundControlPoint
from rasterio.mask import mask as rio_mask
from rasterio.crs import CRS


def create_geotiffs(raster_path, temp_output, output_geotiff, coords):
    # Open the input raster
    with rasterio.open(raster_path) as src:
        orig_width, orig_height = src.width, src.height
        meta = src.meta.copy()

        # Double the dimensions for the output raster
        meta["width"] = orig_width * 2
        meta["height"] = orig_height * 2

        # Adjust the transform for the new dimensions
        new_transform = src.transform * src.transform.scale(
            (orig_width / meta["width"]), (orig_height / meta["height"])
        )
        meta["transform"] = new_transform

        # Define a default no-data value if the original raster doesn't have one
        default_nodata = 255  # Example value, adjust based on your data type and range
        nodata_value = src.nodata if src.nodata is not None else default_nodata
        meta["nodata"] = nodata_value  # Update metadata with the no-data value

        with rasterio.open(temp_output, "w", **meta) as dst:
            for i in range(1, src.count + 1):
                # Use the determined no-data value
                empty_band = np.full(
                    (meta["height"], meta["width"]), nodata_value, dtype=src.dtypes[0]
                )
                dst.write(empty_band, i)

            col_offset = (meta["width"] - orig_width) // 2
            row_offset = (meta["height"] - orig_height) // 2

            for i in range(1, src.count + 1):
                data = src.read(i)
                dst.write(
                    data,
                    i,
                    window=Window(col_offset, row_offset, orig_width, orig_height),
                )

    warp_image_with_gcp(temp_output, output_geotiff, coords)


def warp_image_with_gcp(temp_output, output_path, coords):
    with rasterio.open(temp_output, "r+") as src:
        src.crs = CRS.from_epsg(4326)
        nodata = src.nodatavals[0]

        data = src.read()
        if nodata is not None:
            data_mask = np.any(
                data != nodata, axis=0
            )  # Avoid using the name 'mask' for variables
        else:
            data_mask = np.any(data > 0, axis=0)

        rows, cols = np.where(data_mask)
        extent = np.min(rows), np.min(cols), np.max(rows), np.max(cols)

        # Calculate the spatial coordinates for the extent corners
        minx, maxy = src.transform * (extent[1], extent[0])
        maxx, miny = src.transform * (extent[3] + 1, extent[2] + 1)

        # Transform spatial coordinates (CRS) back to pixel coordinates (row, col)
        top_left = src.index(minx, maxy)  # row, col for top-left
        top_right = src.index(maxx, maxy)  # row, col for top-right
        bottom_right = src.index(maxx, miny)  # row, col for bottom-right
        bottom_left = src.index(minx, miny)  # row, col for bottom-left

        # Mapping the coordinates to GCPs
        gcps = [
            GroundControlPoint(
                col=top_left[1], row=top_left[0], x=coords[0][0], y=coords[0][1]
            ),  # top-left
            GroundControlPoint(
                col=top_right[1], row=top_right[0], x=coords[1][0], y=coords[1][1]
            ),  # top-right
            GroundControlPoint(
                col=bottom_right[1], row=bottom_right[0], x=coords[2][0], y=coords[2][1]
            ),  # bottom-right
            GroundControlPoint(
                col=bottom_left[1], row=bottom_left[0], x=coords[3][0], y=coords[3][1]
            ),  # bottom-left
        ]

        transform = from_gcps(gcps)
        src.transform = transform
        polygon = Polygon(coords)
        gdf = gpd.GeoDataFrame(
            [{"geometry": polygon}], crs="EPSG:4326"
        )  # Ensure CRS matches
        nodata_value = 255
        # Use rio_mask instead of mask to avoid conflict
        out_image, out_transform = rio_mask(
            src,
            [gdf.geometry.iloc[0].__geo_interface__],
            nodata=nodata_value,
            crop=True,
        )
        out_meta = src.meta.copy()
        out_meta.update(
            {
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
            }
        )

        with rasterio.open(output_path, "w", **out_meta) as dst:
            dst.crs = CRS.from_epsg(4326)
            dst.write(out_image)
