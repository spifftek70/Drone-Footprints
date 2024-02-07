#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

from gps_time.core import GPSTime
import os
import fnmatch


def find_MTK(some_dir, tags):
    matches = []
    for root, dirnames, filenames in os.walk(some_dir):
        for filename in fnmatch.filter(filenames, '*.MRK'):
            matches.append(os.path.join(root, filename))
    if len(matches) != 0:
        filedata = getdata(matches)
        coords = findAndReplace(filedata, tags)
        return coords
    else:
        return tags


def getdata(tsFile):
    f = open(tsFile[0], "r")
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
        # gpsTime = GPSTime(week_number=abs(week_col[0]), time_of_week=time_col)
        # dateTime = gpsTime.to_datetime()
        # strDateTime = str(dateTime)
        # newDateTime = strDateTime.replace("-", ":")
        # sep = '.'
        # finalDateFormat = newDateTime.split(sep, 1)[0]
        altstr = idx[8]
        altit = altstr.split(',')
        altitude = altit[0]
        rtkdata = dict(Latitude=str_lat, Longitude=str_lon, Altitude=altitude)
        gpsArray.append(rtkdata)
    f.close()
    return gpsArray


def findAndReplace(list_a, list_b):
    if len(list_a) != len(list_b):
        raise ValueError("Both lists must have the same length.")

    integrated_list_b = []

    for item_a, item_b in zip(list_a, list_b):
        # try:
        if "Latitude" in item_a:
            item_b["Composite:GPSLatitude"] = item_a["Latitude"]
        if "Longitude" in item_a:
            item_b["Composite:GPSLongitude"] = item_a["Longitude"]
        if "Altitude" in item_a:
            item_b['Composite:GPSAltitude'] = item_a["Altitude"]
        # except KeyError:
        if "Latitude" in item_a:
            item_b["XMP:GPSLatitude"] = item_a["Latitude"]
        if "Longitude" in item_a:
            item_b["XMP:GPSLongtitude"] = item_a["Longitude"]
        if "Altitude" in item_a:
            item_b["XMP:RelativeAltitude"] = item_a["Altitude"]
        integrated_list_b.append(item_b)
    return integrated_list_b
