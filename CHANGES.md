Version 1.0 (2024-02-07)
----------------
Working copy 

Uses GSD to calculate corner points
Uses GDAL Warp to map corner points to extents

Version 1.1 (2024-02-15)
----------------
Good for Practical use on NADIR and Non-NADIR images.
Uses FOV to calculate corner points.

Version 1.2 (2024-03-05)
----------------
Uses cv2 findHomography, and warpPerspective to actually warp the images to the proper perspectives.
Uses Gimbal Yaw instead of the Drone Yaw.
Compensates for the Magnetic Declination.
Updated instructions in README.md on Gimbal and Compass Calibration.