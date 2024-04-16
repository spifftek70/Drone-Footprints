#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

from tqdm import tqdm

epsg_code = 4326
rtk = False
correct_magnetic_declinaison = False
utm_zone = ""
hemisphere = ""
cog = False
dtm_path = ""
global_elevation = False
global_target_delta = 0.0
image_equalize = False
im_file_name = ""
relative_altitude = 0.0
absolute_altitude = 0.0
dsm = None
drone_properties = None
lense_correction = True
center_distance = 0.0
nodejgraphical_interface = False
pbar = tqdm(total=0, position=1, bar_format='{desc}')
crs_utm = f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"


def init():
    global epsg_code, rtk, correct_magnetic_declinaison, utm_zone, hemisphere, cog, dtm_path, global_elevation, crs_utm, global_target_delta, pbar, image_equalize, im_file_name, relative_altitude, absolute_altitude, dsm, drone_properties, center_distance, lense_correction, nodejgraphical_interface
    correct_magnetic_declinaison = False
    epsg_code = 4326
    utm_zone = ""
    hemisphere = ""
    rtk = False
    cog = False
    dtm_path = ""
    center_distance = 0.0
    global_elevation = False
    global_target_delta = 0.0
    image_equalize = False
    im_file_name = ""
    relative_altitude = 0.0
    absolute_altitude = 0.0
    dsm = None
    drone_properties = None
    lense_correction = True
    nodejgraphical_interface = False
    pbar = tqdm(total=0, position=1, bar_format='{desc}')
    crs_utm = f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"


def update_epsg(a):
    global epsg_code
    epsg_code = a


def update_center_distance(a):
    global center_distance
    center_distance = a


def update_nodejs_graphical_interface(n):
    global nodejgraphical_interface
    nodejgraphical_interface = n


def update_correct_magnetic_declinaison(b):
    global correct_magnetic_declinaison
    correct_magnetic_declinaison = b


def update_cog(f):
    global cog
    cog = f


def update_rtk(e):
    global rtk
    rtk = e


def update_dtm(u):
    global dtm_path
    dtm_path = u


def update_dsm_open(x):
    global dsm
    dsm = x


def update_elevation(h):
    global global_elevation
    global_elevation = h


def update_target_delta(l):
    global global_target_delta
    global_target_delta = l


def update_equalize(u):
    global image_equalize
    image_equalize = u


def update_file_name(q):
    global im_file_name
    im_file_name = q


def update_rel_altitude(q):
    global relative_altitude
    relative_altitude = q


def update_lense(v):
    global lense_correction
    lense_correction = v


def update_abso_altitude(q):
    global absolute_altitude
    absolute_altitude = q


def update_drone_properties(s):
    global drone_properties
    drone_properties = s


def update_utm_data(c, d):
    global utm_zone, hemisphere, crs_utm
    if not c or not d:
        raise ValueError("Invalid UTM data.")
    utm_zone = c
    hemisphere = d
    crs_utm = f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"


init()
