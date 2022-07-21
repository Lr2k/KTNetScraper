import copy

from .text import Text
from .zen import *

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

        if name is not None: self.name = name
        if unit is not None: self.unit = unit
        if thema is not None: self.thema = thema
        if teachers is not None: self.teachers= teachers
        if date is not None: self.date = date
        if period is not None: self.period = period
        if url is not None: self.url = url
        if target is not None: self.target = target
        if lesson_type is not None: self.lesson_type = lesson_type
        if course is not None: self.course = course
        if upload_date is not None: self.upload_date = upload_date
        if end_date is not None: self.end_date = end_date
        if explanations is not None: self.explanations = explanations
        if file_name is not None: self.file_name = file_name
        
    def get_title(self, title, width=None):
        '''
        Text.get_item()と同様のメソッド。
        
        Notes
        -----
        1) self.targetが指定されていない場合、空白を返す。
        '''
        
        target_icon = '' if self.target is None else self.target
        
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

        element = '' if dict[title] is None else dict[title]

        if width is not None: element = ljust_zen(string=element, word_count=width)
        
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

    def is_target(self):
        '''self.text_listに含まれる全てのText.targetをTrueにする。'''
        for text in self.text_list:
            text.is_target()
    
    def is_not_target(self):
        '''self.text_listに含まれる全てのText.targetをFalseにする。'''
        for text in self.text_list:
            text.is_not_target()
    
    def export(self, index=None, titles=None, width=None, show_item_names=True, separate_with_line=False):
        '''
        Textオブジェクトの保持する情報を行ごとにリストに格納する。
        各行の内容はText.export()に依存する。
        
        Parameters
        ----------
        index : list, tuple, int, str or float. Default is None.
            self.text_listに含まれる要素のうちindexで指定されたものの情報を返す。
        titles : list, str or None. Default is None.
            titlesで指定された項目の情報を返す。
        width : list, int or float. Default is None.
            項目ごとの文字列長を指定する。
            指定しなかった場合、各項目で最も文字列の長い要素の長さが基準となる。
        show_item_names : bool. Default is True.
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
            if show_item_names and (self.title_names is not None):
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
                line = text_list_copy[i].export(titles=titles, width=width, separate_with_line=separate_with_line)
                lines.append(line)
        
        return lines
    
    def show(self, index=None, titles=None, width=None, show_item_names=True, separate_with_line=False):
        '''
        Textオブジェクトの保持する情報を行ごとに出力する。
        出力内容はUnit.export()に依存する。
        
        Parameters
        ----------
        index : list, tuple, int, str or float. Default is None.
            self.textに含まれる要素のうちindexで指定されたものの情報を返す。
        titles : list, str or None. Default is None.
            titlesで指定された項目の情報を返す
        width : list, int or float. Default is None.
            項目ごとの文字列長を指定する。
            指定しなかった場合、各項目で最も文字列の長い要素の長さが基準となる。
        show_item_names : bool. Default is True.
            Trueの場合、一行目に項目名の行を追加する。
        separate_with_line : bool. Default is False.
            Trueの場合は、項目間を" | "で区切る。
            Falseの場合は、項目間を"   "で区切る        
        '''
        lines = self.export(index=index, titles=titles, width=width, show_item_names=show_item_names, separate_with_line=separate_with_line)

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
    def filter(self, titles, values):
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