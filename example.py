import ktnetscraper as kt

import getpass
id = input("StudentID: ")
password = getpass.getpass("Password: ")
scraper = kt.Scraper(id=id, password=password)

scraper.calc_faculty()
scraper.calc_grade()

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

while require_grade:
    grade = int(input("学年："))

    if (1<=grade) and (grade<=6):
        scraper.grade = str(grade)
        require_grade = False
try:
    scraper.login()
    scraper.log.store()
except Exception as e:
    scraper.log.log(status=1, message=e, show=True)
    scraper.log.store()
    exit()

date = ["20220602", "20220603", "20220721"]

try:
    dl_page_url, year_list = scraper.get_dlpage_url(date, return_year=True)
    scraper.log.store()
except Exception as e:
    scraper.log.log(status=1, message=e, show=True)
    scraper.log.store()
    exit()

try:
    unit = kt.data_structures.Unit(scraper.get_text_info(dl_page_url, year_list))
    scraper.log.store()
except Exception as e:
    scraper.log.log(status=1, message=e, show=True)
    scraper.log.store()
    exit()


titles = ["unit", "thema", "date", "period", "target", "file_name"]

unit.show(titles=titles, separate_with_line=True)

SAVE_DIR = "folder1"

try:
    scraper.dl(unit, save_dir=SAVE_DIR)
    scraper.log.store()
except Exception as e:
    scraper.log.log(status=1, message=e, show=True)
    scraper.log.store()
    exit()