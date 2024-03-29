# Copyright (c) 2024
# Author: Dean Hand
# License: AGPL
# Version: 1.0

from magnetic_field_calculator import MagneticFieldCalculator
import magnetismi.magnetismi as api
from datetime import datetime
from Utils.utils import Color
import Utils.config as config


def find_declination(altitude, focal_length, drone_latitude, drone_longitude, datetime_original):
    str_date = datetime.strptime(datetime_original, '%Y:%m:%d %H:%M:%S')

    if str(str_date.year) > str(2019):
        mag_date = api.dti.date(str_date.year, str_date.month, str_date.day)
        # Find the magnetic declination reference
        model = api.Model(mag_date.year)
        field_point = model.at(lat_dd=drone_latitude, lon_dd=drone_longitude, alt_ft=altitude, date=mag_date)
        declination = field_point.dec
    else:
        calculator = MagneticFieldCalculator()
        model = calculator.calculate(latitude=drone_latitude, longitude=drone_longitude)
        dec = model['field-value']['declination']
        declination = dec['value']

    if altitude < 0 or focal_length <= 0:
        config.pbar.write(Color.RED + ValueError("Altitude and focal length must be positive.") + Color.END)
    return declination
