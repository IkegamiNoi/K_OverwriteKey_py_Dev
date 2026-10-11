# task_01_title_instead_of_status

## 目的

キーボードUIのステータス欄（`summary_var` の Label）を削除し、レイアウト名と編集中の案内をウィンドウタイトルへ出す（暫定 39 §3・§6 の 1・2）。
**presentation 限定（`keyboard_window.py` のみ）・domain / application / infrastructure 不変・スキーマ不変。**

## 対象範囲（presentation・`keyseq/presentation/keyboard_window.py` とテスト）

### `keyseq/presentation/keyboard_window.py`

- `__init__` の `self.summary_var` と、それを表示する `ttk.Label(...).pack(fill="x", pady=(0, 8))`（:66-67）を削除する。キャンバスは container の上端から始まる
- `self.title("Keyboard UI")`（:50）は残してよいが、最終的なタイトルは下記のメソッドで決める
- `_update_summary`（:327-375）を `_update_title` に置き換える（呼び出し元 5 か所〔`__init__` / `update_layout` / `update_from_config` / `_begin_edit` / `_cancel_edit`〕も追従）:
  - レイアウト表示名 = `getattr(self._layout, "display_name", "") or getattr(self._layout, "layout_id", "")`（現行と同じ）
  - 編集中（`self._editing_source_key` が真）: `Keyboard UI — 編集中: <self._editing_source_key>（Escでキャンセル）`
  - 通常: レイアウト表示名が空でなければ `Keyboard UI — <表示名>`、空なら `Keyboard UI`
  - 区切りは全角ダッシュ前後に半角空白（` — `・U+2014）。括弧は全角
  - 文言を組み立てる部分は tkinter に依存しないモジュールレベルの純関数（例: `keyboard_window_title(layout_name: str, editing_key: str | None) -> str`）にし、メソッドはそれを `self.title(...)` へ渡すだけにする
- 色分け説明の 7 分岐は削除する（§2-1 で表示しないと確定）

### テスト

- `tests/` に純関数のテストを追加（新規ファイル `tests/test_keyboard_window_title.py`）: 通常 / 表示名が空 / 編集中（表示名の有無に関係なく編集中の文言）
- `tests_ui/test_app_ui_flows.py` の `test_keyboard_window_opens_and_closes`（:2324）付近に、開いた直後のタイトルが `Keyboard UI — ` で始まり、`summary_var` 属性を持たないことの確認を加える（既存テストは変えない・新規テストメソッドで追加してよい）

### 設計メモ / 制約

- `_kind_map` は描画で使うので残す（削除するのは説明文の分岐だけ）
- 編集中の案内から「右クリックでクリア」は落とす（暫定 39 §3 の受容）
- 余計な整形変更・他メソッドの変更をしない

## 読むファイル

- `keyseq/presentation/keyboard_window.py`（全体・編集対象）
- `instructions/history/39_keyboard_ui_window.md` §2-1・§3
- `tests_ui/test_app_ui_flows.py:2318-2330`（既存テストの書き方）
- `tests/` の既存テスト 1 本（書式の手本。例: `tests/test_compact_window_size.py` があればその冒頭 30 行）

## 含まない

- 縦横比固定・`geometry` / `minsize` の変更（task_02）
- 「キーボードUIを常に手前」・一時解除（task_03）
- 正本・codebase_map の更新（task_05）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（新規の純関数テスト 3 ケース以上を含む）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass（タイトルのテストを含む）
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass
- `grep -n "summary_var\|_update_summary" keyseq tests tests_ui` が 0 件

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は本タスクでは行わない（task_02 の目視でタイトル表示もあわせて見る）。
