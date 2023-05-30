'''
今日の教材をダウンロードするシンプルな例。
詳しい仕様はコード内のdocstringを確認。
'''
import getpass
import datetime
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import ktnetscraper as kt


def main():
    scraper = kt.Scraper()

    # ログイン操作
    id = input('学籍番号：')
    password = getpass.getpass('パスワード：')
    scraper.login(id, password)
    
    # ログインステータスを確認
    logged_in = scraper.get_login_status()
    print(f'ログイン：{logged_in}')
    if not logged_in:
        print('ログインに失敗しました。')
        exit()
    
    # 今日の教材情報を取得
    # ログインユーザーの学部・学年と異なる所属向けの資料を取り扱う場合は、
    # 学部・学年を指定する必要がある。
    # 例 (看護2年の場合): 
    # scraper.fetch_handout_infos(date=date, faculty='N', grade='2')
    date = datetime.date.today()
    handout_infos = scraper.fetch_handout_infos(date=date)
    print(handout_infos)
    
    base_dir_name = f'handouts'
    dir_path = os.path.join(os.path.dirname(__file__), base_dir_name,
                            date.strftime('%Y%m%d'))
    try:
        print(dir_path)
        os.makedirs(dir_path)
    except FileExistsError:
        pass
    except Exception as e:
        print(e)

    # 教材情報からURLを取り出し、ダウンロードする。
    for handout in handout_infos:
        file_name = handout['file_name']
        url = handout['url']

        print(f'{file_name}をダウンロードします。 ({url})')
        file_data = scraper.download(url=url)

        file_path = os.path.join(dir_path, file_name)
        with open(file_path, mode='wb') as f:
            f.write(file_data)
        print(f'{file_name}を保存しました。({file_path})')

if __name__=='__main__':
    main()