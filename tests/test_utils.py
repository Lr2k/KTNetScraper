import pytest


# type_checked()

# 引数
# object : int(), str(), list(), None
# _type : int, str, list
# allow_none : True, False, default(None)

from ktnetscraper.utils import type_checked


# 正しい型を入力, None拒否(デフォルト)
@pytest.mark.parametrize(
    "object, _type",
    [
        (123, int),
        ('abc', str),
        ([1, 2, 3], list),
    ]
)
def test_type_checked_0(object, _type):
    assert type_checked(object, _type) == object

# 正しい型を入力, None拒否
@pytest.mark.parametrize(
    "object, _type, allow_none",
    [
        (123, int, False),
        ('abc', str, False),
        ([1, 2, 3], list, False),
    ]
)
def test_type_checked_1(object, _type, allow_none):
    assert type_checked(object, _type, allow_none) == object

# 正しい型を入力, None許可
@pytest.mark.parametrize(
    "object, _type, allow_none",
    [
        (123, int, True),
        ('abc', str, True),
        ([1, 2, 3], list, True),
    ]
)
def test_type_checked_2(object, _type, allow_none):
    assert type_checked(object, _type, allow_none) == object

# 誤まった型を入力, None拒否（デフォルト）-> TypeError
@pytest.mark.parametrize(
    "object, _type",
    [
        ('123', int),
        (123, str),
        ((1, 2, 3), list),
    ]
)
def test_type_checked_3(object, _type):
    with pytest.raises(TypeError):
        type_checked(object, _type)

# 誤まった型を入力, None拒否 -> TypeError
@pytest.mark.parametrize(
    "object, _type, allow_none",
    [
        ('123', int, False),
        (123, str, False),
        ((1, 2, 3), list, False),
    ]
)
def test_type_checked_4(object, _type, allow_none):
    with pytest.raises(TypeError):
        type_checked(object, _type, allow_none)

# 誤まった型を入力, None許可 -> TypeError
@pytest.mark.parametrize(
    "object, _type, allow_none",
    [
        ('123', int, True),
        (123, str, True),
        ((1, 2, 3), list, True),
    ]
)
def test_type_checked_5(object, _type, allow_none):
    with pytest.raises(TypeError):
        type_checked(object, _type, allow_none)

# Noneを入力, None拒否（デフォルト）-> TypeError
@pytest.mark.parametrize(
    "object, _type",
    [
        (None, int),
        (None, str),
        (None, list),
    ]
)
def test_type_checked_6(object, _type):
    with pytest.raises(TypeError):
        type_checked(object, _type)

# Noneを入力, None拒否 -> TypeError
@pytest.mark.parametrize(
    "object, _type, allow_none",
    [
        (None, int, False),
        (None, str, False),
        (None, list, False),
    ]
)
def test_type_checked_7(object, _type, allow_none):
    with pytest.raises(TypeError):
        type_checked(object, _type, allow_none)

# Noneを入力, None許可 -> None
@pytest.mark.parametrize(
    "object, _type, allow_none",
    [
        (None, int, True),
        (None, str, True),
        (None, list, True),
    ]
)
def test_type_checked_8(object, _type, allow_none):
    assert type_checked(object, _type, allow_none) == None



# convert_to_date()

# 引数
# date : datetime.date, datetime.datetime, list[int], list[str],
#        tuple[int], tuple[str], str,

import datetime

from ktnetscraper.utils import convert_to_date


# 正しい入力(2019年4月6日)
@pytest.mark.parametrize(
    "date",
    [
        (datetime.datetime(2019, 4, 6)),
        (datetime.date(2019, 4, 6)),
        ([2019, 4, 6]),
        (['2019', '4', '6']),
        (['2019', '04', '06']),
        ((2019, 4, 6)),
        (('2019', '4', '6')),
        (('2019', '04', '06')),
        ('2019/04/06'),
    ]
)
def test_convert_to_date_0(date):
    correct_date = datetime.date(2019, 4, 6)
    assert convert_to_date(date) == correct_date

# 誤まった入力(型)
@pytest.mark.parametrize(
    "date",
    [
        (20190406),
        (datetime.timedelta(123,23,1))
    ]
)
def test_convert_to_date_1(date):
    with pytest.raises(TypeError):
        convert_to_date(date)



# convert_to_datetime()

# 引数
# date : datetime.date, datetime.datetime, list[int], list[str],
#        tuple[int], tuple[str], str,

import datetime

from ktnetscraper.utils import convert_str_to_datetime


# 正しい入力(2019年4月6日 5時4分)
@pytest.mark.parametrize(
    "datetime_str",
    [
        ('2019/04/06 05:04'),
    ]
)
def test_convert_str_to_datetime_0(datetime_str):
    tz_jst = datetime.timezone(datetime.timedelta(hours=9), 'jst')
    correct_date = datetime.datetime(2019, 4, 6, 5, 4, tzinfo=tz_jst)
    
    assert convert_str_to_datetime(datetime_str) == correct_date