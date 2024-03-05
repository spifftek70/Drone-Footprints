import argparse
import copy
import json
import logging
import sys


def rewind(geojson, rfc7946=True):
    gj = copy.deepcopy(geojson)
    _check_crs(geojson)
    if isinstance(gj, str):
        return json.dumps(_rewind(json.loads(gj), rfc7946))
    else:
        return _rewind(gj, rfc7946)


def _check_crs(geojson):
    if (
        "crs" in geojson
        and "properties" in geojson["crs"]
        and "name" in geojson["crs"]["properties"]
        and geojson["crs"]["properties"]["name"] != "urn:ogc:def:crs:OGC:1.3:CRS84"
    ):
        logging.warning(
            "Co-ordinates in the input data are assumed to be WGS84 with "
            "(lon, lat) ordering, as per RFC 7946. Input with co-ordinates "
            "using any other CRS may lead to unexpected results."
        )


def _rewind(gj, rfc7946):
    if gj["type"] == "FeatureCollection":
        gj["features"] = list(map(lambda obj: _rewind(obj, rfc7946), gj["features"]))
        return gj
    if gj["type"] == "GeometryCollection":
        gj["geometries"] = list(
            map(lambda obj: _rewind(obj, rfc7946), gj["geometries"])
        )
        return gj
    if gj["type"] == "Feature":
        gj["geometry"] = _rewind(gj["geometry"], rfc7946)
    if gj["type"] in ["Polygon", "MultiPolygon"]:
        return correct(gj, rfc7946)
    return gj


def correct(feature, rfc7946):
    if feature["type"] == "Polygon":
        feature["coordinates"] = rewindRings(feature["coordinates"], rfc7946)
    if feature["type"] == "MultiPolygon":
        feature["coordinates"] = list(
            map(lambda obj: rewindRings(obj, rfc7946), feature["coordinates"])
        )
    return feature


def rewindRings(rings, rfc7946):
    if len(rings) == 0:
        return rings

    # change from rfc7946: True/False to clockwise: True/False here
    # RFC 7946 ordering determines how we deal with an entire polygon
    # but at this point we are switching to deal with individual rings
    # (which in isolation are just clockwise or anti-clockwise)
    clockwise = not (bool(rfc7946))

    rings[0] = rewindRing(rings[0], clockwise)
    for i in range(1, len(rings)):
        rings[i] = rewindRing(rings[i], not (clockwise))
    return rings


def kahan_add(a, b, err):
    if abs(a) >= abs(b):
        err += a - (a + b) + b
    else:
        err += b - (a + b) + a
    return a + b, err


def rewindRing(ring, clockwise):
    """
    Two things to note here:
    1. This isn't an accurate area calculation. We only care whether the value
       is positive or negative so a (faster to calculate) approximation will do.
       Refs https://github.com/mapbox/geojson-rewind/pull/28
    2. We use Kahan-Babuska summation to minimise error when dealing with
       very small polygons.
       Refs https://github.com/mapbox/geojson-rewind/pull/32
    """
    area = 0
    error = 0
    i = 0
    length = len(ring)
    j = length - 1

    while i < length:
        area, error = kahan_add(
            area, (ring[i][0] - ring[j][0]) * (ring[j][1] + ring[i][1]), error
        )
        j = i
        i += 1

    if (area + error >= 0) != clockwise:
        return ring[::-1]

    return ring


def main():
    parser = argparse.ArgumentParser(
        description="Enforce RFC 7946 ring winding order on a GeoJSON file"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Input file, if empty stdin is used",
        type=argparse.FileType("r"),
        default=sys.stdin,
    )
    args = parser.parse_args()

    if args.file.isatty():
        parser.print_help()
        return 0

    sys.stdout.write(rewind(args.file.read()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
