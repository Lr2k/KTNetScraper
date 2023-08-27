import requests as rq
from requests import structures
from unittest.mock import patch

import pytest

from ktnetscraper import Scraper
from ktnetscraper.exceptions import (
    WrongIdPasswordException,
)
import template


INDEX_URL = 'https://kt.kanazawa-med.ac.jp/index.php'
LOGIN_URL = 'https://kt.kanazawa-med.ac.jp/login/Check_Password.php'
MENU_URL = 'https://kt.kanazawa-med.ac.jp/login/Menu.php?'
TIMETABLE_URL = 'https://kt.kanazawa-med.ac.jp/timetable/List_Timetable.php'
DLPAGE_URL_HEAD = "https://kt.kanazawa-med.ac.jp/timetable"
DL_URL_HEAD = "https://kt.kanazawa-med.ac.jp/timetable"

PAGE_ENCODING = 'cp932'

CORRECT_ID = 'correct_id'
CORRECT_PASSWORD = 'CORRECT_PASSWORD'
HANDOUT_DATA = b'\x48\x65\x6c\x6c\x6f\x2c\x20\x57\x6f\x72\x6c\x64\x21'

PROXIES_TEST = {'http':'http://init', 'https':'https://init'}


class Response():
    def __init__(self, content: bytes =None, encoding='utf-8',
                 url=None, status_code:int = 200):
        self.content = content
        self.encoding = encoding
        self.text = content.decode(encoding)
        self.url = url
        self.status_code = status_code


def create_response(content: str | bytes, url: str,
                     status_code: int = 200, binary=False):
    if binary:
        response = Response(content=content, url=url,
                            status_code=status_code)
    else:
        content = content.encode(PAGE_ENCODING)
        response = Response(content=content, url=url,
                            status_code=status_code)
    return response


# Scraper()
# 適切な型のattributesを持っていることを確認

# デフォルトで初期化
# 型で初期値を確認
def test_scraper_init_0():
    scraper = Scraper(interval=0)

    assert type(scraper.session) == rq.Session
    assert type(scraper.verify) == bool
    assert scraper.verify == True
    assert type(scraper.enable_proxy) == False
    assert scraper.enable_proxy == False
    assert type(scraper.proxies) == dict
    assert type(scraper.interval) == float
    assert type(scraper.connect_timeout) == float
    assert type(scraper.read_timeout) == float

# 正常動作
# 受け入れ可能な型と初期化後の属性の型, 値を確認
test_session = rq.Session()
test_session.a = 'test'
@pytest.mark.parametrize(
        'session, attrs_session, verify, attrs_verify, ' + \
        'enable_proxy, attrs_enable_proxy, ' + \
        'proxies, attrs_proxies, interval, attrs_interval, ' + \
        'connect_timeout, attrs_connect_timeout, ' + \
        'read_timeout, attrs_read_timeout',
        [
            (test_session, test_session, True, True,
             False, False,
             PROXIES_TEST, PROXIES_TEST,
             10.0, 10.0, 3.0, 3.0, 6.0, 6.0),
            (test_session, test_session, False, False,
             True, True,
             PROXIES_TEST, PROXIES_TEST,
             1, 1.0, 7, 7.0, 2, 2.0)
        ]
)
def test_scraper_init_1(
    session, attrs_session, verify, attrs_verify,
    enable_proxy, attrs_enable_proxy,
    proxies, attrs_proxies, interval, attrs_interval,
    connect_timeout, attrs_connect_timeout,
    read_timeout, attrs_read_timeout):
    
    scraper = Scraper(
        session, verify, enable_proxy, proxies, interval,
        connect_timeout, read_timeout
    )

    assert type(scraper.session) == type(attrs_session)
    assert scraper.session.a == attrs_session.a

    assert type(scraper.verify) == bool
    assert scraper.verify == attrs_verify
    
    assert type(scraper.enable_proxy) == bool
    assert scraper.enable_proxy == attrs_enable_proxy
    
    assert type(scraper.proxies) == dict
    assert scraper.proxies == attrs_proxies

    assert type(scraper.interval) == float
    assert scraper.interval == attrs_interval

    assert type(scraper.connect_timeout) == float
    assert scraper.connect_timeout == attrs_connect_timeout

    assert type(scraper.read_timeout) == float
    assert scraper.read_timeout == attrs_read_timeout

# Scraper.request()
# 初期化時にSessionオブジェクトのモックを渡す

# requestメソッド内でモック.requestに渡された引数が想定道理か確認する
# request()とconf_request()を持たせ、想定する引数を設定し、想定されていない引数が指定された場合はエラーを返す
# 

def mock_session_request(cls, **kwargs):
    url = kwargs['url']

    dl_url = f'{DL_URL_HEAD}/Download.php?test'

    if url == INDEX_URL:
        return create_response(content=template.index_template(),
                               url=url)
    elif url == LOGIN_URL:
        data = kwargs['data']
        if ('strUserId' in data.keys()) and ('strPassWord' in data.keys()):
           if (data['strUserId']=='correct_id') and (data['strPassWord']=='correct_password'):
               return create_response(content=template.menu_template(),
                                      url=url)
        return create_response(content=template.login_failed_template(),
                               url=url)
    elif url == MENU_URL:
        return create_response(content=template.menu_template())
    elif url == TIMETABLE_URL:
        faculty = '医'
        grade = '6'
        date = '2000/01/01'
        
        if 'data' in kwargs.keys():
            data = kwargs['data']
            date = f'{data["intSelectYear"]}/{data["intSelectMonth"]}/{data["intSelectDay"]}'
            if 'strSelectGakubuNen' in data.keys():
                faculty_dict = {'M':'医', 'N':'看護'}
                faculty = faculty_dict[data['strSelectGakubuNen'][0]]
                grade = data['strSelectGakubuNen'][2]
        
        return create_response(
            content=template.timetable_no_class_template(
                faculty=faculty, grade=grade, date=date,
                days_of_week='土'
            ),
            url=url,
        )
    elif DLPAGE_URL_HEAD in url:
        page_content = {
            'faculty': '医', 
            'grade': '3',
            'unit': 'ユニット_1',
            'unit_num': '22',
            'date_month': '10',
            'date_days': '21',
            'days_of_week': '土',
            'period': '2',
            'lesson_type': '講義',
            'thema': 'テーマ_1',
            'core_carriculum': 'X-1-1)',
            'course': 'コース_1',
            'teachers': '教員_1',
            'release_start_at': '1999/12/31 23:59',
            'release_end_at': '2000/01/01 00:00',
            'name': '教材_1',
            'comments': '説明_1',
            'url': dl_url,
            'file_name': 'ファイル1'
        }
        return create_response(
            content=template.handout_info_template(**page_content),
            url=url
        )
    elif DL_URL_HEAD in url:
        return create_response(content=HANDOUT_DATA,
                               url=url, binary=True)
    else:
        # url = 'test'
        content_list = ['test',f'url:{url}']
        kwargs_keys = kwargs.keys()
        if 'proxies' in kwargs_keys:
            content_list.append(f'proxies:{kwargs["proxies"]}')
        else:
            content_list.append('proxies:None')

        if 'verify' in kwargs_keys:
            content_list.append(f'verify:{kwargs["verify"]}')

        return create_response(content=','.join(content_list),
                               url=url)
    
@pytest.fixture
def mock_session_request_fixture(monkeypatch):
    monkeypatch.setattr(rq.Session, 'request', mock_session_request)


# Session.requestに渡される引数を確認


# 返り値の型がrequest.Responseであることを確認する。
def test_scarper_request_0(mock_session_request_fixture):
    scraper = Scraper(interval=0)
    response = scraper.request(url='test', encoding=PAGE_ENCODING)
    assert type(response) == Response

# メソッドに渡された引数が優先されることを確認(enable_proxy)
# proxies無し scraper.enable_proxyに従ってscraper.proxiesが渡される
# proxiesあり proxisが渡される。
# proxies_sess_requ_recieve: Literal['init'->初期化時のアドレス,
#                                    'arg'->引数で指定したアドレス,
#                                    'none'->渡されていない,]
PROXIES_ARG = {'http':'http://arg', 'https':'https://arg'}
@pytest.mark.parametrize(
        'init_enable_proxy, proxies, proxies_sess_requ_recieve',
        [
            (False, None, 'None'),
            (True, None, 'init'),
            (False, PROXIES_ARG, 'arg'),
            (True, PROXIES_ARG, 'arg'),
        ]
)
def test_scraper_request_1(mock_session_request_fixture,
                           init_enable_proxy, proxies,
                           proxies_sess_requ_recieve):
    scraper = Scraper(enable_proxy=init_enable_proxy,
                      proxies=PROXIES_TEST, interval=0)
    response = scraper.request(url='test', proxies=proxies)
    text = response.text

    if 'proxies:None' in text:
        assert f'proxies:{proxies_sess_requ_recieve}' in text
    else:
        assert (f'http://{proxies_sess_requ_recieve}' in text) and \
               (f'https://{proxies_sess_requ_recieve}' in text)


# verify引数が指定されている場合は、Scraper.requestメソッドに渡される。
# verify引数が指定されていない場合は、Scraper.verifyの設定を渡す。
# init_verify, arg_verify, out_verify
# False, None -> False
# True, None -> True
# False, True -> True
# True, False
@pytest.mark.parametrize(
    'init_verify, arg_verify, out_verify',
    [
        (False, None, False),
        (True, None, True),
        (False, True, True),
        (True, False, False),
    ]
)
def test_scraper_request_2(mock_session_request_fixture,
                           init_verify, arg_verify, out_verify):
    scraper = Scraper(verify=init_verify, interval=0)
    response = scraper.request(url='text', verify=arg_verify)
    response.encoding = PAGE_ENCODING
    assert f'verify:{out_verify}' in response.text


# 実際のサーバーを利用したテストを行います。
skip_test = True
def test_scraper():
    if skip_test:
        return
    
    scraper = Scraper()
    id = 'mx0-0000'
    password = 'password'
    scraper.login(id, password)
    assert scraper.get_login_status()
    
    scraper.get_faculty_and_grade()

    handout_infos = scraper.fetch_handout_infos(
        date=["2023/04/12"],
        faculty='M', grade='1'
    )

    for handout in handout_infos:
        scraper.download(url=handout['url'])