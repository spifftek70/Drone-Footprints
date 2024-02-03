# Aerial Drone (aka UAV/UAS) Imagery Footprint and GeoTIFF Utility. 

Name: drone_fp.py
>The purpose of this module is to calculate imagery footprints or field of view (FOV).  This is 
>accomplished by using exiftags from drone images to generate polygons for each image.  The output is 
>a GeoJSON file with:
>* Drone Flightpath (LineString)
>* Drone Location at Image Location (Point)
>* Individual Image Footprints (Polygons)
----------------------------------------------------------------------------------------------------------------

Author: Dean Hand <br>
Date Created: 09/07/2019<br>

----------------------------------------------------------------------------------------------------------------
## Input<br/>
`-i` - The Default root folder for the mission you wish to process.  Required

## Output<br/>
`-o` - The output directory for the GeoJSON file. Required

`-w` - Sensor Width (default is 13.2) Not Required (Check your Drones Specs for information)

`-d` - Sensor Height (default is 8.8) Not Required (Check your Drones Specs for information)

## Example Command
`python Drone_Footprints.py -i '/Users/<user>/Downloads/flight2/images' -o '/Users/<user>/Downloads/flight2/output'

## Sample Dataset
A sample dataset can be found [here](https://drive.google.com/drive/u/1/folders/1Hwrhi-eK_-i8R2NQ3churBls-i4aAXg9)

## Sample JSON Output 
A sample of the json output can be found [here](https://drive.google.com/open?id=1RhSlY9KL2NYpnnVyNqI5c6cLzC0YWMTj)
