#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

from tqdm import tqdm

epsg_code = 4326
rtk = False
decl = False
utm_zone = ""
hemisphere = ""
cog = False
dtm_path = ""
global_elevation = False
global_target_delta = 0.0
image_equalize = False
im_file_name = ""
rel_altitude = 0.0
abso_altitude = 0.0
dsm = None
pbar = tqdm(total=0, position=1, bar_format='{desc}')
crs_utm = f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"


def init():
    global epsg_code, rtk, decl, utm_zone, hemisphere, cog, dtm_path, global_elevation, crs_utm, global_target_delta, pbar, image_equalize, im_file_name, rel_altitude, abso_altitude, dsm
    decl = False
    epsg_code = 4326
    utm_zone = ""
    hemisphere = ""
    rtk = False
    cog = False
    dtm_path = ""
    global_elevation = False
    global_target_delta = 0.0
    image_equalize = False
    im_file_name = ""
    rel_altitude = 0.0
    abso_altitude = 0.0
    dsm = None
    pbar = tqdm(total=0, position=1, bar_format='{desc}')
    crs_utm = f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"


def update_epsg(a):
    global epsg_code
    epsg_code = a


def update_decl(b):
    global decl
    decl = b


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
    global rel_altitude
    rel_altitude = q


def update_abso_altitude(q):
    global abso_altitude
    abso_altitude = q


def update_utm_data(c, d):
    global utm_zone, hemisphere, crs_utm
    if not c or not d:
        raise ValueError("Invalid UTM data.")
    utm_zone = c
    hemisphere = d
    crs_utm = f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"


init()
