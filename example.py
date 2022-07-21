import ktnetscraper as kt

import getpass
id = input("StudentID: ")
password = getpass.getpass("Password: ")
scraper = kt.Scraper(id=id, password=password)

scraper.calc_faculty()
scraper.calc_grade()

print("学年は" + scraper.grade + "ですか？ [Y/n]")
answer = input().strip()
if answer not in ("Y", "y", "yes", "Yes"):
    while True:
        try:
            grade = int(input("学年："))
        except:
            continue

        if (1<=grade) and (grade<=6):
            scraper.grade = str(grade)
            break

scraper.login()
date = ["20220602", "20220603"]

try:
    dl_page_url, year_list = scraper.get_dlpage_url(date, return_year=True)
    scraper.log.store()
except Exception as e:
    scraper.log.log(status=1, message=e)
    scraper.log.store()
    exit()

try:
    unit = kt.data_structures.Unit(scraper.get_text_info(dl_page_url, year_list))
    scraper.log.store()
except Exception as e:
    scraper.log.log(status=1, message=e)
    scraper.log.store()
    exit()


titles = ["unit", "thema", "date", "period", "target", "lesson_type", "course", "file_name", "upload_date"]

unit.show(titles=titles, separate_with_line=True)

SAVE_DIR = "folder1"

try:
    scraper.dl(unit, save_dir=SAVE_DIR)
    scraper.log.store()
except Exception as e:
    scraper.log.log(status=1, message=e)
    scraper.log.store()
    exit()