from typing import Literal
import re

from . import exceptions
from .utils import type_checked, convert_str_to_datetime


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
            return UNKNOWN
        else:
            raise ve
    
    initial_title = text[square_position + 1]
    match initial_title:
        case 'ロ':
            return LOGIN
        case 'メ':
            return MENU
        case '時':
            return TIMETABLE
        case '教':
            return HANDOUT
        case _ :
            return UNKNOWN


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
    text = type_checked(text, str)
    page_type = detect_page_type(text)
    if page_type == LOGIN:
        raise exceptions.LoginRequiredException('ログインしていません。')
    elif page_type != correct_page_type:
        message = f'想定されていない形式のページを受け取りました。(page type:{page_type})'
        raise exceptions.UnexpextedContentException(message)
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
        case 'menu' | 'timetable' | 'handout':
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
    
    faculty_grade = re.search(r'(..)学部\d年', text)
    # 学部
    if faculty_grade.group()[1]=='医':
        faculty = 'M'
    elif faculty_grade.group()[0:2]=='看護':
        faculty ='N'
    else:
        # 学院
        faculty_grade = re.search(r'(...)大学院（\d）\d年')
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
    text = type_checked(text, str).replace('\n', '')
    validate_page_type(text, TIMETABLE)

    # <a href=".|ココから→|/View_Kyozai.php?
    # kn=2023M5200780&kg=49&kz=5|←ここまで|">
    url_pattern = re.compile('<a href=".(/View_Kyozai.*?)">')
    return tuple(DLPAGE_URL_HEAD + url for url in re.findall(url_pattern, text))


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
    text = type_checked(text, str).replace('\n', '')
    validate_page_type(text, HANDOUT)

    # '●'を目印に項目名を探す。
    points = re.finditer("●", text)
    point_position = [point.start() for point in points]

    info_keys = ("unit", "unit_num", "period", "lesson_type", "thema",
                 "course", "teachers", "release_start_at", "release_end_at",
                 "name", "comments", "file_name", "url")
    info_dict = {key: None for key in info_keys}
    simple_contents_keys = {
        "区分": "lesson_type",
        "講義・実習内容": "thema",
        "講座": "course",
        "教材・資料名": "name",
        "教材・資料の説明": "comments",
    }
    simple_contents_titles = ("区分", "講座", "講義・実習内容",
                              "教材・資料名", "教材・資料の説明")

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
        len_br_pos = len(br_position)
        if len_br_pos in (0, 1):
            if len(point_position)-1 != i:
                set = text[point_position[i]+1:point_position[i+2]]

            br_position = [br.start() for br in re.finditer("<br />", set)]

        br_larger_0 = len_br_pos > 0
        title = set[:br_position[0]].strip() if br_larger_0 else set
        element = set[br_position[0]+6:br_position[1]].strip() if br_larger_0 else set


        # 要素に対し、特別な処理が必要ないもの
        if title in simple_contents_titles:
            info_dict[simple_contents_keys[title]] = element
        
        # "本文"はtitleにファイル名も含まれているため、本文を条件分岐の後半に設置すると、
        # ファイル名に"ユニ"などの文字列が含まれる場合に問題が生じる。
        elif "本文" in title:
            # ダウンロード用のURLが含まれる項目
            # hrefが見つからない場合、href_pos -> -1
            href_pos = title.find('href')
            if href_pos != -1:
                dl_link_part = title[href_pos+7:title.rfind('</a')]
                url_end = dl_link_part[:dl_link_part.find('"')]
                file_name = dl_link_part[dl_link_part.find('>')+1:]

                info_dict["url"] = DL_URL_HEAD + url_end
                info_dict["file_name"] = file_name
            else:
                pass
        
        elif "ユニ" in title:
            # ユニット名、回数、日付、時間を含むものに置き換える
            info_dict["unit"] = set[br_position[0]+6:br_position[1]].strip()
            info_dict["unit_num"] = re.sub(r'[第回\s]', '', set[br_position[1]+6:br_position[2]])
            info_dict["period"] = set[br_position[3]-2:br_position[3]-1]

        elif "担当" in title:
            # 担当教員
            info_dict["teachers"] = tuple(
                teacher.strip()
                for teacher in re.split('[,，、､]+', element)
            )

        elif "公開開始日" == title:
            # 公開開始日
            info_dict["release_start_at"] = convert_str_to_datetime(element)

        elif "公開終了日" == title:
            # 公開終了日
            info_dict["release_end_at"] = convert_str_to_datetime(element)

        else:
            pass


    return info_dict