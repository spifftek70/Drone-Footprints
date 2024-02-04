# Aerial Drone (aka UAV/UAS) Imagery Footprint and GeoTIFF Utility. 

Name: drone_fp.py
>The purpose of this module is to calculate imagery footprints of individual drone images.  There is no stitching of 
> images, so the process is actually quite fast. The output is geo-rectified GeoTiff image file and a GeoJSON file 
> with:
>* Drone Flightpath (LineString)
>* Drone Location at location of photo (Point)
>* Individual Image Footprints (Polygons)
----------------------------------------------------------------------------------------------------------------

Author: Dean Hand <br>
Date Created: 09/07/2019<br>

----------------------------------------------------------------------------------------------------------------
## Arguments
`-i` - The Default root folder for the mission you wish to process.  Required

`-o` - The output directory for the GeoJSON file. Required

`-w` - Sensor Width (default is 13.2) Not Required (Check your Drones Specs for information)

`-d` - Sensor Height (default is 8.8) Not Required (Check your Drones Specs for information)

## Example Commands
`python Drone_Footprints.py -i '/Users/<user>/Downloads/flight2/images' -o '/Users/<user>/Downloads/flight2/output`

`python ChatGPT.py -i "/Path/To/Dataset/images" -o "/Path/To/Dataset/output" -w 6.16 -d 4.62`
## Sample Dataset
A sample dataset can be found [here](https://drive.google.com/drive/u/1/folders/1Hwrhi-eK_-i8R2NQ3churBls-i4aAXg9)

## Sample JSON Output 
A sample of the json output can be found [here](https://drive.google.com/open?id=1RhSlY9KL2NYpnnVyNqI5c6cLzC0YWMTj)

## Processing Notes

### The accuracy of this process depends highly on a number of factors.
1. IMU calibration
2. Gimbal calibration
3. Compass Calibration
4. Shooting angle (for best results - `Parallel to Main Path`)
5. Capture Mode (for best results - `Hover&Capture at Point`)
6. Gimbal Roll Angle (for best results - NADIR aka -90° aka straight down)
7. Yaw Degrees - I've found the GimbalYawDegree data from the files to be unreliable at best,
so the code calculates the GSD and FOV using the FlightYawDegree.

## Future Builds

### Sensor Size DB
The file [drone_sensors.csv](drone_fp%2Fdrone_sensors.csv) is the start of autoprocessing for 
senosr width and height.  It is incomplete, but once finshed, I'll incomporate that code into the 
process.

### RTK Processing
Should add much better accuracy to any RTK dataset that's processed.