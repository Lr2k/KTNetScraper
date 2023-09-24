import datetime
import time

import requests as rq

from .exceptions import (
    WrongIdPasswordException,
    UnexpextedContentException,
    IncompleteArgumentException,
)
from .utils import (
    type_checked,
    convert_to_date,
)
from . import parser

# 設定
#==============================#
# サイトのエンコードに適用する文字コード
PAGE_CHARSET = 'cp932'

# 各ページのURL
INDEX_URL = 'https://kt.kanazawa-med.ac.jp/index.php'
LOGIN_URL = 'https://kt.kanazawa-med.ac.jp/login/Check_Password.php'
MENU_URL = 'https://kt.kanazawa-med.ac.jp/login/Menu.php?'
TIMETABLE_URL = 'https://kt.kanazawa-med.ac.jp/timetable/List_Timetable.php'
DLPAGE_URL_HEAD = "https://kt.kanazawa-med.ac.jp/timetable"
DL_URL_HEAD = "https://kt.kanazawa-med.ac.jp/timetable"

# プロキシサーバーのアドレスの初期値
PROXIES = {
    'http' : 'http://proxy2.kanazawa-med.ac.jp:8080',
    'https' : 'http://proxy2.kanazawa-med.ac.jp:8080',
}
#==============================#
 
class Scraper(object):
    '''
    kt.kanazawa-med.ac.jpへのアクセス、ログイン状態の保持、教材情報の収集を行う。
    
    Attributes
    ----------
    session : requests.Session
        Sessionクラス。
    verify : bool
        TLS/SSLを有効化する場合はTrue。
    enable_proxy : bool
        プロキシサーバーを経由しアクセスする設定。
    proxies : dict
        プロキシアドレス。requests.Session.get()の引数proxiesに準ずる。
    interval : float
        ウェブサーバーへの過剰な不可を防ぐためのインターバル(秒)。
        アクセスを繰り返す場合は必ずインターバルを設定してください。
    connect_timeout : float
        接続にかける時間のリミット(秒)
    read_timeout : float
        接続後、読み込みにかける時間のリミット(秒)
    '''
    def __init__(self, session: rq.Session | None = None, verify: bool = True, 
                 enable_proxy: bool = False, proxies: dict | None = None,
                 interval: float | int = 2.0, connect_timeout: float | int = 5.0,
                 read_timeout: float | int = 5.0):
        '''
        Parameters
        ----------
        session : requests.Session, optional
            Sessionクラス。
        verify : bool, default True
            TLS/SSLを有効化する場合はTrue。
        enable_proxy : bool, default False
            プロキシサーバーを経由しアクセスする設定。
        proxies : dict, optional
            プロキシアドレス。requests.Session.get()の引数proxiesに準ずる。
        interval : float or int, default 2.0
            ウェブサーバーへの過剰な不可を防ぐためのインターバル(秒)。
            アクセスを繰り返す場合は必ずインターバルを設定してください。
        connect_timeout : float or int, default 5.0
            接続にかける時間のリミット(秒)
        read_timeout : float or int, default 5.0
            接続後、読み込みにかける時間のリミット(秒)
        '''
        self.session = rq.Session() if session is None else type_checked(session, rq.Session)

        self.verify = type_checked(verify, bool)
        if self.verify == False:
            ignore_insecure_warning()

        self.enable_proxy = type_checked(enable_proxy, bool)
        self.proxies = PROXIES if proxies is None else type_checked(proxies, dict)

        self.interval = float(type_checked(interval, (float, int)))
        
        self.connect_timeout = float(type_checked(connect_timeout, (float, int)))
        self.read_timeout = float(type_checked(read_timeout, (float, int)))
    
    def request(self, **kwargs) -> rq.Response:
        '''
        サーバーへのリクエストを行う。
        引数で指定しない限り、プロキシサーバーに関する設定(proxies)とSSL/TLSに関する設定
        (verify)はインスタンス初期化時の設定に従う。

        Parameters
        ----------
        url : str, optional
            urlを指定する。
        method : str, default 'GET'
            リクエストメソッドをGET, OPTIONS, HEAD, POST, PUT, PATCH, DELETEのいずれかで指定する。
        data : dict, opitonal
            送信するデータ。requests.post()のdata引数に直接渡される。
        verify : bool, optional
            Falseの場合、SSL/TLS認証を無視する。
            指定がなければ、インスタンス初期化時の設定が反映される。
        proxies : dict, optional
            利用するプロキシサーバーのアドレスを指定することで、プロキシサーバーを利用できる。
            指定がなければ、インスタンス初期化時の設定が反映される。
        encoding : str, optional
            Responseオブジェクトのencoding属性を指定する。
        
        Return
        ------
        requests.Response
        
        Notes
        -----
        - Parametersにあげた引数以外にも、requests.Session,request()と同じ引数を利用可能。
        '''
        kwargs_keys = kwargs.keys()
        
        encoding = None
        if 'encoding' in kwargs_keys:
            encoding = kwargs['encoding']
            kwargs.pop('encoding')

        if 'method' not in kwargs_keys:
            kwargs['method'] = 'GET'
        else:
            pass
        
        # 引数の設定を優先
        if 'verify' in kwargs_keys:
            if kwargs['verify'] == False:
                if self.verify == True:
                    # 初期化時に警告を無視する操作を行っていないため
                    ignore_insecure_warning()
            else:
                pass
        else:
            kwargs['verify'] = self.verify

        # 引数の設定を優先
        if 'proxies' in kwargs_keys:
            pass
        elif self.enable_proxy:
            kwargs['proxies'] = self.proxies
        else:
            pass

        time.sleep(self.interval)
        response_data = self.session.request(**kwargs)

        if encoding is not None:
            response_data.encoding = encoding
        return response_data

    def login(self, id: str, password: str) -> None:
        '''
        ログイン処理を行う。

        Parameters
        ----------
        id : str
            学籍番号。ハイフンを含む。
        password : str
            サイトログイン用のパスワード
        
        Raises
        ------
        WrongIdPasswordError :
            学籍番号やパスワードが誤っているためログインに失敗した。
        UnexpextedContentException :
            想定されていない形式のページを受け取った。
        '''
        id = type_checked(id, str)
        password = type_checked(password, str)

        login_data = {
            'strUserId': id,
            'strPassWord': password,
            'strFromAddress': ""
            }
        response = self.request(method='POST', url=LOGIN_URL, data=login_data,
                                encoding=PAGE_CHARSET)
        try:
            parser.login_status(response.text)
            
        except WrongIdPasswordException:
            raise WrongIdPasswordException('学籍番号もしくはパスワードが違います。')
        
        except UnexpextedContentException:
            login_data['strPassWord'] = '*' * len(login_data['strPassWord'])
            raise UnexpextedContentException('想定されていない形式のページを受け取りました。' +\
                                             f'method:post URL:{LOGIN_URL}' +\
                                             f'status_code:{response.status_code} ' +\
                                             'data:{login_data}')


    def login_status(self):
        '''
        ログイン状態を確認する。
        
        Return
        ------
        bool
            ログイン済みの場合はTrue、未ログインの場合はFalse。
        
        Raises
        ------
        UnexpextedContentException :
            想定されていない形式のページを受け取った。
        '''
        response = self.request(method='GET', url=MENU_URL, encoding=PAGE_CHARSET)

        return parser.login_status(response.text)


    def get_faculty_and_grade(self) -> tuple[str, str]:
        '''
        ログインユーザーの学部と学年を取得する。

        Return
        ------
        tuple[str, str]
            ('faculty/学部', 'grade/学年')の形式で返す。
            医学部の場合は'M'、看護学部の場合は'N'を返す。
        
        Raises
        ------
        LoginRequiredException :
            未ログイン状態でサイトにアクセスしている。
        UnexpextedContentException :
            想定されていない形式のページを受け取った。
        '''
        response = self.request(method='GET', url=TIMETABLE_URL, encoding=PAGE_CHARSET)
       
        return parser.get_faculty_and_grade(response.text)
    

    def get_dlpage_urls(self, date: datetime.date | list[int | str] | tuple[int | str] | str,
                          faculty: str | None = None, grade: str | None = None) -> tuple[str]:
        '''
        教材ダウンロードページへのURLを取得する。
        
        Parameters
        ----------
        date : datetime.datetime, datetime.date, list[int|str] or tuple[int|str], str
            URLを取得する時間割ページの日付を指定する。
            listやtupleで指定する場合は(年, 月, 日)の順で指定する。
            strで指定する場合は、年・月・日を'/'で区切る。(例:'1998/5/27', '1998/05/27')
        faculty : str, optional
            学部。指定する場合は学年の設定も必要。
            指定しない場合は、ログインユーザーの学部が適用される。
        grade : str, optional
            学年。指定する場合は学部の設定も必要。
            指定しない場合は、ログインユーザーの学年が適用される。

        Returns
        -------
        tuple[str]
            ダウンロードページのURL。

        Raises
        ------
        IncompleteArgumentException :
            必要な引数が提供されていない。
            faculty引数もしくはgrade引数のみが指定されており、もう一方が不足している。
        LoginRequiredException :
            未ログイン状態でサイトにアクセスした。
        UnexpextedContentException :
            想定されていない形式のページを受け取った。
        '''
        date = convert_to_date(date)

        faculty = type_checked(faculty, str, allow_none=True)
        grade = type_checked(grade, str, allow_none=True)
        if (faculty is None) != (grade is None):
            if faculty is None:
                message = '学年を指定した場合は、学部も指定してください。'
            else:
                message = '学部を指定した場合は、学年も指定してください。'
            raise IncompleteArgumentException(message)
        
        elif faculty is None:
            form = {'intSelectYear':date.strftime('%Y'),
                    'intSelectMonth':date.strftime('%m'),
                    'intSelectDay':date.strftime('%d'),}
        else:    
            form = {'intSelectYear':date.strftime('%Y'),
                    'intSelectMonth':date.strftime('%m'),
                    'intSelectDay':date.strftime('%d'),
                    'strSelectGakubuNen': f'{faculty},{grade}'}

        response = self.request(method='POST', url=TIMETABLE_URL,
                                data=form, encoding=PAGE_CHARSET)

        return parser.get_dlpage_url(response.text)


    def get_handoutinfo_from_dlpage(self, dlpage_url: str) -> dict:
        '''
        教材のダウンロードページにアクセスし、情報を取得する。
        
        Parameters
        ----------
        dlpage_url : str
            教材ダウンロードページのURL

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
        dlpage_url = type_checked(dlpage_url, str)
        
        response = self.request(method='GET', url=dlpage_url,
                                encoding=PAGE_CHARSET)
        
        return parser.get_handout_info(response.text)

    
    def get_handout_infos(self, date: datetime.date | list[int | str] | tuple[int | str],
                          faculty: str | None = None, grade: str | None = None
                          ) -> tuple[dict]:
        '''
        指定した日付に紐づけられている教材の情報を取得する。

        Parameters
        ----------
        date : datetime.datetime, datetime.date, list[int|str] or tuple[int|str], str
            URLを取得する時間割ページの日付を指定する。
            listやtupleで指定する場合は(年, 月, 日)の順で指定する。
            strで指定する場合は、年・月・日を'/'で区切る。(例:'1998/5/27', '1998/05/27')
        faculty : str, optional
            学部。指定する場合は学年の設定も必要。
            指定しない場合は、ログインユーザーの学部が適用される。
        grade : str, optional
            学年。指定する場合は学部の設定も必要。
            指定しない場合は、ログインユーザーの学年が適用される。
        
        Returns
        -------
        tuple[dict]
            (<handout_info>, ...)

            handout_info : dict
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
        IncompleteArgumentException :
            必要な引数が提供されていない。
            faculty引数もしくはgrade引数のみが指定されており、もう一方が不足している。
        LoginRequiredException :
            未ログイン状態でサイトにアクセスした。
        UnexpextedContentException :
            想定されていない形式のページを受け取った。
        '''
        date = convert_to_date(date)
        faculty = type_checked(faculty, str, allow_none=True)
        grade = type_checked(grade, str, allow_none=True)

        dlpage_urls = self.get_dlpage_urls(date=date, faculty=faculty, grade=grade)

        return tuple(
            self.get_handoutinfo_from_dlpage(dlpage_url=dlpage_url)
            for dlpage_url in dlpage_urls
        )

    def download(self, url: str) -> bytes:
        '''
        教材をダウンロードする。

        Parameters
        ----------
        url : str
            教材のダウンロードURL
                
        Returns
        -------
        bytes
            教材データか教材データを格納したリストを返す。
        '''
        url = type_checked(url, str)
        return self.request(method='GET', url=url).content


def ignore_insecure_warning():
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)