# idea_71_unreadable_config_overwritten_on_save.md

## 概要

**起動時に config.json が読めなかった（JSON の解析に失敗した等）とき、アプリは空の設定で起動し、その後に何か 1 つ設定を保存すると、元の config.json を空に近い内容で置き換えてしまう**。
起動する構成セットの指定・言語・フォントサイズ・`scroll_invert` など、元のファイルにあった値がまとめて失われる（手で直せば戻せた内容も消える）。

## 起票経緯（2026-11-26）

phase 82（[暫定 62](../history/62_scroll_direction_setting.md)）のフェーズ完了判定前の Codex 敵対的レビュー 指摘 1（medium）。スクロールの向きの切り替えからも起きるが、起動設定の保存経路そのものの以前からの性質のため、ユーザー判断で phase 82 では直さず分離した。多重起動での上書き（[idea_70](idea_70_config_overwrite_on_multiple_instances.md)）とは別の経路。

## 現状

- `keyseq/presentation/startup_settings.py:4-17` `load_startup_settings`: 読込の例外で `on_read_error` を呼び、`{}`（+ `ui_font_delta_pt`）を返す。アプリは警告を出して操作を続けられる。
- `keyseq/presentation/controllers/config_io/startup_io.py:43-60` `write_startup`: `_startup_settings` に変更分を重ねてファイル全体を書く（元のファイルを読み直さない）。Codex の申告では `JsonRepository.save_json` が `os.replace` で置き換える（未確認）。
- 正本: `data_schema.md` §5.4（「config.json が読めないときも `en` で開き、今までどおりの読込失敗の警告を出す」）。読めなかったファイルの扱い（保全・退避）は定めていない。

## 提案（方向性・要設計）

- 案 A: 「ファイルが無い」と「あるが読めない」を分け、読めなかったときは保存の前に元のファイルを退避する（例 `config.json.broken-<日時>`）か、保存を止めて知らせる。
- 案 B: 読めなかった間は起動設定を書かない（設定の変更は実行中だけ効く）と警告に書く。
- 構成セットの保存の経路（`split_payloads.py` の起動設定の書き出し）も同じ扱いにする。

## 想定スコープ

- presentation の config_io・起動処理（・application の起動設定の書き出し）。JSON スキーマは不変の見込み。仕様変更あり（読込失敗時の保存の規則）。
