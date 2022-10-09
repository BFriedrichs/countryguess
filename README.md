**countryguess** looks up country information by fuzzy name matching. It tries
to be lean (but not mean) and fast: All dependencies are in the Python Standard
Library and country data is loaded lazily on demand.

### Usage

`guess_country()` uses the default country data that is packaged.

    >>> from countryguess import guess_country
    >>> guess_country("britain")
    {
        'name_short': 'United Kingdom',
        'name_official': 'United Kingdom of Great Britain and Northern Ireland',
        'iso2': 'GB',
        'iso3': 'GBR',
        ...
    }
    >>> guess_country("no such country")
    None
    >>> guess_country("no such country", default="Oh, well.")
    'Oh, well.'
    >>> guess_country("PoRtUgAl", attribute="iso2")
    'PT'
    >>> guess_country("TW", attribute="name_official")  # 2-letter code
    'Republic of China'
    >>> guess_country("TWN", attribute="name_short")    # 3-letter code
    'Taiwan'

You can also create a `CountryData` instance yourself to provide your own
country data.

    >>> from countryguess import CountryData
    >>> countries = CountryData("path/to/countries.json")
    >>> countries["vIeTnAm"]
    {'name_short': 'Vietnam', ...}
    >>> countries["vn"]
    {'name_short': 'Vietnam', ...}
    >>> countries["asdf"]
    KeyError: 'asdf'
    >>> countries.get("asdf")
    None
    >>> countries.get("kuwait")
    {'name_short': 'Kuwait', ...}

On `CountryData` instances, every key in the JSON data is accessible as a
method.

    >>> countries.name_official("portugal")
    'Portuguese Republic'
    >>> countries.continent("vanuatu")
    'Oceania'

### Country Lookup

Countries are identified by name, 2-letter code
([ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2)) or 3-letter code
([ISO 3166-3](https://en.wikipedia.org/wiki/ISO_3166-3)). All identifiers are
matched case-insensitively.

Names are matched with regular expressions that are stored in the JSON data. If
that fails, fuzzy matching against ``name_short`` and ``name_official`` is done
with [difflib](https://docs.python.org/3/library/difflib.html).

### Country Data

Country information is read from a JSON file. One is shipped with the package,
but you can also provide your own to the `CountryData` class as described
above. The information in the default file was gratefully extracted from
[country-converter](https://pypi.org/project/country-converter/). (Many thanks!)

The country data file must contain a list of JSON objects. Each object
represents a country that must contain at least the following keys:

- `name_short`
- `name_official`
- `iso2`
- `iso3`
- `regex`

### Command Line Interface

**countryguess** comes with a simple CLI with the same name. It takes one or two
arguments:

    $ countryguess oman
    {
        "name_short": "Oman",
        "name_official": "Sultanate of Oman",
        ...
    }
    $ countryguess 'puerto ricco' name_official
    Puerto Rico

### Contributing

All kinds of bug reports, feature requests and suggestions are welcome!
