#!/Users/dean/Apps/Drone-Footprints/.venv/bin/python3.12

import sys

from osgeo.gdal import UseExceptions, deprecation_warn

# import osgeo_utils.gdalmove as a convenience to use as a script
from osgeo_utils.gdalmove import *  # noqa
from osgeo_utils.gdalmove import main

UseExceptions()

deprecation_warn("gdalmove")
sys.exit(main(sys.argv))
