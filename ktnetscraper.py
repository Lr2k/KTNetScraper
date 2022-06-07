import requests as rq
from bs4 import BeautifulSoup
import unicodedata
import re, os
import datetime
import copy

# InsecureRequestWarningを非表示にする。
# この警告は requestsのgetの引数にverify=Falseを指定した場合に発生するもの。
# 携帯ネット.comは金沢医科大学のサイトであり安全であることが確かなため、
# これらのエラー・警告を無視する。
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WrongIdPassError(Exception):
    '''学籍番号またはパスワードが間違っていることを知らせる例外クラス。'''
    pass

class Text(object):
    '''
    教材(レジュメ)の情報に関する情報を保持し、それらの情報を操作するメソッドを持つ。

    Attributes
    ----------
    name : str
        教材情報のページに登録されている教材・資料の名前。
        ファイル名とは異なる。拡張子はついていない。
    unit : str
        ユニット名。
    unit_num : int
        ユニットの何回目の授業かを示す。
        登録されていない教材もある。"第〇回"。
    thema : str
        講義・実習内容。登録されていない教材もある。
    teachers : list
        教員名。複数人が登録されている場合、名前の間はカンマ","で区切られている。
    lesson_type : str 
        授業の区分・ジャンル。"演習" や "講義" など。
    course : str
        講座名。ユニット名とは異なる。
    upload_date : str
        教材の公開開始日。
        日付は8桁の半角数字で構成される文字列で保持する。
    end_date : str
        教材の公開終了日。
        日付は8桁の半角数字で構成される文字列で保持する。
    explanations : str
        教材の説明。
    file_name : str
        教材のファイル名。拡張子をもつ。
    date : str
        教材が登録されている授業が行われる日付。
        8桁の半角数字で構成される。
    period : str
        教材が登録されている授業が行われる時限。
        1桁の半角数字で構成される。
    url : str
        ダウンロード用のURL
    target : bool
        ダウンロードする対象の場合はTrue、ダウンロードしない対象の場合はFalse。

    '''
    def __init__(self, name=None, unit=None, unit_num=None, thema=None, teachers=None, date=None, period=None, url=None, lesson_type=None, course=None, upload_date=None, end_date=None, explanations=None, file_name=None, target=True):
        '''
        Parameters
        ----------
        teachers : list or str
            教員名。複数人登録されている場合はカンマ","で区切られている。
            strの場合は要素がひとつのlistに変換する。
        upload_date : str or int
            教材の公開開始日。
            日付は8桁の半角数字で構成される文字列で保持する。
            intの場合はstrに変換する。
        end_date : str
            教材の公開終了日。
            日付は8桁の半角数字で構成される文字列で保持する。
            intの場合はstrに変換する。
        date : str or int
            教材が登録されている授業が行われる日付。
            8桁の半角数字で構成される。intの場合はstrに変換する。
        period : str or int
            教材が登録されている授業が行われる時限。
            1桁の半角数字で構成される。intの場合はstrに変換する。
        '''

        self.name = name        
        self.unit = unit        
        self.unit_num = unit_num
        self.thema = thema      
        
        if type(teachers)==str:
            self.teachers = [teachers]
        elif type(teachers)==list:
            self.teachers = teachers
        else:
            self.teachers = None

        self.lesson_type = lesson_type    
        self.course = course              
        
        self.upload_date = str(upload_date) if type(upload_date) in (int, str) else None

        self.end_date = str(end_date) if type(end_date) in (int, str) else None

        self.explanations = explanations 
        self.file_name = file_name        

        self.date = str(date) if type(date) in (int, str) else None

        self.period = str(period) if type(period) in (int, str) else None

        self.url = url      
        self.target = target

    def show(self, titles=None, width=None, separate_with_line=False):
        '''
        Textの保持する情報を一行の文字列にまとめ、返す。

        Parameters
        ----------
        titles : list, tuple or str. Default is None.
            文字列に並べる項目とその順番を指定する。
            一項目のみの指定は要素が一つのリストに変換する。
        width : list , tuple or str. Default is None.
            項目ごとの文字列長を指定する。半角は1文字、全角は2文字としてカウントする。
            widthがstrやintの場合は項目の数と合わせリストに変換する。
        separate_with_line : bool. Default is False.
            Trueの場合は、項目間を" | "で区切る。
            Falseの場合は、項目間を"   "で区切る。

        Returns
        -------
        line : str
            一行の文字列にTextの情報を連ねたもの。
        
        Notes
        -----
        1) titlesがNoneだった場合、既定の順で項目を並べる
        2) 文字列幅の指定がなかった項目は、文字幅が制限されない。
        widthの要素数と項目数が合わなかった場合、各項目に対し文字幅の指定を先頭詰めで適用する。
        後半の項目は文字幅の指定がないものとする。
        '''

        if titles is None:
            # 表示する項目が指定されなかった場合の項目の指定
            titles = ["unit",
                    "target_icon",
                    "name",
                    "teachers",
                    "thema",
                    "date",
                    "period"]
        
        elif titles=="all":
            # すべての項目について返す。
            titles = [
                "name",
                "unit",
                "unit_num",
                "thema",
                "teachers",
                "lesson_type",
                "course",
                "upload_date",
                "end_date",
                "explanations",
                "file_name",
                "date",
                "period",
                "url",
                "target"
            ]

        elif type(titles)==str:
            # titlesがstr型で渡された場合、要素が一つのリストに変換する
            titles=[titles]
        else:
            pass

        # widthがint型(もしくはfloat型・str型)で渡された場合、要素がひとつのリストに変換する
        if type(width) in (float, str):
            width = [int(width)]*len(titles)
        elif type(width)==int:
            width = [width]*len(titles)
        elif width is None:
            width = [None]*len(titles)
        elif len(titles) > len(width):
            lack = len(titles) - len(width)
            for i in range(lack):
                width.append(None)
        else:
            pass

        items_list = []
        for i in range(len(titles)):
            # 文字列の幅を調節
            items_list.append(self.get_item(titles[i], width[i]))
        
        line = ""
        # <value1> | <value2> | <value3> |...
        for i in range(len(items_list)):
            if i == 0:
                # 一行目の頭には線や空白を入れない。
                line += str(items_list[i])
            else:
                sepa = ''       # dummy
                if separate_with_line==True:
                    if type(self)==Text:
                        sepa = " | "
                    elif type(self)==TitleNames:
                        sepa = "   "
                else:
                    sepa = "   "
                line += sepa + str(items_list[i])
        
        return line

    def get_url(self):
        '''
        ダウンロードの対象に指定されている教材のURLを返す。
        
        Returns
        -------
        url : str
            ダウンロード用のURL。
        
        Notes
        -----
        1) self.targetがTrueのものをダウンロード対象とする。
        '''

        url = self.url if self.target else None
        
        return url

        '''-------------------ここまで3項式適用------------------------'''
    
    def be_target(self):
        '''ダウンロード対象に指定する。'''
        self.target = True
    
    def not_target(self):
        '''ダウンロードの対象から外す。'''
        self.target = False
    
    def invert_target(self):
        '''
        self.targetのbool値を反転させる。
        '''
        self.target = not self.target

    def get_item(self, title, width=None):
        '''
        titleで指定された項目を返す。
        
        Parameters
        ----------
        width : int
            文字列の幅を指定する。Noneの場合は指定なし。

        Returns
        -------
        element : str
            titleで指定された項目。widthにあわせて文字列長は調整されている。

        Notes
        -----
        1) widthで指定された幅で文字列の長さに項目を調節する。
        2) target_iconにはダウンロード対象の場合"◆"、ダウンロードの
        対象出ないときは"◇"を用いる。self.targetがbool値を取っていな
        い場合は"　"を用いる。
        '''

        if self.target==True:
            target_icon = "◆"
        elif self.target==False:
            target_icon = "◇"
        else:
            target_icon = "　"

        date = self.date[0:4] + "/" + self.date[4:6] + "/" + self.date[6:8] if (title=="date") and (self.date is not None) else None
        period = self.period + '限' if (title=="period") and (self.period!=None) else None
        upload_date = self.upload_date[0:4] + "/" + self.upload_date[4:6] + "/" + self.upload_date[6:8] if (title=="upload_date") and (self.upload_date!=None) else None
        end_date = self.end_date[0:4] + "/" + self.end_date[4:6] + "/" + self.end_date[6:8] if (title=="end_date") and (self.end_date!=None) else None

        dict = {"name": self.name,
                "unit": self.unit,
                "unit_num": self.unit_num,
                "thema": self.thema,
                "teachers": self.teachers,
                "date": date,
                "period": period,
                "url": self.url,
                "target_icon": target_icon,
                "target": self.target,
                "lesson_type": self.lesson_type,
                "course": self.course,
                "upload_date": upload_date,
                "end_date": end_date,
                "explanations": self.explanations,
                "file_name": self.file_name,
                None: None}

        item = dict[title]

        if item is None:
            item = ''
        else:
            pass

        if width is None:
            pass
        else:
            item = ljust_zen(string=item, word_count=width)   # 文字列長の調節
        
        return item


class TitleNames(Text):
    '''
    Textクラスの項目名を設定する。
    Textクラスを親クラスとして継承する。
    
    Notes
    -----
    1) Textクラスのように具体的な情報を保持するクラスではない。
    '''

    def __init__(self, name=None, unit=None, thema=None, teachers=None, date=None, period=None, url=None, target=None, lesson_type=None, course=None, upload_date=None, end_date=None, explanations=None, file_name=None):
        super().__init__(name=name, unit=unit, thema=thema, teachers=teachers, date=date, period=period, url=url, lesson_type=lesson_type, course=course, upload_date=upload_date, end_date=end_date, explanations=explanations, file_name=file_name)
        self.target = target
        self.date = date
        self.period = period
    
    def set_titles(self, name=None, unit=None, thema=None, teachers=None, date=None, period=None, url=None, target=None, lesson_type=None, course=None, upload_date=None, end_date=None, explanations=None, file_name=None):
        '''項目名を設定する。'''

        if name is not None:
            self.name = name
        if unit is not None:
            self.unit = unit
        if thema is not None:
            self.thema = thema
        if teachers is not None:
            self.teachers= teachers
        if date is not None:
            self.date = date
        if period is not None:
            self.period = period
        if url is not None:
            self.url = url
        if target is not None:
            self.target = target
        if lesson_type is not None:
            self.lesson_type = lesson_type
        if course is not None:
            self.course = course
        if upload_date is not None:
            self.upload_date = upload_date
        if end_date is not None:
            self.end_date = end_date
        if explanations is not None:
            self.explanations = explanations
        if file_name is not None:
            self.file_name = file_name
        
    def get_title(self, title, width=None):
        '''
        Text.get_item()と同様のメソッド。
        
        Notes
        -----
        1) self.targetが指定されていない場合、空白を返す。
        '''

        if self.target is None:
            target_icon = ""
        else:
            target_icon = self.target

        
        dict = {"name": self.name,
                "unit": self.unit,
                "thema": self.thema,
                "teachers": self.teachers,
                "date": self.date,
                "period": self.period,
                "url": self.url,
                "target_icon": target_icon,
                "target": self.target,
                None: ""}   # Noneの場合は空白

        element = dict[title]
        if element is None:
            element = ''
        else:
            pass

        if width is None:
            pass
        else:
            element = ljust_zen(string=element, word_count=width)
        
        return element
        

class Unit(object):
    '''
    Textクラスのオブジェクトを複数保持し、まとめて操作する。
    
    Attributes
    ----------
    name : str
        Unitの名前
    text_list : list
        複数のTextオブジェクトを格納したリスト
    title_names : Title_names or None 
        Title_namesオブジェクトを保持
    '''

    def __init__(self, text_list=None, name=None, title_names=None):
        '''
        Parameters
        ----------
        name : name, default None
            Unitの名前
        text_list : list, defoult None
            複数のTextオブジェクトを格納したリスト
        title_names : Title_names or None, dafault None 
            Title_namesオブジェクトを保持
        '''
        self.name = name
        self.text_list = list() if text_list is None else text_list
        self.title_names = title_names
    
    def append(self, text):
        '''
        self.text_listにtextオブジェクトを追加する。
        
        Parameters
        ----------
        text : Text or list
            Textオブジェクトもしくはそれを格納したリスト
        '''
        if type(text)==list:
            end = len(self.text_list)
            self.text_list[end:end] = text
        else:
            self.text_list.append(text)

    def be_target(self):
        '''self.text_listに含まれる全てのText.targetをTrueにする。'''
        for text in self.text_list:
            text.be_target()
    
    def not_target(self):
        '''self.text_listに含まれる全てのText.targetをFalseにする。'''
        for text in self.text_list:
            text.not_target()
    
    def show(self, index=None, titles=None, width=None, show_title=True, separate_with_line=False):
        '''
        Textオブジェクトの保持する情報を行ごとにリストに格納する。
        各行の内容はText.show()に依存する。
        
        Parameters
        ----------
        index : list, tuple, int, str or float. Default is None.
            self.text_listに含まれる要素のうちindexで指定されたものの情報を返す。
        titles : list, str or None. Default is None.
            titlesで指定された項目の情報を返す。
        width : list, int or float. Default is None.
            項目ごとの文字列長を指定する。
            指定しなかった場合、各項目で最も文字列の長い要素の長さが基準となる。
        show_title : bool. Default is True.
            Trueの場合、一行目(配列の先頭)に項目名の行を追加する。
        separate_with_line : bool. Default is False.
            Trueの場合は、項目間を" | "で区切る。
            Falseの場合は、項目間を"   "で区切る
                
        Returns
        -------
        lines : list
            Textオブジェクトの保持していた情報を行ごとにリストに格納する。

        Notes
        -----
        1) indexが指定されていない場合は全て表示する。
        '''
        lines = list()
        if len(self.text_list) == 0:
            # 空のリストに対しmax()関数が使えないため。
            pass

        else:
            # インデックスを指定されなかった場合は全て表示する
            if index is None:
                index = [x for x in range(len(self.text_list))]
            
            # インデックスがint型(もしくはfloat型)で渡された場合要素がひとつのリストに変換する
            if type(index) in (float, str):
                index = int(index)
            if type(index)==int:
                index = [index]
            
            if titles=="all":
                # すべての項目について返す。
                titles = [
                    "name",
                    "unit",
                    "unit_num",
                    "thema",
                    "teachers",
                    "lesson_type",
                    "course",
                    "upload_date",
                    "end_date",
                    "explanations",
                    "file_name",
                    "date",
                    "period",
                    "url",
                    "target"
                ]
            elif type(titles) == str:
                titles = [titles]
            elif titles is None:
                titles = ["unit",
                        "target_icon",
                        "name",
                        "teachers",
                        "thema",
                        "date",
                        "period"]

            # widthが指定されていない場合、各項目ごとで最も長い文字列に合わせる
            if width is None:
                width=[None]*len(titles)

            # title=Trueの場合self.text_listの先頭にself.title_namesを割り込ませる
            text_list_copy = copy.copy(self.text_list)
            if show_title and (self.title_names is not None):
                text_list_copy.insert(0, self.title_names)
                # indexの要素全てに1を足し頭に0を加える
                index = [i + 1 for i in index]
                index.insert(0, 0)
            
            # 各項目ごとに処理する
            for i in range(len(titles)):
                # widthで指定されているものを除き長さを確認する。
                if width[i] is None:
                    # ループ処理でindexで指定されているtextオブジェクトそれぞれ確認し最大値
                    element_len = list()
                    for j in index:
                        element = text_list_copy[j].get_item(titles[i])
                        element_len.append(len_zen2(str(element)))                    
                    width[i] = max(element_len)
                else:
                    pass
                
            for i in index:
                line = text_list_copy[i].show(titles=titles, width=width, separate_with_line=separate_with_line)
                lines.append(line)
        
        return lines
    
    def print(self, index=None, titles=None, width=None, show_title=True, separate_with_line=False):
        '''
        Textオブジェクトの保持する情報を行ごとに出力する。
        出力内容はUnit.show()に依存する。
        
        Parameters
        ----------
        index : list, tuple, int, str or float. Default is None.
            self.textに含まれる要素のうちindexで指定されたものの情報を返す。
        titles : list, str or None. Default is None.
            titlesで指定された項目の情報を返す
        width : list, int or float. Default is None.
            項目ごとの文字列長を指定する。
            指定しなかった場合、各項目で最も文字列の長い要素の長さが基準となる。
        show_title : bool. Default is True.
            Trueの場合、一行目に項目名の行を追加する。
        separate_with_line : bool. Default is False.
            Trueの場合は、項目間を" | "で区切る。
            Falseの場合は、項目間を"   "で区切る        
        '''
        lines = self.show(index=index, titles=titles, width=width, show_title=show_title, separate_with_line=separate_with_line)
        print(0)
        for line in lines:
            print(line)

    def simple_sort(self, title, reverse=False):
        '''
        指定した項目で、self.text_listの並び順をソートする。
        
        Parameters
        ----------
        title : str
            指定した項目で、self.text_listの並び順をソートする。
        reverse : bool. Default is False.
            Falseの場合は昇順、Trueの場合は降順でソートする。
            デフォルトでは昇順。
        '''
        # sort_dictのkeyにtitle、valueにself.text_listのindexをリストで登録
        # 同じtitleのものはsort_dict
        sort_dict = {}
        for i in range(len(self.text_list)):
            key = self.text_list[i].title(title)

            # sort_dictにすでに同じキーが登録されている場合,
            # valueのリストにインデックスを追加する
            if key in sort_dict:
                sort_dict[key].append(i)
            else:
                sort_dict[key] = [i]
        
        # ソート機能
        list = sorted(sort_dict.items(), reverse=reverse)
        
        # self.text_listを更新
        sorted_text_list = []

        # タイトルごと
        for indexes in list:
            for index in indexes[1]:
                sorted_text_list.append(self.text_list[index])
        
        self.text_list = sorted_text_list

    def sort(self, titles=None, reverse=False):
        '''
        一つまたは複数の項目でself.text_listの並び順をソートする。
        各項目ごとに昇順・降順を指定できる。
        
        Parameters
        ----------
        titles : list or str. Default is None.
            titlesで指定する優先度順にself.text_listの並び順をソートする。
        reverse : list or bool. Default is False
            各項目ごと、もしくは全体の昇順・降順を指定する。
            デフォルトでは昇順。
        
        Notes
        -----
        1) reverseが単体のbool値の場合、全体を昇順もしくは降順でソートする。
        2) titlesを指定しなかった場合、日付・時限・名前の順でソートする。
        '''
        
        if type(titles)==str:
            titles = [titles]

        # titlesが指定されていない場合、date -> period -> nameの優先順でソートする。
        if titles is None:
            titles = ["date", "period", "name"]

        # reverseはリストで取り込む。
        # reverseが単体のbool値の場合、titlesと同じ要素数のリストに変換する。
        if type(reverse)==bool :
            reverse = [reverse]*len(titles)

        # 複数の候補を指定して、ソートする
        # ソートの仕組み自体は同クラスのsortを用いる。
        # 低優先度の指定から順にソートを行うことで実現する。
        titles.reverse()
        for i in range(len(titles)):
            title = titles[i]
            rev = reverse[i]
            self.simple_sort(title=title, reverse=rev)
    
     # ひとつの項目につき、複数のvalueをリスト(またはタプル)で指定可能
    # 複数の項目に対し、それぞれ複数のvalueを与える場合は2次元配列で指定する。
    # 複数の項目を指定した場合、全ての項目で示されるvalueを満たす物を返す
    def find(self, titles, values):
        '''
        項目と要素を指定することで、当てはまる教材をself.text_listから検索しインデックスを返す。
        複数の項目をリストやタプルで選択可能。複数の項目について指定した場合、全ての条件を満たすTextのインデックスを返す。
        それぞれ、複数の要素で検索することも可能。この場合はどちらかの要素を持つTextのインデックスを返す。
        例えば、ユニット名が算数と国語の教材のうち2020/01/01, 2020/01/02に行われた授業の教材を検索する場合
        titles=["unit", "date"] values=[["算数", "国語"], ["20200101", "20200102"]] で検索をする。
        
        Parameters
        ----------
        titles : list, tuple or str.
            項目名を指定する。複数を指定した場合はそれぞれの項目間でAND検索となる。
        values : list(1D, 2D), tuple(1D, 2D), str or int.
            検索に用いるキーワードを指定する。1つの項目に対し、2つ以上のキーワードで検索をする場合は2次配列を用いる。
        
        Returns
        -------
        indexes : list
            検索結果をself.text_listのインデックスで返す。
        '''

        # titlesが単体のstrで渡された場合、要素が一つのリストに変換する
        if type(titles) in (str, int):
            titles = [str(titles)]
            
            if type(values)!=list and type(values)!=tuple:
                values = [[values]]
            # 1次元配列の場合
            elif type(values[0])!=list and type(values[0])!=tuple:
                values = [values]
            else:
                pass
        
        # n個の項目につきひとつのvalueが1次元配列で指定された場合は、
        # n×1の二次配列配列に変換する
        # valuesの要素のうち一部がlistやtupleでない場合も、完全な2次配列に変換する。
        for i in range(len(values)):
            if type(values[i])!=list and type(values[i])!=tuple:
                values[i] = [values[i]]
        
        indexes = list()
        for i in range(len(titles)):
            title = titles[i]

            indexes_temp = list()

            # 該当するvalueを持つtextのインデックスがindexes_tempに含まれなかった場合indexes_tempに加える
            for value in values[i]:
                for index in range(len(self.text_list)):
                    if self.text_list[index].title(title) == value and index not in indexes_temp:
                        indexes_temp.append(index)

            # indexes_tempに含まれているがindexesに含まれていない要素をindexesから取り除く
            if i == 0:
                indexes = copy.copy(indexes_temp)
            else:
                indexes = indexes & indexes_temp

        return indexes

    def refer(self, indexes):
        '''
        インデックスで指定された複数のTextオブジェクトを返す。ただしcopy.deepcopyメソッドは用いられていないため、
        受け取ったTextオブジェクトに加えられた変更は、Unitオブジェクトが保持する同じTextオブジェクトに反映される。
        
        Parameters
        ----------
        indexes : list, tuple or int.
            返すTextオブジェクトのインデックスを指定する。
        
        Returns
        -------
        texts_temp : list
            Textオブジェクトを格納したリストを返す。
            一つのみの指定だった場合でも、リストに格納する。
        '''

        texts_temp = list()
        for i in indexes:
            texts_temp.append(self.text_list[i])
        
        return texts_temp
    
    def copy(self, indexes=None):
        '''
        Textオブジェクトを格納したリストをコピーし,返す。コピーされたTextオブジェクトは
        新たな独立したTextオブジェクトとして生成されたものである。
        インデックスを指定した場合、指定されたTextオブジェクトのみをリストに格納し返す。
        インデックスを指定された場合は、指定された順番でTextオブジェクトを格納する。

        Parameters
        ----------
        indexes : list, tuple or int. Default is None.
            コピーするTextのインデックスを指定する。
        
        Returns
        -------
        texts_temp : list
            コピーされたTextオブジェクトを格納。
        '''
        if indexes is None:
            indexes = list(range(len(self.text_list)))
        elif type(indexes)==int:
            indexes = list(indexes)
        else:
            pass
        
        texts_temp = list()
        for i in indexes:
            texts_temp.append(copy.deepcopy(self.text_list[i]))
        
        return texts_temp

    def delete(self, indexes=None):
        '''
        self.text_listに格納されているTextオブジェクトを削除する。
        indexesでインデックスを指定した場合は、指定されたTextオブジェクトのみを削除する。
        
        Parameters
        ----------
        indexes : list, tuple or int. Default is None.
            削除するTextオブジェクトを指定する。
        
        Notes
        -----
        1) indexesを引数に渡さなかった場合は、slef.text_listに格納されている全てのTextオブジェクトを削除する。
        '''
        if indexes is None:
            self.text_list.clear()
        else:
            if type(indexes)==int:
                indexes = list(indexes)
            else:
                pass

            for i in indexes.reverse():
                del self.text_list[i]

    def pop(self, indexes=None):
        '''
        self.text_listに格納されているTextオブジェクトのコピーを渡し、もとのTextオブジェクトは削除する。
        
        Parameters
        ----------
        indexes : list, tuple or int. Default is None.
            対象のTextオブジェクトを指定する。

        Notes
        -----
        1) indexesを引数に渡さなかった場合は、slef.text_listに格納されている全てのTextオブジェクトを扱う。
        '''
        texts_temp = self.copy(indexes)
        self.delete_texts(indexes)

        return texts_temp

    def set_titles(self, name=None, unit=None, thema=None, teachers=None, date=None, period=None, url=None, target=None, lesson_type=None, course=None, upload_date=None, end_date=None, explanations=None, file_name=None):
        '''self.title_namesに登録されている項目名を変更する。指定されなかった項目名は変更されない。'''
        self.title_names.set_titles(name=name, unit=unit, thema=thema, teachers=teachers, date=date, period=period, url=url, lesson_type=lesson_type, course=course, upload_date=upload_date, end_date=end_date, explanations=explanations, file_name=file_name)
    
    def init_titles(self, name=None, unit=None, thema=None, teachers=None, date=None, period=None, url=None, target=None, lesson_type=None, course=None, upload_date=None, end_date=None, explanations=None, file_name=None):
        '''self.title_namesに登録されている項目名を初期化する。以前の項目名は全て削除される。'''
        self.title_names = TitleNames(self, name=None, unit=None, thema=None, teachers=None, date=None, period=None, url=None, target=None, lesson_type=None, course=None, upload_date=None, end_date=None, explanations=None, file_name=None)


class Scraper(object):
    '''
    kt.kanazawa-med.ac.jpへのアクセス、ログインの維持、教材情報の収集を行う。
    
    Attributes
    ----------
    session : requests.Session
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
    def __init__(self, session=None, id=None, password=None, faculty=None, grade=None):

        self.session = session
        self.id = id
        self.password = password
        self.faculty = faculty      # 大文字 M or N
        self.grade = grade
    

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
        # TODO: エラーメッセージを廃止、例外を返す(raise)。
        #       https://getpocket.com/read/2772745088を参考にすること。
        if id is not None:
            self.id = id
        else:
            pass

        if password is not None:
            self.password = password
        else:
            pass

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
                
            else:
                pass
        
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
        
        # str型でも受け取れるようにする
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

            # textの初期化
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
                    print(br_position)
                    print("本文～")
                    print(title)
                    dl_link = BeautifulSoup(title, 'html.parser').select("a[href^='./Download']")[0]

                    dl_url_part = dl_link.get('href')
                    DL_URL_HEAD = "https://kt.kanazawa-med.ac.jp/timetable"

                    dl_url = DL_URL_HEAD + dl_url_part[1:]
                    file_name = dl_link.getText()
                    print(file_name)
                    input()

                    text.url = dl_url
                    text.file_name = file_name
                elif "ユニ" in title:
                    # ユニット名
                    # element を再度抽出
                    # ユニット名、回数、日付、時間を含むものに置き換える
                    unit = set[br_position[0]+6:br_position[1]].strip()
                    unit_num = set[br_position[1]+6:br_position[2]].strip()[1:3]
                    date = set[br_position[2]+6:br_position[3]].strip()[:6].replace('月', '').replace('日', '')
                    period = set[br_position[3]-2:br_position[3]-1]
                    text.unit = unit
                    text.unit_num = unit_num
                    text.date = _year + date
                    text.period = period
                elif "区分" in title:
                    # 区分
                    text.lesson_type = element
                elif "講義" in title:
                    # 講義・実習内容
                    text.thema = element
                elif "講座" in title:
                    # 講座名
                    text.course = element
                elif "担当" in title:
                    # 担当教員
                    text.teachers= element
                elif "公開開始日" == title:
                    # 公開開始日
                    text.upload_date = element.split()[0].replace('/', '')
                elif "公開終了日" == title:
                    # 公開終了日
                    text.end_date = element.split()[0].replace('/', '')
                elif "教材・資料名" == title:
                    # 教材・資料名
                    text.name = element
                elif "教材・資料の説明" == title:
                    # 教材・資料の説明
                    text.explanations = element
                else:
                    pass

            text_list.append(text)
            
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

        # 単体のものをリストに格納する。ただしUnitオブジェクトはUnit.text_listを展開する。
        if type(text).__name__ in ('str', 'Text'):
            text = [text]
        elif type(text).__name__ == 'Unit':
            text = text.text_list
        print(text)
        
        if save == True:
            # ファイルを保存する場合
            if type(save_dir).__name__ in ('str', 'NoneType'):
                save_dir = [save_dir]
            if len(save_dir)==1:
                save_dir *= len(text)

            if type(file_name).__name__ in ('str', 'NoneType'):
                file_name = [file_name] * len(text)
            print(file_name)

            # ダウンロードに失敗した教材のindexを格納
            failed = list()
            # 各要素ごとにダウンロードを実行
              
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
                
                print(_file_name)
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
                print(_save_path)

                count = 0
                limit = 5   # ５回チャレンジ
                while True:
                    count += 1
                    try:
                        data = self.session.get(_text, verify=False).content
                        
                        with open(_save_path, mode='wb') as f:
                            # バイナリ書き込みモード
                            f.write(data)
                        break
                    except Exception as e:
                        if count >= limit:
                            print(e)
                            failed.append(i)
                            break
                        else:
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
                
                count = 0
                limit = 5   # ５回チャレンジ

                while True:
                    count += 1
                    try:
                        data = self.session.get(_text, verify=False).content
                        break
                    except:
                        if count >= limit:
                            data = None
                            break
                        else:
                            pass  
                
                data_list.append(data)
            
            return data_list


class Logger(object):
    '''
    ログを保持し保存する。

    Attributes
    ----------
    path : str
        ログを保存するパス。
    status : str
        一番最新のログに関するステータス。
        'PROGRESS': プロセスの進捗に関するログであることを示す
        'ERROR': エラーに関するログであることを示す
        'WARNING': 警告に関するログであることを示す
    date : str
        ログに付属する日付情報。'YYYY/MM/DD'
    time : str
        ログに付属する時間情報。24時間表記 'HH:MM:SS'
    message : str
        ログに関するメッセージ。改行は非推奨。
    arc : list
        過去のログを保持する。
        saveメソッドで保存するたびにクリアする。
        最新のログも保持する。
    '''
    def __init__(self, path='log.txt', status=None, date=None, time=None, message=None, archive=list()):
        self.path = path
        self.status = status
        self.date = date
        self.time = time
        self.message = message
        self.archive = archive
    
    def log(self, status=0, date=None, time=None, message=None):
        '''
        ログを保持し、self.archiveの末尾に加える。
        前回のログは削除される。
        
        Parameters
        ----------
        status : int or str
            0: 'PROGRESS'
            1: 'ERROR'
            2: 'WARNING'
            'PROGRESS', 'ERROR', 'WARNING'を直接指定することも可能。省略で指定することも可能。
            ただし'E'と指定した場合は'ERROR'と解釈する。
            独自の値を指定することもできるが、ファイルに出力した際に書体が崩れる可能性がある。
        date : str, datetime.datetime, datetime.date or int
            日付を指定する。'YYYYMMDD'もしくは'YYYY/MM/DD'で指定可能。
            指定がない場合は現在の日付が適用される。
            datetimeオブジェクトを指定した場合はtimeに引数は不要。
        time : str, datetime.datetime, datetime.time or int
            時刻を指定する。'HHMMSS'もしくは'HH:MM:SS'
            指定がない場合は現在時刻が適用される。
            dateの引数にdatetimeオブジェクトを指定した場合はtimeの指定は不要。
            ただし、timeに引数が指定されれば指定された値が優先される。
            datetimeオブジェクトで指定可能。
        message : str
            メッセージを指定する。改行は取り除かれる。
            文頭に'n@'がある場合は改行を取り除かない。        
        '''
        # statusに関する処理
        if type(status)==str:
            status.strip()
            status_up = status.upper()    # 小文字で既定の文字列を指定された場合の検証用
            # str型で数字が指定されていいた場合
            if status in '012':
                status = {'0':'PROGRESS', '1':'ERROR', '2':'WARNING'}[status]
            elif 'PROGRESS'.startswith(status_up):
                status = 'PROGRESS'
            elif 'ERROR'.startswith(status_up):
                status = 'ERROR'
            elif 'WARNING'.startswith(status_up):
                status = 'WARNING'
            else:
                pass
        elif (0 <= status, status <= 2):
            # statusをint型で指定した場合
            status = ('PROGRESS', 'ERROR', 'WARNING')[status]
        else:
            pass

        self.status = status

        #dateに関する処理
        # date is None, time=='xxxxxx' -> date==現在の日付, time=='xxxxxx'
        # date is None, time is None -> date==現在の日付, time==現在の時刻
        # date=='xxxxxxxx', time is None -> date=='xxxxxxxx', time==現在の時刻 

        # 0埋めで日付の表示として適切な文字列に変換する。[YYYY/MM/DD]
        format_date = lambda year, month, day: "{:0>4}/{:0>2}/{:0>2}".format(year, month, day)

        dt_now = datetime.datetime.now()
        if date is None:
            date = format_date(dt_now.year, dt_now.month, dt_now.day)
        elif type(date)==int:
            str(date)
        elif type(date).__name__=='datetime':
            # datetimeオブジェクトを指定された場合、
            # timeが指定されていなければdatetimeオブジェクトから時間を指定する。
            if time is None:
                time = date
            date = format_date(date.year, date.month, date.day)
        elif type(date).__name__=='date':
            # dateオブジェクトで指定された場合。
            date = format_date(date.year, date.month, date.day)

        if not '/' in date:
            # dateが数字のみで構成されている場合
            date = format_date(date[0:4], date[4:6], date[6:8])
        
        self.date = date

        # timeに関する処理
        format_time = lambda hour, minute, second: "{:0>2}:{:0>2}:{:0>2}".format(hour, minute, second)

        if time is None:
            # 現時刻
            time = format_time(dt_now.hour, dt_now.minute, dt_now.second)
        elif type(time)==int:
            str(time)
        elif type(time).__name__ in ('datetime', 'time'):
            time = format_time(time.hour, time.minute, time.second)
        
        if not ':' in time:
            time = format_time(time[0:2], time[2:4], time[4:6])
        
        self.time = time

        # messageに関する処理
        message.strip()
        if message[0:2]!='n@':
            # 改行コードを削除
            message = message.replace('\n', '')

        self.message = message

        # loggerオブジェクトをself.archiveに追加
        logger_tmp = Logger(path=None, status=status, date=date, time=time, message=message, archive=None)
        self.archive.append(logger_tmp)

    def save(self, path=None, clear=True):
        '''
        self.archiveにあるログをファイルに保存する。
        指定したファイルが既に存在する場合、末尾に追加する。
        
        Parameters
        ----------
        path : str
            ログファイルのパスを指定する。
            存在しなければ新規作成。存在れば末に加える。
        clear: bool. default is True.
            Trueの場合、ログを保存したのちself.archiveの内容を削除する。
        '''
        if path is None:
            path = self.path
        
        with open(path, mode='a') as f:
            f.write(self.show(clear=clear))

    def show(self, clear=False, newline=True, aslist=False):
        '''
        self.archiveにあるログを書式を整えて1行ごとに格納したリストもしくは一連の文字列で返す。
        
        Parameters
        ----------
        clear : bool. dafault is False.
            Trueを指定した場合、リストを返したのちself.archiveの内容を削除する。
        newline : bool. default is False.
            Trueを指定した場合、それぞれの行末に改行コードを挿入する。
        list : bool. default is True.
            Trueを指定した場合、行ごとにリストに格納する。
            Falseを指定した場合、一連の文字列としてstr型で返す。
        
        Return
        ------
        lines : list or str.
        '''
        if newline:
            nl = '\n'
        else:
            nl = ''

        lines = list()
        for log in self.archive:
            # statusの処理
            # 既定の文字列であれば8文字で調整する
            status = log.status.ljust(8) if log.status in ('PROGRESS', 'ERROR', 'WARNING') else log.status

            lines.append(log.date + ' ' + log.time + ' ' + status + ' ' + log.message + nl)

        if aslist:
            pass
        else:
            lines_tmp = str()
            for line in lines:
                lines_tmp += line
            lines = lines_tmp
        
        if clear:
            self.clear()
        
        return lines
    
    def print(self, clear=False):
        '''
        self.archiveの内容を標準出力する。
        
        Parameters
        ----------
        clear : bool. default is False.
            Trueを指定した場合は出力後、self.archiveの内容を削除する。
        '''
        lines = self.show(clear=clear, newline=False, aslist=True)
        for line in lines:
            print(line)

    def clear(self):
        '''
        self.archiveの中身を削除する。
        '''
        self.archive = list()
        

def len_sepa(string):
    # 半角を1、全角を2として文字列の長さをカウントする。
    string = str(string)

    len_list = list()
    for letter in string:
        
        letter_type = unicodedata.east_asian_width(letter)
        if letter_type in 'FWA':
            len_list.append(2)
        else:
            len_list.append(1)
    
    return len_list

# 半角を1文字、全角を2文字としてカウントする
def len_zen2(string):
    len_list = len_sepa(string)

    length = 0
    for i in len_list:
        length += i
    
    return length

# emmbeding_letter=' ' : 左詰めであいた右側を埋めるのに使う文字
def ljust_zen(word_count, string, emmbeding_letter=' '):
    string = str(string)
    len_list = len_sepa(string)

    # 何文字目まで残せるかカウントする
    length = 0
    for i in range(len(len_list)):
        # あと何文字埋められるかカウント
        if word_count - (length+len_list[i]) > -1:
            length += len_list[i]
            i += 1
        else:
            break

    left_letters = string[0:length]
    
    letters = left_letters + str(emmbeding_letter)*(word_count-length)

    return letters

def rjust_zen(string, word_count, emmbeding_letter=' '):
    len_list = len_sepa(string)

    # 何文字目まで残せるかカウントする
    length = 0
    for i in range(len(len_list)):
        # あと何文字埋められるかカウント
        if word_count- (length+len_list[i]) > -1:
            length += len_list[i]
            i += 1
        else:
            break
    left_letters = string[0:i]
    
    letters = str(emmbeding_letter)*(word_count-length) + left_letters

    return letters

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

    for line in today.show(titles=titles, separate_with_line=True):
        print(line)
    
    SAVE_DIR = ""
    datalist = scraper.dl(today, save_dir=SAVE_DIR)

    for data in datalist:
        print(type(data))

if __name__=='__main__':
    main()