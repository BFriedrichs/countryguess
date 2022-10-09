#!/usr/bin/env python3

import csv
import io
import json
import os
import subprocess
import urllib.request

csv_data_url = (
    'https://github.com/konstantinstadler/country_converter/'
    'raw/master/country_converter/country_data.tsv'
)

json_file = os.path.join(
    os.path.dirname(__file__),
    'countryguess/_countrydata.json',
)

patches = {
    # https://github.com/konstantinstadler/country_converter/issues/92
    # https://github.com/konstantinstadler/country_converter/commit/6a06051e915e76a9ffc29fe0c08808cf403df99f
    'United Kingdom of Great Britain and Northern Ireland': {
        'iso2': 'GB',
    },
}

with urllib.request.urlopen(csv_data_url) as csv_request:
    # Read TSV data
    response_string = csv_request.read().decode('utf-8')
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
    with open(json_file, 'w') as f:
        f.write(json_data + '\n')

    # Show differences
    subprocess.run(['git', 'diff', json_file])
