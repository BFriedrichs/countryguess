from typing import TYPE_CHECKING, Dict, Optional

from ._countrydata import CountryData

if TYPE_CHECKING:
    from re import Pattern


_countrydata = None


def guess_country(
    country,
    regex_map: Optional[Dict[str, "Pattern"]] = None,
    attribute: Optional[str] = None,
    default: Optional[str] = None
):
    """
    :param regex_map: A map where the keys are the name of the country
        (should be equal to `name_short` in the json file) and the values are a
        regex `Pattern` that will substitute the regex in the json file.
        It's useful when you don't want to persist your own json file and want
        to change just a few regex patterns.
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
