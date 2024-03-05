"""Adapted from C code as distributed per https://www.ngdc.noaa.gov/geomag/WMM/DoDWMM.shtml."""
import argparse
import datetime as dti
import logging
import math
from dataclasses import dataclass

from magnetismi import ABS_LAT_DD_ANY_ARCITC, DEFAULT_MAG_VAR, FEET_TO_KILOMETER, fractional_year_from_date, log
from magnetismi.model.cof import MODEL_FROM_YEAR, YEARS_COVERED, Coefficients


@dataclass
class MagneticVector:
    dec: float
    dip: float
    ti: float
    bh: float
    bx: float
    by: float
    bz: float
    lat: float
    lon: float
    alt: float
    time: float


class Model:
    """Yes."""

    def __init__(self, year: int):
        """Maybe."""
        self.coefficients = Coefficients(year)

    def at(self, lat_dd: float, lon_dd: float, alt_ft: float = 0.0, date: dti.date = dti.date.today()):
        """Get the values at ..."""
        if date.year not in YEARS_COVERED or self.coefficients.model['model_id'] != MODEL_FROM_YEAR[date.year]:
            raise ValueError(f'Model ID ({self.coefficients.model["model_id"]}) is not covering year ({date.year})')

        time = fractional_year_from_date(date)  # date('Y') + date('z')/365
        alt = alt_ft * FEET_TO_KILOMETER

        model = self.coefficients.model
        coeffs = self.coefficients
        dt = time - model['epoch']
        glat = lat_dd
        glon = lon_dd
        rlat = math.radians(glat)
        rlon = math.radians(glon)
        srlon = math.sin(rlon)
        srlat = math.sin(rlat)
        crlon = math.cos(rlon)
        crlat = math.cos(rlat)
        srlat_2 = srlat * srlat
        crlat_2 = crlat * crlat
        coeffs.sp[1] = srlon
        coeffs.cp[1] = crlon

        # watch these:
        r = ca = sa = 1.0
        st = ct = 0.0

        # Convert from geodetic to spherical coordinates
        q = math.sqrt(coeffs.a2 - coeffs.c2 * srlat_2)
        q1 = alt * q
        q2 = ((q1 + coeffs.a2) / (q1 + coeffs.b2)) * ((q1 + coeffs.a2) / (q1 + coeffs.b2))
        ct = srlat / math.sqrt(q2 * crlat_2 + srlat_2)
        st = math.sqrt(1.0 - (ct * ct))
        r2 = (alt * alt) + 2.0 * q1 + (coeffs.a4 - coeffs.c4 * srlat_2) / (q * q)
        r = math.sqrt(r2)
        d = math.sqrt(coeffs.a2 * crlat_2 + coeffs.b2 * srlat_2)
        ca = (alt + d) / r
        sa = coeffs.c2 * crlat * srlat / (r * d)

        for m in range(2, coeffs.maxord + 1):
            coeffs.sp[m] = coeffs.sp[1] * coeffs.cp[m - 1] + coeffs.cp[1] * coeffs.sp[m - 1]
            coeffs.cp[m] = coeffs.cp[1] * coeffs.cp[m - 1] - coeffs.sp[1] * coeffs.sp[m - 1]

        aor = coeffs.re / r
        ar = aor * aor
        br = bt = bp = bpp = 0.0
        for n in range(1, coeffs.maxord + 1):
            ar *= aor

            m = 0
            D4 = n + m + 1  # (n+m+D3)/D3 with D3 = 1
            while D4 > 0:  # for (m=0,D3=1,D4=(n+m+D3)/D3;D4>0;D4--,m+=D3):

                # Compute unnormalized associated Legendre polynomials and derivatives from recursion formula
                if n == m:
                    coeffs.p[m][n] = st * coeffs.p[m - 1][n - 1]
                    coeffs.dp[m][n] = st * coeffs.dp[m - 1][n - 1] + ct * coeffs.p[m - 1][n - 1]
                elif n == 1 and m == 0:
                    coeffs.p[m][n] = ct * coeffs.p[m][n - 1]
                    coeffs.dp[m][n] = ct * coeffs.dp[m][n - 1] - st * coeffs.p[m][n - 1]
                elif n > 1 and n != m:
                    if m > n - 2:
                        coeffs.p[m][n - 2] = 0
                        coeffs.dp[m][n - 2] = 0.0
                    coeffs.p[m][n] = ct * coeffs.p[m][n - 1] - coeffs.k[m][n] * coeffs.p[m][n - 2]
                    coeffs.dp[m][n] = (
                        ct * coeffs.dp[m][n - 1] - st * coeffs.p[m][n - 1] - coeffs.k[m][n] * coeffs.dp[m][n - 2]
                    )

                # Time adjust the Gauss coefficients
                coeffs.tc[m][n] = coeffs.c[m][n] + dt * coeffs.cd[m][n]
                if m != 0:
                    coeffs.tc[n][m - 1] = coeffs.c[n][m - 1] + dt * coeffs.cd[n][m - 1]

                # Accumulate terms of the spherical harmonic expansions
                par = ar * coeffs.p[m][n]

                temp1 = coeffs.tc[m][n] * coeffs.cp[m]
                temp2 = coeffs.tc[m][n] * coeffs.sp[m]
                if n != 0:
                    temp1 += coeffs.tc[n][m - 1] * coeffs.sp[m]
                    temp2 -= coeffs.tc[n][m - 1] * coeffs.cp[m]

                bt -= ar * temp1 * coeffs.dp[m][n]
                bp += coeffs.fm[m] * temp2 * par
                br += coeffs.fn[n] * temp1 * par

                # Special case: North/South geographic poles
                if st == 0.0 and m == 1:
                    coeffs.pp[n] = (
                        coeffs.pp[n - 1] if n == 1 else ct * coeffs.pp[n - 1] - coeffs.k[m][n] * coeffs.pp[n - 2]
                    )
                    parp = ar * coeffs.pp[n]
                    bpp += coeffs.fm[m] * temp2 * parp

                D4 -= 1
                m += 1

        bp = bpp if st == 0.0 else bp / st

        # Rotate magnetic vector components from spherical to geodetic coordinates
        bx = -bt * ca - br * sa
        by = bp
        bz = bt * sa - br * ca

        # Compute declination (dec), inclination (dip), and total intensity (ti)
        bh = math.sqrt((bx * bx) + (by * by))
        ti = math.sqrt((bh * bh) + (bz * bz))
        dec = math.degrees(math.atan2(by, bx))
        dip = math.degrees(math.atan2(bz, bh))

        # Either compute magnetic grid variation if the current geodetic position is in the arctic or antarctic
        #   i.e. glat > +55 degrees or glat < -55 degrees
        # or, set magnetic grid variation to marker value
        gv = DEFAULT_MAG_VAR
        if math.fabs(glat) >= ABS_LAT_DD_ANY_ARCITC:
            if glat > 0.0:
                gv = dec - glon if glon >= 0.0 else dec + math.fabs(glon)
            if glat < 0.0:
                gv = dec + glon if glon >= 0.0 else dec - math.fabs(glon)
            while gv > +180.0:
                gv = gv - 360.0
            while gv < -180.0:
                gv = gv + 360.0

        return MagneticVector(
            dec=dec, dip=dip, ti=ti, bh=bh, bx=bx, by=by, bz=bz, lat=lat_dd, lon=lon_dd, alt=alt_ft, time=time
        )


def calc(options: argparse.Namespace) -> int:
    """Drive the calculation."""
    quiet = options.quiet
    verbose = options.verbose
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    lat_dd = options.lat_dd
    lon_dd = options.lon_dd
    alt_ft = options.alt_ft
    date = options.date_in
    start_time = dti.datetime.now(tz=dti.timezone.utc)
    log.info(f'starting calculation at {date} for {alt_ft=}, {lat_dd=}, and {lon_dd=}')
    model = Model(date.year)
    log.info(f'- fetched model with id {model.coefficients.model["model_id"]} ')
    data = model.at(lat_dd=lat_dd, lon_dd=lon_dd, alt_ft=alt_ft, date=date)
    log.info(f'- result for {data.time=}, {data.alt=}, {data.lat=}, and {data.lon=}:')
    log.info(f'  Declination D = {data.dec}, inclination I = {data.dip} in degrees')
    log.info(f'  North X = {data.bx}, East Y = {data.by}, Down Z = {data.bz} component in nT')
    log.info(f'  Horizontal H = {data.bh}, total T = {data.ti} intensity in nT')
    end_time = dti.datetime.now(tz=dti.timezone.utc)
    log.info(f'calculation complete after {(end_time - start_time).total_seconds()} seconds')
    print(f'INP(time={data.time}, alt={data.alt}, lat={data.lat}, long={data.lon})')
    print(f'OUT(D={data.dec}, I={data.dip}, X={data.bx}, Y={data.by}, Z={data.bz}, H={data.bh}, T={data.ti})')
    return 0
