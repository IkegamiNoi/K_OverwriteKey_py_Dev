# task_02_compact_header_expanders

## 目的

省略表示の上部の「フック」の枠（`CompactHookFrame`）と「表示」の枠（`CompactDisplayFrame`）を、それぞれ見出しのクリックで開閉できる Expander にし、
開閉の状態を `config/config.json` の新しいキー `compact_header_view` に保存する。開閉でウィンドウの大きさは変えず、最小の高さだけ測り直す（暫定 42 §4・§9-5〜7）。
**presentation 限定・domain / application 不変。JSON は config.json に任意キー 1 つ追加（無い / 不正なら両方開く・後方互換）。**

## 対象範囲（presentation・省略表示の上部 + 開閉の制御 + テスト）

### 新規 `keyseq/presentation/compact_header_view.py`（tkinter 非依存）

- `COMPACT_HEADER_VIEW_KEY = "compact_header_view"`
- `parse_compact_header_view(raw: object) -> dict[str, bool]`: 返り値は常に `{"hook": bool, "display": bool}`。`raw` が dict でなければ両方 True。
  各値は bool ならその値・それ以外（キーが無い・bool でない）はその値だけ True（独立に検証。手本 = `compact_pane_heights.py:6-18` の `parse_compact_sequence_view`）

### 新規 `keyseq/presentation/controllers/compact_header_controller.py`

- `CompactHeaderController(app)`: 初期化で `parse_compact_header_view(app._startup_settings.get(COMPACT_HEADER_VIEW_KEY))` を持つ
- 枠の登録（2 つ）と開閉: 見出しのクリックで対象の枠だけを反転し、見た目を切り替え、
  ①閉じるときフォーカスがその枠の中（`focus_get()` がその枠か子孫）なら `compact_view.trigger_box.trigger_list` へ `focus_set()` ②省略表示の最小の高さを測り直す（下記）
  ③`app.startup_io.write_startup({COMPACT_HEADER_VIEW_KEY: {"hook": <今の値>, "display": <今の値>}})` を 1 回（**常に両方の値を書く**・未知のキーは保持しない）
- 起動時（読み込んだ値で閉じている枠）は見た目だけ合わせ、保存はしない
- `app.py` で `CompactSequenceController` と同じ並び（:243 付近）に生成し、`CompactView` の組み立て後に 2 つの枠を登録する

### `keyseq/presentation/views/compact_view/`（`compact_view.py`・`hook_frame.py`・`display_frame.py`）

- 見出し: 開 = 枠（`LabelFrame`）の見出しに `▾ フック` / `▾ 表示`、閉 = 枠ごと `pack_forget` して同じ位置に `▸ フック` / `▸ 表示` の `ttk.Label` を 1 行置く
  （見出しの作法 = `views/compact_view/sequence_frame.py:13-15,40-41`: `anchor="w"`・`cursor="hand2"`・`<Button-1>` でクリック）。
  開いたときの見出しもクリックできること（`LabelFrame` の `labelwidget` に Label を使う等）。**見出しを二重に出さない**
- 並び順（フック → 表示）は開閉で変えない（`pack(before=...)` 等で位置を保つ）。表示の枠の `pady=(8, 0)`（`compact_view.py:30`）は閉じても見出しの行に引き継ぐ
- 枠の中身（ボタン・Entry・Combobox・Checkbutton）と `app.hook.register_hook_buttons`・`app.layout.register_layout_combo` 等の登録は変えない（閉じても機能は効く）

### `keyseq/presentation/controllers/compact_window_controller.py`

- 最小の高さの測り直しを公開メソッドにする: 今の `on_font_changed`（:89-98）の本体（`_compact_mode` の確認・`_measure()`・最小より低ければ `_apply_size((幅, 最小))`・そうでなければ `minsize`）を
  `refresh_minimum_height()` に移し、`on_font_changed` はそれを呼ぶ。開閉の制御も同じものを呼ぶ
- `_measure`（:50-67）は `header_area.winfo_reqheight()` で上部を数えているので、**式は変えない**（閉じた枠は見出しの 1 行分になることをテストで確かめる）
- 開閉でウィンドウの大きさは変えない（最小より低いときに最小まで伸ばす以外）

### テスト

- 新規 `tests/test_compact_header_view.py`: `parse_compact_header_view` の dict でない（None・list・文字列）/ 空 dict / 片方だけ不正（`"x"`・1・None）/ 両方 False / 未知のキーを含む、の各ケース
- 新規 `tests_ui/test_compact_header_view.py`（App はクラスで共有・`write_startup` をパッチ・作法 = `tests_ui/test_compact_sequence_view.py:26-40`）:
  1. 既定で両方開き、見出しが `▾ フック` / `▾ 表示`
  2. フックの見出しをクリック → 閉じて `▸ フック` の 1 行・表示の枠はそのまま・並び順が保たれる・ウィンドウの幅と高さが変わらない・トリガー一覧の欄が伸びる
  3. 開閉のたびに `write_startup` が `{"compact_header_view": {"hook": .., "display": ..}}` で 1 回呼ばれる（両方の値）
  4. 保存値 `{"hook": False, "display": "x"}` で起動 → フックだけ閉じて起動し、起動時に `write_startup` を呼ばない（作法 = `test_compact_sequence_view.py:155-166`）
  5. 閉じると省略表示の最小の高さ（`compact_window.minimum_height`）が下がり、開くと戻る。最小より低いウィンドウで開くと最小まで伸びる
  6. フォーカスが閉じる枠の中（例: `stop_key_entry`）にあるとき、閉じるとトリガー一覧へ移る
  7. 閉じていても `hook_toggle_btn` 等の登録が生きている（`app.hook` の更新でボタンの文言が変わる等、既存の登録が外れていないこと）
  - 各テストは `addCleanup` で開閉の状態とウィンドウの大きさを元へ戻す

### 設計メモ / 制約

- 手本 = 省略表示のシーケンス欄（`compact_sequence_controller.py:58-81`・`sequence_frame.py`）。ただし本タスクは `PanedWindow` ではなく `header_area` の pack の出し入れ
- 開閉の状態の持ち主はコントローラ（view に保存処理を書かない）。`compact_pane_heights.py` へ混ぜない（高さの規則のモジュールのため。新規モジュールに置く）
- `config.json` を直接 read-modify-write しない（`startup_io.write_startup` 1 本）
- フル表示の上部は変えない

## 読むファイル

1. `instructions/history/42_window_size_fit.md` §4
2. `keyseq/presentation/views/compact_view/compact_view.py`・`hook_frame.py`・`display_frame.py`（全体）
3. `keyseq/presentation/views/compact_view/sequence_frame.py:11-48`（見出しの作法）
4. `keyseq/presentation/controllers/compact_sequence_controller.py:17-35,58-81`（開閉と保存の手本）
5. `keyseq/presentation/compact_pane_heights.py:1-18`（保存値の検証の手本）
6. `keyseq/presentation/controllers/compact_window_controller.py:50-98`
7. `keyseq/presentation/app.py:240-250,350-360`（コントローラの生成・CompactView の生成）
8. `tests_ui/test_compact_sequence_view.py:1-60,136-190,402-415`（テストの作法）・`tests/test_compact_pane_heights.py`（単体テストの作法）

## 含まない

- フル表示のスクロール・最小の大きさ（task_03・task_04）
- 正本 `features.md` §4.6・`data_schema.md` §5.4・`codebase_map.md` の更新（task_06）
- 見出しへの状態の要約の表示 / フル表示の上部の開閉（暫定 42 §10）

## 確認

（実行は verifier・`.venv` python）
- `compileall -q keyseq main.py tests tests_ui` clean
- `tests/test_compact_header_view.py`・`tests_ui/test_compact_header_view.py` pass（上記 1〜7）
- `tests_ui/test_compact_window.py`・`test_compact_sequence_view.py`・`test_call_view_compact.py` pass（既存の省略表示の挙動の不変）
- `unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` 全 pass（件数が減っていない）
- 実行後に `config/config.json` の mtime が変わっていない

## 完了条件

- 上記確認 pass・**reviewer 採用**
- **ユーザーの実機目視**（本タスクで実施）: 省略表示で「フック」「表示」を開閉 → 見出しの 1 行になる・トリガー一覧が伸びる・ウィンドウの大きさが変わらない・再起動後も開閉が残る /
  あわせて task_01 のステータス欄（幅 270 の省略表示で `フック: 一時停止` が見える）
