# Copyright (c) 2024
# Author: Dean Hand
# License: AGPL
# Version: 1.0

import geojson
from geojson_rewind import rewind
from shapely.geometry import Polygon


def create_geojson_feature(coord_array, Drone_Lon, Drone_Lat, properties):
    """
    Create GeoJSON features for a single image's metadata.

    Args:
        data (dict): A dictionary containing metadata for one image.
        coord_array (list): A list of coordinate pairs that define the image's footprint.
        sensor_info (tuple): Contains sensor width, sensor height, drone make, and drone model.
        file_Name (str): The name of the file being processed.

    Returns:
        tuple: Contains a GeoJSON point feature and a GeoJSON polygon feature.
    """
    # Properties setup and other related processing goes here.
    # This is simplified to focus on structure. Implement as needed based on the original function.

    polygon = Polygon(coord_array)
    geojson_polygon = geojson.dumps(polygon)
    rewound_polygon = rewind(geojson.loads(geojson_polygon))
    array_rw = rewound_polygon["coordinates"][0]
    closed_array = [
        (array_rw[0]),
        (array_rw[3]),
        (array_rw[2]),
        (array_rw[1]),
        (array_rw[0]),
    ]

    type_point = dict(type="Point", coordinates=[Drone_Lon[0], Drone_Lat[0]])
    type_polygon = dict(type="Polygon", coordinates=[closed_array])
    feature_point = dict(
        type="Feature", geometry=type_point, properties=properties
    )
    feature_polygon = dict(
        type="Feature", geometry=type_polygon, properties=properties
    )

    return feature_point, feature_polygon
