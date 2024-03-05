"""Command line program for magnetic field calculator API."""

# pylint: disable=C0103
# pylint: disable=R0201
# pylint: disable=W0703

import argparse
import sys

from . import MagneticFieldCalculator

def calculate_field_value(result):
    """Get and print field value."""

    field_value = result['field-value']
    declination = field_value['declination']
    inclination = field_value['inclination']
    total_intensity = field_value['total-intensity']
    north_intensity = field_value['north-intensity']
    east_intensity = field_value['east-intensity']
    vertical_intensity = field_value['vertical-intensity']
    horizontal_intensity = field_value['horizontal-intensity']

    print('FIELD VALUE:')
    print('Declination:', declination['value'], declination['units'])
    print('Inclination:', inclination['value'], inclination['units'])
    print('Total intensity:', total_intensity['value'], total_intensity['units'])
    print('North intensity:', north_intensity['value'], north_intensity['units'])
    print('East intensity:', east_intensity['value'], east_intensity['units'])
    print('Vertical intensity:', vertical_intensity['value'], vertical_intensity['units'])
    print('Horizontal intensity:', horizontal_intensity['value'], horizontal_intensity['units'])

def calculate_secular_variation(result):
    """Get and print secular variation."""

    secular_variation = result['secular-variation']
    declination = secular_variation['declination']
    inclination = secular_variation['inclination']
    total_intensity = secular_variation['total-intensity']
    north_intensity = secular_variation['north-intensity']
    east_intensity = secular_variation['east-intensity']
    vertical_intensity = secular_variation['vertical-intensity']
    horizontal_intensity = secular_variation['horizontal-intensity']

    print('SECULAR VARIATION:')
    print('Declination:', declination['value'], declination['units'])
    print('Inclination:', inclination['value'], inclination['units'])
    print('Total intensity:', total_intensity['value'], total_intensity['units'])
    print('North intensity:', north_intensity['value'], north_intensity['units'])
    print('East intensity:', east_intensity['value'], east_intensity['units'])
    print('Vertical intensity:', vertical_intensity['value'], vertical_intensity['units'])
    print('Horizontal intensity:', horizontal_intensity['value'], horizontal_intensity['units'])

def main():
    """Handle command line program."""

    parser = argparse.ArgumentParser(
        prog=__package__,
        description='Python API for British Geological Survey magnetic field calculator'
    )

    parser.add_argument('--model', action='store', default='wmm')
    parser.add_argument('--revision', action='store', default='current')
    parser.add_argument('--sub-revision', action='store', default=None)
    parser.add_argument('--custom-url', action='store', default=None)

    parser.add_argument('latitude', action='store')
    parser.add_argument('longitude', action='store')

    parser.add_argument('--altitude', action='store', default=None)
    parser.add_argument('--depth', action='store', default=None)
    parser.add_argument('--radius', action='store', default=None)

    parser.add_argument('--year', action='store', default=None)
    parser.add_argument('--date', action='store', default=None)

    parser.add_argument('--username', action='store', default=None)
    parser.add_argument('--password', action='store', default=None)

    args = parser.parse_args()

    try:
        calculator = MagneticFieldCalculator(
            args.model,
            args.revision,
            args.sub_revision,
            args.custom_url
        )

        result = calculator.calculate(
            args.latitude,
            args.longitude,
            args.altitude,
            args.depth,
            args.radius,
            args.year,
            args.date,
            args.username,
            args.password
        )

    except BaseException as err:
        print(str(err), file=sys.stderr)
        sys.exit(1)

    calculate_field_value(result)
    print()
    calculate_secular_variation(result)

if __name__ == '__main__':
    main()
