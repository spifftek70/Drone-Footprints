# Copyright (c) 2024
# Author: Dean Hand
# License: AGPL
# Version: 1.0

import geojson
from geojson_rewind import rewind
from shapely.geometry import Polygon


def create_geojson_feature(coord_array, Drone_Lon, Drone_Lat, properties):
    # print("\n\n HEY YOU FUCKED UP\n\n")
    """
    Create GeoJSON features for a single image's metadata.

    Args:
        coord_array (list): A list of coordinate pairs that define the image's footprint.
        Drone_Lon (list): List containing drone longitude.
        Drone_Lat (list): List containing drone latitude.
        properties (dict): Additional properties for the GeoJSON feature.

    Returns:
        tuple: Contains a GeoJSON point feature and a GeoJSON polygon feature.
    """
    polygon = Polygon(coord_array)
    square_meters = polygon.area  # Calculate area in square meters
    
    geojson_polygon = geojson.dumps(polygon)
    rewound_polygon = geojson.loads(geojson_polygon)
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
    # feature_polygon = dict(
    #     type="Feature", geometry=type_polygon, properties={**properties, 'square_meters': square_meters}
    # )
    sqrmtrs = {'square_meters': square_meters}
    properties[17].append(sqrmtrs)
    feature_polygon = dict(
        type="Feature", geometry=type_polygon, properties=properties
    )
    # print("properties: ", properties)
    return feature_point, feature_polygon
