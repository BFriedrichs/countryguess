from ._countrydata import CountryData

_countrydata = None


def guess_country(country, attribute=None, default=None, regex_map=None):
    """
    Use built-in country data to identify `country`

    See :meth:`.CountryData.get` for more information.
    """
    global _countrydata
    if _countrydata is None:
        _countrydata = CountryData()

    info = _countrydata.get(country, regex_map=regex_map)
    if info:
        if attribute:
            try:
                return info[attribute.lower()]
            except KeyError:
                raise AttributeError(attribute)
        else:
            return info
    else:
        return default
