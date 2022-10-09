import copy
import re
from unittest.mock import Mock, call

import pytest

from countryguess import _countrydata


@pytest.mark.parametrize(
    argnames='json_data, permissions, exp_result',
    argvalues=(
        (
            '[{"name_short": "Sweden", "regex": "^sweden(?:ish|)$"}]',
            None,
            [{'name_short': 'Sweden', 'regex': re.compile('^sweden(?:ish|)$', flags=re.IGNORECASE)}],
        ),
        (
            '[',
            0o000,
            OSError('Cannot read {filepath}: Permission denied'),
        ),
        (
            '[',
            None,
            OSError('Invalid JSON: {filepath}'),
        ),
    ),
    ids=lambda v: repr(v),
)
def test_read_country_data(json_data, permissions, exp_result, tmp_path):
    filepath = tmp_path / 'countrydata.json'
    filepath.write_text(json_data)
    if permissions is not None:
        filepath.chmod(permissions)

    if isinstance(exp_result, Exception):
        exp_msg = str(exp_result).format(filepath=filepath)
        with pytest.raises(type(exp_result), match=rf'^{re.escape(exp_msg)}$'):
            _countrydata._read_country_data(filepath)
    else:
        return_value = _countrydata._read_country_data(filepath)
        assert return_value == exp_result


def test_lazy_load(mocker):
    self = Mock(
        _countries=None,
        _filepath='path/to/countrydata',
    )
    mocks = Mock()
    mocks.attach_mock(
        self.func,
        'func',
    )
    mocks.attach_mock(
        mocker.patch(
            'countryguess._countrydata._read_country_data',
            return_value='mock country data',
        ),
        'read_country_data',
    )
    mocks.attach_mock(
        mocker.patch.context_manager(_countrydata, '_lock'),
        'lock',
    )

    wrapped = _countrydata._lazy_load(self.func)
    for _ in range(6):
        return_value = wrapped(self, 1, two='3')

    assert return_value is self.func.return_value
    assert mocks.mock_calls == [
        call.lock.__enter__(),
        call.read_country_data(self._filepath),
        call.lock.__exit__(None, None, None),
        call.func(self, 1, two='3'),
        call.func(self, 1, two='3'),
        call.func(self, 1, two='3'),
        call.func(self, 1, two='3'),
        call.func(self, 1, two='3'),
        call.func(self, 1, two='3'),
    ]
    assert self._countries is mocks.read_country_data.return_value


@pytest.mark.parametrize(
    argnames='property_name',
    argvalues=(
        'countries',
        'codes_iso2',
        'codes_iso3',
        'names_official',
        'names_short',
    ),
    ids=lambda v: repr(v),
)
def test_CountryData_lazy_loaded_property(property_name):
    countrydata = _countrydata.CountryData()
    assert countrydata._countries is None
    print(getattr(countrydata, property_name))
    assert isinstance(countrydata._countries, list)


@pytest.mark.parametrize(
    argnames='method_name, args, kwargs',
    argvalues=(
        ('_find_country', ('antarctica',), {}),
        ('__getattr__', ('iso2',), {}),
    ),
    ids=lambda v: repr(v),
)
def test_CountryData_lazy_loaded_method(method_name, args, kwargs):
    countrydata = _countrydata.CountryData()
    assert countrydata._countries is None
    print('getting method:', method_name)
    method = getattr(countrydata, method_name)
    print('method:', method)
    method(*args, **kwargs)
    assert isinstance(countrydata._countries, list)


def test_CountryData_property_countries():
    countrydata = _countrydata.CountryData()
    orig_countries = copy.deepcopy(countrydata.countries)
    countries = countrydata.countries
    assert countries == countrydata.countries
    del countries[0]
    countries[0]['name_official'] = 'Foo Country'
    assert countries != countrydata.countries
    assert orig_countries == countrydata.countries


property_test_data = '''[
{"iso3": "ABC", "iso2": "AB", "name_short": "Foo", "name_official": "The Foo", "regex": "irrelevant"},
{"iso3": "DEF", "iso2": "DE", "name_short": "Bar", "name_official": "The Bar", "regex": "irrelevant"},
{"iso3": "GHI", "iso2": "GH", "name_short": "Baz", "name_official": "The Baz", "regex": "irrelevant"}
]'''

@pytest.mark.parametrize(
    argnames='property_name, exp_value',
    argvalues=(
        ('codes_iso3', ('ABC', 'DEF', 'GHI')),
        ('codes_iso2', ('AB', 'DE', 'GH')),
        ('names_short', ('Foo', 'Bar', 'Baz')),
        ('names_official', ('The Foo', 'The Bar', 'The Baz')),
    ),
    ids=lambda v: repr(v),
)
def test_CountryData_country_attribute_property(property_name, exp_value, tmp_path):
    filepath = tmp_path / 'countrydata.json'
    filepath.write_text(property_test_data)
    countrydata = _countrydata.CountryData(filepath)

    value = getattr(countrydata, property_name)
    assert value == exp_value

    # Return value is cached
    for _ in range(6):
        assert value is getattr(countrydata, property_name)


@pytest.mark.parametrize(
    argnames='string, exp_info_index',
    argvalues=(
        # ISO2
        ('ab', 0),
        ('dE', 1),
        ('GH', 2),
        ('xy', None),

        # ISO3
        ('ABC', 0),
        ('Def', 1),
        ('ghi', 2),
        ('xyz', None),

        # Regex
        ('FOOlala', 0),
        ('foooolala', 0),
        ('fOOOooolala', 0),
        ('baristan', 1),
        ('Bahristan', 1),
        ('BARistan', 1),
        ('BAHRistan', 1),
        ('Bazvia', 2),
        ('baZvia', 2),
        ('Basvia', 2),
        ('BASvia', 2),

        # Fuzzy
        ('foolalu', 0),
        ('BARistan', 1),
        ('bAsvian kingdom', 2),
        ('adsf', None),
    ),
    ids=lambda v: repr(v),
)
def test_CountryData_find_country(string, exp_info_index, mocker):
    countrydata = _countrydata.CountryData()
    countrydata._countries = [
        {
            'iso3': 'ABC',
            'iso2': 'AB',
            'name_short': 'Foolala',
            'name_official': 'Fooland',
            'regex': re.compile('^fo+lala$', flags=re.IGNORECASE),
        },
        {
            'iso3': 'DEF',
            'iso2': 'DE',
            'name_short': 'Baristan',
            'name_official': 'Republic of Baristan',
            'regex': re.compile('^bah?ristan$', flags=re.IGNORECASE),
        },
        {
            'iso3': 'GHI',
            'iso2': 'GH',
            'name_short': 'Bazvia',
            'name_official': 'Bazvian Kingdom',
            'regex': re.compile('^ba[zs]via$', flags=re.IGNORECASE),
        },
    ]
    info = countrydata._find_country(string)
    print(info)
    if exp_info_index is None:
        assert info is None
    else:
        assert countrydata._countries.index(info) == exp_info_index


@pytest.mark.parametrize(
    argnames='country, default, find_country, exp_return_value',
    argvalues=(
        ('foo', None, Mock(return_value={'iso2': 'FO'}), {'iso2': 'FO'}),
        ('foo', 'default', Mock(return_value={'iso2': 'FO'}), {'iso2': 'FO'}),
        ('foo', None, Mock(return_value=None), None),
        ('foo', 'default', Mock(return_value=None), 'default'),
    ),
    ids=lambda v: repr(v),
)
def test_CountryData_get(country, default, find_country, exp_return_value, mocker):
    mocker.patch('countryguess._countrydata.CountryData._find_country', find_country)
    countrydata = _countrydata.CountryData()
    return_value = countrydata.get(country, default=default)
    assert return_value == exp_return_value


@pytest.mark.parametrize(
    argnames='country, get, exp_result',
    argvalues=(
        ('foo', Mock(return_value={'iso2': 'FO'}), {'iso2': 'FO'}),
        ('foo', Mock(return_value=None), KeyError('foo')),
    ),
    ids=lambda v: repr(v),
)
def test_CountryData_getitem(country, get, exp_result, mocker):
    mocker.patch('countryguess._countrydata.CountryData.get', get)
    countrydata = _countrydata.CountryData()
    if isinstance(exp_result, Exception):
        with pytest.raises(type(exp_result), match=rf'^{re.escape(str(exp_result))}$'):
            countrydata[country]
    else:
        return_value = countrydata[country]
        assert return_value == exp_result


@pytest.mark.parametrize(
    argnames='attribute, country, exp_result',
    argvalues=(
        ('iso2', 'foo', 'FO'),
        ('iso3', 'foo', 'FOO'),
        ('iso4', 'foo', AttributeError('iso4')),
    ),
    ids=lambda v: repr(v),
)
def test_CountryData_getattr(attribute, country, exp_result, mocker):
    countrydata = _countrydata.CountryData()
    countrydata._countries = [
        {
            'iso2': 'FO',
            'iso3': 'FOO',
        },
    ]
    if isinstance(exp_result, Exception):
        with pytest.raises(type(exp_result), match=rf'^{re.escape(str(exp_result))}$'):
            getattr(countrydata, attribute)
    else:
        return_value = getattr(countrydata, attribute)(country)
        assert return_value == exp_result
