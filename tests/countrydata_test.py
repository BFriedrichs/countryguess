import copy
import io
import re
import sys
from unittest.mock import Mock, call

import pytest

from countryguess import __project_name__, _countrydata


def test_lazy_load_countries(mocker):
    self = Mock(
        _countries=None,
        _filepath='path/to/countrydata',
    )
    mocks = Mock()
    mocks.attach_mock(self.func, 'func')
    mocks.attach_mock(self._load_countries, '_load_countries')
    self._load_countries.return_value = 'mock countries'

    wrapped = _countrydata._lazy_load_countries(self.func)
    for _ in range(6):
        return_value = wrapped(self, 1, two='3')

    assert return_value is self.func.return_value
    assert mocks.mock_calls == [
        call._load_countries(),
        call.func(self, 1, two='3'),
        call.func(self, 1, two='3'),
        call.func(self, 1, two='3'),
        call.func(self, 1, two='3'),
        call.func(self, 1, two='3'),
        call.func(self, 1, two='3'),
    ]
    assert self._countries is mocks._load_countries.return_value


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
    getattr(countrydata, property_name)
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
    method = getattr(countrydata, method_name)
    method(*args, **kwargs)
    assert isinstance(countrydata._countries, list)


@pytest.mark.parametrize(
    argnames='filepath, filecontent, exp_countries',
    argvalues=(
        (
            'custom/countries.json',
            '[{"name_short": "Customland", "regex": "^custom$"}]',
            [{'name_short': 'Customland', 'regex': re.compile('^custom$', flags=re.IGNORECASE)}],
        ),
        (
            None,
            '[{"name_short": "Kingdom of Default", "regex": "^default$"}]',
            [{'name_short': 'Kingdom of Default', 'regex': re.compile('^default$', flags=re.IGNORECASE)}],
        ),
    ),
    ids=lambda v: repr(v),
)
def test_load_countries(filepath, filecontent, exp_countries, tmp_path, mocker):
    if sys.version_info <= (3, 9, 0):
        # TODO: Remove this when Python 3.9 is no longer supported
        open_text_mock = mocker.patch('importlib.resources.open_text', return_value=(
            io.StringIO('[{"name_short": "Kingdom of Default", "regex": "^default$"}]')
        ))

        def assert_expectations():
            assert open_text_mock.call_args_list == [call(__project_name__, '_countrydata.json')]

    else:
        # Python 3.13 removes importlib.resources.open_text()
        files_mock = mocker.patch('importlib.resources.files')
        package_path_mock = files_mock.return_value
        joinpath_mock = package_path_mock.joinpath
        file_path_mock = joinpath_mock.return_value
        open_mock = file_path_mock.open
        open_mock.return_value = (
            io.StringIO('[{"name_short": "Kingdom of Default", "regex": "^default$"}]')
        )

        def assert_expectations():
            assert files_mock.mock_calls == [
                call(__project_name__),
                call().joinpath('_countrydata.json'),
                call().joinpath().open('r', encoding='utf8'),
            ]

    if filepath:
        filepath = tmp_path / filepath
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(filecontent)

    countrydata = _countrydata.CountryData(filepath)
    return_value = countrydata._load_countries()
    assert return_value == exp_countries

    if filepath is None:
        assert_expectations()


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
def test_CountryData_property(property_name, exp_value, tmp_path):
    filepath = tmp_path / 'countrydata.json'
    filepath.write_text(property_test_data)
    countrydata = _countrydata.CountryData(filepath)

    value = getattr(countrydata, property_name)
    assert value == exp_value

    # Return value is cached
    for _ in range(6):
        assert value is getattr(countrydata, property_name)


@pytest.fixture
def find_country_countries():
    return [
        {
            'iso2': 'AB',
            'iso3': 'ABC',
            'name_short': 'Foolala',
            'name_official': 'Fooland',
            'regex': re.compile('^fo+lala$', flags=re.IGNORECASE),
        },
        {
            'iso2': 'DE',
            'iso3': 'DEF',
            'name_short': 'Baristan',
            'name_official': 'Republic of Baristan',
            'regex': re.compile('^bah?ristan$', flags=re.IGNORECASE),
        },
        {
            'iso2': 'GH',
            'iso3': 'GHI',
            'name_short': 'Bazvia',
            'name_official': 'Bazvian Kingdom',
            'regex': re.compile('^ba[zs]via$', flags=re.IGNORECASE),
        },
    ]

@pytest.mark.parametrize(
    argnames='string, exp_info_index',
    argvalues=(
        ('ab', 0),
        ('De', 1),
        ('GH', 2),
        ('xy', None),
    ),
    ids=lambda v: repr(v),
)
def test_CountryData_find_country_by_iso2(string, exp_info_index, find_country_countries):
    countrydata = _countrydata.CountryData()
    countrydata._countries = find_country_countries
    info = countrydata._find_country(string)
    if exp_info_index is None:
        assert info is None
    else:
        info_index = countrydata._countries.index(info)
        assert info_index == exp_info_index

@pytest.mark.parametrize(
    argnames='string, exp_info_index',
    argvalues=(
        ('abc', 0),
        ('DeF', 1),
        ('GHI', 2),
        ('xyz', None),
    ),
    ids=lambda v: repr(v),
)
def test_CountryData_find_country_by_iso3(string, exp_info_index, find_country_countries):
    countrydata = _countrydata.CountryData()
    countrydata._countries = find_country_countries
    info = countrydata._find_country(string)
    if exp_info_index is None:
        assert info is None
    else:
        info_index = countrydata._countries.index(info)
        assert info_index == exp_info_index

@pytest.mark.parametrize(
    argnames='string, regex_map, exp_info_index',
    argvalues=(
        (
            'aaaaaabbbbbb',
            {
                'ab': re.compile(r'^a+b+$'),
                'de': re.compile(r'^dee?EEE?fff?$'),
                'gh': re.compile(r'^.*$'),
            },
            0,
        ),
        (
            'deEEEff',
            {
                'ab': re.compile(r'^a+b+$'),
                'de': re.compile(r'^dee?EEE?fff?$'),
                'gh': re.compile(r'^.*$'),
            },
            1,
        ),
        (
            'anything',
            {
                'ab': re.compile(r'^a+b+$'),
                'de': re.compile(r'^dee?EEE?fff?$'),
                'gh': re.compile(r'^[a-z]+$'),
            },
            2,
        ),
        (
            '123',
            {
                'ab': re.compile(r'^a+b+$'),
                'de': re.compile(r'^dee?EEE?fff?$'),
                'gh': re.compile(r'^[a-z]+$'),
            },
            None,
        ),
    ),
    ids=lambda v: repr(v),
)
def test_CountryData_find_country_by_custom_regex(string, regex_map, exp_info_index, find_country_countries, mocker):
    countrydata = _countrydata.CountryData()
    mocker.patch.object(countrydata, '_validate_regex_map')
    countrydata._countries = find_country_countries
    info = countrydata._find_country(string, regex_map=regex_map)
    if exp_info_index is None:
        assert info is None
    else:
        info_index = countrydata._countries.index(info)
        assert info_index == exp_info_index

    if exp_info_index is not None:
        assert countrydata._validate_regex_map.call_args_list == []
    else:
        assert countrydata._validate_regex_map.call_args_list == [call(regex_map)]

@pytest.mark.parametrize(
    argnames='string, exp_info_index',
    argvalues=(
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
        ('this should not match any country', None),
    ),
    ids=lambda v: repr(v),
)
def test_CountryData_find_country_by_hardcoded_regex(string, exp_info_index, find_country_countries):
    countrydata = _countrydata.CountryData()
    countrydata._countries = find_country_countries
    info = countrydata._find_country(string)
    if exp_info_index is None:
        assert info is None
    else:
        info_index = countrydata._countries.index(info)
        assert info_index == exp_info_index

@pytest.mark.parametrize(
    argnames='string, exp_info_index',
    argvalues=(
        ('Foolalu', 0),
        ('Foolalulala', None),
        ('Brepublic bof Baristan', 1),
        ('Brepublic bof Baristanianism', None),
        ('Basvian Kingdork', 2),
        ('Basvian Queendom', None),
    ),
    ids=lambda v: repr(v),
)
def test_CountryData_find_country_by_fuzzy_match(string, exp_info_index, find_country_countries):
    countrydata = _countrydata.CountryData()
    countrydata._countries = find_country_countries
    info = countrydata._find_country(string)
    if exp_info_index is None:
        assert info is None
    else:
        info_index = countrydata._countries.index(info)
        assert info_index == exp_info_index


@pytest.mark.parametrize(
    argnames='regex_map, exp_exception',
    argvalues=(
        (['a', 'b'], RuntimeError("Not a dict-like object: ['a', 'b']")),
        ({'a': 'b'}, RuntimeError("Not a ISO 3166-1 alpha-2 country code: 'a'")),
        ({'TV': 'b'}, RuntimeError("Not a regular expression (see re.compile()): 'b'")),
        ({'TV': re.compile('toovaloodldoo')}, None),
    ),
    ids=lambda v: repr(v),
)
def test_CountryData_validate_regex_map(regex_map, exp_exception):
    countrydata = _countrydata.CountryData()
    if isinstance(exp_exception, Exception):
        with pytest.raises(type(exp_exception), match=rf'^{re.escape(str(exp_exception))}$'):
            countrydata._validate_regex_map(regex_map)
    else:
        countrydata._validate_regex_map(regex_map)


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
    regex_map = Mock()
    mocker.patch('countryguess._countrydata.CountryData._find_country', find_country)
    countrydata = _countrydata.CountryData()
    return_value = countrydata.get(country, default=default, regex_map=regex_map)
    assert return_value == exp_return_value
    assert countrydata._find_country.call_args_list == [
        call(country, regex_map=regex_map)
    ]


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
