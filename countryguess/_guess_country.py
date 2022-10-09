from ._countrydata import CountryData

_countrydata = None


def guess_country(country, attribute=None, default=None):
    global _countrydata
    if _countrydata is None:
        _countrydata = CountryData()

    info = _countrydata.get(country)
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
