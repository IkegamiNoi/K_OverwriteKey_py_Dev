# task_03_keymap_trigger_texts

## 目的

キーマップ・トリガー・停止 / 切替 / 置換のキーまわりの画面に出る文言へ、暫定 51 の用語表・個別確定文・表記規則を当てる（§2・§2.2 C8・C9・C13・C16・§3.1・§3.2・§3.3 (c)・§3.4「上位の割り当て」・§3.6）。
**presentation と application（画面に出る文言）の文字列のみ。挙動不変・JSON スキーマ不変。**

## 対象範囲（担当ファイルの文字列・ファイル単位）

**対象文字列の一覧 = `instructions/phase/68_ui_terminology/tools/task_03_strings.md`（313 件・実装前）**。全行を見て、当たる規則があれば置換する。
担当ファイル: `controllers/keymap_panel/`（keymap_add_flow・keymap_list_edit・keymap_panel_controller）・`controllers/trigger_panel/`・`controllers/hook_controller.py`・`key_capture.py`・`layout_controller.py`・
`presentation/app.py`（:123-124 以外）・`application/keymap_switch_batch.py`・`hotkey_service.py`・`hook_coordinator.py`・`action_executor.py`・`presentation/hook_button_texts.py`・
`dialogs/keymap_edit_dialog.py`・`keymap_switch_batch_dialog.py`・`trigger_dialog.py`。

主な置換（網羅は一覧と暫定 51 が正）:

- **A2**: 文言中の「keymap」→「キーマップ」（`keymap_panel_controller.py:225・255-393` ほか）
- **A3・A4**: §3.2 A3/A4 の列挙どおり（`keymap_panel_controller.py:625・629・635・654・656・667・670`・`action_executor.py:334`・`app.py:236・249`・`keymap_switch_batch.py:113`・`keymap_panel_controller.py:202`）。
  「キーマップ一時停止」「キーマップ再開」（`hook_button_texts.py:14-15`）は据え置き
- **A5**: 「停止トリガー」（`app.py:230`）・「フック停止トリガー」（`trigger_row_edit.py:39・90`）→「停止キー」
- **A6**: 「直接切替キー」「キーマップ直接切替キー」→「切替キー」（全廃）
- **A7・A8**: 「未保存のトリガー一覧・シーケンスも破棄されます」（`keymap_list_edit.py:110`・`keymap_panel_controller.py:316`）→「未保存のトリガーセット・出力シーケンスも破棄されます」
- **§3.3 (c)・A20**: 重複検査の種類名「トリガー一覧」（`app.py:233・246`）→「トリガーキー」/「通常トリガー」（`keymap_switch_batch.py:111`・`keymap_panel_controller.py:197`）→「トリガーキー」/「トリガーのキー」（`hook_controller.py:292`）→「トリガーキー」
- **A10**: `hook_button_texts.py:3-7`・`keymap_edit_dialog.py:157`・`keymap_switch_batch_dialog.py:224`・`trigger_dialog.py:92` のキーの「取得」→「記録」（D4 で「記録中: …」）
- **A11**: `keymap_panel_controller.py:387・393・399`・`trigger_row_edit.py:63・74・87-99` →「編集」。`trigger_box.py` / `keymap_box.py` のボタンは task_06。据え置き = 「名前変更」・指示文「〜を変更してください」・「呼び出し先を変更できません」（`trigger_panel_controller.py:34`）・結果通知
- **A15**: `hook_controller.py:285`・`trigger_panel_controller.py:256` の既定値「上位の割り当て」→「他のキー設定」
- **C8**: `keymap_add_flow.py:78`「読込キーマップの追加」→「ファイルからキーマップを追加」
- **C9**: 「〜は変更なしです」→「〜に変更はありません」（`keymap_panel_controller.py:276・544・600・656` ほか担当ファイル内）
- **C13**: `hook_controller.py:389-390` →「送信キーの指定に誤りがある可能性があります。内容を確認してください。」
- **C16**: `trigger_dialog.py:57・103` の例文を初期表示の形に揃える（D2 で「例: 」）
- **§3.6 D1〜D9・D11**: 担当ファイルの全文言に当てる（細則どおり）。**D3 は当てない（task_06）**

### 設計メモ / 制約

- 据え置き（§3.1・§3.2）: キー名・ID の差し込み・ログ専用の文言・docstring・コメント・画面のリストの見出し「トリガー一覧」（task_06 の担当ファイルにある）。
- `key_capture.py` の `{self._label}` に入る名前は呼び出し元（`app.py` 等）で決まる。呼び出し元の名前を A5 等で直す。
- 文言を検査している既存テストは新しい文言へ追従させる（期待する挙動は変えない）。tests_ui がボタンを文言で探している場合も追従する。

## 読むファイル

1. `instructions/history/51_ui_terminology.md` の §2・§2.2（C8・C9・C13・C16）・§3.1・§3.2（A2〜A6・A10・A11・A20）・§3.3・§3.4 末行・§3.6
2. `instructions/phase/68_ui_terminology/tools/task_03_strings.md`（対象一覧）
3. 担当ファイル（一覧に出てくる行の周辺だけ）

## 含まない

- 担当外ファイルの文言（保存・読込 = task_02 / アクション = task_04 / プリセット・整理・退避 = task_05 / メニュー・表示・`trigger_box.py`・`keymap_box.py`・`hook_frame.py` = task_06）
- 「…」の付与 / 除去（task_06）・前後差分（task_07）・正本反映と実機目視（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` / `-s tests_ui` 全 pass・`-m tests.smoke_app` OK
- `extract_ja.py` を担当ファイルへ流し、「やめる語」（暫定 51 §2）が残っていない（残すものは据え置きの理由を報告）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_08 でまとめて実施。
