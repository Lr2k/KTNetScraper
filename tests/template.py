INDEX_PATH = r'page_template\index.html'
LOGIN_FAILED_PATH = r'page_template\login_failed.html'
MENU_PATH = r'page_template\menu.html'
TIMETABLE_NO_CLASS_PATH = r'page_template\timetable_no_class.html'

TIMETABLE_PATH = r'page_template\timetable_template.html'
CLASS_TEMPLATE_PATH = r'page_template\timetable_part_class_template.html'
HANDOUT_TEMPLATE_PATH = r'page_template\class_part_handout_template.html'
LINK_TEMPLATE_PATH = r'page_template\handout_part_link_template.html'

HANDOUT_INFO_PATH = r'page_template\handout_info.html'

ENCODING = 'cp932'



def default(value, default_value=''):
    '''
    valueがNoneの場合, デフォルト値(default_value)を返す。
    '''
    return default_value if value is None else value


def dlpage_url(arg_1=None, arg_2=None, arg_3=None):
    arg_1 = default(arg_1, '2000M1000000')
    arg_2 = default(arg_2, '50')
    arg_3 = default(arg_3, '1')
    return f'./View_Kyozai.php?kn={arg_1}&kg={arg_2}&kz={arg_3}'


# テンプレートの解析
def find_bracket(string: str) -> tuple[int, int]:
    '''
    文字列の{% ~ %}で示された範囲を返す。
    複数存在する場合は、最も先頭に位置するものについて返す。
    存在しない場合は(None, None)を返す。
    '''
    open_bracket_position = string.find('{%')
    if open_bracket_position == -1:
        return None, None
    else:
        close_bracket_postition = string.find('%}') + 2
        return open_bracket_position, close_bracket_postition


def replace_bracket(string, dictionary):
    '''
    文字列の{% ~ %}で示された部分を、dictionaryで指定された文字列に置き換える。
    '''
    continue_replace = True
    while continue_replace:
        open_bracket_position, close_bracket_postition = find_bracket(string)

        if open_bracket_position is None:
            break
        else:
            bracket = string[open_bracket_position:close_bracket_postition]

            key = bracket[2:-2].strip()
            value = dictionary[key] if key in dictionary.keys() else ''

            string = string.replace(bracket, str(value))

    return string


# テンプレートの展開
def open_template(path : str, dictionary: dict = None,
                  remove_new_line : bool = False) -> str:
    '''
    テンプレートを読み込み{% ~ %}で示された部分を、
    dictionaryで指定された文字列に置き換える。
    '''
    dictionary = dictionary if dictionary is not None else {}

    with open(path, mode='r', encoding=ENCODING) as f:
        text = f.read()
    
    if remove_new_line:
        text = text.replace('\n', '')
    else:
        pass

    return replace_bracket(text, dictionary)


def index_template() -> str:
    return open_template(INDEX_PATH)


def login_failed_template() -> str:
    return open_template(LOGIN_FAILED_PATH)


def menu_template() -> str:
    return open_template(MENU_PATH)



def handout_template(urls: list[str] | tuple[str] = None,
                     handout_names: list[str] | tuple[str] = None) -> str:
    '''
    時間割ページに表示される'●教材'の項目を生成する。
    '''
    urls = default(urls, [''])
    handout_names = default(handout_names, [''])

    link_list = [open_template(LINK_TEMPLATE_PATH,
                               {'url': url, 'name': name})
                 for url, name in zip(urls, handout_names)]
    links = ''.join(link_list) + '\n'
    
    return open_template(HANDOUT_TEMPLATE_PATH, {'link': links})


def class_template(period=None, unit_name=None, thema=None,
                   room=None, teachers=None, handout=None) -> str:
    contents = {
        'period' : default(period),
        'unit_name' : default(unit_name),
        'thema' : default(thema),
        'room' : default(room),
        'teachers' : default(teachers),
    }

    if handout is not None:
        contents['handout'] = handout

    return open_template(CLASS_TEMPLATE_PATH, contents)


def timetable_template(faculty=None, grade=None, date=None,
                       days_of_week=None, class_infos=None,
                       ) -> str:
    contents = {
        'faculty' : default(faculty),
        'grade'  : default(grade),
        'date' : default(date),
        'days_of_week' : default(days_of_week),
        'class_infos' : default(class_infos),
    }

    return open_template(TIMETABLE_PATH, contents)


def timetable_no_class_template(faculty=None, grade=None,
                                date=None, days_of_week=None) -> str:
    contents = {
        'faculty' : default(faculty),
        'grade' : default(grade),
        'date' : default(date),
        'days_of_week' : default(days_of_week),
    }
    return open_template(TIMETABLE_NO_CLASS_PATH, contents)


def handout_info_template(faculty=None, grade=None, unit_name=None,
                          unit_num=None, date_month=None, date_days=None,
                          days_of_week=None, period=None, lesson_type=None,
                          thema=None, core_carriculum=None, course=None,
                          teachers=None, release_start_at=None,
                          release_end_at=None, name=None, comments=None,
                          url=None, file_name=None) -> str:
    contents = {
        'faculty' : default(faculty),
        'grade' : default(grade),
        'unit_name' : default(unit_name),
        'unit_num' : default(unit_num),
        'date_month' : default(date_month),
        'date_days' : default(date_days),
        'days_of_week' : default(days_of_week),
        'period' : default(period),
        'lesson_type' : default(lesson_type),
        'thema' : default(thema),
        'core_carriculum' : default(core_carriculum),
        'course' : default(course),
        'teachers' : default(teachers),
        'release_start_at' : default(release_start_at),
        'release_end_at' : default(release_end_at),
        'name' : default(name),
        'comments' : default(comments),
        'url' : default(url),
        'file_name' : default(file_name),
    }

    return open_template(HANDOUT_INFO_PATH, contents)


def _test_replace_bracket():
    text = '<html><head><title>{%title%}</title></head><body><div>{%body%}</div><div>{% body %}</div><div>{%body2%}</div></body></html>'
    dictionary = {'title' : 'タイトル', 'body' : 'ボディ'} # body2なし
    return replace_bracket(text, dictionary)


def _test_handout(num=1):
    urls = [f'https://test{i}.url' for i in range(1, num+1)]
    names = [f'handout_{i}' for i in range(1, num+1)]

    return handout_template(urls, names)


def _test_class(class_i=1):
    return class_template(
        period=f'{class_i}',
        unit_name=f'ユニット{class_i}',
        thema=f'テーマ{class_i}',
        room=f'C3{class_i}',
        teachers=f'教員{class_i}',
        handout='[HANDOUT AREA]',
    )


def _test_timetable(class_num=1):
    return timetable_template(
        faculty='理', grade='2', date='2000/01/01',
        days_of_week='土', class_infos='[CLASS INFOS AREA]'
    )

def _test_timetable_no_class():
    return timetable_no_class_template(
        faculty='理', grade='2', date='2000/01/01', days_of_week='土',
    )

if __name__=='__main__':
    print(_test_timetable_no_class())