import re
from unittest.mock import call

import pytest

from countryguess import _guess_country


@pytest.fixture(autouse=True)
def remove_CountryData_instances():
    try:
        yield
    finally:
        _guess_country._countrydata = None


def test_guess_country_loads_countrydata_on_demand(mocker):
    CountryData_mock = mocker.patch('countryguess._guess_country.CountryData')
    assert _guess_country._countrydata is None
    for _ in range(12):
        _guess_country.guess_country('foo')
    assert _guess_country._countrydata is CountryData_mock.return_value
    CountryData_mock.call_args_list == [call()]


@pytest.mark.parametrize(
    argnames='info, attribute, default, exp_result',
    argvalues=(
        ({'iso2': 'AB', 'iso3': 'ABC'}, None, None, {'iso2': 'AB', 'iso3': 'ABC'}),
        ({'iso2': 'AB', 'iso3': 'ABC'}, None, 'whatever', {'iso2': 'AB', 'iso3': 'ABC'}),
        ({'iso2': 'AB', 'iso3': 'ABC'}, 'iso2', None, 'AB'),
        ({'iso2': 'AB', 'iso3': 'ABC'}, 'ISO2', None, 'AB'),
        ({'iso2': 'AB', 'iso3': 'ABC'}, 'iso3', None, 'ABC'),
        ({'iso2': 'AB', 'iso3': 'ABC'}, 'iso3', 'whatever', 'ABC'),
        ({'iso2': 'AB', 'iso3': 'ABC'}, 'iso4', None, AttributeError('iso4')),
        (None, None, 'whatever', 'whatever'),
        (None, 'iso3', 'whatever', 'whatever'),
    ),
    ids=lambda v: repr(v),
)
def test_guess_country_return_value(info, attribute, default, exp_result, mocker):
    CountryData_mock = mocker.patch('countryguess._guess_country.CountryData')
    CountryData_mock.return_value.get.return_value = info

    if isinstance(exp_result, Exception):
        with pytest.raises(type(exp_result), match=rf'^{re.escape(str(exp_result))}$'):
            _guess_country.guess_country('foo', attribute=attribute, default=default)
    else:
        return_value = _guess_country.guess_country('foo', attribute=attribute, default=default)
        assert return_value == exp_result

    assert CountryData_mock.return_value.get.call_args_list == [call('foo', regex_map=None)]
