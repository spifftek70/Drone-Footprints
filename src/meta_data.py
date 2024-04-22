# Copyright (c) 2024
# Author: Dean Hand
# License: AGPL
# Version: 1.0
import datetime
from tqdm import tqdm
from loguru import logger
from Utils.utils import Color
from sensor_data import extract_sensor_info
import Utils.config as config
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
    nb_processed_images = 0
    file_name = ""
    sensor_make = ""
    camera_make = ""
    sensor_model = ""
    lens_FOVw = 0.0
    lens_FOVh = 0.0
    logger.info("Processing images for GeoTiff and GeoJSON creation.")
    drone_checks = []
    images_array = []
    for data in metadata:
        # pprint(data)clear
        try:
            image=ImageDrone(data,sensor_dimensions,config)
            images_array.append(image)
            pbar.set_description_str(f'{Color.YELLOW}Current file: {image.file_name}{Color.END}')

            # Extract detailed sensor and drone info for the current image

            properties, drone_check = extract_sensor_info(data, sensor_dimensions, image.file_name)
            drone_checks.append(drone_check)
            lens_FOVw = properties['lens_FOVw1'] if 'lens_FOVw1' in properties else 1.0
            lens_FOVh = properties['lens_FOV1h'] if 'lens_FOV1h' in properties else 1.0

            config.update_file_name(image.file_name)
            config.update_abso_altitude(image.absolute_altitude)
            config.update_rel_altitude(image.relative_altitude)

            # Calculate Field of View (FOV) or any other necessary geometric calculations
            image.coord_array, image.footprint_coordinates = HighAccuracyFOVCalculator(image,
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
            i=nb_processed_images).get_fov_bbox()

            image.create_geojson_feature(properties)
            # Generate GeoTIFF for the current image
            image.generate_geotiff(indir_path, geotiff_dir)


            feature_collection["features"].append(image.feature_point)
            feature_collection["features"].append(image.feature_polygon)

            # Update line coordinates for potential LineString creation
            line_coordinates.append([image.longitude, image.latitude])


            outer.update(1)

        except TypeError as t:
            logger.exception(f"Missing metadata key: {t} for image: {file_name}")
        except KeyError as k:
            logger.exception(f"Missing metadata key: {k} for image: {file_name}")
        except ValueError as e:
            logger.exception(f"Invalid value for metadata key: {e} for image: {file_name}")
        nb_processed_images = nb_processed_images + 1

    # Add lines to the GeoJSON feature collection if necessary
      Drone_props = config.drone_properties
      now = datetime.datetime.now()
      process_date = f"{now.strftime('%Y-%m-%d %H-%M')}"
      line_geometry = dict(type="LineString", coordinates=line_coordinates)
              if False in drone_checks and Drone_props['SensorModel'] != "M3M":
          logger.warning("Multiple Drone types Detected.")
          mission_props = dict(date=datetime_original, Process_date=process_date, epsg=config.epsg_code,
                               cog=config.cog, drone_model="Multiple", sensor_make="Multiple")
      elif False in drone_checks and Drone_props['SensorModel'] == "M3M":
          mission_props = dict(date=datetime_original, Process_date=process_date, epsg=config.epsg_code,
                               cog=config.cog, drone_model=Drone_props['DroneModel'], sensor_make=Drone_props['SensorModel'])
      else:
          logger.info("drone props", Drone_props, "\n", "mods", Drone_props['DroneModel'])
          mission_props = dict(date=datetime_original, Process_date=process_date, epsg=config.epsg_code,
                               cog=config.cog, drone_model=Drone_props['DroneModel'], sensor_make=Drone_props['SensorModel'])
      line_feature = dict(type="Feature", geometry=line_geometry, properties=mission_props)
      feature_collection["features"].insert(0, line_feature)

    pbar.close()
    outer.close()
    return feature_collection,images_array
