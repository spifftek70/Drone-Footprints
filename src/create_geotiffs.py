#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

from osgeo import osr, gdal
import pandas as pd
from coordinate_conversions import convert_wgs_to_utm


def create_geotiffs(image_path, output_file, coord_array):
    """
    Warps an image using the provided list of GCPs to align it with geographic north.
    The output image will be saved to the specified path.
    """

    # Open the input dataset
    gdal.DontUseExceptions()
    ds = gdal.Open(image_path)
    # gt = ds.GetGeoTransform()
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    wkt = srs.ExportToWkt()
    # Open the input dataset

    """
        Warps an image using the provided list of coordinates to align it with geographic north.
        Each coordinate should be a tuple of (longitude, latitude).
        The output image will be saved to the specified path.
        """
    # Create a DataFrame from the coord_array
    df = pd.DataFrame(coord_array, columns=['Longitude', 'Latitude'])
    # For a real application, these should be accurately determined
    df['z'] = 0  # Default elevation
    df['i_pix'] = [0, cols, cols, 0]  # Example pixel X coordinates
    df['j_pix'] = [0, 0, rows, rows]  # Example pixel Y coordinates
    # Create GCPs
    gcps = [gdal.GCP(row['Longitude'], row['Latitude'], row['z'], row['i_pix'], row['j_pix']) for index, row in
            df.iterrows()]

    ds.SetGCPs(gcps, wkt)
    vrt_ds = gdal.Translate(output_file, ds, format='GTiff', GCPs=gcps, outputSRS=wkt)
    # Close the dataset
    ds = None
    vrt_ds = None