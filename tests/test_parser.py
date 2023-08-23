import pytest

from ktnetscraper import parser, exceptions
from template import (
    login_succed_template,
    login_failed_template,
    index_template,
    timetable_no_class_template,
    handout_info_template,
)


# login_status
# 引数
# text : login_succes.html, login_failed.html

# ログイン成功 -> True
def test_login_status_0():
    login_succed_page = login_succed_template()
    assert parser.login_status(login_succed_page) == True

# 時間割ページ -> ログイン済み -> True
def test_login_status_1():
    timetable_no_class_page = timetable_no_class_template()
    assert parser.login_status(timetable_no_class_page)

# 教材ページ -> ログイン済み -> True
def test_login_status_2():
    handout_info_page = handout_info_template()

# ログイン失敗 -> False
def test_login_status_3():
    login_failed_page = login_failed_template()
    assert parser.login_status(login_failed_page) == False

# 未ログインによるindexページへのリダイレクト -> False
def test_login_status_4():
    index_page = index_template()
    assert parser.login_status(index_page) == False

# UnexpextedContentException
def test_login_status_e0():
    page = ''
    with pytest.raises(exceptions.UnexpextedContentException):
        parser.login_status(page)

# UnexpextedContentException
def test_login_status_e1():
    page = '<?xml version="1.0" encoding="Shift_JIS"?>'
    with pytest.raises(exceptions.UnexpextedContentException):
        parser.login_status(page)