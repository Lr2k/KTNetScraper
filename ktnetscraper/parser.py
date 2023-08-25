from typing import Literal
import re

import exceptions
from utils import type_checked

def detect_page_type(text: str) -> Literal['login', 'menu', 'timetable',
                                           'change_timetable', 'handout', 
                                           'unknown']:
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
    text = type_checked(text).replace('\n', '')
    page_type = detect_page_type(text)
    if page_type == 'login':
        raise exceptions.LoginRequiredException(message='ログインしていません。')
    elif page_type != 'timetable':
        message = f'想定されていない形式のページを受け取りました。(page type:{page_type})'
        raise exceptions.UnexpextedContentException(message=message)
    else:
        pass
    
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