#!/usr/bin/env python3

import csv
import io
import json
import os
import re
import subprocess
import urllib.request

upstream_url = 'https://github.com/konstantinstadler/country_converter/'
cwd = os.path.dirname(__file__)

country_data_url = f'{upstream_url}/raw/master/country_converter/country_data.tsv'
country_data_file = os.path.join(cwd, 'countryguess/_countrydata.json')

readme_url = f'{upstream_url}/raw/master/README.md'
readme_file = os.path.join(cwd, 'README.md')


def show_diff(path):
    subprocess.run(['git', '-C', cwd, '--no-pager', 'diff', '--word-diff', path])


def fetch_country_data():
    patches = {
        # https://github.com/konstantinstadler/country_converter/issues/92
        # https://github.com/konstantinstadler/country_converter/commit/6a06051e915e76a9ffc29fe0c08808cf403df99f
        # https://github.com/konstantinstadler/country_converter/blob/master/country_converter/country_data.tsv#L242
        'United Kingdom of Great Britain and Northern Ireland': {
            'iso2': 'GB',
        },
    }

    with urllib.request.urlopen(country_data_url) as request:
        # Read TSV data
        response_string = request.read().decode('utf-8')
        data = csv.DictReader(io.StringIO(response_string), dialect=csv.excel_tab)
        country_list = [
            {
                k.lower(): v
                for k, v in country.items()
            }
            for country in data
        ]

        # Apply patches
        for country in country_list:
            if country['name_official'] in patches:
                for k, v in patches[country['name_official']].items():
                    country[k] = v

        # Overwrite packaged file
        json_data = json.dumps(country_list, indent=2)
        with open(country_data_file, 'w') as f:
            f.write(json_data + '\n')

        show_diff(country_data_file)


def fetch_classifications_from_README():

    def get_classification_schemes():
        with urllib.request.urlopen(readme_url) as request:
            text = request.read().decode('utf-8')
        # with open('../country_converter/README.md') as request:
        #     text = request.read()
            match = re.search(
                r'## Classification schemes.*?(1\..*?)(?:\s*\n\s*){2,}',
                text,
                flags=re.DOTALL | re.MULTILINE,
            )
            if match:
                return match.group(1)
            else:
                raise RuntimeError('Failed to extract classification schemes')

    def replace_classification_schemes():
        readme = open(readme_file, 'r').read()
        schemes_regex = re.compile(
            r'<!-- CLASSIFICATION_SCHEMES.*CLASSIFICATION_SCHEMES -->',
            flags=re.DOTALL | re.MULTILINE,
        )
        schemes_template = (
            '<!-- CLASSIFICATION_SCHEMES (see fetch_data_from_country_converter.py) -->\n'
            '{schemes}\n'
            '<!-- CLASSIFICATION_SCHEMES -->'
        )

        if not re.search(schemes_regex, readme):
            raise RuntimeError('Failed to find classification schemes in README.md')

        readme = re.sub(
            schemes_regex,
            schemes_template.format(schemes=get_classification_schemes()),
            readme,
        )
        with open(readme_file, 'w') as f:
            f.write(readme)

    replace_classification_schemes()

    show_diff(readme_file)


fetch_country_data()
fetch_classifications_from_README()
