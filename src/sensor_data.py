# Copyright (c) 2024
# Author: Dean Hand
# License: AGPL
# Version: 1.0

from loguru import logger
from Utils import config

def extract_sensor_info(data:dict, sensor_dimensions:dict, im_file_name:str) -> tuple[dict,bool]:

    """
    Extract sensor, drone information, and other metadata from a single metadata entry.

    Args:
        data (dict): A dictionary containing metadata for one image.
        sensor_dimensions (dict): A dictionary containing sensor dimension information.
        im_file_name (str): Name of the file
    Returns:
        tuple: Contains extracted metadata including sensor width, sensor height, drone make, drone model, and additional metadata.
    """
    # Extracting latitude, longitude, and altitude details
    drone_latitude = float(data.get("Composite:GPSLatitude") or data.get("EXIF:GPSLatitude"))
    drone_longitude = float(data.get("Composite:GPSLongitude") or data.get("EXIF:GPSLongitude"))
    drone_relative_altitude = float(data.get("XMP:RelativeAltitude") or data.get("Composite:GPSAltitude"))
    drone_absolute_altitude = float(data.get("XMP:AbsoluteAltitude") or data.get("Composite:GPSAltitude"))

    # Extracting gimbal and flight orientation details
    gimbal_roll_degree = float(
        data.get("XMP:GimbalRollDegree") or data.get("MakerNotes:CameraRoll") or data.get("XMP:Roll"))
    gimbal_pitch_degree = float(
        data.get("XMP:GimbalPitchDegree") or data.get("MakerNotes:CameraPitch") or data.get("XMP:Pitch"))
    gimbal_yaw_degree = float(
        data.get("XMP:GimbalYawDegree") or data.get("MakerNotes:CameraYaw") or data.get("XMP:Yaw"))
    flight_pitch_degree = float(data.get("XMP:FlightPitchDegree") or data.get("MakerNotes:Pitch") or 999)
    flight_roll_degree = float(data.get("XMP:FlightRollDegree") or data.get("MakerNotes:Roll") or 999)
    flight_yaw_degree = float(data.get("XMP:FlightYawDegree") or data.get("MakerNotes:Yaw") or 999)

    # Extracting image and sensor details
    image_width = int(data.get("EXIF:ImageWidth") or data.get("EXIF:ExifImageWidth"))
    image_height = int(data.get("EXIF:ImageHeight") or data.get("EXIF:ExifImageHeight"))
    focal_length = float(data.get("EXIF:FocalLength"))
    max_aperture_value = data.get("EXIF:MaxApertureValue")
    # date/time of original image capture
    datetime_original = data.get("EXIF:DateTimeOriginal", "Unknown")
    # Get sensor model and rig camera index from metadata
    sensor_model_data = data.get("EXIF:Model", "default")  # Fallback to 'default' if not specified
    sensor_index = str(data.get("XMP:RigCameraIndex")) or int(data.get('XMP:SensorIndex'))
    sensor_make=""

 

    if sensor_model_data != "default":
        # DJI Phantom4 and DJI Phantom4 RTK have the same sensor and lens
        if sensor_model_data == "FC6310R":
            sensor_model_data = "FC6310"

        # Prioritize direct match with sensor model and rig camera index
        key = (sensor_model_data, sensor_index)
        sensor_info = sensor_dimensions.get(key)

        # If no direct match, try just with sensor model (for cases without multiple entries)
        if not sensor_info:
            sensor_info = next(
                (value for (model, idx), value in sensor_dimensions.items() if model == sensor_model_data), None)
    else:
        # Use default when sensor_model_data is 'default'
        sensor_info = sensor_dimensions.get(("default", 'nan'))

    # Ensure we have valid sensor_info; otherwise, log error or take necessary action
    if not sensor_info:
        logger.error(
            f"No sensor information found for {im_file_name} with sensor model {sensor_model_data} and rig camera index {sensor_index}. Using defaults.")

        sensor_info = sensor_dimensions.get(("default", 'nan'))

    drone_make, drone_model, camera_make, sensor_model, cam_index, sensor_width, sensor_height, lens_FOVw, lens_FOVh = sensor_info

    if sensor_model in ["FC2103", "FC220", "FC300X", "FC200"]:
        sensor_model = f"{drone_model} {sensor_model}"

    drone_info = dict(DroneMake=drone_make,
                      DroneModel=drone_model,
                      CameraMake=camera_make,
                      SensorModel=sensor_model,
                      SensorWidth=sensor_width,
                      SensorHeight=sensor_height,
                      Lens_FOVw=lens_FOVw,
                      Lens_FOVh=lens_FOVh,
                      FocalLength=focal_length,
                      MaxApertureValue=max_aperture_value)
    
    ## First time in this loop
    if config.drone_properties is None:
        same_drone_as_previous_image = True
    ## Is it the same drone as previous image ? 
    elif config.drone_properties['DroneModel'] == drone_info['DroneModel']:
        same_drone_as_previous_image = True
    ## Is it not same drone as previous image. But we missed the case with Drone A - Drone B - Drone B    
    else:
        same_drone_as_previous_image = False
    config.update_drone_properties(drone_info)

    if sensor_model and drone_make is None:
        drone_model = ""
        drone_make = "Unknown Drone"

    gsd = (sensor_width * drone_relative_altitude) / (focal_length * image_width)

    # Packaging additional metadata for return
    if gimbal_pitch_degree == 999:
        properties = dict(
            File_Name=im_file_name,
            Focal_Length=focal_length,
            Image_Width=image_width,
            Image_Height=image_height,
            Sensor_Model=sensor_model,
            Sensor_index=sensor_index,
            Sensor_Make=sensor_make,
            RelativeAltitude=drone_relative_altitude,
            AbsoluteAltitude=drone_absolute_altitude,
            FlightYawDegree=gimbal_yaw_degree,
            FlightPitchDegree=gimbal_pitch_degree,
            FlightRollDegree=gimbal_roll_degree,
            DateTimeOriginal=datetime_original,
            GimbalPitchDegree=gimbal_pitch_degree,
            GimbalYawDegree=gimbal_yaw_degree,
            GimbalRollDegree=gimbal_roll_degree,
            DroneCoordinates=[drone_longitude, drone_latitude],
            Sensor_Width=sensor_width,
            Sensor_Height=sensor_height,
            CameraMake=camera_make,
            MaxApertureValue=max_aperture_value,
            lens_FOVh1=lens_FOVh,
            lens_FOVw1=lens_FOVw,
            GSD=gsd,
            epsgCode=config.epsg_code
        )
    else:
        properties = dict(
            File_Name=im_file_name,
            Focal_Length=focal_length,
            Image_Width=image_width,
            Image_Height=image_height,
            Sensor_Model=sensor_model,
            Sensor_index=sensor_index,
            Sensor_Make=sensor_make,
            RelativeAltitude=drone_relative_altitude,
            AbsoluteAltitude=drone_absolute_altitude,
            FlightYawDegree=flight_yaw_degree,
            FlightPitchDegree=flight_pitch_degree,
            FlightRollDegree=flight_roll_degree,
            DateTimeOriginal=datetime_original,
            GimbalPitchDegree=gimbal_pitch_degree,
            GimbalYawDegree=gimbal_yaw_degree,
            GimbalRollDegree=gimbal_roll_degree,
            DroneCoordinates=[drone_longitude, drone_latitude],
            Sensor_Width=sensor_width,
            Sensor_Height=sensor_height,
            CameraMake=camera_make,
            Drone_Make=drone_make,
            Drone_Model=drone_model,
            MaxApertureValue=max_aperture_value,
            lens_FOV1h=lens_FOVh,
            lens_FOVw1=lens_FOVw,
            GSD=gsd,
            epsgCode=config.epsg_code
        )

    return properties, same_drone_as_previous_image
