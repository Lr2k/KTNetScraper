from email import message
import ktnetscraper as kt

import os
import getpass


scraper = kt.Scraper()

# 学籍番号・パスワードの入力とログイン処理
while True:
    id = input("StudentID: ")
    password = getpass.getpass("Password: ")

    try:
        scraper.login(id=id, password=password)
        break
    except Exception as e:
        # scraper.log はLoggerオブジェクトで、ログを保持する機能を持つ。
        # logメソッドにより新規のログを追加。
        scraper.log.log(status=1, message=e)
        print("ログインに失敗しました。")

# 入力された学籍番号から学部、学年を推測。
try:
    scraper.calc_faculty()
    scraper.calc_grade()
except Exception as e:
    scraper.log.log(status=1, message=e)

# 学年が正しいか確認
require_grade = False
while True:
    print("学年は" + scraper.grade + "ですか？ [Y/n]")
    answer = input().strip()
    if answer in ('Y', 'y', 'yes', 'Yes'):
        require_grade = False
        break
    elif answer in ('N', 'n', 'no', 'No'):
        require_grade = True
        break
    else:
        pass

# 学年が異なっていた場合に正しい学年を入力
while require_grade:
    grade = int(input("学年："))

    if (1<=grade) and (grade<=6):
        scraper.grade = str(grade)
        require_grade = False

# 日付は文字列で指定
# リストやタプルに複数格納して指定可能
date = ["20220602", "20220603", "20220721"]

# 時間割ページから教材のダウンロードページのURLを取得。
try:
    dl_page_url, year_list = scraper.get_dlpage_url(date, return_year=True)
    scraper.log.store()
except Exception as e:
    scraper.log.log(status=1, message=e, show=True)
    # storeメソッドによりこれまでのログをファイルに出力する。
    # デフォルトではカレントディレクトリに "scraper.log" という名前で保存される。
    scraper.log.store()
    exit()

# 教材のダウンロードページから教材のダウンロードURLを含む情報を取得しTextオブジェクトに格納。
try:
    unit = kt.data_structures.Unit(scraper.get_text_info(dl_page_url, year_list))
    scraper.log.store()
except Exception as e:
    scraper.log.log(status=1, message=e, show=True)
    scraper.log.store()
    exit()

# 情報を取得した教材の一覧を表示
# titlesで一覧を表示する位に並べる項目を指定
titles = ["unit", "thema", "date", "period", "target", "file_name"]
unit.show(titles=titles, separate_with_line=True)

# 教材をダウンロードし保存
# ユニットごとにフォルダを分けて保存
SAVE_DIR_BASE = "folder1"
save_dir_list = os.listdir(SAVE_DIR_BASE)
for text in unit.text_list:
    try:
        save_dir_path = os.path.join(SAVE_DIR_BASE, text.unit)
        if text.unit not in save_dir_list:
            os.makedirs(save_dir_path)
            save_dir_list.append(text.unit)
        
        scraper.dl(text, save_dir_path)
        scraper.log.store()
    
    except Exception as e:
        scraper.log.log(status=1, message=e, show=True)
        scraper.log.store()
        exit()