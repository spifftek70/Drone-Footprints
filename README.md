# Aerial Drone (aka UAV/UAS) Imagery Footprint and GeoTIFF Utility. 

Name: drone_fp.py
The purpose of this module is to calculate imagery footprints of individual drone images.  There is no stitching of 
 images, so the process is actually quite fast. The output is geo-rectified GeoTiff image file and a GeoJSON file 
 with:
* Drone Flightpath (LineString)
* Drone location at point of photo (Point)
* Individual Image Footprints (Polygons)

----------------------------------------------------------------------------------------------------------------
Author: Dean Hand <br>
Date Created: 09/07/2019<br>
----------------------------------------------------------------------------------------------------------------

## Arguments
`-i` - The Default root folder for the mission you wish to process.  Required

`-o` - The output directory for the GeoJSON file and GeoTiffs. Required

`-w` - Sensor Width (default is 13.2) Not Required (Check your Drones Specs for information)

`-d` - Sensor Height (default is 8.8) Not Required (Check your Drones Specs for information)

----------------------------------------------------------------------------------------------------------------

## Example Commands
`python Drone_Footprints.py -i '/Users/<user>/Downloads/flight2/images' -o '/Users/<user>/Downloads/flight2/output`

`python Drone_Footprints.py -i "/Path/To/Dataset/images" -o "/Path/To/Dataset/output" -w 6.16 -d 4.62`

----------------------------------------------------------------------------------------------------------------

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

### Sort into Datasets
It is highly recommended that you sort the images you want processed into corresponding datasets

- Separate Images by flight mission
  - Create a mission folder for each flight mission
  - Create an image folder within the mission folder

``````
├── /Path/to/mission_folder
│   ├── images
``````

### Outputs locations
It is a good practice to set your output folder `-o` location within your flight mission folder as shown in 
[Example Commands](#example-commands), but it is not required.
``````
├── /Path/to/output_folder
│   ├── geotiffs
│   │   ├── image1.tif
│   │   ├── image1.tif
│   ├── geojsons
│   │   ├── M_2024-02-06_11-16.json
``````
Geojson name is constructed using the date/time of processing like so:
 - `M` = mission
 - `2024-02-06` = year, month, day
 - `11-16` = hour, minute

----------------------------------------------------------------------------------------------------------------

## Future Builds

### Sensor Size DB
The file [drone_sensors.csv](drone_fp%2Fdrone_sensors.csv) is the start of autoprocessing for 
senosr width and height.  It is incomplete, but once finshed, I'll incomporate that code into the 
process.

### RTK Processing
Should add much better accuracy to any RTK dataset that's processed.

----------------------------------------------------------------------------------------------------------------
## Sample Outputs

### Sample Dataset
 - [Mesa 02-04-2024](https://drive.google.com/drive/folders/16BR0h04ATS6uYavgXros031j8kfbCZJp?usp=share_link)
 - [Mesa 01-28-2024-a](https://drive.google.com/drive/folders/1eE4UY3IXOdtwvZhvHdsvN5eP0siKtKVU?usp=share_link)
 - [Mesa 01-28-2024](https://drive.google.com/drive/folders/1tx55rh3CgyDzteBAS7c3qEHLJobb902M?usp=share_link)
 - [Mesa 01-25-2024](https://drive.google.com/drive/folders/13jCmLv4FMEQnQJ1fm8c5k3OO_kBJC-hq?usp=share_link)

### Sample JSON Output 
[M_2024-02-04_07-03.json](samples%2Fgeojson%2FM_2024-02-04_07-03.json)

### Sample GeoTIFFs
- [DJI_0261.tif](samples%2Fgeotiffs%2FDJI_0261.tif)
- [DJI_0267.tif](samples%2Fgeotiffs%2FDJI_0267.tif)
- [DJI_0273.tif](samples%2Fgeotiffs%2FDJI_0273.tif)
- [DJI_0280.tif](samples%2Fgeotiffs%2FDJI_0280.tif)

### Sample Screenshots (QGIS)
<img src="samples%2Fscreenshots%2Fscreenshot1.png" alt="drawing" width="600"/>
<img src="samples%2Fscreenshots%2Fscreenshot2.png" alt="drawing" width="600"/>

[![IMAGE ALT TEXT HERE](samples%2Fscreenshots%2Fezgif-2-5968847bb5.gif)](https://youtu.be/eaPfwUOpPlo)

----------------------------------------------------------------------------------------------------------------
