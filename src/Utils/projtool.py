from osgeo import gdal, osr
from pyproj import Transformer


def translate_to_geo_tgt():
    crs_geo_out = "epsg:4326"
    crs_utm = "+proj=utm +zone=12 +datum=WGS84 +units=m +no_defs"

    filename = "/Users/dean/Downloads/raster.tif"
    raster = gdal.Open(filename)
    output_raster = "/Users/dean/Downloads/raster2.tif"
    transform = Transformer.from_crs(crs_utm, crs_geo_out, always_xy=True)
    gdal.Translate(output_raster, raster, outputSRS=crs_geo_out)
    warp = None  # Closes the files


if __name__ == "__main__":
    translate_to_geo_tgt()
    "+proj=utm +zone=12 +datum=WGS84 +units=m +no_defs"
