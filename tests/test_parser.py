from functools import partial

import pytest

from ktnetscraper import parser, exceptions
from template import (
    menu_template,
    login_failed_template,
    index_template,
    timetable_no_class_template,
    handout_info_template,
    timetable_template,
    class_template,
    handout_template,
    dlpage_url,
)


# detect_paeg_type
# 引数
# text : login_page, menu_page, timetable_page, handout_page, 不明なページ

# 正常動作
# 判定可能なページ
@pytest.mark.parametrize(
        'page, out',
        [
            (index_template(), 'login'),
            (menu_template(), 'menu'),
            (timetable_no_class_template(), 'timetable'),
            (handout_info_template(), 'handout')
        ]
)
def test_detect_page_type_0(page, out):
    assert parser.detect_page_type(page) == out

# 不明なページ
@pytest.mark.parametrize(
        'page, out',
        [
            ('', 'unknown'),
            ('<?xml version="1.0" encoding="Shift_JIS"?>', 'unknown'),
        ]
)
def test_detect_page_type_0(page, out):
    assert parser.detect_page_type(page) == out


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


# get_dlpage_url
# 引数
# text: timetable
# 返り値
# URL : (<url>, ...)

#　未入力: class_infos
m1_timetable_template = partial(timetable_template,
                                faculty='医', grade='1',
                                date='2000/01/01', days_of_week='土')
simple_class = class_template(
    period='1', unit_name='ユニット', thema='テーマ',
    room='C11', teachers='教員'
)


# 正常動作
# 授業の無い日, 教材がない日
@pytest.mark.parametrize(
        'page',
        [
            (timetable_no_class_template()),
            (m1_timetable_template(class_infos=simple_class * 6))
        ]
)
def test_get_dlpage_url_0(page):
    urls = parser.get_dlpage_url(page)
    assert type(urls) == tuple
    assert len(urls) == 0

# 世界一最悪なテストを書きました、ごめんなさい
# 条件１：授業１つ、教材１つ
# 条件２：授業３つ、　1授業につき教材リンク１つ
# 条件３：授業３つ、1授業につき教材リンク３つ
class_num_3 = 3
handout_per_class_3 = 3
@pytest.mark.parametrize(
        'handout_infos_list, class_info_list',
        [   
            # 条件１
            (({'urls':(dlpage_url(arg_2='1')), 'handout_names':('教材1')}),    # handout_info_list
             ({'period':'1', 'unit_name':'ユニット1', 'thema':'テーマ1', 'room':'C11',
               'teachers':'教員1'})),                                           # class_info_list
            # 条件２
            ([{'urls':(dlpage_url(arg_2=f'{c_i}')), 'handout_names':(f'教材{c_i}')}
              for c_i in range(class_num_3)],                                   # handout_info_list
             [{'period':f'{c_i}', 'unit_name':f'ユニット{c_i}', 'thema':f'テーマ{c_i}',
               'room':f'C1{c_i}', 'teachers':f'教員{c_i}'}
              for c_i in range(class_num_3)]),                                  # class_info_list
            # 条件３
            ([{'urls':[dlpage_url(arg_2=f'{c_i}', arg_3=f'{h_i}') for h_i in range(handout_per_class_3)],
               'handout_names':[f'教材{c_i*h_i}' for h_i in range(handout_per_class_3)]}
              for c_i in range(class_num_3)],                                   # handout_info_list 
             [{'period':f'{c_i}', 'unit_name':f'ユニット{c_i}', 'thema':f'テーマ{c_i}',
               'room':f'C1{c_i}', 'teachers':f'教員{c_i}'}  
              for c_i in range(class_num_3)]),                                  # class_info_list
        ]
)
def test_get_dlpage_url_1(handout_infos_list, class_info_list):
    class_text = ''
    for c_i, class_info in enumerate(class_info_list):
        h_infos = handout_infos_list[c_i]
        class_info['handout'] = handout_template(urls=h_infos['urls'], 
                                                 handout_names=h_infos['handout_names'])
        class_text += class_template(**class_info)
    
    timetable_page = m1_timetable_template(class_infos=class_text)
    
    dlpage_urls = set(parser.get_dlpage_url(timetable_page))
    correct_dlpage_urls = set(handout_infos_list['urls'])
    assert dlpage_urls == correct_dlpage_urls

# エラー
# indexへリダイレクト -> LoginRequiredException
def test_get_dlpage_url_e0():
    index_page = index_template()
    with pytest.raises(exceptions.LoginRequiredException):
        parser.get_dlpage_url(index_page)

# menu, handout -> UnexpextedContentException
@pytest.mark.parametrize(
        'page',
        [
            (menu_template()),
            (handout_info_template())
        ]
)
def test_get_dlpage_url_e1(page):
    with pytest.raises(exceptions.UnexpextedContentException):
        parser.get_dlpage_url(page)