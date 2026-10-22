# task_04_sequence_action_texts

## 目的

出力シーケンスとアクションまわりの画面に出る文言（ダイアログの欄・入力検査・実行時のエラー）へ、暫定 51 の用語表・個別確定文・表記規則を当てる（§2・§2.2 C1〜C5・§3.1・§3.2・§3.6）。
**presentation（アクションのダイアログ）・application / domain / infrastructure の画面に出る文言の文字列のみ。挙動不変・保存値不変（C3 は表示名だけで保存値 `empty` は不変）・JSON スキーマ不変。**

## 対象範囲（担当ファイルの文字列・ファイル単位）

**対象文字列の一覧 = `instructions/phase/68_ui_terminology/tools/task_04_strings.md`（296 件・実装前）**。全行を見て、当たる規則があれば置換する。
担当ファイル: `dialogs/action_dialog.py`・`action_control_fields.py`・`action_key_hold_fields.py`・`action_mouse_scroll_fields.py`・`preset_dialog.py` /
`application/` の sequence_steps・call_context・sequence_runner/・sequence_history・file_line_loader・file_line_reader・held_inputs・key_repeat・screen_grid_session /
`domain/`（screen_grid/ を除く）/ `infrastructure/input_gateway.py`。

主な置換（網羅は一覧と暫定 51 が正）:

- **C1**: `action_control_fields.py:372`「ファイルが空です。」→「ファイルを指定してください。」（D9 より優先）
- **C2**: `action_control_fields.py:130` →「呼び出し先の「間隔(ms)」で実行します（連続実行OFFでも使います）」（D5 で空白なし）
- **C3**: `action_control_fields.py:43`（選択肢の表示名）「空を送る」→「何も送らない」。**表示名 → 値の対応（`OUT_OF_RANGE_VALUES`）の値は不変**。既存の行を開いたときの表示も新しい名前で出ること
- **C4**: 本タスクは `sequence_steps.py:283` を「「戻す」「先頭へ」は出力シーケンスに単独で登録してください。」へ（`trigger_panel/action_edit.py` の分は task_03）
- **C5**: `call_graph.py:78`・`call_context.py:153`・`control_target.py:35` →「「戻す」「先頭へ」のトリガーは呼び出せません / 指定できません」
- **A7**: 文中の「シーケンス」単独を「出力シーケンス」に（狭い見出しは task_06）
- **A10**: キーの「記録」・座標の「取得」の使い分け（`action_dialog.py:65・384・397`・`action_key_hold_fields.py` は記録 / `action_dialog.py:121・300・351・359` は取得のまま）。`action_dialog.py:351`「…取得中：画面上の…」→「取得中: 画面上の…」（文頭の「…」を外す・D4）
- **A12**: `action_dialog.py:78`「OSショートカット（プリセット）」→「プリセット」・`action_dialog.py:588`「ホットキープリセット編集」→「プリセット編集」
- **A19**: なし見込み（あれば当てる）
- **D8**: 利用者に見える「〜が不正です」→「〜が正しくありません」（domain・application の検査文を含む）
- **D9**: 入力ダイアログの検査「〜が空です。」→「〜を入力してください。」（`action_dialog.py:205・213`・`action_control_fields.py:275・375`・`preset_dialog.py:46・49` ほか）。内部・ファイルの中身の検査（`domain/hotkey.py:11` ほか）は据え置き
- **§3.6 D1・D2・D4〜D7**: 担当ファイルの全文言に当てる（細則どおり）。**D3 は当てない（task_06）**

### 設計メモ / 制約

- **D4 の行末**: 直後が改行のコロンには空白を入れない（`:\n` のまま。`: \n` にしない・decisions 2026-10-23）。
- **B 項は含めない**: アクションの種類コンボの値（`hotkey` / `text` / `mouse_click` 等）と、エラー中の種類の値（「mouse_click の X/Y が空です。」の `mouse_click`）は据え置く（§2.1 Q1）。ただし同じ文の他の語・表記（D5・D8・D9）は当てる。
- 「hotkey として反映されます」の hotkey は Q1 で据え置き。
- ログ専用の文言・docstring・コメントは触らない。
- 文言を検査している既存テストは新しい文言へ追従させる（期待する挙動は変えない）。

## 読むファイル

1. `instructions/history/51_ui_terminology.md` の §2・§2.1 Q1・§2.2（C1〜C5）・§3.1・§3.2（A7・A10・A12）・§3.6
2. `instructions/phase/68_ui_terminology/tools/task_04_strings.md`（対象一覧）
3. 担当ファイル（一覧に出てくる行の周辺だけ）

## 含まない

- 担当外ファイル（`controllers/trigger_panel/action_edit.py` の C4 = task_03）
- B 項（内部名の表示名化）・「…」の付与 / 除去（task_06）・前後差分（task_07）・正本反映と実機目視（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- C3 の既存の行（`out_of_range: empty`）を開いて「何も送らない」が選ばれ、OK で `empty` のまま保存されるテスト（既存の追従で可）pass
- `-m unittest discover -s tests` / `-s tests_ui` 全 pass・`-m tests.smoke_app` OK
- `extract_ja.py` を担当ファイルへ流し、「やめる語」が残っていない（残すものは据え置きの理由を報告）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_08 でまとめて実施。
