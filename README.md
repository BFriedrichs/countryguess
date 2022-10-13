**countryguess** looks up country information by fuzzy name matching. It tries
to be lean (but not mean) and fast: All dependencies are in the Python Standard
Library and country data is loaded lazily on demand.

Code: [Codeberg](https://codeberg.org/plotski/countryguess)
Package: [PyPI](https://pypi.org/project/countryguess)

### Usage

`guess_country()` uses the default country data that is packaged.

```python
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
```

You can also create a `CountryData` instance yourself to provide your own
country data.

```python
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
```

On `CountryData` instances, every key in the JSON data is accessible as a
method.

```python
>>> countries.name_official("portugal")
'Portuguese Republic'
>>> countries.continent("vanuatu")
'Oceania'
```

### Country Lookup

Countries are identified by name, 2-letter code
([ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)) or
3-letter code
([ISO 3166-1 alpha-3](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3)). All
identifiers are matched case-insensitively.

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

#### Packaged Classification Schemes

The following classification schemes are available in the included country data.

<!-- CLASSIFICATION_SCHEMES (see fetch_data_from_country_converter.py) -->
1.  ISO2 (ISO 3166-1 alpha-2)
2.  ISO3 (ISO 3166-1 alpha-3)
3.  ISO - numeric (ISO 3166-1 numeric)
4.  UN numeric code (M.49 - follows to a large extend ISO-numeric)
5.  A standard or short name
6.  The "official" name
7.  Continent
8.  UN region
9.  [EXIOBASE](http://exiobase.eu/) 1 classification
10. [EXIOBASE](http://exiobase.eu/) 2 classification
11. [EXIOBASE](http://exiobase.eu/) 3 classification
12. [WIOD](http://www.wiod.org/home) classification
13. [Eora](http://www.worldmrio.com/)
14. [OECD](http://www.oecd.org/about/membersandpartners/list-oecd-member-countries.htm)
    membership (per year)
15. [MESSAGE](http://www.iiasa.ac.at/web/home/research/researchPrograms/Energy/MESSAGE-model-regions.en.html)
    11-region classification
16. [IMAGE](https://models.pbl.nl/image/index.php/Welcome_to_IMAGE_3.0_Documentation)
17. [REMIND](https://www.pik-potsdam.de/en/institute/departments/transformation-pathways/models/remind)
18. [UN](http://www.un.org/en/members/) membership (per year)
19. [EU](https://ec.europa.eu/eurostat/statistics-explained/index.php/Glossary:EU_enlargements)
    membership (including EU12, EU15, EU25, EU27, EU27_2007, EU28)
20. [EEA](https://ec.europa.eu/eurostat/statistics-explained/index.php/Glossary:European_Economic_Area_(EEA))
    membership
21. [Schengen](https://en.wikipedia.org/wiki/Schengen_Area) region
22. [Cecilia](https://cecilia2050.eu/system/files/De%20Koning%20et%20al.%20%282014%29_Scenarios%20for%202050_0.pdf)
    2050 classification
23. [APEC](https://en.wikipedia.org/wiki/Asia-Pacific_Economic_Cooperation)
24. [BRIC](https://en.wikipedia.org/wiki/BRIC)
25. [BASIC](https://en.wikipedia.org/wiki/BASIC_countries)
26. [CIS](https://en.wikipedia.org/wiki/Commonwealth_of_Independent_States)
    (as by 2019, excl. Turkmenistan)
27. [G7](https://en.wikipedia.org/wiki/Group_of_Seven)
28. [G20](https://en.wikipedia.org/wiki/G20) (listing all EU member
    states as individual members)
29. [FAOcode](http://www.fao.org/faostat/en/#definitions) (numeric)
30. [GBDcode](http://ghdx.healthdata.org/) (numeric - Global Burden of
    Disease country codes)
31. [IEA](https://www.iea.org/countries) (World Energy Balances 2021)
32. [DACcode](https://www.oecd.org/dac/financing-sustainable-development/development-finance-standards/dacandcrscodelists.htm)
    (numeric - OECD Development Assistance Committee)
<!-- CLASSIFICATION_SCHEMES -->

### Command Line Interface

**countryguess** comes with a simple CLI with the same name. It takes one or two
arguments:

```sh
$ countryguess oman
{
    "name_short": "Oman",
    "name_official": "Sultanate of Oman",
    ...
}
$ countryguess 'puerto ricco' name_official
Puerto Rico
```

### Contributing

All kinds of bug reports, feature requests and suggestions are welcome!
