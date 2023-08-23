import pytest

from ktnetscraper import parser, exceptions
from template import (
    menu_template,
    login_failed_template,
    index_template,
    timetable_no_class_template,
    handout_info_template,
)


# login_status
# 引数
# text : login_succes.html, login_failed.html

# 正常動作
# メニューへリダイレクト -> ログイン成功 -> True
def test_login_status_0():
    menu_page = menu_template()
    assert parser.login_status(menu_page) == True

# 時間割ページ -> ログイン済み -> True
def test_login_status_1():
    timetable_no_class_page = timetable_no_class_template()
    assert parser.login_status(timetable_no_class_page) == True

# 教材ページ -> ログイン済み -> True
def test_login_status_2():
    handout_info_page = handout_info_template()
    assert parser.login_status(handout_info_page) == True

# ログイン失敗 -> False
def test_login_status_3():
    login_failed_page = login_failed_template()
    assert parser.login_status(login_failed_page) == False

# 未ログインによるindexページへのリダイレクト -> False
def test_login_status_4():
    index_page = index_template()
    assert parser.login_status(index_page) == False

# エラー
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


# get_faculty_and_grade
# 引数
# 医学部ページ, 看護学部ページ 複数学年
# 返り値
# 医 -> M, 看 -> N  学年：'1' ~ '6'

# 正常動作
@pytest.mark.parametrize(
        "arg_faculty, arg_grade, out_faculty, out_grade",
        [
            ('医', '1', ('M', '1')),
            ('医', '2', ('M', '2')),
            ('医', '3', ('M', '3')),
            ('看護', '1', ('N', '1')),
            ('看護', '2', ('N', '2')),
            ('看護', '3', ('N', '3')),
        ]
)
def test_get_faculty_and_grade_0(arg_faculty, arg_grade, out):
    timetable_page = timetable_no_class_template(
        faculty=arg_faculty, grade=arg_grade,
        date='2000/01/02', days_of_week='日'
    )
    assert parser.get_faculty_and_grade(timetable_page) == out

# エラー
# 未ログイン -> indexへリダイレクト -> LoginRequiredException
def test_get_faculty_and_grade_e0():
    index_page = index_template()
    with pytest.raises(exceptions.LoginRequiredException):
        parser.get_faculty_and_grade(index_page)

# UnexpextedContentException
def test_get_faculty_and_grade_e0():
    page = ''
    with pytest.raises(exceptions.UnexpextedContentException):
        parser.get_faculty_and_grade(page)

# UnexpextedContentException
def test_get_faculty_and_grade_e1():
    page = '<?xml version="1.0" encoding="Shift_JIS"?>'
    with pytest.raises(exceptions.UnexpextedContentException):
        parser.get_faculty_and_grade(page)

# メニュー, 教材情報 -> UnexpextedContentException
@pytest.mark.parametrize(
        'page',
        [
            (menu_template()),
            (handout_info_template())
        ]
)
def test_get_faculty_and_grade_e1(page):
    with pytest.raises(exceptions.UnexpextedContentException):
        parser.get_faculty_and_grade(page)