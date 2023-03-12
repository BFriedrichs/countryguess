import collections
import difflib
import functools
import importlib.resources
import json
import re
import sys

from . import __project_name__


def _lazy_load_countries(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Read country data from file unless we've already done that
        if not self._countries:
            self._countries = self._load_countries()

        # Call wrapped function transparently
        return func(self, *args, **kwargs)

    return wrapper


class CountryData:
    def __init__(self, filepath=None):
        self._filepath = filepath
        self._countries = None

    def _load_countries(self):
        if self._filepath is not None:
            stream = open(self._filepath, 'r')
        else:
            if sys.version_info <= (3, 9, 0):
                # TODO: Remove this when Python 3.9 is no longer supported
                stream = importlib.resources.open_text(__project_name__, '_countrydata.json')
            else:
                # Python 3.13 removes importlib.resources.open_text()
                package_path = importlib.resources.files(__project_name__)
                file_path = package_path.joinpath('_countrydata.json')
                stream = file_path.open('r', encoding='utf8')

        country_list = json.load(stream)

        for info in country_list:
            info['regex'] = re.compile(info['regex'], flags=re.IGNORECASE)

        return country_list

    @property
    @_lazy_load_countries
    def countries(self):
        """
        :class:`list` of country :class:`dict` objects

        This is the same data that was read from the provided country data file.
        """
        return [country.copy() for country in self._countries]

    @functools.cached_property
    @_lazy_load_countries
    def codes_iso2(self):
        """Sequence of ISO 3166-1 alpha-2 country codes"""
        return tuple(country['iso2'] for country in self._countries)

    @functools.cached_property
    @_lazy_load_countries
    def codes_iso3(self):
        """Sequence of ISO 3166-1 alpha-3 country codes"""
        return tuple(country['iso3'] for country in self._countries)

    @functools.cached_property
    @_lazy_load_countries
    def names_official(self):
        """Sequence of official country names"""
        return tuple(country['name_official'] for country in self._countries)

    @functools.cached_property
    @_lazy_load_countries
    def names_short(self):
        """Sequence of colloqial country names"""
        return tuple(country['name_short'] for country in self._countries)

    @_lazy_load_countries
    def _find_country(self, string, regex_map=None):
        # ISO 3166-1 alpha-2
        if len(string) == 2:
            info = self._find_country_by_code(string, self.codes_iso2)
            if info:
                return info

        # ISO 3166-1 alpha-3
        if len(string) == 3:
            info = self._find_country_by_code(string, self.codes_iso3)
            if info:
                return info

        # Custom regular expressions
        if regex_map:
            for iso2, regex in regex_map.items():
                if regex.search(string):
                    return self._find_country_by_code(iso2, self.codes_iso2)
            # Because validation is expensive, we only do it if we couldn't find
            # a match
            self._validate_regex_map(regex_map)

        # Hardcoded regular expressions
        for info in self._countries:
            if info['regex'].search(string):
                return info

        # Fuzzy country name
        for names in (self.names_official, self.names_short):
            matches = difflib.get_close_matches(string, names, n=1, cutoff=0.8)
            if matches:
                name = matches[0]
                index = names.index(name)
                return self._countries[index]

    def _validate_regex_map(self, regex_map):
        if not isinstance(regex_map, collections.abc.Mapping):
            raise RuntimeError(f'Not a dict-like object: {regex_map!r}')

        for iso2, regex in regex_map.items():
            if iso2 not in self.codes_iso2:
                raise RuntimeError(f'Not a ISO 3166-1 alpha-2 country code: {iso2!r}')

            elif not isinstance(regex, re.Pattern):
                raise RuntimeError(f'Not a regular expression (see re.compile()): {regex!r}')

    def _find_country_by_code(self, code, codes):
        try:
            index = codes.index(code.upper())
        except ValueError:
            pass
        else:
            return self._countries[index]

    def get(self, country, default=None, regex_map=None):
        """
        Return country data as :class:`dict`

        :param str country: Country name, 2-letter code or 3-letter code

            This is case-insensitive.

            If a country name is provided, it is first matched against the
            regular expressions. If that fails,
            :func:`difflib.get_close_matches` is used for fuzzy matching.

        :param default: Default return value if `country` is not found
        :param dict regex_map: Map ISO 3166-1 alpha-2 country codes
            (:class:`str`) to regular expressions (:class:`re.Pattern`, see
            :func:`re.compile`)
        """
        info = self._find_country(country, regex_map=regex_map)
        if info:
            return info
        else:
            return default

    def __getitem__(self, country):
        info = self.get(country)
        if info:
            return info
        else:
            raise KeyError(country)

    @_lazy_load_countries
    def __getattr__(self, attribute):
        # Raise exception now, not when get_attribute() is called. This means
        # accessing `countrydata.iso4` raises AttributeError as it should.
        try:
            self._countries[0][attribute]
        except KeyError:
            raise AttributeError(attribute)

        def get_attribute(country):
            info = self.get(country)
            return info[attribute]

        return get_attribute
