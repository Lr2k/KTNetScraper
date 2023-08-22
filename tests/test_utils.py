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

del type_checked