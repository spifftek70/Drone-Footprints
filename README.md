# Aerial Drone (aka UAV/UAS) Imagery Footprint and GeoTIFF Utility.

> Author: Dean Hand \
> Date Created: 09/07/2019 \
> Name: Drone_Footprints.py

The purpose of this application is to accurately calculate the geographic footprints of individual drone images.
Initially, it extracts specific metadata from the drone image files to determine each image's Field of View (FOV).
Following this, the application performs a series of calculations to establish the geospatial reference of each image.
Subsequently, it adjusts the image to align accurately with the Earth's surface within that FOV, ensuring precise
geolocation without the need for stitching images together. This results in a remarkably efficient process. The final
output includes a orthorectified GeoTiff image file, accompanied by a GeoJSON file detailing:

- The Drone's Flight Path (as a LineString),
- The Drone's Location at the moment the photo was taken (as a Point),
- The Footprints of Individual Images (as Polygons).

----------------------------------------------------------------------------------------------------------------

## Installation

- Ready-made gdal version 3.8.3 or later.
  On Ubuntu, you can install as follows:

```
sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable
sudo apt-get update
sudo apt-get install libgdal-dev
```

Installation via pip

First, you probably want to install into a virtual environment or similar, for example:

```
python3 -m venv .venv # Install with compatible maximum version of Python (Requires-Python >=3.7,<3.11)
source .venv/bin/activate
```

The we install using the requirements list as follows:

```
pip install --no-cache-dir --force-reinstall -r requirements.txt  # this current version of GDAL demands the extra tags
```

### Requirements

Python 3.6 and above

----------------------------------------------------------------------------------------------------------------

## :bulb: Processing Notes and Tips

### Arguments

`-i` - The Default root folder path for the mission you wish to process. Required

`-o` - The output directory path for the GeoJSON file and GeoTiffs. Required

`-w` - Sensor Width (default is 13.2), Not Required (Check your Drones Specs for information)

`-t` - Sensor Height (default is 8.8), Not Required (Check your Drones Specs for information)

`-d` - Magnetic Declination (default is "n"), Not Required.

`-e` - Desired EPSG for output GeoTiffs (default is `4326`) Not Required

`-m` - Path to a Digital Surface Model file to use for more accuracy. Not Required

`-v` - Utilze [open_elevation.com](https://open_elevation.com) for more accuracy. (location dependent). Not Required (
Extends processing time)

`-c` - Format output GeoTiff as a Cloud Optimized GeoTiff (default is "n"). Not Required (Extends processing time)

`-z` - Improves local contrast, which can make details more visible (default is "n"). Not Required (Significantly
extends processing time)

`-l` - Applies lens distortion correction using [lensfun](https://lensfun.github.io) api (default is "y"). Not Required. 

:warning: _you can only select `-m` or `-v` but not both!_
----------------------------------------------------------------------------------------------------------------

### Example Commands

From the `src` directory, run the following commands:

```
python Drone_Footprints.py -i '/Path/To/Dataset1/images' -o '/Path/To/Dataset1/output
```

```
python Drone_Footprints.py -i "/Path/To/Dataset2/images" -o "/Path/To/Dataset2/output" -w 6.16 -d 4.62
```

```
python Drone_Footprints.py -i "/Path/To/Dataset3/images" -o "/Path/To/Dataset3/output" -e 3857
```

```
python Drone_Footprints.py -i "/Path/To/Dataset4/images" -o "/Path/To/Dataset4/output" -e 3857 -c n
```

----------------------------------------------------------------------------------------------------------------

### :warning: Tips for the most accurate results:

## Preflight

1. IMU calibration - Do this once a month
2. Prior to each mission:
    - Calibration the drone's gimbal
    - Calibration the drone's compass
    - Restart the drone
3. Shooting angle - for best results, select `Parallel to Main Path`
4. Gimbal Pitch Angle - for best results, capture at NADIR (aka -90° aka straight down)
5. Wind - Plays havoc on your drone's telemetry, so plan your missions accordingly
6. Immediately after take-off, go STRAIGHT UP. Take a photo immiedately above the homepoint to establish an
   elevation/altitude reference point

### Preprocessing

#### Sort into Datasets

It is highly recommended that you sort the images you want processed into corresponding datasets

- Separate Images by flight mission
- Create a mission folder for each flight mission
- Create an image folder within the mission folder

``````
├── /Path/to/mission_folder
│   ├── images
``````

----------------------------------------------------------------------------------------------------------------

## Postprocessing

- If each image appears to be off-angle by a few degrees, it could be magnetic declination. Rerun them back through, but
  change the `-d` flag and see if that fixes the issue.
  Sometimes electro-magnetic fields can mess witht he aircrafts compass.

#### Outputs locations

It is a good practice to set your output folder `-o` location within your flight mission folder as shown in
[Example Commands](#example-commands), but it is not required.

``````
├── /Path/to/output_folder
│   ├── geotiffs
│   │   ├── image1.tif
│   │   ├── image1.tif
│   ├── geojsons
│   │   ├── M_2024-02-06_11-16.json
│   ├── logfiles
│   │   ├── L_M_2024-03-21_13-49.log
``````

Geojson name is constructed using the date/time of processing like so:

- `M` = mission
- `2024-02-06` = year, month, day
- `11-16` = hour, minute

----------------------------------------------------------------------------------------------------------------

## :boom: Future Works

### Sensor Size checks

- There still remains many empty cells in  [drone_sensors.csv](src%2Fdrone_sensors.csv), but will update it as that
  information becomes available.
- Addition sensor and platform compatibilities

----------------------------------------------------------------------------------------------------------------

## :star: Sample datatsets

### Raw zipped Datasets

- <a href="https://drive.google.com/uc?export=download&id=15WzT_V9unsGuAp_I2M4PaBOkFC2unkq_" download>dataset 1</a>
- <a href="https://drive.google.com/uc?export=download&id=15UVtXf0tpiCSDObSIc62UPv0Kabq_5Ks" download>dataset 2</a>
- <a href="https://drive.google.com/uc?export=download&id=15UivtQ-YccOu4GXBrb7BtEvaeLi-JwW7" download>dataset 3</a>
- <a href="https://drive.google.com/uc?export=download&id=15U6Uvwv2c1s4MeIhNIwW6mPMW4xdwOnO" download>dataset 4</a>
- <a href="https://drive.google.com/uc?export=download&id=15P_G8sRB2AssxfrWul4VAyyBZpRIT2Ys" download>dataset 5</a>
- <a href="https://drive.google.com/uc?export=download&id=15RICP1BA8HvVUVMd4TXiOQ3fswzwMmkY" download>dataset 6</a>

----------------------------------------------------------------------------------------------------------------

## :star: Sample Outputs

### Sample JSON Output

- [M_2024-02-04_07-03.json](samples%2Fgeojson%2FM_2024-02-04_07-03.json)

### Sample GeoTIFFs

- [DJI_0261.tif](samples%2Fgeotiffs%2FDJI_0261.tif)
- [DJI_0267.tif](samples%2Fgeotiffs%2FDJI_0267.tif)
- [DJI_0273.tif](samples%2Fgeotiffs%2FDJI_0273.tif)
- [DJI_0280.tif](samples%2Fgeotiffs%2FDJI_0280.tif)

### Sample Screenshots (QGIS)

<img src="samples%2Fscreenshots%2Fscreenshot1.png" alt="drawing" width="600"/>
<img src="samples%2Fscreenshots%2Fscreenshot2.png" alt="drawing" width="600"/>
<img src="samples%2Fscreenshots%2Fsingle_geotiff_compare.gif" alt="drawing" width="600"/>

[![IMAGE ALT TEXT HERE](samples%2Fscreenshots%2Fezgif-2-5968847bb5.gif)](https://youtu.be/eaPfwUOpPlo)

----------------------------------------------------------------------------------------------------------------

## Drone Compatibility

Tested and works with:

- Phantom 3 & 4 Series
- Mavic 2 Series
- Mavic 3 Multispectral
- EVO II

----------------------------------------------------------------------------------------------------------------

## known Issues

1. Might not work with some Drones due to difference in metadata keys/values. Older collections may not work for the
   same reason.
2. This accuracy of this process is highly dependent on the accuracy of the drone's telemetry. Like all compasses, the
   drone's compass is highly susceptible to electromagnetic interference. Therefore, Datasets collected in areas of high
   magnetic interference (i.e. power lines, large metal structures, etc) will have a higher margin of error.
3. Fisheye lenses are impossible to completely compensate for. Sorry.

----------------------------------------------------------------------------------------------------------------