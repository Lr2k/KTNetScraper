# KTNetScraper/ktnetscraper
## Overview
金沢医科大学携帯ネットコミュニケーション/携帯ネット.com (https://kt.kanazawa-med.ac.jp) から、教材情報や教材ファイルの抽出をするパッケージ

## Requirement

**python3.10** (他のバージョンでは検証していません。)

ライブラリ：**requests**

## **Warning**
初期状態ではrequestsが kt.kanazawa-med.ac.jp のサーバー証明書を検証できないため、SSL/TLSを利用できません。
SSL/TLSを無視した通信は、中間者攻撃に対し脆弱です。
SSL/TLSを有効化するには、requestsのcertifiが持つCAバンドルに情報を追加する必要があります。
問題が生じてもご自身で対処できる方のみ、tls-setup-guide.mdを参考に自己責任で設定を変更してください。

## Usage
**0. scraperの初期化**

```python
import ktnetscraper as kt

scraper = kt.Scraper(verify=False)
```
※TLSを利用しない場合は、verifyをFalseに。

**1. ログイン**

```python
scraper.login(id, password)
```

**2. 日付を指定し、教材情報を取得**

`datetime.date` `datetime.datetime` `(YYYY,MM,DD)` `[YYYY,MM,DD]` の内、いずれかの形式で教材情報を参照する日付を指定する。

```python
infos : tuple[dict] = scraper.fetch_handout_infos(date)
```

教材情報はdictに格納されており、各項目に対応するkeyとvalueのクラスは以下の通り。

* "unit" : `str` ユニット名 
* "unit_num" : `str` ユニットの何回目の講義か
* "date" : `datetime.date` 講義が行われる日付
* "period" : `str` 講義が行われる時限 
* "lesson_type" : `str` 講義の区分
* "thema" : `str` 講義内容
* "course" : `str` 講座名
* "teachers" : `tuple[str]` 教員名
* "release_start_at" : `datetime.datetime` 教材の公開開始日時
* "release_end_at" : `datetime.datetime` 教材の公開終了日時
* "name" : `str` 教材の名前
* "comments" : `str` 教材に関する説明
* "file_name" : `str` 教材のファイル名
* "url" : `str` 教材のダウンロードURL

**3. 教材ファイルをダウンロード**

```python
url = infos[0]['url']
file_data = scraper.download(url)
```

## Note

詳しい仕様はdocstringを確認

## Version

1.1.0

## Author

[**Kikyo**](https://twitter.com/kikyo0870555)

## License

MIT
