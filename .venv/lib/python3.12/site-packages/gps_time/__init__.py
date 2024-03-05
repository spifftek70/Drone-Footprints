__version__ = "2.8.8"
__copyright__ = "Copyright (C) 2020 The Aerospace Corporation"

import logging
from .logutils import (AlignedColorFormatter, BasicColorTheme,
                       display_distro_statement, )

logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
theme = BasicColorTheme()
formatter = AlignedColorFormatter(theme)
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.setLevel(logging.ERROR)

logger.debug("Running gps_time version " + __version__)
logger.debug(__copyright__)

from .core import GPSTime  # noqa: F401,E402
