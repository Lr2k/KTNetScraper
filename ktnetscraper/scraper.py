import re
import os
import datetime
import time

import requests as rq
from bs4 import BeautifulSoup

from .exceptions import (
    WrongIdPasswordException,
    LoginRequiredException,
    UnexpextedContentException,
    IncompleteArgumentException,
)
from .utils import (
    type_checked,
    convert_to_date,
    convert_str_to_datetime,
)

# InsecureRequestWarningを非表示にする。
# この警告は、requestsのgetの引数にverify=Falseを指定した場合に発生するもの。
# 携帯ネット.comは金沢医科大学のサイトであり安全であることが確かなため、
# これらのエラー・警告を無視する。
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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

# プロキシサーバーのアドレスの初期値
_PROXIES = {
    'http' : 'http://proxy2.kanazawa-med.ac.jp:8080',
    'https' : 'http://proxy2.kanazawa-med.ac.jp:8080',
}
#==============================#


class Scraper(object):
    '''
    kt.kanazawa-med.ac.jpへのアクセス、ログイン状態の保持、教材情報の収集を行う。
    
    Attributes
    ----------
    session : requests.session.Session
        Sessionクラス。
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
    def __init__(self, session: rq.Session | None = None, enable_proxy: bool = False,
                 proxies: dict | None = None, interval: float | int = 2.0,
                 connect_timeout: float | int = 5.0, read_timeout: float | int = 5.0):
        '''
        Parameters
        ----------
        session : requests.Session, optional
            Sessionクラス。
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

        self.enable_proxy = type_checked(enable_proxy, bool)
        self.proxies = _PROXIES if proxies is None else type_checked(proxies, dict)

        self.interval = type_checked(interval, (float, int))
        
        self.connect_timeout = type_checked(connect_timeout, (float, int))
        self.read_timeout = type_checked(read_timeout, (float, int))

    def post(self, encoding: str | None = None, remove_new_line: bool = False,
             **kwargs) -> str | rq.Response:
        '''
        requestsを用いたPostを行う。サイトに最適化したPostを行う。
        proxyと文字コード等の処理も行う。

        Parameters
        ----------
        url : str or bytes
            urlを指定する。
        data : dict, opitonal
            送信データ。requests.post()のdata引数に直接渡される。
        timeout : tuple or list, optional
            connect timeoutとread timeoutの時間を指定する。
        verify : bool. Default is False.
            Falseの場合、SSL認証を無視する。
        encoding : str, optional
            文字コードを指定した場合は、受け取ったResponseオブジェクトをエンコードする。
            Noneを指定した場合は、Responseオブジェクトを返す。 
        remove_new_line: bool, default False
            Trueを指定した場合、改行コードを取り除く。

        Response
        --------
        str or requests.Response
            encodingで文字コードを指定した場合は、エンコードした文字列を返す。
            encodingでNoneを指定した場合は、Responseオブジェクトを返す。

        Raises
        ------
        requests.exceptions.ReadTimeout :
            読み込み時間が既定の時間を超えた。
        requests.exceptions.ConnectTimeout :
            接続時間が既定の時間を超えた。
        '''
        encoding = type_checked(encoding, str, allow_none=True)
        remove_new_line = type_checked(remove_new_line, bool)

        if self.enable_proxy:
            if "proxies" not in kwargs.keys():
                kwargs["proxies"] = self.proxies
        else:
            kwargs["proxies"] = None

        time.sleep(INTERVAL)
        response_data = self.session.post(**kwargs)

        if encoding is not None:
            response_data.encoding = encoding
            response_data = response_data.text
            if remove_new_line:
                response_data = response_data.replace('\n', '')

        return response_data

    def get(self, encoding: str | None = None,  remove_new_line: bool = False,
            **kwargs) -> str | rq.Response:
        '''
        requestsを用いたgetを行う。
        プロキシ設定の管理も行う。

        Parameters
        ----------
        url : str, optional
            urlを指定する。
        data : dict, opitonal
            送信データ。requests.post()のdata引数に直接渡される。
        timeout : tuple or list, optional
            connect timeoutとread timeoutの時間を指定する。
        verify : bool default False
            Falseの場合、SSL認証を無視する。
        encoding : str, optional
            文字コードを指定した場合は、指定した文字コードでエンコードしたテキストを返す。
            Noneを引数に渡した場合は、Responseオブジェクトを返す。
        remove_new_line : bool, default False
            Trueの場合、改行コードを取り除く。
        
        Return
        ------
        str or requests.Response
            encodingで文字コードを指定した場合は、その文字コードでエンコードした文字列を返す。
            encodingでNoneを指定した場合は、Responseオブジェクトを返す。

        Raises
        ------ 
        requests.exceptions.ReadTimeout :
            読み込み時間が既定の時間を超えた。
        requests.exceptions.ConnectTimeout :
            接続時間が既定の時間を超えた。
        '''
        encoding = type_checked(encoding, str, allow_none=True)
        remove_new_line = type_checked(remove_new_line, bool)

        if self.enable_proxy:
            if "proxies" not in kwargs.keys():
                kwargs["proxies"] = self.proxies
        else:
            kwargs["proxies"] = None

        time.sleep(INTERVAL)
        response_data = self.session.get(**kwargs)

        if encoding is not None:
            response_data.encoding = encoding
            response_data = response_data.text
            if remove_new_line:
                response_data = response_data.replace('\n', '')

        return response_data

    def login(self, id: str, password: str) -> None:
        '''
        ログイン処理を行う。
        実行後、login_statusメソッドでログインステータスを確認することを推奨。

        Parameters
        ----------
        id : str, optional
            学籍番号。ハイフンを含む。
            引数に学籍番号を渡すとインスタンス変数idに格納される。
        password : str, optional
            サイトログイン用のパスワード
            引数にパスワードを渡すとインスタンス変数passwordに格納される。
        
        Raises
        ------
        WrongIdPasswordError :
            学籍番号やパスワードが誤っているためログインに失敗した。
        '''
        id = type_checked(id, str)
        password = type_checked(password, str)

        login_data = {
            'strUserId': id,
            'strPassWord': password,
            'strFromAddress': ""
            }
        response_login = self.post(url=LOGIN_URL, data=login_data, verify=False,
                                   timeout=(_CONNECT_TIMEOUT, _READ_TIMEOUT),
                                   encoding=PAGE_CHARSET)
        if "ログインに失敗しました。" in response_login:
            raise WrongIdPasswordException('学籍番号もしくはパスワードが違います。')
        elif "■メニュー" in response_login:
            # ログインに成功
            pass
        else:
            raise UnexpextedContentException('想定されていない形式のページを受け取りました。'\
                                             f'method:post URL:{LOGIN_URL} data:{login_data}')

    def get_login_status(self):
        '''
        メニューページにアクセスし、ログイン状態を確認する。
        
        Return
        ------
        bool
            ログイン済みの場合はTrue、未ログインの場合はFalse。
        '''
        response = self.get(url=MENU_URL, timeout=(_CONNECT_TIMEOUT, _READ_TIMEOUT),
                            verify=False, encoding=PAGE_CHARSET, remove_new_line=True)

        if "■メニュー" in response:
            status = True
        elif "■ログイン":
            status = False
        else:
            raise UnexpextedContentException('想定されていない形式のページを受け取りました。'\
                                             f'method:get URL:{MENU_URL} data:')

        return status

    def get_faculty_and_grade(self) -> tuple[str, str]:
        '''
        サイトからログインユーザーの学部と学年を取得する。

        Return
        ------
        tuple[str, str]
            (faculty/学部, grade/学部)の形式で返す。
            医学部の場合は'M'、看護学部の場合は'N'を返す。
        
        Raises
        ------
        LoginRequiredException :
            未ログイン状態でサイトにアクセスしている。
        '''
        timetable_page = self.get(url=TIMETABLE_URL, encoding=PAGE_CHARSET,
                                  verify=False, remove_new_line=True)
        if '■ログイン' in timetable_page:
            raise LoginRequiredException('ログインしていません。')
        elif '■時間割' in timetable_page:
            # 問題なし
            pass
        else:
            raise UnexpextedContentException('想定されていない形式のページを受け取りました。'\
                                             f'method:get URL:{TIMETABLE_URL} data:None')

        faculty_grade = re.search('(..)学部\d年', timetable_page)
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

    def fetch_dlpage_urls(self, date: datetime.date | list[int | str] | tuple[int | str] | str,
                          faculty: str | None = None, grade: str | None = None) -> tuple[str]:
        '''
        各教材のダウンロードページへのURLを取得する。
        
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

        timetable_text = self.post(url=TIMETABLE_URL, data=form, verify=False,
                                   encoding=PAGE_CHARSET, remove_new_line=True)

        dlpage_urls : tuple
        if "ユニット名" in timetable_text:
            # 授業がある日のページを開いた場合の動作
            soup = BeautifulSoup(timetable_text, 'html.parser')
            # ダウンロードページのURLを取得
            dlpage_urls_list = []
            for link in soup.select("a[href^='./View_Kyozai']"):
                dlpage_urls_list.append(DLPAGE_URL_HEAD + link.get('href')[1:])
            dlpage_urls = tuple(dlpage_urls_list)
        elif "この日に講義はありません" in timetable_text:
            dlpage_urls = ()
        elif "■ログイン" in timetable_text:
            raise LoginRequiredException('ログインしていません。')
        else:
            raise UnexpextedContentException('想定されていない形式のページを受け取りました。'\
                                             f'method:get URL:{TIMETABLE_URL} data:{form}')

        return dlpage_urls

    def fetch_handout_from_dlpage(self, dlpage_url: str,
                                  date: datetime.date | list[int | str] | tuple[int | str] | str
                                  ) -> dict:
        '''
        教材のダウンロードページにアクセスし、情報を取得する。
        
        Parameters
        ----------
        dlpage_url : str
            教材ダウンロードページのURL
        date : datetime.datetime, datetime.date, list[int|str] or tuple[int|str], str
            URLを取得する時間割ページの日付を指定する。
            listやtupleで指定する場合は(年, 月, 日)の順で指定する。
            strで指定する場合は、年・月・日を'/'で区切る。(例:'1998/5/27', '1998/05/27')

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
        '''
        dlpage_url = type_checked(dlpage_url, str)
        date = convert_to_date(date)
        
        if os.path.isfile(path=dlpage_url):
            # ローカルファイルのパスの場合
            with open(dlpage_url, mode='r') as f:
                info_text = f.read().replace('\n', '')
        else:
            # URLの場合
            info_text = self.get(url=dlpage_url, verify=False, encoding=PAGE_CHARSET,
                                 remove_new_line=True)
            if "■教材情報" in info_text:
                pass
            elif "■ログイン" in info_text:
                raise LoginRequiredException('ログインしていません。')
            else:
                raise UnexpextedContentException('想定されていない形式のページを受け取りました。'\
                                                 f'method:get URL:{dlpage_url} data:')

        # '●'を目印に項目名を探す。
        points = re.finditer("●", info_text)
        point_position = [point.start() for point in points]

        info_keys = ("unit", "unit_num", "date", "period", "lesson_type", "thema",
                     "course", "teachers", "release_start_at", "release_end_at",
                     "name", "comments", "file_name", "url")
        info_dict = {key: None for key in info_keys}

        for i in (range(len(point_position))):
            if len(point_position)-2 <= i:
                # 一番後ろ、もしくは後ろから二番目の"●"の場合
                set = info_text[point_position[i]+1:]
            else:
                set = info_text[point_position[i]+1:point_position[i+1]]

            br_position = [br.start() for br in re.finditer("<br />", set)]

            # ●教材・資料名<br />　●R４高齢者の内分泌疾患4年<br />●教材・資料の説明
            # ↑のように要素内に'●'が使用されていると正常に読み込めない
            # 以下、その対策
            if len(br_position) in (0, 1):
                if len(point_position)-1 != i:
                    set = info_text[point_position[i]+1:point_position[i+2]]

                br_position = [br.start() for br in re.finditer("<br />", set)]

            title = set[:br_position[0]].strip() if len(br_position) > 0 else set
            element = set[br_position[0]+6:br_position[1]].strip() if len(br_position) > 0 else set

            if "本文" in title:
                # ダウンロード用のURLが含まれる項目
                dl_link = BeautifulSoup(title, 'html.parser').select("a[href^='./Download']")[0]

                dl_url_part = dl_link.get('href')
                DL_URL_HEAD = "https://kt.kanazawa-med.ac.jp/timetable"

                info_dict["url"] = DL_URL_HEAD + dl_url_part[1:]
                info_dict["file_name"] = dl_link.getText()

            elif "ユニ" in title:
                # ユニット名、回数、日付、時間を含むものに置き換える
                info_dict["unit"] = set[br_position[0]+6:br_position[1]].strip()
                info_dict["unit_num"] = set[br_position[1]+6:br_position[2]].strip()[1:3]
                info_dict["date"] = date
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
    
    def fetch_handout_infos(self, date: datetime.date | list[int | str] | tuple[int | str],
                            faculty: str | None = None, grade: str | None = None) -> tuple[dict]:
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
        '''
        date = convert_to_date(date)
        faculty = type_checked(faculty, str, allow_none=True)
        grade = type_checked(grade, str, allow_none=True)

        dlpage_urls = self.fetch_dlpage_urls(date=date, faculty=faculty, grade=grade)

        handout_infos_list = []
        for dlpage_url in dlpage_urls:
            handout_infos_list.append(self.fetch_handout_from_dlpage(dlpage_url=dlpage_url,
                                                                     date=date))

        return tuple(handout_infos_list)

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
        return self.get(url=url, verify=False).content