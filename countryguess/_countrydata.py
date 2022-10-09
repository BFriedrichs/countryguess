import difflib
import functools
import importlib.resources
import json
import re
import threading

_lock = threading.Lock()


def _read_country_data(filepath):
    try:
        with open(filepath, 'r') as f:
            country_list = json.load(f)

    except OSError as e:
        msg = e.strerror if e.strerror else str(e)
        raise OSError(f'Cannot read {filepath}: {msg}')

    except ValueError:
        raise OSError(f'Invalid JSON: {filepath}')

    else:
        for info in country_list:
            info['regex'] = re.compile(info['regex'], flags=re.IGNORECASE)

        return country_list


def _lazy_load(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Read country data from file unless we've already done that
        if not self._countries:
            with _lock:
                self._countries = _read_country_data(self._filepath)

        # Call wrapped function transparently
        return func(self, *args, **kwargs)

    return wrapper


class CountryData:
    DEFAULT_FILEPATH = _countrydata_filepath = importlib.resources.path(
        'countryguess',
        '_countrydata.json',
    )

    def __init__(self, filepath=None):
        if filepath is not None:
            self._filepath = filepath
        else:
            self._filepath = self.DEFAULT_FILEPATH
        self._countries = None

    @property
    @_lazy_load
    def countries(self):
        """
        :class:`list` of country :class:`dict` objects

        This is the same data that was read from the provided country data file.
        """
        return [country.copy() for country in self._countries]

    @functools.cached_property
    @_lazy_load
    def codes_iso2(self):
        """Sequence of ISO 3166-2 country codes"""
        return tuple(country['iso2'] for country in self._countries)

    @functools.cached_property
    @_lazy_load
    def codes_iso3(self):
        """Sequence of ISO 3166-3 country codes"""
        return tuple(country['iso3'] for country in self._countries)

    @functools.cached_property
    @_lazy_load
    def names_official(self):
        """Sequence of official country names"""
        return tuple(country['name_official'] for country in self._countries)

    @functools.cached_property
    @_lazy_load
    def names_short(self):
        """Sequence of colloqial country names"""
        return tuple(country['name_short'] for country in self._countries)

    @_lazy_load
    def _find_country(self, string):
        # ISO 3166-2
        if len(string) == 2:
            info = self._find_country_by_code(string, self.codes_iso2)
            if info:
                return info

        # ISO 3166-3
        if len(string) == 3:
            info = self._find_country_by_code(string, self.codes_iso3)
            if info:
                return info

        # Regular expression
        for info in self._countries:
            if info['regex'].search(string):
                return info

        # Fuzzy country name
        for names in (self.names_official, self.names_short):
            matches = difflib.get_close_matches(string, names, n=1, cutoff=0.7)
            if matches:
                name = matches[0]
                index = names.index(name)
                return self._countries[index]

    def _find_country_by_code(self, code, codes):
        try:
            index = codes.index(code.upper())
        except ValueError:
            pass
        else:
            return self._countries[index]

    def get(self, country, default=None):
        """
        Return country data as :class:`dict`

        :param str country: Country name, ISO 3166-2 or ISO 3166-3 code

            This is case-insensitive.

            If a country name is provided, it is first matched against the
            regular expressions. If that fails,
            :func:`difflib.get_close_matches` is used for fuzzy matching.

        :param default: Default return value if `country` is not found
        """
        info = self._find_country(country)
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

    @_lazy_load
    def __getattr__(self, attribute):
        print('getting attr:', attribute)
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
