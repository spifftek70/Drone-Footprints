"""Module for magnetic field calculator API."""

# pylint: disable=R0903
# pylint: disable=R0913
# pylint: disable=R0914

import base64

from urllib.error import HTTPError, URLError
import urllib.parse
import urllib.request

import json

class RequestError(ValueError):
    """Exception for wrong request."""

class ApiError(ValueError):
    """Exception for API error."""

class MagneticFieldCalculator:
    """Class for magnetic field calculator API."""

    main_url = 'http://geomag.bgs.ac.uk/web_service/GMModels'
    custom_url = None

    model = None
    revision = None
    sub_revision = None

    def __init__(self, model='wmm', revision='current', sub_revision=None, custom_url=None):
        """
        Initialize the class.

        Details about web service:
        -- https://geomag.bgs.ac.uk/data_service/models_compass/wmm_calc.html
        -- https://geomag.bgs.ac.uk/web_service/GMModels/help/general
        -- https://geomag.bgs.ac.uk/web_service/GMModels/help/models
        -- https://geomag.bgs.ac.uk/web_service/GMModels/help/parameters

        Input:
        -- model -- Model to be used.
        -- revision -- Revision to be used.
        -- sub_revision -- Sub revision to be used.
        -- custom_url -- Custom URL of the API.
        --
        """

        self.model = model
        self.revision = revision
        self.sub_revision = sub_revision
        self.custom_url = custom_url

    def calculate(
            self,

            latitude,
            longitude,

            altitude=None,
            depth=None,
            radius=None,

            year=None,
            date=None,

            username=None,
            password=None
    ):
        """
        Calculate magnetic field using the API.

        Input:
        -- latitude -- The latitude where magnetic values are requested.
        -- longitude -- The longitude where magnetic values are requested.
        -- altitude -- The height above mean sea level where magnetic values are requested.
        -- depth -- The depth below mean sea level.
        -- radius -- The radial distance from the centre of the earth.
        -- year -- The year for which magnetic field values are requested.
        -- date -- The date when magnetic field values are requested.
        -- username -- Username for HTTP auth for protected models.
        -- password -- Password for HTTP auth for protected models.
        For more details see <http://geomag.bgs.ac.uk/web_service/GMModels/help/parameters>.

        Output:
        -- model -- Used model.
        -- model_revision -- Used model revision, including sub revision.
        -- date -- Used date.
        -- coordinates -- Used coordinates.
        -- -- latitude -- Used latitude.
        -- -- longitude -- Used longitude.
        -- -- altitude / depth / geocentric-radius -- Used height.
        -- field-value -- Field value.
        -- -- declination -- Declination.
        -- -- inclination -- Inclination.
        -- -- total-intensity -- Total intensity.
        -- -- north-intensity -- North intensity.
        -- -- east-intensity -- East intensity.
        -- -- vertical-intensity -- Vertical intensity.
        -- -- horizontal-intensity -- Horizontal intensity.
        -- secular-variation -- Secular variation.
        -- -- declination -- Declination.
        -- -- inclination -- Inclination.
        -- -- total-intensity -- Total intensity.
        -- -- north-intensity -- North intensity.
        -- -- east-intensity -- East intensity.
        -- -- vertical-intensity -- Vertical intensity.
        -- -- horizontal-intensity -- Horizontal intensity.
        Output is returned as dictionary. Some output properties will have `units`
        and `value` sub properties. Output format will depend on used input,
        specially for height and date.
        """

        request = {
            'latitude': latitude,
            'longitude': longitude,

            'altitude': altitude,
            'depth': depth,
            'radius': radius,

            'year': year,
            'date': date,

            'format': 'json',
        }

        parameters = urllib.parse.urlencode({k: v for k, v in request.items() if v is not None})

        for base_url in self.custom_url, self.main_url:
            if base_url:
                try:
                    url = base_url \
                    + '/' + self.model \
                    + '/' + self.revision \
                    + ('v' + self.sub_revision if self.sub_revision else '') \
                    + '?' + parameters

                    request = urllib.request.Request(url)

                    if username and password:
                        auth = base64.b64encode(b'%s:%s' % (username, password))
                        request.add_header("Authorization", "Basic %s" % auth)

                    response = urllib.request.urlopen(url).read()
                    result = json.loads(response.decode('utf-8'))

                    break

                except (URLError, ValueError) as err:
                    error = err

        try:
            return result['geomagnetic-field-model-result']

        except (NameError, KeyError):
            # pylint: disable=E1101
            # pylint: disable=R1720

            if isinstance(error, HTTPError):
                if error.code == 400:
                    raise RequestError(error.read().decode('utf-8').strip('\n'))
                else:
                    raise ApiError(str(error))

            elif isinstance(error, URLError):
                raise ApiError(str(error))

            elif isinstance(error, ValueError):
                raise RequestError(str(error))

            raise ValueError('Can\'t get result because of wrong request or API error')

            # pylint: enable=R1720
            # pylint: enable=E1101
