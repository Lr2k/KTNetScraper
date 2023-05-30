import datetime

def type_checked(object, _type, allow_none=False):
    '''
    Exceptions
    ----------
    TypeError :
        オブジェクトのクラスが指定されているクラスと異なる。
    '''
    if isinstance(object, _type):
        return object
    elif allow_none and (object is None):
        return None
    else:
        if isinstance(_type, tuple):
            if len(_type) == 1:
                correct_type = _type[0].__name__
            else:
                correct_type = ''
                for type_i in range(len(_type)):
                    if type_i == len(_type) - 1:
                        correct_type += _type[type_i].__name__ + 'のいずれか'
                    else:
                        correct_type += _type[type_i].__name__ + '・'
        else:
            correct_type = _type.__name__

        raise TypeError(f'{type(object).__name__}は不適切なクラスです。{_type.__name__}を指定してください。')

def convert_to_date(date: datetime.datetime | datetime.date | list[int, str] | tuple[int, str] | str,
                    ) -> datetime.date:
    '''
    datetimeオブジェクトやdateオブジェクト、list、tuple、str型が
    引数として渡された場合、タイムゾーンを日本に設定したdateオブジェクト
    に変換し返す。
    listやtupleで指定する場合は(年, 月, 日)の順で指定する。
    strで指定する場合は、年・月・日を'/'で区切る。(例:'1998/5/27', '1998/05/27')

    Parameters
    ----------
    date : datetime.datetime, datetime.date, list[int|str], tuple[int|str] or str
    '''
    if type(date) == datetime.datetime:
        date = date.date()
    elif type(date) == datetime.date:
        pass
    elif type(date) in (list, tuple):
        date = datetime.date(year=int(date[0]),
                            month=int(date[1]),
                            day=int(date[2]))
    elif type(date) == str:
        date = date.split('/')
        date = datetime.date(year=int(date[0]),
                                 month=int(date[1]),
                                 day=int(date[2]))
    else:
        raise TypeError(f'{type(date).__name__}は引数に指定できません。'\
                         'datetime.datetime, datetime.date, list, tuple, strの'\
                         'いずれかで指定してください。')
    
    return date

def convert_str_to_datetime(date: str) -> datetime.datetime:
    '''
    文字列の日時をdatetimeオブジェクトに変換する。
    文字列の形式は'YYYY/MM/DD HH:mm'

    Parameters
    ----------
    date : str
        日時。
    
    Returns
    -------
    datetime.datetime
        タイムゾーンはJSTに設定されている。
    '''
    date = type_checked(date, str)
    if len(date) != 16:
        raise ValueError(f'YYYY/MM/DD HH:mmの形式で日時を指定してください。({date})')
    
    date = date.split()
    date = [date[0].split('/'), date[1].split(':')]
    tz_jst = datetime.timezone(offset=datetime.timedelta(hours=9), name='JST')
    return datetime.datetime(year=int(date[0][0]), month=int(date[0][1]),
                             day=int(date[0][2]), hour=int(date[1][0]),
                             minute=int(date[1][1]), tzinfo=tz_jst)