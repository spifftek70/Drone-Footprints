import Utils.config as config
from loguru import logger

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def extract_sensor_info(data, sensor_dimensions, im_file_name):
    """
    Extract sensor, drone information, and other metadata from a single metadata entry.

    Args:
        data (dict): A dictionary containing metadata for one image.
        sensor_dimensions (dict): A dictionary containing sensor dimension information.

    Returns:
        tuple: Contains extracted metadata including sensor width, sensor height, drone make, drone model, and additional metadata.
    """
    # Extracting latitude, longitude, and altitude details
    drone_latitude = safe_float(data.get("Composite:GPSLatitude") or data.get("EXIF:GPSLatitude"))
    drone_longitude = safe_float(data.get("Composite:GPSLongitude") or data.get("EXIF:GPSLongitude"))
    drone_relative_altitude = safe_float(data.get("XMP:RelativeAltitude"))
    drone_absolute_altitude = safe_float(data.get("XMP:AbsoluteAltitude") or data.get("EXIF:GPSAltitude") or data.get("Composite:GPSAltitude"))
    focal_length = safe_float(data.get("EXIF:FocalLength"))

    # Extracting gimbal and flight orientation details
    gimbal_roll_degree = safe_float(data.get("XMP:GimbalRollDegree") or data.get("MakerNotes:CameraRoll") or data.get("XMP:Roll"))
    gimbal_pitch_degree = safe_float(data.get("XMP:GimbalPitchDegree") or data.get("MakerNotes:CameraPitch") or data.get("XMP:Pitch"))
    gimbal_yaw_degree = safe_float(data.get("XMP:GimbalYawDegree") or data.get("MakerNotes:CameraYaw") or data.get("XMP:Yaw"))
    flight_pitch_degree = safe_float(data.get("XMP:FlightPitchDegree") or data.get("MakerNotes:Pitch") or 999)
    flight_roll_degree = safe_float(data.get("XMP:FlightRollDegree") or data.get("MakerNotes:Roll") or 999)
    flight_yaw_degree = safe_float(data.get("XMP:FlightYawDegree") or data.get("MakerNotes:Yaw") or 999)
        
    # Extracting image and sensor details
    image_width = int(data.get("EXIF:ImageWidth") or data.get("EXIF:ExifImageWidth"))
    image_height = int(data.get("EXIF:ImageHeight") or data.get("EXIF:ExifImageHeight"))
    max_aperture_value = data.get("EXIF:MaxApertureValue")
    datetime_original = data.get("EXIF:DateTimeOriginal", "Unknown")
    sensor_model_data = data.get("EXIF:Model", "default")
    sensort_index = str(data.get("XMP:RigCameraIndex")) or int(data.get('XMP:SensorIndex') or '5')

    if gimbal_roll_degree == 0.0 and gimbal_pitch_degree == 0.0 and gimbal_yaw_degree == 0.0:
        flight_pitch_degree = gimbal_pitch_degree
        flight_roll_degree = gimbal_roll_degree
        flight_yaw_degree = gimbal_yaw_degree
    
    # Extracting sensor information from sensor_dimensions
    key = (sensor_model_data, sensort_index)
    sensor_info = sensor_dimensions.get(key)
    if sensor_model_data == 'Test_Pro':
        sensor_model_data = 'L1D-20c'
    if not sensor_info:
        sensor_info = next((value for (model, idx), value in sensor_dimensions.items() if model == sensor_model_data), None)
    if not sensor_info:
        logger.error(f"No sensor information found for {im_file_name} with sensor model {sensor_model_data}. Exiting.")
        exit(0)
        sensor_info = sensor_dimensions.get(("default", 'nan'))

    drone_make = sensor_info['drone_make']
    drone_model = sensor_info['drone_model']
    # sensor_model = sensor_info['sensor_model']
    sensor_model = sensor_model_data
    sensor_make = data.get("EXIF:Make", "default")
    # sensor_make = sensor_info['camera_make'] 
    sensor_width = sensor_info['sensor_width']
    sensor_height = sensor_info['sensor_height']
    lens_FOVw = sensor_info['lens_FOVw']
    lens_FOVh = sensor_info['lens_FOVh']

    # Ensure sensor_width and sensor_height are floats
    try:
        sensor_width = float(sensor_width)
    except ValueError:
        logger.error(f"Invalid sensor width for file: {im_file_name}")
        sensor_width = 0.0  # or handle it appropriately

    try:
        sensor_height = float(sensor_height)
    except ValueError:
        logger.error(f"Invalid sensor height for file: {im_file_name}")
        sensor_height = 0.0  # or handle it appropriately

    drone_info = dict(
        DroneMake=drone_make,
        DroneModel=drone_model,
        CameraMake=sensort_index,
        SensorModel=sensor_model,
        SensorMake=sensor_make,  # Adding sensor_make to drone_info
        SensorWidth=sensor_width,
        SensorHeight=sensor_height,
        Lens_FOVw=lens_FOVw,
        Lens_FOVh=lens_FOVh,
        FocalLength=focal_length,
        MaxApertureValue=max_aperture_value
    )

    if config.drone_properties is None:
        drone_check = True
    elif config.drone_properties['DroneModel'] == drone_info['DroneModel']:
        drone_check = True
    else:
        drone_check = False
    config.update_drone_properties(drone_info)

    if sensor_model and drone_make is None:
        drone_model = ""
        drone_make = "Unknown Drone"
    else:
        drone_model = drone_info['DroneModel']
        drone_make = drone_info['DroneMake']

    try:
        focal_length = float(focal_length)
        image_width = float(image_width)
        drone_relative_altitude = float(drone_relative_altitude)

        # logger.info(f"sensor_width type: {type(sensor_width)}")
        # logger.info(f"sensor_height type: {type(sensor_height)}")
        # logger.info(f"focal_length type: {type(focal_length)}")
        # logger.info(f"image_width type: {type(image_width)}")
        # logger.info(f"drone_relative_altitude type: {type(drone_relative_altitude)}")

        gsd = (sensor_width * drone_relative_altitude) / (focal_length * image_width)
    except TypeError as t:
        logger.exception(f"Type error: {t} for image: {im_file_name}")
        raise
    except KeyError as k:
        logger.exception(f"Missing metadata key: {k} for image: {im_file_name}")
        raise
    except ValueError as e:
        logger.exception(f"Invalid value for metadata key: {e} for image: {im_file_name}")
        raise

    if gimbal_pitch_degree == 999:
        properties = dict(
            File_Name=im_file_name,
            Focal_Length=focal_length,
            Image_Width=image_width,
            Image_Height=image_height,
            Sensor_Model=sensor_model,
            Sensor_index=sensort_index,
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
            # CameraMake=camera_make,
            Drone_Make=drone_make,
            Drone_Model=drone_model,
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
            Sensor_index=sensort_index,
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
            # CameraMake=camera_make,
            Drone_Make=drone_make,
            Drone_Model=drone_model,
            MaxApertureValue=max_aperture_value,
            lens_FOV1h=lens_FOVh,
            lens_FOVw1=lens_FOVw,
            GSD=gsd,
            epsgCode=config.epsg_code
        )

    return properties, drone_check