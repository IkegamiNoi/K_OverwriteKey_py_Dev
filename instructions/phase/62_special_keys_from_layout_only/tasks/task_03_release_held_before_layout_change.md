# task_03_release_held_before_layout_change

## 目的

送信側が引く値（登録済みのレイアウト `_keyboard_layout_entries` と選んでいる id）を置き換える**前に**、押したままのキーを `held_inputs.release_all()` ですべて離す（暫定 45 §6・案 B）。
レイアウトで決まったキー（`muhenkan` 等）を押したままレイアウトが変わると、離すときに新しいレイアウトで引き直してしまい、離せなくなる。これを防ぐ。
**presentation 限定**（`layout_controller.py`）。application・infrastructure・domain は不変。JSON スキーマ不変。

## 対象範囲（presentation 限定・`layout_controller.py` のみ）

### `keyseq/presentation/controllers/layout_controller.py`

- private メソッド `_release_held_inputs_before_layout_change(self) -> None` を追加する
  - `getattr(self._app, "held_inputs", None)` が無ければ何もしない
  - `errors = held_inputs.release_all()` を呼ぶ
  - errors が空でなければ、`hook_controller._release_held_inputs`（`keyseq/presentation/controllers/hook_controller.py:224-230`）と同じ形で通知する: `self._app.hook.show_action_error("", {"type": "key_hold", "value": "すべて解放"}, RuntimeError("\n".join(str(e) for e in errors)))`
    - `self._app.hook` が無ければ通知を省く
  - **通知の後も処理を続ける**（切替は止めない）
- 呼ぶ場所（置き換えの**前**）
  - `reload_keyboard_layouts`: `self._keyboard_layout_entries = collect_keyboard_layouts(...)` の**前**で、毎回呼ぶ（中身が変わったかは見ない）
  - `sync_keyboard_layout_controls` と `set_keyboard_layout_selection`: 選ぶ id（`selected`）を決めたあと、`self.keyboard_layout_id = selected` の**前**で、**`selected != self.keyboard_layout_id` のときだけ**呼ぶ

### テスト

- `tests/test_layout_controller_scan_code.py` に追加する（`app` のスタブで `held_inputs` / `hook` を `Mock` にする。`collect_keyboard_layouts` や UI の部品は差し替えてよい）
  - `reload_keyboard_layouts`: `release_all` が `_keyboard_layout_entries` の置き換えより前に呼ばれる（`collect_keyboard_layouts` を差し替え、呼ばれた時点で `release_all` が呼ばれ済みであることを確かめる）
  - `set_keyboard_layout_selection`
    - id が変わるとき: `release_all` が 1 回、`keyboard_layout_id` の書き換えより前に呼ばれる（呼ばれた時点で `keyboard_layout_id` が古い id）
    - id が変わらないとき: `release_all` を呼ばない
  - `sync_keyboard_layout_controls`: id が変わるときだけ呼ぶ（変わるとき / 変わらないときの 2 件）
  - `release_all` が例外のリストを返したとき: `hook.show_action_error` が 1 回呼ばれ、切替は進む（`keyboard_layout_id` が新しい id）
  - `held_inputs` が無い `app`: 例外にならず切替が進む

### 設計メモ / 制約

- 直接置換は押してすぐ離すので対象外（暫定 45 §6）
- `held_inputs.release_all` / `hook_controller` は変えない（通知の形をまねるだけ）
- 受け入れ条件 §7 #11 に当たる

## 読むファイル

1. `instructions/history/45_special_keys_from_layout_only.md` §6
2. `keyseq/presentation/controllers/layout_controller.py`（編集対象。:195-262 を中心に読む）
3. `keyseq/presentation/controllers/hook_controller.py:224-230`（通知の手本）
4. `keyseq/application/held_inputs.py:194-222`（`release_all` の戻り値）
5. `tests/test_layout_controller_scan_code.py`（スタブの作り方の手本）

## 含まない

- 正本反映（task_04）
- 失敗した記録の再試行のやり方の変更（受容・暫定 45 §6）
- 受け取りと送信で同じレイアウトの写しを使う形（idea_51）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_layout_controller_scan_code` が全 pass
- 既存テストが全 pass: `unittest discover -s tests` / `unittest discover -s tests_ui` / `-m tests.smoke_app`
- **実機目視（ユーザー・JIS キーボード・jis.json を選ぶ）**（暫定 45 §7 #12）
  1. 無変換をトリガーにしたキーマップで、無変換を押して反応する
  2. 出力に `muhenkan` / `zenkaku_hankaku` を書き、実行すると物理キーを押したときと同じ動き（IME の切替）になる
  3. （任意）US TKL を選ぶと、出力の `muhenkan` の検査がエラーになる

## 完了条件

- 上記の確認（自動テスト）が pass し、**reviewer が採用**していること。
- 実機目視は本タスクで行う（ユーザー）。結果が NG なら、本タスク内で原因を切り分ける。
