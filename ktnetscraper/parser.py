from typing import Literal
import re

from bs4 import BeautifulSoup

import exceptions
from utils import type_checked, convert_str_to_datetime


DLPAGE_URL_HEAD = "https://kt.kanazawa-med.ac.jp/timetable"
DL_URL_HEAD = "https://kt.kanazawa-med.ac.jp/timetable"

# page_type 
LOGIN = 'login'
MENU = 'menu'
TIMETABLE = 'timetable'
HANDOUT = 'handout'
UNKNOWN = 'unknown'


def detect_page_type(text: str) -> Literal['login', 'menu', 'timetable',
                                           'handout', 'unknown']:
    '''
    どのページか判定する。
    
    Parameters
    ----------
    text : str
        ページソース
    
    Returns
    -------
    str
        ログインページ -> 'login'
        メニュー -> 'menu'
        時間割ページ -> 'timetable'
        教材情報 -> 'handout'
        上記以外 -> 'unknown'
    '''
    text = type_checked(text, str).replace('\n', '')
    try:
        square_position = text.index('■')
    except ValueError as ve:
        if f'{ve}' == 'substring not found':
            return 'unknown'
        else:
            raise ve
    
    initial_title = text[square_position + 1]
    match initial_title:
        case 'ロ':
            return 'login'
        case 'メ':
            return 'menu'
        case '時':
            return 'timetable'
        case '教':
            return 'handout'
        case _ :
            return 'unknown'


def validate_page_type(text: str, correct_page_type: str) -> None:
    '''
    ページのタイプを検証する。
    
    Parameters
    ----------
    text : str
        ページのソース
    page_type : str
        正しいページのタイプ

    Raises
    ------
    LoginRequiredException :
        未ログイン状態で取得したページの可能性がある。
    UnexpextedContentException :
        想定されていない形式のページ。
    '''
    page_type = detect_page_type(text)
    if page_type == LOGIN:
        raise exceptions.LoginRequiredException(message='ログインしていません。')
    elif page_type != correct_page_type:
        message = f'想定されていない形式のページを受け取りました。(page type:{page_type})'
        raise exceptions.UnexpextedContentException(message=message)
    else:
        pass

    return page_type


def login_status(text: str) -> bool:
    '''
    ログインに成功しているか判定する。

    Parameters
    ----------
    text : str
        メニューページのソース
    
    Returns
    -------
    bool
        ログイン済みの場合、Trueを返す。
    
    Raises
    ------
    UnexpextedContentException :
        想定されていない形式のページを受け取った。
    '''
    text = type_checked(text, str).replace('\n', '')
    page_type = detect_page_type(text)
    match page_type:
        case 'menu':
            return True
        case 'login':
            return False
        case _ :
            message = f'ログイン処理後に取得したページソースを指定してください。' + \
                       '(page type:{page_type})'
            raise exceptions.UnexpextedContentException(message)


def get_faculty_and_grade(text: str) -> tuple[str, str]:
    '''
    ログインユーザーの学部と学年を取得する。

    Parameters
    ----------
    text : str
        時間割ページのソース

    Return
    ------
    tuple[str, str]
        (faculty/学部, grade/学部)の形式で返す。
        医学部の場合は'M'、看護学部の場合は'N'を返す。
    
    Raises
    ------
    LoginRequiredException :
        未ログイン状態で取得したページの可能性がある。
    UnexpextedContentException :
        想定されていない形式のページを受け取った。
    '''
    text = type_checked(text, str).replace('\n', '')
    validate_page_type(text, TIMETABLE)
    
    faculty_grade = re.search('(..)学部\d年', text)
    # 学部
    if faculty_grade.group()[1]=='医':
        faculty = 'M'
    elif faculty_grade.group()[0:2]=='看護':
        faculty ='N'
    else:
        # 学院
        faculty_grade = re.search('(...)大学院（\d）\d年')
        if faculty_grade.group()[0:3] == '看護学':
            faculty = 'K'
        else:
            faculty = 'D'
    
    grade = faculty_grade.group()[-2]
    
    return (faculty, grade)


def get_dlpage_url(text: str) -> tuple[str]:
    '''
    教材ダウンロードページへのURLを取得する。
    
    Parameters
    ----------
    text : str
        時間割ページのソース
    
    Returns
    -------
    tuple[str]
        ダウンロードページのURL。

    Raises
    ------
    LoginRequiredException :
        未ログイン状態でサイトにアクセスした。
    UnexpextedContentException :
        想定されていない形式のページを受け取った。
    '''
    text = type_checked(text).repalce('\n', '')
    validate_page_type(text, TIMETABLE)

    soup = BeautifulSoup(text, 'html.parser')
    dlpage_urls = tuple(DLPAGE_URL_HEAD + link.get('href')[1:]
                        for link in soup.select("a[href^='./View_Kyozai']"))

    return dlpage_urls


def get_handout_info(text: str) -> dict:
    '''
    教材のダウンロードページにアクセスし、情報を取得する。
    
    Parameters
    ----------
    text : str
        教材ページのソース

    Returns
    -------
    dict
        取得した教材情報をdictに格納する。\n
        サイトに情報が掲載されていない項目は値がNoneとなる。\n
        <key> : <type of value>\n
        "unit" : str
            ユニット名
        "unit_num" : str
            ユニットの何回目の講義か
        "date" : datetime.date
            講義が行われる日付
        "period" : str
            講義が行われる時限
        "lesson_type" : str
            講義の区分
        "thema" : str
            講義内容
        "course" : str
            講座名
        "teachers" : tuple[str]
            教員名
        "release_start_at" : datetime.datetime
            教材の公開開始日時
        "release_end_at" : datetime.datetime
            教材の公開終了日時
        "name" : str
            教材の名前
        "comments" : str
            教材に関する説明
        "file_name" : str
            教材の拡張子付きファイル名
        "url" : str
            教材のダウンロードURL

    Raises
    ------
    LoginRequiredException :
        未ログイン状態でサイトにアクセスした。
    UnexpextedContentException :
        想定されていない形式のページを受け取った。
    '''
    text = type_checked(text).repalce('\n', '')
    validate_page_type(text, HANDOUT)

    # '●'を目印に項目名を探す。
    points = re.finditer("●", text)
    point_position = [point.start() for point in points]

    info_keys = ("unit", "unit_num", "period", "lesson_type", "thema",
                    "course", "teachers", "release_start_at", "release_end_at",
                    "name", "comments", "file_name", "url")
    info_dict = {key: None for key in info_keys}

    for i in (range(len(point_position))):
        if len(point_position)-2 <= i:
            # 一番後ろ、もしくは後ろから二番目の"●"の場合
            set = text[point_position[i]+1:]
        else:
            set = text[point_position[i]+1:point_position[i+1]]

        br_position = [br.start() for br in re.finditer("<br />", set)]

        # ●教材・資料名<br />　●R４高齢者の内分泌疾患4年<br />●教材・資料の説明
        # ↑のように要素内に'●'が使用されていると正常に読み込めない
        # 以下、その対策
        if len(br_position) in (0, 1):
            if len(point_position)-1 != i:
                set = text[point_position[i]+1:point_position[i+2]]

            br_position = [br.start() for br in re.finditer("<br />", set)]

        title = set[:br_position[0]].strip() if len(br_position) > 0 else set
        element = set[br_position[0]+6:br_position[1]].strip() if len(br_position) > 0 else set

        if "本文" in title:
            # ダウンロード用のURLが含まれる項目
            dl_link = BeautifulSoup(title, 'html.parser').select("a[href^='./Download']")[0]

            dl_url_part = dl_link.get('href')

            info_dict["url"] = DL_URL_HEAD + dl_url_part[1:]
            info_dict["file_name"] = dl_link.getText()

        elif "ユニ" in title:
            # ユニット名、回数、日付、時間を含むものに置き換える
            info_dict["unit"] = set[br_position[0]+6:br_position[1]].strip()
            info_dict["unit_num"] = set[br_position[1]+6:br_position[2]].strip()[1:3]
            info_dict["period"] = set[br_position[3]-2:br_position[3]-1]

        elif "区分" in title:
            # 区分
            info_dict["lesson_type"] = element

        elif "講義" in title:
            # 講義・実習内容
            info_dict["thema"] = element

        elif "講座" in title:
            # 講座名
            info_dict["course"] = element

        elif "担当" in title:
            # 担当教員
            teachers = element.split(',')
            teachers = [teacher.strip() for teacher in teachers]
            info_dict["teachers"] = tuple(teachers)

        elif "公開開始日" == title:
            # 公開開始日
            info_dict["release_start_at"] = convert_str_to_datetime(element)

        elif "公開終了日" == title:
            # 公開終了日
            info_dict["release_end_at"] = convert_str_to_datetime(element)

        elif "教材・資料名" == title:
            # 教材・資料名
            info_dict["name"] = element
        
        elif "教材・資料の説明" == title:
            # 教材・資料の説明
            info_dict["comments"] = element

        else:
            pass

    return info_dict