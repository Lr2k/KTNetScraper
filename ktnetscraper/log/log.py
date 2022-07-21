import datetime

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
    archive : list
        過去のログを保持する。
        storeメソッドで保存するたびにクリアする。
        最新のログも保持する。
    '''

    def __init__(self, path='log.txt', status=None, date=None, time=None, message=None, archive=None, enable_logging=True, show=False):
        '''
        Parameters
        ----------
        enable_logging : bool
            Trueの場合、logメソッドを有効化する。
        show : bool. Default is False.
            Trueの場合、logメソッド実行時にmessageを標準出力する。
        '''
        self.path = path
        self.status = status
        self.date = date
        self.time = time
        self.message = message
        self.archive = archive if archive is not None else list()
        self.enable_logging = enable_logging
        self.show = show

    def log(self, status=0, date=None, time=None, message='', show=None):
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
        show : bool or NoneType. Default is None.
            Trueの場合、messageを標準出力する。
            指定がない(show=None)場合、self.showの設定が適用される。      
        '''
        message = str(message)

        if self.enable_logging == False:
            # logメソッドの無効化
            return

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

        if show is None:
            show = self.show
        
        line = self.export_latest()
        if show:
            print(line)
        else:
            return line

    def store(self, path=None, clear=True):
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
            f.write(self.export(clear=clear))

    def export(self, clear=False, newline=True, aslist=False):
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
    
    def export_latest(self):
        date = self.date + ' ' if self.date is not None else ''
        time = self.time + ' ' if self.time is not None else ''
        status = self.status + ' ' if self.status is not None else ''
        message = self.message if self.message is not None else ''

        line = date + time + status + message
        return line

    def show(self, clear=False):
        '''
        self.archiveの内容を標準出力する。
        
        Parameters
        ----------
        clear : bool. default is False.
            Trueを指定した場合は出力後、self.archiveの内容を削除する。
        '''
        lines = self.export(clear=clear, newline=False, aslist=True)
        for line in lines:
            print(line)

    def clear(self):
        '''
        self.archiveの中身を削除する。
        '''
        self.archive = list()
