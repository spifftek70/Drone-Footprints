#  Copyright (c) 2024.
#  __author__ = "Dean Hand"
#  __license__ = "AGPL"
#  __version__ = "1.0"

global epsg_code


def init():
    global epsg_code
    epsg_code = 4326


def update_epsg(a):
    global epsg_code
    epsg_code = a
