import argparse
import json
import re
import sys

from . import guess_country


def parse_args(argv):
    argparser = argparse.ArgumentParser()

    argparser.add_argument(
        'COUNTRY',
        help='Fuzzy name, 3-letter or 3-letter country code',
    )
    argparser.add_argument(
        'ATTRIBUTE',
        nargs='?',
        default=None,
        help=(
            'Print only specific country attribute; if not provided, '
            'print all attributes as JSON'
        ),
    )
    return argparser.parse_args(argv)


def run():
    args = parse_args(sys.argv[1:])

    try:
        info = guess_country(args.COUNTRY, attribute=args.ATTRIBUTE)

    except AttributeError:
        print(f'No such attribute: {args.ATTRIBUTE}', file=sys.stderr)

    else:
        if isinstance(info, dict):
            print(json.dumps(info, indent=4, default=_serialize_object))
        elif info is not None:
            print(_serialize_object(info))
        else:
            print(f'No such country: {args.COUNTRY}', file=sys.stderr)


def _serialize_object(obj):
    if isinstance(obj, re.Pattern):
        return obj.pattern
    else:
        return str(obj)
