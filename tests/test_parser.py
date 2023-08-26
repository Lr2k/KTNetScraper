from functools import partial
import datetime

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


tz_jst = datetime.timezone(datetime.timedelta(hours=9), name='JST')


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
        "arg_faculty, arg_grade, out",
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
            ([{'urls':[dlpage_url(arg_2='1')], 'handout_names':['教材1']}],    # handout_info_list
             [{'period':'1', 'unit_name':'ユニット1', 'thema':'テーマ1', 'room':'C11',
               'teachers':'教員1'}]),                                           # class_info_list
            # 条件２
            ([{'urls':[dlpage_url(arg_2=f'{c_i}')], 'handout_names':[f'教材{c_i}']}
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
    correct_dlpage_url_list = [urls for handout_infos in handout_infos_list
                               for urls in handout_infos['urls']]
    correct_dlpage_urls = set('https://kt.kanazawa-med.ac.jp/timetable' + url[1:]
                              for url in correct_dlpage_url_list)

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

# get_handout_info

# 正常動作
@pytest.mark.parametrize(
        'contents, correct_handout',
        [
            ({'faculty': '医',
              'grade': 1,
              'unit': 'ユニットA',
              'unit_num': '2',
              'date_month': '03',
              'date_days': '04',
              'days_of_week': '土',
              'period': '5',
              'lesson_type': '講義',
              'thema': 'テーマB',
              'core_carriculum': 'X-1-1)',
              'course': 'C学',
              'teachers': '教員D',
              'release_start_at': '2000/01/01 03:34',
              'release_end_at': '2001/12/23 19:03',
              'name': '教材E',
              'comments': '当日この資料は配付しません。必要であれば印刷・持参して下さい。',
              'url': './Download.php?year=2000&kn=2000M0000000&kg=50&kz=1',
              'file_name': 'レジュメ６.pdf'},
             {'unit': 'ユニットA',
              'unit_num': '2',
              'period': '5',
              'lesson_type': '講義',
              'thema': 'テーマB',
              'course': 'C学',
              'teachers': ('教員D',),
              'release_start_at': datetime.datetime(2000, 1, 1, 3, 34,
                                                    tzinfo=tz_jst),
              'release_end_at': datetime.datetime(2001, 12, 23, 19, 3,
                                                   tzinfo=tz_jst),
               'name': '教材E',
               'comments': '当日この資料は配付しません。必要であれば印刷・持参して下さい。',
               'url': 'https://kt.kanazawa-med.ac.jp/timetable/Download.php?year=2000&kn=2000M0000000&kg=50&kz=1',
               'file_name': 'レジュメ６.pdf'}),
               # ハイリスク
             ({'faculty': '看護',
              'grade': 6,
              'unit': 'FORTRAN　（Aクラス Bクラス●1コース）',
              'unit_num': '12345',
              'date_month': '05',
              'date_days': '27',
              'days_of_week': '月',
              'period': '9',
              'lesson_type': '演習',
              'thema': '　　　　―　確認練習',
              'core_carriculum': 'X-1-1)',
              'course': '一般教育機構●量子力学',
              'teachers': '牧瀬教授,岡部講師, 橋田講師､椎名講師、比屋定助教',
              'release_start_at': '2010/07/28 12:56',
              'release_end_at': '2010/07/23 12:56',
              'name': '零化域のミッシングリンク',
              'comments': 'あ●い・う　え お',
              'url': './Download.php?year=2000&kn=2000M0000000&kg=50&kz=1',
              'file_name': 'Absolute Zero.stn'},
             {'unit': 'FORTRAN　（Aクラス Bクラス●1コース）',
              'unit_num': '12345',
              'period': '9',
              'lesson_type': '演習',
              'thema': '―　確認練習',
              'course': '一般教育機構●量子力学',
              'teachers': ('牧瀬教授', '岡部講師', '橋田講師', '椎名講師', '比屋定助教'),
              'release_start_at': datetime.datetime(2010, 7, 28, 12, 56,
                                                    tzinfo=tz_jst),
              'release_end_at': datetime.datetime(2010, 7, 23, 12, 56,
                                                   tzinfo=tz_jst),
               'name': '零化域のミッシングリンク',
               'comments': 'あ●い・う　え お',
               'url': 'https://kt.kanazawa-med.ac.jp/timetable/Download.php?year=2000&kn=2000M0000000&kg=50&kz=1',
               'file_name': 'Absolute Zero.stn'})
        ]
)
def test_get_handout_info_0(contents, correct_handout):
    handout_info_page = handout_info_template(**contents)
    handout = parser.get_handout_info(handout_info_page)
    assert handout == correct_handout


# エラー
# index -> LoginRequiredException
def test_get_handout_info_e0():
    index_page = index_template()
    with pytest.raises(exceptions.LoginRequiredException):
        parser.get_handout_info(index_page)

# menu, timetable -> UnexpextedContentException
@pytest.mark.parametrize(
        'page',
        [
            (menu_template()),
            (timetable_template())
        ]
)
def test_get_handout_info_e1(page):
    with pytest.raises(exceptions.UnexpextedContentException):
        parser.get_handout_info(page)