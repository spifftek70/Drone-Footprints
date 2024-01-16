from gps_time.core import GPSTime
import os
import fnmatch


def find_MTK(some_dir, tags):
    matches = []
    for root, dirnames, filenames in os.walk(some_dir):
        for filename in fnmatch.filter(filenames, '*.MRK'):
            matches.append(os.path.join(root, filename))
    if len(matches) == 0:
        return tags
    else:
        filedata = getdata(matches)
        coords = findAndReplace(tags, filedata)
        return coords


def getdata(matches):
    f = open(matches[0], "r")
    lines = f.readlines()
    gpsArray = []
    for x in lines:
        idx = [x for x in x.split('\t')]
        row_col = idx[0]
        time_col = idx[1]
        ini_list = idx[2]
        sec_list = ini_list.strip('][').split(', ')
        week_col = list(map(int, sec_list))
        lat_col = idx[6]
        lon_col = idx[7]
        str_lat = lat_col.split(',', 1)[0]
        str_lon = lon_col.split(',', 1)[0]
        coord = [float(str_lat), float(str_lon)]
        gpsTime = GPSTime(week_number=int(week_col[0]), time_of_week=time_col)
        dateTime = gpsTime.to_datetime()
        strDateTime = str(dateTime)
        newDateTime = strDateTime.replace("-", ":")
        sep = '.'
        finalDateFormat = newDateTime.split(sep, 1)[0]
        date_time = {}
        LatDic = {}
        LngDic = {}
        LatDic["Latitude"] = str_lat
        LngDic["Longitude"] = str_lon
        date_time["DateTime"] = finalDateFormat
        gpsArray.append([date_time, LatDic, LngDic])
    f.close()
    return gpsArray


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
    return array1
