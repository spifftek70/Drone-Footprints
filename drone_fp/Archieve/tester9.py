import rasterio
from rasterio.transform import Affine
from rasterio.features import geometry_mask
from rasterio.transform import from_bounds
from shapely.geometry import Polygon
import numpy as np
from PIL import Image

# Define the four corners of the Polygon in decimal degrees (lon, lat)
corner1 = -90.2091130886842, 38.615323394756054  # San Francisco, CA
corner2 = -90.20951378243316, 38.61633528615079  # San Francisco, CA
corner3 = -90.20998547370318, 38.61587875406702  # San Francisco, CA
corner4 = -90.20864139594796, 38.61577992328533  # San Francisco, CA

# Create a Polygon geometry from the four corners
polygon = Polygon([corner1, corner2, corner3, corner4])

# Define the output GeoTIFF file path
output_tiff_path = '/Users/dean/Downloads/LSMap/images/new_jpgs/DJI_0470.tif'

# Load the JPEG image
input_jpeg_path = '/Users/dean/Downloads/LSMap/images/DJI_0470.JPG'
jpeg_image = Image.open(input_jpeg_path)

# Get the image dimensions (width and height)
image_width, image_height = jpeg_image.size

# Define the transform for the GeoTIFF
transform=rasterio.transform.from_bounds(*bbox, width=bbox_size[0], height= bbox_size[1])

transform = from_bounds(corner1, corner2, corner3, corner4, image_width, image_height )

# Create a mask using the Polygon geometry
mask = geometry_mask([polygon], out_shape=(image_height, image_width), transform=transform, invert=True)

# Convert the JPEG image to a NumPy array
image_array = np.array(jpeg_image)

# Apply the mask to the image array
masked_image = np.zeros_like(image_array)
for i in range(image_array.shape[2]):
    masked_image[:, :, i] = image_array[:, :, i] * mask

# Create a new GeoTIFF file
with rasterio.open(output_tiff_path, 'w', driver='GTiff', width=image_width, height=image_height,
                   count=image_array.shape[2], dtype=image_array.dtype, crs='EPSG:4326',
                   transform=transform) as dst:
    dst.write(masked_image.transpose(2, 0, 1))

# Close the GeoTIFF file
dst.close()

print(f"GeoTIFF image created at '{output_tiff_path}'")
