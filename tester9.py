# Define the two arrays
array1 = {
    "SourceFile": "/Users/dean/Downloads/pagefarm1a/images/100_0003_0001.JPG",
    "ExifTool:Warning": "[minor] Possibly incorrect maker notes offsets (fix by 1783?)",
    # ... (other key-value pairs)
    "EXIF:GPSLatitude": 38.7163138055556,
    "EXIF:GPSLongitude": -90.517171,
    # ... (other key-value pairs)
}

array2 = [
    [
        {"DateTime": "2019:09:04 15:15:51"},
        {"Latitude": "38.71631383"},
        {"Longitude": "-90.51717100"},
    ],
    # ... (other arrays with DateTime, Latitude, and Longitude)
]

def findAndReplace(array1, array2):
    # Iterate through array2
    for item in array2:
        # Extract DateTime, Latitude, and Longitude from the item in array2
        datetime2 = item[0]["DateTime"]
        latitude2 = item[1]["Latitude"]
        longitude2 = item[2]["Longitude"]

        # Check if DateTime in array1 matches DateTime in array2
        if array1.get("EXIF:DateTimeOriginal") == datetime2:
            # If there is a match, replace GPSLatitude and GPSLongitude in array1
            array1["EXIF:GPSLatitude"] = float(latitude2)
            array1["EXIF:GPSLongitude"] = float(longitude2)
    # return array1

# Print the updated array1
    print(array1)
    exit()
