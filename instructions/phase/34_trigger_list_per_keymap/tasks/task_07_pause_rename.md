# task_07_pause_rename

## 目的

「通常トリガー無効化」の表示を実態（直接切替・置換・トリガーをまとめて止める）に合わせて改名する（暫定仕様 25 §2-17・§8.4）。
**表示文言のみの変更**。挙動・内部名（`custom_input_enabled` / `TRIGGER_*_TEXT` 等の定数名・メソッド名）・JSON は変えない。presentation 限定。

## 対象範囲（presentation 限定・表示文言のみ）

- `keyseq/presentation/hook_button_texts.py:11-12`: ボタンの対を **「キーマップ一時停止」⇔「キーマップ再開」** に（定数名は据え置き）。
  ボタン幅を文言で揺らさない既存の仕組み（対の文言の長い方に合わせる〔`features.md` 104 行付近・`TRIGGER_TOGGLE_TEXTS`〕）が新しい対でも働くこと。
- ステータス欄（`trigger_panel_controller.py:276, 299` 付近）: 「通常トリガー: ON/OFF」を **「キーマップ: 動作中 / 一時停止」** の意味に改める。
  既存の「キーマップ: <名前>」表示と 1 項目に統合してよい（例「キーマップ: <名前>」/ 一時停止中は「キーマップ: <名前>（一時停止）」）。
  現行の「(待機)」表記（`keymap_panel_controller.py:546` `get_active_keymap_text`）はこの表記に置き換える。フック停止中の表示は現行の意味を保つ。
- 「有効/無効トグルキー」のラベル（`views/full_view/hook_frame.py:40` / `views/compact_view/hook_frame.py:37`）とエラーメッセージ
  （`hook_controller.py:211` / `trigger_panel_controller.py:400, 441`）→ **「一時停止/再開キー」**。
- 「モード切替キー」表記（`keymap_panel_controller.py:144`）と、停止 / トグルキーの取得時の重複メッセージで使う「トグルキー」表記（`app.py:155, 164`）も **「一時停止/再開キー」** に揃える。
- コメント・docstring の旧表記（`compact_view.py:16` / `full_view/hook_frame.py:39` 等）も新表記に揃える（挙動なし）。
- 「通常トリガーと重複しています」等、**トリガー一覧を指す「通常トリガー」**の表記は変えない。キーボード表示の `MODE` 表記も変えない（§8.4 の対象外）。

### テスト（更新・追加）

- 旧文言を期待している既存テストを新文言へ更新（文言変更によるもののみ。アサーションを緩めない）。
- 新規: ボタンの対の文言・ステータスの一時停止表示・「一時停止/再開キー」ラベルを確かめる（既存の文言テストに足す形でよい）。
- 旧文言の残存検出: `keyseq/presentation` 配下に「通常トリガー無効化」「通常トリガー有効化」「有効/無効トグルキー」「モード切替キー」「(待機)」が無いことを確かめる（静的テスト or 確認コマンド）。

## 読むファイル

- `instructions/history/25_trigger_list_per_keymap.md` §8.4
- 上記の各ファイルの該当行の前後のみ / `instructions/common/spec_detail/features.md:100-110`（対の文言の幅の規定）

## 含まない

- 内部名・定数名・メソッド名の改名（暫定 §11）/ 挙動の変更 / `instructions/` 配下の編集（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（skip 7 据え置き）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass
- `git grep -n "通常トリガー無効化\|通常トリガー有効化\|有効/無効トグルキー\|モード切替キー\|(待機)" -- keyseq` が 0 件

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視はユーザーが行う（task_08 の前にまとめて依頼）。
