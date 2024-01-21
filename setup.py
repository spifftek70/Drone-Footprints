from setuptools import setup
import re

with open('drone_fp/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE).group(1)

setup(
    name='drone_fp',
    version=version,
    description='Drone_image footprint calculator',
    long_description="""
    Calculates the imagery footprint on the ground using exiftags in drone images.
    """,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Drone Image Processors',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Programming Language :: Python :: 3.6'
    ],
    packages=['drone_fp'],
    keywords=['drone_fp', 'DJI', 'exif'],
    # url='',
    author='Dean Hand',
    author_email='spifftek@yahoo.com',
    install_requires=[
        'geojson',
        'argparse',
        'geopandas',
        'fiona',
        'pyproj',
        'numpy',
        'utm',
        'geojson_rewind',
        'GDAL',
        'progress',
        'shapely',
        'geometry',
        'quaternion',
        'numpy',
        'progressbar',
        'pyexiftool',
        'geopy',
        'GDAL',
        'gps-time',
        'datetime',
        'rioxarray'
    ],
    zip_safe=False
)
