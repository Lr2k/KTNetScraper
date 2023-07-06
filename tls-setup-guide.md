# SSL/TLSの有効か

**1. https://jp.globalsign.com/support/rootcertificates/ssl.html から中間CA証明書をダウンロードする。**

**2. ダウンロードした証明書をテキストエディタで開き、ファイルの内容をコピーする。**

**3. コピーした内容をcertifiモジュール内のcacert.pemの末尾に貼り付ける。**

certifiはrequestsにルート証明書のリストを提供するライブラリであり、リストはcertfiモジュールのcacert.pemに保存されている。

(例：`C:\Users\<user_name>\AppData\Local\Programs\Python\Python310\Lib\site-packages\certifi\cacert.pem`, `venv\Lib\site-packages\certifi\cacert.pem`)

**4. ktnetscraperのscraper.pyを開き、ENABLE_TLS=Trueに設定する。**