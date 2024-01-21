from osgeo import gdal  # For read and manipulate rasters
from affine import Affine  # For easly manipulation of affine matrix


# Some functions declaration for clarify the code


def raster_center(raster):
    """This function return the pixel coordinates of the raster center
    """

    # We get the size (in pixels) of the raster
    # using gdal
    width, height = raster.RasterXSize, raster.RasterYSize

    # We calculate the middle of raster
    xmed = width / 2
    ymed = height / 2

    return (xmed, ymed)


def rotate_gt(affine_matrix, angle, pivot=None):
    """This function generate a rotated affine matrix
    """

    # The gdal affine matrix format is not the same
    # of the Affine format, so we use a bullit-in function
    # to change it
    # see : https://github.com/sgillies/affine/blob/master/affine/__init__.py#L178
    affine_src = Affine.from_gdal(*affine_matrix)
    # We made the rotation. For this we calculate a rotation matrix,
    # with the rotation method and we combine it with the original affine matrix
    # Be carful, the star operator (*) is surcharged by Affine package. He make
    # a matrix multiplication, not a basic multiplication
    affine_dst = affine_src * affine_src.rotation(angle, pivot)
    # We retrun the rotated matrix in gdal format
    return affine_dst.to_gdal()


# Import the raster to rotate
# Here I use a sample of GDAL, dowloaded here : https://download.osgeo.org/geotiff/samples/spot/chicago/SP27GTIF.TIF
# and transformed in nc with qgis
# NB: the transformation in nc is specific for the original question,
# this step is not neccecary if you copy/past this code
dataset_src = gdal.Open("/Users/dean/Downloads/LSMap2/images/output/DJI_0726.tif")

# For no overwriting the original raster I make a copy

# I Get the reading/writing driver (GTIFF)
driver = gdal.GetDriverByName("GTiff")
# A new raster, the destination file, is created.
# This raster is a copy of the source raster (same size, values...)
datase_dst = driver.CreateCopy("SP27GTIF_rotate.TIF", dataset_src, strict=0)

# Now we can rotate the raster

# First step, we get the affine tranformation matrix of the initial fine
# More info here : https://gdal.org/tutorials/geotransforms_tut.html#geotransforms-tut
gt_affine = dataset_src.GetGeoTransform()

# Second we get the center of the raster to set the rotation center
# Be carefull, the center is in pixel number, not in projected coordinates
# More info on the  "raster_center" comment's
center = raster_center(dataset_src)

# Third we rotate the destination raster, datase_dst, with setting a new
# affine matrix made by the "rotate_gt" function.
# gt_affine is the initial affine matrix
# -33 is an exemple angle (in degrees)
# and center the center of raster
datase_dst.SetGeoTransform(rotate_gt(gt_affine, -90, center))
