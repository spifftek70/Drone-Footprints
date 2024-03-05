import calendar
import datetime as dti
import logging
import os
import pathlib
from typing import List, no_type_check

# [[[fill git_describe()]]]
__version__ = '2022.10.9+parent.8ba013b1'
# [[[end]]] (checksum: d66c693c48c69dde4fe7f21697cf846d)
__version_info__ = tuple(
    e if '-' not in e else e.split('-')[0] for part in __version__.split('+') for e in part.split('.') if e != 'parent'
)
__all__: List[str] = []

ABS_LAT_DD_ANY_ARCITC = 55.0

APP_NAME = 'Magnetism (Finnish: magnetismi) - another opinionated World Magnetic Model calculator.'
APP_ALIAS = 'magnetismi'
APP_ENV = 'MAGNETISMI'
DEBUG = bool(os.getenv(f'{APP_ENV}_DEBUG', ''))
VERBOSE = bool(os.getenv(f'{APP_ENV}_VERBOSE', ''))
QUIET = False
STRICT = bool(os.getenv(f'{APP_ENV}_STRICT', ''))
DEFAULT_MAG_VAR = -999.0
ENCODING = 'utf-8'
ENCODING_ERRORS_POLICY = 'ignore'
FEET_TO_KILOMETER = 1.0 / 3280.8399
DEFAULT_CONFIG_NAME = '.magnetismi.json'
DEFAULT_LF_ONLY = 'YES'
log = logging.getLogger()  # Module level logger is sufficient
LOG_FOLDER = pathlib.Path('logs')
LOG_FILE = f'{APP_ALIAS}.log'
LOG_PATH = pathlib.Path(LOG_FOLDER, LOG_FILE) if LOG_FOLDER.is_dir() else pathlib.Path(LOG_FILE)
LOG_LEVEL = logging.INFO

TS_FORMAT_LOG = '%Y-%m-%dT%H:%M:%S'
TS_FORMAT_PAYLOADS = '%Y-%m-%d %H:%M:%S.%f UTC'


@no_type_check
def formatTime_RFC3339(self, record, datefmt=None):  # noqa
    """HACK A DID ACK we could inject .astimezone() to localize ..."""
    return dti.datetime.fromtimestamp(record.created, dti.timezone.utc).isoformat()  # pragma: no cover


@no_type_check
def init_logger(name=None, level=None):
    """Initialize module level logger"""
    global log  # pylint: disable=global-statement

    log_format = {
        'format': '%(asctime)s %(levelname)s [%(name)s]: %(message)s',
        'datefmt': TS_FORMAT_LOG,
        # 'filename': LOG_PATH,
        'level': LOG_LEVEL if level is None else level,
    }
    logging.Formatter.formatTime = formatTime_RFC3339
    logging.basicConfig(**log_format)
    log = logging.getLogger(APP_ENV if name is None else name)
    log.propagate = True


def date_from_fractional_year(date: float) -> dti.date:
    """Going back ..."""
    y_int = int(date)
    rest_y_float = date - y_int
    days_in_year = 365 + calendar.isleap(y_int)
    rest_d_float = round(rest_y_float * days_in_year, 1)
    if rest_d_float:
        day_counts = [c for _, c in (calendar.monthrange(y_int, m) for m in range(1, 12 + 1))]
        day_cum = [day_counts[0]] + [0] * 11
        for m, c in enumerate(day_counts[1:], start=2):
            day_cum[m - 1] = day_cum[m - 2] + c
        m_int = 1  # Well, not really, but, ... happy linter
        for m, c in enumerate(day_cum, start=1):
            if c < rest_d_float:
                continue
            m_int = m
            break

        d_int = int(rest_d_float - day_cum[m_int - 2])
    else:
        m_int, d_int = 1, 1
    return dti.date(y_int, m_int, d_int)


def fractional_year_from_date(date: dti.date) -> float:
    """... and forth."""
    days_in_year = float(365 + calendar.isleap(date.year))
    return date.year + ((date - dti.date(date.year, 1, 1)).days / days_in_year)


init_logger(name=APP_ENV, level=logging.DEBUG if DEBUG else None)
