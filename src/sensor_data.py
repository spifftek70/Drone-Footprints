# Copyright (c) 2024
# Author: Dean Hand
# License: AGPL
# Version: 1.0


def extract_sensor_info(data, sensor_dimensions, im_file_name, sensor_make, sensor_model, lens_FOVw, lens_FOVh):
    """
    Extract sensor, drone information, and other metadata from a single metadata entry.

    Args:
        data (dict): A dictionary containing metadata for one image.
        sensor_dimensions (dict): A dictionary containing sensor dimension information.

    Returns:
        tuple: Contains extracted metadata including sensor width, sensor height, drone make, drone model, and additional metadata.
    """
    # Extracting latitude, longitude, and altitude details
    Drone_Lat = float(data.get("Composite:GPSLatitude") or data.get("EXIF:GPSLatitude"))
    Drone_Lon = float(data.get("Composite:GPSLongitude") or data.get("EXIF:GPSLongitude"))
    re_altitude = float(data.get("XMP:RelativeAltitude") or data.get("Composite:GPSAltitude"))
    ab_altitude = float(data.get("XMP:AbsoluteAltitude") or data.get("Composite:GPSAltitude"))

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

    # Sensor model and make
    sensor_model = data.get("EXIF:Model", "default")  # Fallback to 'default' if not found
    rig_camera_idx = data.get("XMP:RigCameraIndex") or data.get('XMP:SensorIndex') or 5

    # date/time of original image capture
    datetime_original = data.get("EXIF:DateTimeOriginal", "Unknown")

    # Getting sensor dimensions
    if sensor_model == "M3M":
        sensor_model = str(rig_camera_idx)
    sensor_width, sensor_height, drone_make, drone_model, lens_FOVw, lens_FOVh = (
        sensor_dimensions.get(sensor_model, sensor_dimensions.get("default"))
    )
    # print("camera stuff and shit", sensor_width, sensor_height, drone_make, drone_model, lens_FOVw, lens_FOVh)
    if sensor_model and drone_make is None:
        drone_model = ""
        drone_make = "Unknown Drone"

    gsd = (sensor_width * re_altitude) / (focal_length * image_width)

    # Packaging additional metadata for return
    if gimbal_pitch_degree == 999:
        properties = dict(
            File_Name=im_file_name,
            Focal_Length=focal_length,
            Image_Width=image_width,
            Image_Height=image_height,
            Sensor_Model=sensor_model,
            Sensor_index=rig_camera_idx,
            Sensor_Make=sensor_make,
            RelativeAltitude=re_altitude,
            AbsoluteAltitude=ab_altitude,
            FlightYawDegree=gimbal_yaw_degree,
            FlightPitchDegree=gimbal_pitch_degree,
            FlightRollDegree=gimbal_roll_degree,
            DateTimeOriginal=datetime_original,
            GimbalPitchDegree=gimbal_pitch_degree,
            GimbalYawDegree=gimbal_yaw_degree,
            GimbalRollDegree=gimbal_roll_degree,
            DroneCoordinates=[Drone_Lon, Drone_Lat],
            Sensor_Width=sensor_width,
            Sensor_Height=sensor_height,
            lens_FOVh1=lens_FOVh,
            lens_FOVw1=lens_FOVw,
            GSD=gsd
        )
    else:
        properties = dict(
            File_Name=im_file_name,
            Focal_Length=focal_length,
            Image_Width=image_width,
            Image_Height=image_height,
            Sensor_Model=sensor_model,
            Sensor_index=rig_camera_idx,
            Sensor_Make=sensor_make,
            RelativeAltitude=re_altitude,
            AbsoluteAltitude=ab_altitude,
            FlightYawDegree=flight_yaw_degree,
            FlightPitchDegree=flight_pitch_degree,
            FlightRollDegree=flight_roll_degree,
            DateTimeOriginal=datetime_original,
            GimbalPitchDegree=gimbal_pitch_degree,
            GimbalYawDegree=gimbal_yaw_degree,
            GimbalRollDegree=gimbal_roll_degree,
            DroneCoordinates=[Drone_Lon, Drone_Lat],
            Sensor_Width=sensor_width,
            Sensor_Height=sensor_height,
            Drone_Make=drone_make,
            Drone_Model=drone_model,
            lens_FOV1h=lens_FOVh,
            lens_FOVw1=lens_FOVw,
            GSD=gsd
        )
    return properties
