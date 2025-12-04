# Copyright (c) 2024
# Author: Dean Hand
# License: AGPL
# Version: 1.0
import datetime
import itertools
from pathlib import Path
from tqdm import tqdm
from loguru import logger
from Utils.utils import Color
from Utils import config
from imagedrone import ImageDrone
from functools import lru_cache


def process_metadata(metadata:list[dict], config, indir_path:Path, geotiff_dir:Path, sensor_dimensions:dict) -> tuple[dict, list[ImageDrone]]:
    """
    Process and convert image metadata into GeoJSON features and create GeoTIFFs.

    Args:
        metadata (list[dict]): Metadata from each image file.
        indir_path (Path): Input directory path containing the original images.
        geotiff_dir (Path): Output directory path for saving generated GeoTIFFs.
        sensor_dimensions (dict): A dictionary with sensor model keys and dimension values.

    Returns:
        dict: A GeoJSON FeatureCollection comprising features derived from the image metadata.
    """
    feature_collection = {"type": "FeatureCollection", "features": []}
    line_coordinates = []
    local_config = config
    outer_tqdm = tqdm(total=len(metadata),position=0,desc=f'{Color.CYAN}Image Files',leave=False)
    pbar_tqdm = tqdm(total=len(metadata), position=1, leave=False, bar_format='{desc}')
    line_feature = ""
    nb_processed_images = 0
    logger.info("Processing images for GeoTiff and GeoJSON creation.")
    #same_drone_as_previous_image_array = []
    images_array : list[ImageDrone] = []

    datetime_original = ""
    for data in metadata:
        # pprint(data)clear
        try:
            image = ImageDrone(metadata=data, sensor_dimensions=sensor_dimensions, config=local_config,logger=logger)
            images_array.append(image)
            pbar_tqdm.set_description_str(f'{Color.YELLOW}Current file: {image.file_name}{Color.END}')

            # Extract detailed sensor and drone info for the current image

            #properties, same_drone_as_previous_image = extract_sensor_info(data, sensor_dimensions, image.file_name)
            #same_drone_as_previous_image_array.append(same_drone_as_previous_image)

            datetime_original = image.datetime_original
            local_config.im_file_name= image.file_name
            local_config.absolute_altitude = image.absolute_altitude
            local_config.relative_altitude = image.relative_altitude

            # Calculate Field of View (FOV) or any other necessary geometric calculations
            image.get_HighAccuracyFOV()

            image.create_geojson_feature()

            # Only add features if they were successfully created
            if image.feature_point and image.feature_polygon:
                # Generate GeoTIFF for the current image
                image.generate_geotiff(indir_path, geotiff_dir)

                feature_collection["features"].append(image.feature_point)
                feature_collection["features"].append(image.feature_polygon)
            else:
                logger.warning(f"Skipping GeoJSON features for {image.file_name} due to missing footprint data")

            # Update line coordinates for potential LineString creation
            line_coordinates.append([image.longitude, image.latitude])

            outer_tqdm.update(1)

        except TypeError as t:
            logger.exception(f"Missing metadata key: {t} for image: {image.file_name}")
        except KeyError as k:
            logger.exception(f"Missing metadata key: {k} for image: {image.file_name}")
        except ValueError as e:
            logger.exception(f"Invalid value for metadata key: {e} for image: {image.file_name}")
        nb_processed_images = nb_processed_images + 1


    now = datetime.datetime.now()
    process_date = f"{now.strftime('%Y-%m-%d %H-%M')}"
    line_geometry = dict(type="LineString", coordinates=line_coordinates)

    same_drone_for_all_images : bool = None
    ### Compare drone_data for all images
    for a , b in itertools.combinations(images_array, 2):
        if not same_drone_for_all_images:
            same_drone_for_all_images = a.drone_hash == b.drone_hash
        else:
            same_drone_for_all_images = a.drone_hash == b.drone_hash == same_drone_for_all_images


    mission_props = dict(date=datetime_original, Process_date=process_date, epsg=local_config.epsg_code,
                             cog=local_config.cog, drone_model=image.drone_model,
                             sensor_make=image.sensor_model)

    if not same_drone_for_all_images and image.sensor_model != "M3M":
        mission_props = dict(date=datetime_original, Process_date=process_date, epsg=local_config.epsg_code,
                             cog=local_config.cog, drone_model="Multiple", sensor_make="Multiple")


    # # multiple drones and Mavic 3 Multispectral
    # if False in same_drone_as_previous_image_array and drone_props['SensorModel'] == "M3M":
    #     mission_props = dict(date=datetime_original, Process_date=process_date, epsg=config.epsg_code,
    #                          cog=config.cog, drone_model=drone_props['DroneModel'],
    #                          sensor_make=drone_props['SensorModel'])
    # # multiple drones and not Mavic 3 Multispectral
    # elif False in same_drone_as_previous_image_array:
    #     mission_props = dict(date=datetime_original, Process_date=process_date, epsg=config.epsg_code,
    #                          cog=config.cog, drone_model="Multiple", sensor_make="Multiple")
    #     # only one drone
    # else:
    #     mission_props = dict(date=datetime_original, Process_date=process_date, epsg=config.epsg_code,
    #                          cog=config.cog, drone_model=drone_props['DroneModel'],
    #                          sensor_make=drone_props['SensorModel'])

    line_feature = dict(type="Feature", geometry=line_geometry, properties=mission_props)
    feature_collection["features"].insert(0, line_feature)

    pbar_tqdm.close()
    outer_tqdm.close()
    return feature_collection, images_array

@lru_cache(maxsize=100)
def get_cached_declination(lat_rounded, lon_rounded, date_str):
    # Round to 0.1 degrees for caching
    return calculate_declination(lat_rounded, lon_rounded, date_str)
