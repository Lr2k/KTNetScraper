# ChageLog
## [1.1.1] - 2023-09-24
### Fixed
- Screaper.get_handoutinfo_from_dlpageメソッドに不要な引数'date'を削除。
- urllib3の要求バージョンをv2.0.0未満に制限

## [1.1.0] - 2023-08-28
### Changed
- requestメソッドの仕様を変更。
- 軽微な調整。

### Added
- parserモジュールを追加。

## [1.0.2] - 2023-07-06
### Changed
- getメソッドとpostメソッドの機能をrequestメソッドに統合。
- サイトへの接続にSSL/TLSを利用できるようになった。

## [1.0.1] - 2023-06-17
### Changed
- モジュール内の定数として実装していたいくつかの設定項目を、Scraperの初期化メソッドの引数で設定するように変更。
- コード内、docstringの内容を一部修正。
