# idea_70_config_overwrite_on_multiple_instances.md

## 概要

**同じ設定フォルダでアプリを 2 つ起動すると、片方の config.json の保存が、もう片方の起動時点の内容で全体を書き直し、保存済みの値が消える**（言語・フォントサイズ・phase 82 の `scroll_invert` など config.json の全設定）。
例: A で縦の反転を保存 → B でフォントサイズを変える → 次回の起動で反転が消えている。逆順では B が保存した言語が A の切り替えで巻き戻る。

## 起票経緯（2026-11-26）

phase 82（[暫定 62](../history/62_scroll_direction_setting.md)）の Codex 敵対的レビュー 指摘 1（high）。本設定に限らない既存の性質のため、ユーザー判断でスコープ外として分離した。

## 現状

- `StartupIo.write_startup`（`keyseq/presentation/controllers/config_io/startup_io.py:43-60`）は、起動時に読んだ `_startup_settings` に変更分を重ねて config.json を丸ごと書く（書く直前にファイルを読み直さない）。
- 構成セットの保存にも config.json を書く経路がある（Codex の申告: `keymap_set_io.py:159-173`・`split_payloads.py:496-508`・未確認）。
- 多重起動の制御は無い（`grep` で該当なし。Codex の申告: `main.py:11-15`）。
- 正本: `data_schema.md` §5.4（config.json）。

## 提案（方向性・要設計）

- 案 A: 同じ設定フォルダへの多重起動を止める（ロックファイル等。2 つ目は既存の窓を前面へ / 知らせて終了）。
- 案 B: 書き込みのたびに最新のファイルを読み直し、変更したキーだけを重ねて書く（構成セットの保存の経路も含めて 1 つの入口にする）。
- 案 A と B の併用も検討する。まず多重起動を実際に使う場面があるかを確かめる。

## 想定スコープ

- presentation の config_io（・案 A なら起動処理）。JSON スキーマは不変の見込み。仕様変更あり（起動時の挙動または書き込みの規則）。
