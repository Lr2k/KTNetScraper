import requests as rq
from bs4 import BeautifulSoup
import re, os
import datetime

from .log import *
from .data_structures import *

# InsecureRequestWarningを非表示にする。
# この警告は requestsのgetの引数にverify=Falseを指定した場合に発生するもの。
# 携帯ネット.comは金沢医科大学のサイトであり安全であることが確かなため、
# これらのエラー・警告を無視する。
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WrongIdPassError(Exception):
    '''学籍番号またはパスワードが間違っていることを知らせる例外クラス。'''
    pass

class Scraper(object):
    '''
    kt.kanazawa-med.ac.jpへのアクセス、ログインの維持、教材情報の収集を行う。
    
    Attributes
    ----------
    session : requests.Session()
        Sessionクラス。
    id : str
        学籍番号。ハイフンを含む。
    password : str
        サイトログイン用のパスワード
    faculty : str
        学部。医学部の場合は"M"。看護学部の場合は"N"。大文字のみ。
    grade : str
        学年。一桁の半角数字。1年の場合は"1"。
    '''

    def __init__(self, session=None, id=None, password=None, faculty=None, grade=None, logging=True):
        '''
        Parameters
        ----------
        logging : bool
            Trueの場合、Logクラスによりログを残す。
        session : requests.Session()
            Sessionクラス。
        id : str
            学籍番号。ハイフンを含む。
        password : str
            サイトログイン用のパスワード
        faculty : str
            学部。医学部の場合は"M"。看護学部の場合は"N"。大文字のみ。
        grade : str
            学年。一桁の半角数字。1年の場合は"1"。'''

        self.session = session
        self.id = id
        self.password = password
        self.faculty = faculty      # 大文字 M or N
        self.grade = grade

        #loggerの初期化
        self.log = log.Logger(path='scraper.log')    

    def login(self, id=None, password=None, session=None):
        '''
        ログイン処理をする。
        Parameters
        ----------
        id : str
            学籍番号。ハイフンを含む。
            引数にidを渡すとself.idに登録される。
        password : str
            サイトログイン用のパスワード
            引数にpasswordを渡すとself.passwordに登録される。  
        session : requests.Session
            Sessionクラス。
        
        Notes
        -----
        1) 学籍番号、パスワードの誤りによりログインを失敗した場合はWrongIdPassErrorを返す。
        2) 想定されるエラー
            rq.exceptions.ReadTimeout : 読み込み時間が既定の時間を超えた場合。
            rq.exceptions.ConnectTimeout : 接続時間が既定の時間を超えた場合。

        '''
        # id, passwordが指定されていない場合はself.id, self.passwordを利用する。
        if id is not None:
            self.id = id

        if password is not None:
            self.password = password

        if session is not None:
            self.session = session
        elif self.session is None:
            self.session = rq.Session()
        else:
            pass
        
        # URLs
        INDEX_URL = "https://kt.kanazawa-med.ac.jp/index.php"
        LOGIN_URL = "https://kt.kanazawa-med.ac.jp/login/Check_Password.php"
        
        # indexページにアクセス
        response_index = self.session.get(url=INDEX_URL, verify=False)
        
        # ログイン時にpostする内容
        login_data = {
            'strUserId':self.id,
            'strPassWord':self.password,
            'strFromAddress':""
            }
        
        _CONNECT_TIMEOUT = 3.0   # 接続にかかる時間のリミット
        _READ_TIMEOUT = 5.0      # 読み込みにかかる時間のリミット

        response_login = self.session.post(url=LOGIN_URL, data=login_data, timeout=(_CONNECT_TIMEOUT, _READ_TIMEOUT))
        # debug

        response_login.encoding = 'cp932'

        if "ログインに失敗しました。" in response_login.text:
            self.log.log(status=1, message="ログインに失敗しました。 ID:" + self.id + " PassWord:" + '*'*len(self.password))
            raise WrongIdPassError
        else:
            pass

    def calc_faculty(self, id=None, return_value=False):
        '''
        学籍番号から学部を推測する。
        
        Parameters
        ----------
        id : str. Default is None.
            学籍番号。引数を渡さなければ、self.idから推測する。
        return_value : bool. Default is False.
            Trueを渡した場合は返り値として推測した学部を返し、self.facultyに反映しない。
            Falseを渡した場合は返り値を返さず、推測した学年をself.facultyに反映する。
        
        Return
        ------
        facutly : str
            推測した学部。引数にreturn_value=Trueを渡した場合のみ
        '''
        if id is None:
            id = self.id
        else:
            pass
        
        faculty = str()
        if id[0] == "m":    # 医学部
            faculty = "M"
        elif id[0] == "n":  # 看護学部
            faculty = "N"
        else:
            pass

        if return_value==True:
            return faculty
        else:
            self.faculty = faculty

    def calc_grade(self, id=None, return_value=False):
        '''
        学籍番号から学年を推測する。
        
        Parameters
        ----------
        id : str. Default is None.
            学籍番号。引数を渡さなければ、self.idから推測する。
        return_value : bool. Default is False.
            Trueを渡した場合は返り値として推測した学年を返し、self.gradeに反映しない。
            Falseを渡した場合は返り値を返さず、推測した学年をself.gradeに反映する。

        Return
        ------
        grade : str
            推測した学年。
            引数にreturn_value=Trueを渡した場合のみ。
        '''
        if id is None:
            id = self.id

        # 今日の日付を取得する
        dt_now = datetime.date.today()

        # 現在の年度を計算する
        year_now, month_now = dt_now.year, dt_now.month

        # 学籍番号から入学年度を計算する
        # ma0 -> 2000年度に入学
        id_alphabet = id[1]
        id_num = id[2]

        small_char = "abcdefghijklmnopqrstuvwxyz"
        
        decades_num = small_char.find(id_alphabet)
        year_admission = 2000 + decades_num*10 + int(id_num)
        
        # fyear:年度
        # 現在の年度を計算する
        if month_now <= 3:
            fyear_now = year_now - 1
        else:
            fyear_now = year_now
        
        grade = str(fyear_now - year_admission + 1)

        if return_value==True:
            return grade
        else: 
            self.grade = grade

    def get_dlpage_url(self, date_list, faculty=None, grade=None, session=None, return_year=False):
        '''
        各教材のダウンロードページへのURLを取得する。
        
        Parameters
        ----------
        date_list : list, tuple, str or int
            日付。複数の日付を指定する場合はリストやタプルに格納する。
            "YYYYMMDD"の形式で渡す。
        faculty : str. Default is None:
            学部。指定がない場合はself.facultyを用いる。
        grade : str
            学年。指定がない場合はself.gradeを用いる。
        session : requests.Session
            Sessionクラス。指定がない場合はself.sessionを用いる。
        return_year : bool. Default is False.
            Trueを指定した場合、授業が行われる年を格納したリストを返す。

        Returns
        -------
        dl_page_url_list : list
            ダウンロードページのURLを格納したリスト。
        year_list : list
            授業が行われる年を格納したリスト。ダウンロードページごとに要素を持つ。
        '''
        # date_listはリスト型もしくはstr型でうけとる
        # 日付の指定は"YYYYMMDD"
        if type(date_list) in (str, int):
            single = True
            date_list = [str(date_list)]
        else:
            pass

        if faculty is None:
            faculty = self.faculty
        
        if grade is None:
            grade = self.grade
        
        if session is None:
            session = self.session

        TIMETABLE_URL = "https://kt.kanazawa-med.ac.jp/timetable/List_Timetable.php"

        dl_page_url_list = list()
        year_list = list()
        for date in date_list:
            date = str(date)

            form = {
                'intSelectYear':date[0:4],
                'intSelectMonth':date[4:6],
                'intSelectDay':date[6:8],
                'strSelectGakubuNen': faculty + "," + grade
            }


            timetable_page = self.session.post(url=TIMETABLE_URL, data=form, verify=False)
            timetable_page.encoding = 'cp932'
            timetable_text = timetable_page.text.replace('\n', '')

            if "この日に講義はありません" in timetable_text:
                message = "時間割が存在しません。(" + date[0:4] + "/" + date[4:6] + "/" + date[6:8] + ")"
                self.log.log(status=0, message = message)
                pass

            elif "ユニット名" in timetable_text:
                # 授業がある日のページを開いた場合の動作
                soup = BeautifulSoup(timetable_text, 'html.parser')

                dl_page_url_head = "https://kt.kanazawa-med.ac.jp/timetable"



                for link in soup.select("a[href^='./View_Kyozai']"):
                    dl_page_url_element = link.get('href')[1:]
                    dl_page_url = dl_page_url_head + dl_page_url_element
                    dl_page_url_list.append(dl_page_url)
                    year_list.append(date[0:4])

                    message = date[0:4] + "/" + date[4:6] + "/" + date[6:8] + "の時間割ページからダウンロードページのURL(" + dl_page_url + ")を取得しました。"
                    self.log.log(status=0, message=message)
                
            else:
                message = "教材が見つかりませんでした。(" + date[0:4] + "/" + date[4:6] + "/" + date[6:8] + ")"
                self.log.log(status=0, message=message)
        
        if return_year:
            return dl_page_url_list, year_list
        else:
            return dl_page_url_list
    
    def get_text_info(self, dl_page_url, year="????"):
        '''
        ダウンロードページにアクセスし、教材の情報を取得する。
        取得した情報はTextオブジェクトに格納される。
        
        Parameters
        ----------
        dl_page_url : list or str.
            ダウンロードページ用のURL、またはそれを格納したリスト。
        year : list, str or int.
            授業が行われる年を指定する。
            str型もしくはint型で指定した場合は、全ての授業日を同じ年で指定する。

        Returns
        -------
        text_list : list
            取得した教材情報を保持するTextオブジェクトを格納したリスト。
        
        Notes
        -----
        1) 授業日(date)や時限(period)に関する情報は取得できないため、引数で指定する必要がある。
        '''
        
        if type(dl_page_url) == str:
            dl_page_url = [dl_page_url]
        else:
            pass
        
        if type(year) in (str, int):
            year = [str(year)[0:4]] * len(dl_page_url)
        else:
            pass

        text_list = list()
        for i in range(len(dl_page_url)):
            url = dl_page_url[i]
            _year = year[i]

            message = "ダウンロードページ(" + url + ")から教材情報を取得します。"
            self.log.log(status=0, message=message)
            kinds_of_value = list()

            text = Text()

            if (url[1]==':') or (url[0]=='.'):
                # ローカルファイルのパスの場合
                with open(url, mode='r') as f:
                    info_text = f.read().replace('\n', '')
            else:
                # URLの場合
                info_page = self.session.get(url, verify=False)
                info_page.encoding = 'cp932'
                info_text = info_page.text.replace('\n', '')

            # '●'を目印に項目名を探す。
            points = re.finditer("●", info_text)
            point_position = [point.start() for point in points]
            
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

                if title[:2] == "本文":
                    # ダウンロード用のURLが含まれる項目
                    dl_link = BeautifulSoup(title, 'html.parser').select("a[href^='./Download']")[0]

                    dl_url_part = dl_link.get('href')
                    DL_URL_HEAD = "https://kt.kanazawa-med.ac.jp/timetable"

                    dl_url = DL_URL_HEAD + dl_url_part[1:]
                    file_name = dl_link.getText()

                    text.url = dl_url
                    text.file_name = file_name

                    kinds_of_value.append("ダウンロードURL").append("ファイル名")

                elif "ユニ" in title:
                    # ユニット名、回数、日付、時間を含むものに置き換える
                    unit = set[br_position[0]+6:br_position[1]].strip()
                    unit_num = set[br_position[1]+6:br_position[2]].strip()[1:3]
                    date = set[br_position[2]+6:br_position[3]].strip()[:6].replace('月', '').replace('日', '')
                    period = set[br_position[3]-2:br_position[3]-1]
                    text.unit = unit
                    text.unit_num = unit_num
                    text.date = _year + date
                    text.period = period

                    kinds_of_value.append("ユニット名・回").append("授業日程")

                elif "区分" in title:
                    # 区分
                    text.lesson_type = element

                    kinds_of_value.append("区分")

                elif "講義" in title:
                    # 講義・実習内容
                    text.thema = element

                    kinds_of_value.append("講義・実習内容")

                elif "講座" in title:
                    # 講座名
                    text.course = element

                    kinds_of_value.append("講座名")

                elif "担当" in title:
                    # 担当教員
                    text.teachers= element
                    
                    kinds_of_value.append("担当教員")

                elif "公開開始日" == title:
                    # 公開開始日
                    text.upload_date = element.split()[0].replace('/', '')

                    kinds_of_value.append("公開開始日")

                elif "公開終了日" == title:
                    # 公開終了日
                    text.end_date = element.split()[0].replace('/', '')

                    kinds_of_value.append("公開終了日")

                elif "教材・資料名" == title:
                    # 教材・資料名
                    text.name = element

                    kinds_of_value.append("教材・資料名")
                
                elif "教材・資料の説明" == title:
                    # 教材・資料の説明
                    text.explanations = element

                    kinds_of_value.append("教材・資料の説明")

                else:
                    pass

            text_list.append(text)

            message = ""
            len_kinds_of_value = len(kinds_of_value)
            for i in range(len_kinds_of_value):
                kind = kinds_of_value[i]
                if i != len_kinds_of_value - 1:
                    message += ("'" + kind +"', ")
                else:
                    message += ("'" + kind +"'に関する情報を取得しました。")
            
            if message == "":
                message = "教材に関する情報を取得できませんでした。(" + url + ")"
            
        return text_list
    
    def dl(self, text, save_dir=None, file_name=None, save=True):
        '''
        ダウンロード用のURLからファイルをダウンロードする。

        Parameters
        ----------
        text: Text, Unit, str or list.
            引数として、TextオブジェクトもしくはUnitオブジェクトを渡す。
            str型でURLを直接指定も可。リストやタプルで複数していできるオブジェクトはText, strのみ。
        save_dir: str or list.
            保存先のパス、ファイル名を含まない。
            パスを指定しなかった場合はカレントディレクトリに保存する。
            保存先に同名のファイルが存在した場合、上書きする。
            複数の教材にたいしそれぞれ保存先を指定することが可能。
        file_name : str or list.
            Textオブジェクトによって指定されているファイル名と異なるファイル名を指定する場合に指定する。
            拡張子まで含める。
            file_nameを指定した場合はそのファイル名でファイルを保存する。
            save_dirを空にして、file_nameでパスを指定すればフルパスで保存先を指定可能。
        save: bool
            Falseを引数として渡した場合、保存をせずダウンロードしたデータを返す。   

        Return
        ------
        data : list or int
            save=Falseを指定した場合に、ダウンロードしたデータをリストに格納し返す。
            ダウンロードに失敗した教材については、空の要素をリストに追加する。
            save=Trueを指定した場合は、ダウンロードに失敗したテキストのindexを格納したリストを返す。
            Textもしくはstrでダウンロードをする教材を指定した場合はダウンロードに失敗した際、0を格納したリストを返す。
            全てのダウンロードに成功した場合は空のリストを返す。
        '''
        # 複数の型に対応できるよう、text, save_dir, file_nameをそれぞれ展開もしくリストへ格納する。
        # text, save_dir, file_nameはそれぞれの要素が１対１対１で対応するように
        # 指定のない項目については "" を指定する。

        if type(text).__name__ in ('str', 'Text'):
            text = [text]
        elif type(text).__name__ == 'Unit':
            text = text.text_list
        
        if save:
            if type(save_dir).__name__ in ('str', 'NoneType'):
                save_dir = [save_dir]
            if len(save_dir)==1:
                save_dir *= len(text)

            if type(file_name).__name__ in ('str', 'NoneType'):
                file_name = [file_name] * len(text)

            # ダウンロードに失敗した教材のindexを格納
            failed = list()
              
            for i in range(len(text)):
                _text = text[i]
                _file_name = file_name[i]
  
                if type(_text).__name__=='Text':
                    # Textオブジェクト固有の処理
                    if _text.target==False:
                        # targetの対象でない場合は終了
                        continue   # <- 問題あり
                    
                    if _file_name in ('', None):
                        # ファイル名の指定が無ければText.file_name
                        _file_name = _text.file_name

                    _text = _text.url
                
                if _file_name in ('', None):
                    # 利用できるファイル名がない場合
                    failed.append(i)
                    continue

                _save_dir = save_dir[i]
                if _save_dir is None:
                    # 保存先の指定がなかった場合、カレントディレクトリに保存
                    _save_dir = ('')
                    
                # ディレクトリの存在確認・作成
                if not os.path.exists(_save_dir):
                    os.makedirs(_save_dir)

                _save_path = os.path.join(_save_dir, _file_name)

                message = _file_name + "をダウンロードします。(" + _text + ")"
                self.log.log(status=0, message=message)

                count = 0
                limit = 5   # ５回チャレンジ
                while True:
                    count += 1
                    try:
                        data = self.session.get(_text, verify=False).content
                        message = _file_name + "のダウンロードに成功しました。"
                        self.log.log(status=0, message=message)

                        message = _file_name + "を保存します。(" + _save_path + ")"
                        self.log.log(status=0, message=message)

                        with open(_save_path, mode='wb') as f:
                            # バイナリ書き込みモード
                            f.write(data)
                            message = _file_name + "の保存に成功しました。"
                            self.log.log(status=0, message=message)
                        break
                    except Exception as e:
                        if count >= limit:
                            failed.append(i)
                            message = _file_name + "のダウンロード・保存に失敗しました。(" + str(i) + "):" + e 
                            self.log.log(status=2, message=message)
                            break
                        else:
                            message = _file_name + "のダウンロード・保存に失敗しました。(" + str(i) + "):" + e
                            self.log.log(status=2, message=message)
                            pass
            return failed

        else:
            data_list = list()
            for i in range(len(text)):
                _text = text[i]

                if type(_text).__name__=='Text':
                    _text = _text.url
                    if _text.target == False:
                        continue
                
                message = _text + "からファイルをダウンロードします。(" + _text + ")"
                self.log.log(status=0, message=message)
                
                count = 0
                limit = 5   # ５回チャレンジ

                while True:
                    count += 1
                    try:
                        data = self.session.get(_text, verify=False).content
                        message = _file_name + "から、ファイルのダウンロードに成功しました。"
                        self.log.log(status=0, message=message)
                        break
                    except:
                        if count >= limit:
                            data = None
                            message = _file_name + "から、ファイルのダウンロードに失敗しました。(" + str(i) + "):" + e
                            self.log.log(status=2, message=message)
                            break
                        else:
                            message = _file_name + "から、ファイルのダウンロードに失敗しました。(" + str(i) + "):" + e
                            self.log.log(status=2, message=message)
                            pass  
                
                data_list.append(data)
            
            return data_list



# 以下、サンプルコード。
def main():
    import getpass
    
    ID = input("StudentID: ")
    Pass = getpass.getpass("Password: ")
    scraper = Scraper(id=ID, password=Pass, faculty="M", grade="4")

    scraper.login()
    date = ["20220602", "20220603"]
    dl_page_url, year_list = scraper.get_dlpage_url(date)
    today = Unit(scraper.get_text_info(dl_page_url, year_list))

    titles = ["unit", "thema", "date", "period", "target", "lesson_type", "course", "file_name", "upload_date"]

    for line in today.export(titles=titles, separate_with_line=True):
        print(line)
    
    SAVE_DIR = ""
    datalist = scraper.dl(today, save_dir=SAVE_DIR)

    for data in datalist:
        print(type(data))

if __name__=='__main__':
    main()