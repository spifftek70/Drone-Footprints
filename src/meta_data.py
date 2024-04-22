# Copyright (c) 2024
# Author: Dean Hand
# License: AGPL
# Version: 1.0

import os
from pathlib import Path
from FOV_prep import calculate_fov
from create_geotiffs import generate_geotiff
from create_geojson import create_geojson_feature
from sensor_data import extract_sensor_info
from Utils.utils import Color
from tqdm import tqdm
from loguru import logger
# from Utils.logger_config import *
import Utils.config as config
import datetime
from imagedrone import ImageDrone
from new_fov import HighAccuracyFOVCalculator

def process_metadata(metadata, indir_path, geotiff_dir, sensor_dimensions):
    """
    Process and convert image metadata into GeoJSON features and create GeoTIFFs.

    Args:
        metadata (List[dict]): Metadata from each image file.
        indir_path (Path): Input directory path containing the original images.
        geotiff_dir (Path): Output directory path for saving generated GeoTIFFs.
        sensor_dimensions (dict): A dictionary with sensor model keys and dimension values.

    Returns:
        dict: A GeoJSON FeatureCollection comprising features derived from the image metadata.
    """
    feature_collection = {"type": "FeatureCollection", "features": []}
    line_coordinates = []
    outer = tqdm(total=len(metadata), position=0, desc=Color.CYAN + 'Image Files', leave=False)  # Removed Color for simplicity
    pbar = tqdm(total=len(metadata), position=1, leave=False, bar_format='{desc}')
    line_feature = ""
    i = 0
    file_Name = ""
    sensor_make = ""
    camera_make = ""
    sensor_model = ""
    lens_FOVw = 0.0
    lens_FOVh = 0.0
    logger.info("Processing images for GeoTiff and GeoJSON creation.")
    images_array = []
    for data in metadata:
        try:
            image=ImageDrone(data,sensor_dimensions,config)
            images_array.append(image)
            file_Name = str(data.get("File:FileName"))
            pbar.set_description_str(f'{Color.YELLOW}Current file: {file_Name}{Color.END}')

            # Extract detailed sensor and drone info for the current image
            properties = extract_sensor_info(data, sensor_dimensions, file_Name, sensor_make, camera_make, sensor_model, lens_FOVw,
                                             lens_FOVh)
            re_altitude = float(properties['RelativeAltitude']) if 'RelativeAltitude' in properties else None,
            ab_altitude = float(properties['AbsoluteAltitude']) if 'AbsoluteAltitude' in properties else None,
            focal_length = float(properties['Focal_Length']) if 'Focal_Length' in properties else None,
            sensor_width = str(properties['Sensor_Width']) if 'Sensor_Width' in properties else None,
            sensor_height = str(properties['Sensor_Height']) if 'Sensor_Height' in properties else None,
            gimbal_roll_deg = float(properties['GimbalRollDegree']) if 'GimbalRollDegree' in properties else None,
            gimbal_pitch_deg = float(properties['GimbalPitchDegree']) if 'GimbalPitchDegree' in properties else None,
            gimbal_yaw_deg = float(properties['GimbalYawDegree']) if 'GimbalYawDegree' in properties else None,
            flight_roll_deg = float(properties['FlightRollDegree']) if 'FlightRollDegree' in properties else None,
            flight_pitch_deg = float(properties['FlightPitchDegree']) if 'FlightPitchDegree' in properties else None,
            flight_yaw_deg = float(properties['FlightYawDegree']) if 'FlightYawDegree' in properties else None,
            drone_latitude = float(properties['DroneCoordinates'][1]) if 'DroneCoordinates' in properties and \
                                                                         properties['DroneCoordinates'] else None,
            drone_longitude = float(properties['DroneCoordinates'][0]) if 'DroneCoordinates' in properties and \
                                                                          properties['DroneCoordinates'] else None,
            lens_FOVw = properties['lens_FOVw1'] if 'lens_FOVw1' in properties else 1.0
            lens_FOVh = properties['lens_FOV1h'] if 'lens_FOV1h' in properties else 1.0
            datetime_original = properties['DateTimeOriginal'] if 'DateTimeOriginal' in properties else None,
            drone_make = str(properties['Drone_Make']) if 'Drone_Make' in properties else None,
            drone_model = str(properties['Drone_Model']) if 'Drone_Model' in properties else None,
            Sensor_Make = str(properties['Sensor_Make']) if 'Sensor_Make' in properties else None,
            Sensor_Model = str(properties['Sensor_Model']) if 'Sensor_Model' in properties else None
            Sensor_index = properties['Sensor_index'] if 'Sensor_index' in properties else None
            i = i
            # file_Name = properties['file_name'] if 'file_name' in properties else None
            config.update_file_name(file_Name)
            config.update_abso_altitude(ab_altitude[0])
            config.update_rel_altitude(re_altitude[0])
            image_width = int(properties['Image_Width']) if 'Image_Width' in properties else 1.0
            image_height = int(properties['Image_Height']) if 'Image_Height' in properties else 1.0
            # Calculate Field of View (FOV) or any other necessary geometric calculations
            coord_array, polybox = calculate_fov(
                re_altitude[0],
                ab_altitude[0],
                focal_length[0],
                sensor_width[0],
                sensor_height[0],
                image_width,
                image_height,
                gimbal_roll_deg[0],
                gimbal_pitch_deg[0],
                gimbal_yaw_deg[0],
                flight_roll_deg[0],
                flight_pitch_deg[0],
                flight_yaw_deg[0],
                drone_latitude[0],
                drone_longitude[0],
                datetime_original[0],
                lens_FOVw,
                lens_FOVh,
                i
            )
            image.coord_array, image.footprint_coordinates = HighAccuracyFOVCalculator(
            drone_gps=(image.latitude, image.longitude),
            drone_altitude=image.relative_altitude,
            camera_info=   {
            'sensor_width': image.sensor_width,  # mm
            'sensor_height': image.sensor_height,  # mm (Optional if not used in calculations)
            'image_width': image.image_width,  # pixels
            'image_height': image.image_height,  # pixels
            'Focal_Length': image.focal_length,  # mm
            'lens_FOVw': image.lens_FOV_width,  # lens distortion in mm
            'lens_FOVh': image.lens_FOV_height  # lens distortion in mm 
            },
            gimbal_orientation = {
            'roll': image.gimbal_roll_degree,  # Gimbal roll in degrees
            'pitch': image.gimbal_pitch_degree,  # Gimbal pitch in degrees (negative if pointing downwards)
            'yaw': image.gimbal_yaw_degree,  # Gimbal yaw in degrees
             },
            flight_orientation = {
            'roll': image.flight_roll_degree,  # Flight roll in degrees
            'pitch': image.gimbal_pitch_degree,  # Flight pitch in degrees
            'yaw': image.flight_yaw_degree,  # Flight yaw in degrees (direction of flight)
            },
            datetime_original = image.datetime_original,
            i=i).get_fov_bbox()

            image.create_geojson_feature(properties)
            image.generate_geotiff(indir_path, geotiff_dir)

            # Create GeoJSON features for the current image
            feature_point, feature_polygon = create_geojson_feature(polybox, drone_longitude, drone_latitude,
                                                                    properties)
            feature_collection["features"].append(feature_point)
            feature_collection["features"].append(feature_polygon)

            # Update line coordinates for potential LineString creation
            line_coordinates.append([drone_longitude[0], drone_latitude[0]])

            # Generate GeoTIFF for the current image
            image_path = os.path.join(indir_path, file_Name)
            output_file = f"{Path(file_Name).stem}.tif"
            geotiff_file = Path(geotiff_dir) / output_file
            generate_geotiff(image_path, geotiff_file, coord_array)

            outer.update(1)

        except TypeError as t:
            logger.exception(f"Missing metadata key: {t} for image: {file_Name}")
        except KeyError as k:
           logger.exception(f"Missing metadata key: {k} for image: {file_Name}")
        except ValueError as e:
            logger.exception(f"Invalid value for metadata key: {e} for image: {file_Name}")
        i = i + 1
    # Add lines to the GeoJSON feature collection if necessary
    if line_coordinates:
        now = datetime.datetime.now()
        process_date = f"{now.strftime('%Y-%m-%d %H-%M')}"
        line_geometry = dict(type="LineString", coordinates=line_coordinates)
        mission_props = dict(date=datetime_original, Process_date=process_date, epsg=config.epsg_code, cog=config.cog)
        line_feature = dict(type="Feature", geometry=line_geometry, properties=mission_props)
        feature_collection["features"].insert(0, line_feature)
    pbar.close()
    outer.close()
    return feature_collection, i
