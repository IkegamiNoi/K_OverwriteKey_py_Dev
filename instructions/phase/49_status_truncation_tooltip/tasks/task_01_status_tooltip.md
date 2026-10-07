# task_01_status_tooltip

## 目的

ステータス欄・ステータスバー（左: ファイル状態 / 中央: 一時メッセージ）が見切れているとき、マウスを乗せると 1 行化する前の全文（改行入り）をツールチップで出す（phase.md「確定」1〜4）。
子ファイル保存ダイアログのツールチップを presentation 層の共有部品へ昇格して両方から使う。
**presentation 限定・domain / application 不変・JSON / config.json 不変。子ファイル保存ダイアログのツールチップの挙動は不変。**

## 対象範囲（presentation 限定）

### 新規 `keyseq/presentation/hover_tooltip.py`（共有部品・tkinter を使ってよい）

- `child_save_dialog.py:154-188` の `_bind_tooltip` の挙動をそのまま移した共有部品。名前は内容を表すもの（例 `HoverTooltip` クラス + `bind_hover_tooltip(widget, text, should_show) -> HoverTooltip`）
  - `text` は**文字列を返す callable**（固定文字列の呼び出し側は `lambda: text` で渡す）・`should_show: Callable[[], bool]`
  - マウスが入ったら（`<Enter>`）`should_show()` が真で `text()` が空でなければ、マウス位置の右下（+12, +12）に `overrideredirect` の Toplevel と Label（padding=4）で出す。`<Leave>` / `<Button>` で閉じる（`add` の有無も含め今の bind の仕方を保つ）
  - **`refresh()`**: 出している間に呼ばれたら、`should_show()` が偽 か `text()` が空なら閉じ、そうでなければ Label の文言を新しい `text()` へ差し替える（位置は保つ）。出していなければ何もしない（確定 3）
  - 複数行の文言は行を保って左揃えで出す（`justify="left"`）
  - 例外は今と同じく吸収する（Toplevel の生成・破棄の失敗でアプリを止めない）
- 新規ファイルは 300 行以内の目安

### `keyseq/presentation/controllers/config_io/child_save_dialog.py`

- `_bind_tooltip` を削除し、`_add_text_cell` から共有部品を呼ぶ（`lambda: text` と今の `should_show`）。**旧位置に転送用の口を残さない**（恒久的な互換レイヤーの禁止）

### `keyseq/presentation/ui_vars.py`

- 全文用の `tk.StringVar` を 3 つ足す（例 `status_full_var` / `file_status_full_var` / `flash_message_full_var`）。表示用の 3 つ（`status_var` / `file_status_var` / `flash_message_var`）と対にする

### 全文の書き込み（表示用を書く箇所すべてで全文も書く）

- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py` `update_status`（:406-441）:
  - 省略表示: 全文 = 各値を 1 行化しない `f"フック: {hook_state} / キーマップ: {keymap_text}\n選択: {sel_key}{suffix}"`（`suffix` も 1 行化しない次の行）・表示 = 今の文言（各値を `one_line`）
  - フル表示: 全文 = 表示と同じ文言
  - **このファイルの行数を増やさない（639 行以下）**。必要なら全文と表示の組み立てを短くまとめる
- `keyseq/presentation/app.py`（:306-345）: `_update_file_status`（全文 = `text`）/ `_refresh_status_bar`・`_set_flash_message`（全文 = `self._flash_message`）/ `_clear_flash_message`（全文も ""）。
  表示用の 1 行化（`_status_bar_text`）は今のまま。app.py は 657 行なので、全文と表示の 2 つを書く処理を 1 つの小さなメソッドにまとめて増分を抑える

### `keyseq/presentation/views/status_bar.py`

- 3 つの Label を変数に受け、それぞれへ共有部品を付ける:
  - `text` = 対応する全文用の変数の `get()`
  - `should_show` = **見切れているか** = Label の要求幅（`winfo_reqwidth()`・表示中の文言とフォントで決まる）が実際の幅（`winfo_width()`）より大きい。幅が 1 以下（未配置）なら偽
  - 全文用・表示用の変数の書き込み（`trace_add("write", ...)`）と Label の `<Configure>` で `refresh()` を呼ぶ（文言の変化・窓の幅の変化・フォント変更に追従。確定 3）
- Label の見た目・pack / grid の配置・`before=` の順序は変えない

### テスト

- 新規 `tests_ui/test_status_tooltip.py`（App を作るなら `tests_ui/test_keymap_set_history_flow.py:17-34` の ExitStack 手法で実 `config/` を隔離・`setUpClass` で共有）:
  ①フル表示で窓を狭めて見切れたステータス欄に `<Enter>` → ツールチップが出て全文が入っている ②見切れていなければ出ない
  ③省略表示で、改行を含む値（例: 次の行が改行入りの text アクション）のとき、欄は各値 1 行化・ツールチップは改行入りの全文
  ④ステータスバー中央の一時メッセージ（複数行）が見切れているとき改行入りの全文が出る・出している間に `_set_flash_message` で文言が変わると中身が追従し、`_clear_flash_message` で閉じる
  ⑤出している間に窓を広げて見切れなくなったら閉じる ⑥`<Leave>` で閉じ Toplevel が残らない
- 共有部品の単体（`tests_ui/test_hover_tooltip.py` 等）: 固定文字列・`refresh()` での差し替え / 閉じる
- `tests_ui/test_child_save_dialog.py:788-830, 1306-1340` の `_bind_tooltip` の差し替え・参照を新しい位置（共有部品の関数を `child_save_dialog` モジュールが import した名前）へ追随（期待値は変えない）

### 文書

- `instructions/common/codebase_map.md`: `hover_tooltip.py` の行（presentation 直下の一覧）・`status_bar.py` の行（ツールチップ）・`ui_vars.py` の全文用変数・`child_save_dialog.py` の行（共有部品を使う）

## 読むファイル

- `keyseq/presentation/controllers/config_io/child_save_dialog.py:105-190`
- `keyseq/presentation/views/status_bar.py`・`keyseq/presentation/ui_vars.py`（全体）
- `keyseq/presentation/app.py:300-345`・`controllers/trigger_panel/trigger_panel_controller.py:400-445`・`presentation/status_text.py`
- `tests_ui/test_child_save_dialog.py:780-830, 1300-1345`・`tests_ui/test_keymap_set_history_flow.py:17-34`・`tests_ui/test_compact_window.py`（省略表示への切替とステータスの検査の流儀）
- `instructions/common/codebase_map.md` の presentation 直下の一覧・「メニュー / ステータス」節

## 含まない

- 正本 `features.md` の改訂（task_02）
- ステータス以外へのツールチップ・表示の遅延・欄の折り返し / 幅の自動調整
- `hook_controller.py:240`・`pane_measure.py:32` の `flash_message_var` の読み手の変更（表示用のまま）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` clean
- 追加・変更したテストを含めて tests・tests_ui 全体・`-m tests.smoke_app` pass。実 `config/` を汚さない
- `trigger_panel_controller.py` が 639 行以下・`child_save_dialog.py` に `_bind_tooltip` が無い（`grep`）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視（ユーザー）: 本タスクで実施（フル・省略で幅を狭めて乗せる / 見切れていなければ出ない / 一時メッセージの表示中・実行中の追従 / 子ファイル保存ダイアログのツールチップが従来どおり）
