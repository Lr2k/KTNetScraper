from .zen import *

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

    def export(self, titles=None, width=None, separate_with_line=False):
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
                    else:
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
    
    def is_target(self):
        '''ダウンロード対象に指定する。'''
        self.target = True
    
    def is_not_target(self):
        '''ダウンロードの対象から外す。'''
        self.target = False
    
    def switch_target_flag(self):
        '''
        self.targetの値を反転させる。
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

        item = '' if dict[title] is None else dict[title]

        if width is not None:
            item = ljust_zen(string=item, word_count=width)   # 文字列長の調節
        
        return item