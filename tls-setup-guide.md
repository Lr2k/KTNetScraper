# SSL/TLSの有効化

※自己責任でお願いします。

**1. https://jp.globalsign.com/support/rootcertificates/ssl.html から中間CA証明書をダウンロードする。**

**2. ダウンロードした証明書をテキストエディタで開き、ファイルの内容をコピーする。**

**3. コピーした内容をcertifiモジュール内のcacert.pemの末尾に貼り付ける。**

certifiはrequestsにルート証明書のリストを提供するライブラリであり、リストはcertfiモジュールのcacert.pemに保存されている。
(例：`C:\Users\<user_name>\AppData\Local\Programs\Python\Python310\Lib\site-packages\certifi\cacert.pem`, `venv\Lib\site-packages\certifi\cacert.pem`)

**4. Scraperインスタンス生成時、もしくはrequestメソッド呼び出し時に引数としてverify=Trueを渡す。**
※初期化メソッドのverify引数のデフォルトはTrue.

```python
scraper = kt.Scraper(verify=True)
```

```python
scraper.request(verify=True)
```
