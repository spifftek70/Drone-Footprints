#!/Users/dean/Apps/Drone-Footprints/.venv/bin/python3.12

import sys

from osgeo.gdal import UseExceptions, deprecation_warn

# import osgeo_utils.pct2rgb as a convenience to use as a script
from osgeo_utils.pct2rgb import *  # noqa
from osgeo_utils.pct2rgb import main

UseExceptions()

deprecation_warn("pct2rgb")
sys.exit(main(sys.argv))
