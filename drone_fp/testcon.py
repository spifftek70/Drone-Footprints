import math

def calculate_drone_imagery_footprint_corners(Focal_Length, Image_Width, Image_Height, RelativeAltitude, DroneRollDegree, DroneYawDegree, DronePitchDegree, GimbalRollDegree, GimbalYawDegree, GimbalPitchDegree, Zone, Hemisphere, Easting, Northing, sensor_width, sensor_height):
    # Constants
    # earth_radius = 6378137  # Earth radius in meters

    # Convert degrees to radians
    DroneRollRad = math.radians(DroneRollDegree)
    DroneYawRad = math.radians(DroneYawDegree)
    DronePitchRad = math.radians(DronePitchDegree)
    GimbalRollRad = math.radians(GimbalRollDegree)
    GimbalYawRad = math.radians(GimbalYawDegree)
    GimbalPitchRad = math.radians(GimbalPitchDegree)

    # Calculate the drone's pitch, roll, and yaw relative to the gimbal
    DronePitchRelativeRad = DronePitchRad - GimbalPitchRad
    DroneRollRelativeRad = DroneRollRad - GimbalRollRad
    DroneYawRelativeRad = DroneYawRad - GimbalYawRad

    # Calculate the Field of View (FOV) in both horizontal and vertical directions
    # FOV_horizontal = IFOV_horizontal * Image_Width
    # FOV_vertical = IFOV_vertical * Image_Height

    FOV_horizontal = 2 * math.degrees(math.atan(sensor_width / (2 * Focal_Length)))  # Field of View - Width
    FOV_vertical = 2 * math.degrees(math.atan(sensor_height / (2 * Focal_Length)))  # Field of View - Height

    # Calculate the sensor's angular resolution (IFOV) in both horizontal and vertical directions
    # IFOV_horizontal = math.degrees(math.atan(sensor_width / (2 * Focal_Length)))
    # IFOV_vertical = math.degrees(math.atan(sensor_height / (2 * Focal_Length)))

    # Calc IFOV, based on right angle trig of one-half the lens angles
    IFOV_horizontal = 2 * (math.tan(math.radians(0.5 * FOV_horizontal)) * RelativeAltitude)
    IFOV_vertical = 2 * (math.tan(math.radians(0.5 * FOV_vertical)) * RelativeAltitude)

    # Calc pixel resolutions based on the IFOV and sensor size
    pixel_resx = (IFOV_horizontal / Image_Width) * 100
    pixel_resy = (IFOV_vertical / Image_Height) * 100

    # Calculate the half FOV angles in radians
    half_FOV_horizontal_rad = math.radians(FOV_horizontal / 2)
    half_FOV_vertical_rad = math.radians(FOV_vertical / 2)

    # Calculate the offsets for the four corners of the image
    offset_top_left = (-half_FOV_horizontal_rad, half_FOV_vertical_rad)
    offset_top_right = (half_FOV_horizontal_rad, half_FOV_vertical_rad)
    offset_bottom_left = (-half_FOV_horizontal_rad, -half_FOV_vertical_rad)
    offset_bottom_right = (half_FOV_horizontal_rad, -half_FOV_vertical_rad)

    # Calculate the UTM coordinates for each corner, considering DroneRollRelativeRad and northing_offset
    def calculate_corner_coordinates(offset):
        northing_offset = (math.cos(DroneYawRelativeRad) * math.cos(DronePitchRelativeRad) * RelativeAltitude)
        easting_offset = (math.sin(DroneYawRelativeRad) * math.cos(DronePitchRelativeRad) * RelativeAltitude)

        # Apply the DroneRollRelativeRad for roll correction
        easting_offset_roll_corrected = easting_offset * math.cos(DroneRollRelativeRad)
        northing_offset_roll_corrected = northing_offset * math.cos(DroneRollRelativeRad)

        UTM_easting = Easting + easting_offset_roll_corrected + (offset[0] * RelativeAltitude)
        UTM_northing = Northing + northing_offset_roll_corrected + (offset[1] * RelativeAltitude)

        return UTM_easting, UTM_northing

    top_left = calculate_corner_coordinates(offset_top_left)
    top_right = calculate_corner_coordinates(offset_top_right)
    bottom_left = calculate_corner_coordinates(offset_bottom_left)
    bottom_right = calculate_corner_coordinates(offset_bottom_right)

    return [bottom_right, bottom_left, top_left, top_right]

