import string
import os, sys
import random
import time
from functools import partial

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ktnetscraper import parser
from tests import template

hiragana = 'あぁいぃうぅえぇおぉかきくけこがぎぐげごさしすせそざじずぜぞたちつてとっだぢづでどなにぬねのはひふへほばびぶべぼぱぴぷぺぽまみむめもやゆよゃゅょらりるれろわをん'
katakana = 'アァイィウゥエェオォカキクケコガギグゲゴサシスセソザジズゼゾタチツテトッダヂヅデドナニヌネノハヒフヘホバビブベボパピプペポマミムメモヤユヨャュョラリルレロワヲン'
han_kana = 'ｱｧｲｨｳｩｴｪｵｫｶｷｸｹｺｶﾞｷﾞｸﾞｹﾞｺﾞｻｼｽｾｿｻﾞｼﾞｽﾞｾﾞｿﾞﾀﾁﾂﾃﾄｯﾀﾞﾁﾞﾂﾞﾃﾞﾄﾞﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾊﾞﾋﾞﾌﾞﾍﾞﾎﾞﾊﾟﾋﾟﾌﾟﾍﾟﾎﾟﾏﾐﾑﾒﾓﾔﾕﾖｬｭｮﾗﾘﾙﾚﾛﾜｦﾝ'
alphabet = string.ascii_letters
nums_zen = '１２３４５６７８９０'
nums_han = '1234567890'
kanji_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'char', 'kanji.txt')
with open(kanji_path, mode='r', encoding='utf-8') as f:
    kanji = f.read()
chars = f'{hiragana}{katakana}{han_kana}{alphabet}{nums_zen}{nums_han}{kanji}'
chars_num = len(chars)



def random_strings(length: int = 10, num: int = 1) -> tuple[str]:
    '''
    ひらがな、カタカナ、漢字、数字、アルファベットを含むランダムな文字列を複数返す。

    Parameters
    ----------
    length : int
        文字列の長さ
    num : int
        文字列の数
    
    Returns
    -------
    tuple[str]
    '''
    return tuple(''.join(random.choices(chars, k=length)) for _ in range(num))



def parser_speed(func, page: str, num_runs: int = 10) -> int:
    total_time = 0.0
    ls = []
    for _ in range(num_runs):
        start = time.time()
        out = func(page)
        total_time += time.time() - start
        ls.append(out)

    return total_time / num_runs


def detect_page_type_speed(num_runs: int = 50, scale: int = 1):
    num_runs *= scale
    total_time = 0.0
    page_list = (
        template.index_template(),
        template.menu_template(),
        template.timetable_no_class_template(),
        template.handout_info_template(),
    )
    total_runs = num_runs * 4
    for i in range(total_runs):
        page = page_list[i%4]
        total_time += parser_speed(parser.detect_page_type, page)
    
    return total_time / total_runs


def login_status_speed(num_runs=40, scale=1):
    num_runs *= scale
    total_time = 0.0
    page_list = (
        template.index_template(),
        template.login_failed_template(),
        template.menu_template(),
        template.timetable_no_class_template(),
        template.handout_info_template(),
    )
    total_runs = num_runs * 5
    for i in range(total_runs):
        page = page_list[i%5]
        total_time += parser_speed(parser.login_status, page)
    
    return total_time / total_runs


def single_handout_class_infos(i: int = 1):
    handout_url_part = r'./View_Kyozai.php?kn=2023M5200780&kg=49&kz='
    return template.class_template(
        f'{i}', f'ユニット{i}', f'テーマ{i}',f'C1{i}', '教員{i}',
        handout=template.handout_template(
            urls=[f'{handout_url_part}{i}'],
            handout_names=[f'ファイル{i}'],
        )
    )


def get_faculty_and_grade_speed(num_runs: int = 17, scale: int = 1):
    num_runs *= scale
    total_time = 0.0
    
    class_infos = ''.join([single_handout_class_infos(i) for i in range(6)])
    timetable_template_tmp = partial(template.timetable_template,
                                     date='2000/01/01', days_of_week='土',
                                     class_infos=class_infos)
    
    m_page_list = [timetable_template_tmp(faculty='医', grade=i) for i in range(6)]
    n_page_list = [timetable_template_tmp(faculty='看護', grade=i) for i in range(6)]
    page_list = tuple(m_page_list + n_page_list)
    
    page_num = len(page_list)
    total_runs = num_runs * page_num
    for i in range(total_runs):
        page = page_list[i%page_num]
        total_time += parser_speed(parser.get_faculty_and_grade, page)
    
    return total_time / total_runs


def get_dlpage_url_speed(num_runs: int = 200, scale: int = 1):
    num_runs *= scale
    total_time = 0.0
    class_infos = ''.join([single_handout_class_infos(i) for i in range(6)])
    page = template.timetable_template(
        date='2000/01/01', days_of_week='土',
        faculty='医', grade='1',
        class_infos=class_infos
    )
    
    for _ in range(num_runs):
        total_time += parser_speed(parser.get_dlpage_url, page)
    
    return total_time / num_runs


def get_hadout_info_speed(num_runs: int = 200, scale: int = 1):
    num_runs *= scale
    total_time = 0.0
    dl_url = r'./Download.php?year=0000&kn=0000X0000000&kg=00&kz=0'

    handout_info_template_part = partial(
        template.handout_info_template,
        faculty='医', grade='1', date_month='04', date_days='23',
        days_of_week='土', unit_num='20', period='1', core_carriculum='X-1-1)',
        release_start_at='1999/12/31 23:59', release_end_at='2000/01/01 00:00',
        url=dl_url,
    )

    for _ in range(num_runs):
        unit, lesson_type, thema, course = random_strings(20, 4)
        teachers = ','.join(random_strings(6, 5))
        name, comments, file_name = random_strings(100, 3)
        page = handout_info_template_part(
            unit=unit, lesson_type=lesson_type, thema=thema,
            course=course, teachers=teachers, name=name,
            comments=comments, file_name=file_name
        )
        total_time += parser_speed(parser.get_handout_info, page)
    
    return total_time / num_runs


def main():
    import datetime
    print(datetime.date.today().strftime('%Y/%m/%d'))

    scale = int(input('scale:'))
    
    print('detect_page_type     : ', detect_page_type_speed(scale=scale))
    print('login_status         : ', login_status_speed(scale=scale))
    print('get_faculty_and_grade: ', get_faculty_and_grade_speed(scale=scale))
    print('get_dlpage_url       : ', get_dlpage_url_speed(scale=scale))
    print('get_hadout_info      : ', get_hadout_info_speed(scale=scale))



if __name__=='__main__':
    main()


    # 2023/08/28
    # scale:2
    # detect_page_type     :  3.008425235748291e-06
    # login_status         :  5.008399486541748e-06
    # get_faculty_and_grade:  2.255030706817029e-05
    # get_dlpage_url       :  0.004830000281333926
    # get_hadout_info      :  6.843656301498411e-05

    # 2023/08/28
    # scale:200
    # detect_page_type     :  2.8680944442749074e-06
    # login_status         :  3.5449016094207814e-06
    # get_faculty_and_grade:  2.249866490270539e-05
    # get_dlpage_url       :  1.7417964339255963e-05
    # get_hadout_info      :  6.075025677681106e-05