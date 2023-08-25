from typing import Literal
import re

import exceptions

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
            message = f'{page_type}ページを受け取りました。ログイン処理後に取得したページソースを' + \
                    'text引数に指定してください。'
            raise exceptions.UnexpextedContentException(message)