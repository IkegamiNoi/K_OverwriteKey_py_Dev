# task_02_internal_values

## 目的

表示文字列を内部値（Combobox / StringVar の値・分岐の比較・辞書のキー）に使っている箇所を、内部コードで判定する形へ
置き換える（暫定 55 §6.3「表示文字列を内部値に使わない」・§9 受け入れ条件 8）。後の task で文言を `tr` に替えても
動きが変わらないようにするための下準備。**presentation 限定・表示する日本語の文言は 1 文字も変えない・`tr` はまだ使わない・
JSON スキーマ不変**。

## 対象範囲（presentation 限定・挙動不変）

### 共通の形（全対象に適用）

- 表示ラベルの表は「内部コード → ラベル」の向きで持ち、**ラベルは関数の呼び出し時に作る**（モジュール定数に日本語のラベルを
  入れない。後の task でラベルを `tr(...)` に替えるだけで済むように。暫定 55 §3.2「モジュール定数に訳した文言を入れない」）。
  例: `def _direction_labels() -> dict[str, str]: return {"up": "上", ...}`（順序 = 表示順）。
- 部品（ダイアログ・欄）は作るときにその表を 1 回呼んでインスタンスに持ち、Combobox の `values` はその表のラベル、
  値の読み取りは「今のラベル → コード」の逆引き（インスタンスが持つ表から）で行う。**判定・分岐はコードで行う**
  （`== "キー"` のような表示文字列の比較を残さない）。
- ラジオボタン等で値を自由に決められるものは、変数の値そのものを内部コードにする（例: `edge_var` の値 = `"down"` / `"up"`）。

### `keyseq/presentation/dialogs/action_key_hold_fields.py`

- 対象（`target_var` の `"キー"` / `"マウスのボタン"`）・押す / 離す（`edge_var` の `"押す"` / `"離す"`）・マウスのボタン
  （`{"左": "left", "右": "right", "中": "middle"}`）を上記の形へ。比較箇所（123・132・145・156 行付近）はコードで判定する。
- 外から `target_var` を読む箇所（`action_dialog.py:262`）のために、コードを返すメソッド（例 `target_kind() -> str`）を足す。

### `keyseq/presentation/dialogs/action_dialog.py`

- 262 行付近の `self.key_hold_fields.target_var.get() == "マウスのボタン"` を、上記のメソッドのコードで判定する。

### `keyseq/presentation/dialogs/action_control_fields.py`

- `SYSTEM_OPERATIONS`（ラベル → op）・`SYSTEM_LABELS`・`OUT_OF_RANGE_VALUES`（ラベル → 値）を上記の形へ（op / 値 → ラベルの関数）。
  `mode == "edit"` で「ループ」を除く処理は op（`OP_LOOP_START`）で除く。229 行の既定（`"カウンター +1"`）は `OP_COUNTER_INC` のラベルで。
  `ENCODINGS`（`"UTF-8"` / `"Shift_JIS"`。日本語ではない）は変えない。

### `keyseq/presentation/dialogs/action_mouse_scroll_fields.py`

- `_DIRECTION_VALUES` / `_DIRECTION_LABELS`（`"上"` 等）と Combobox の `values=("上", "下", "左", "右")`・既定 `"下"` を上記の形へ。

### `keyseq/presentation/controllers/keymap_panel/keymap_add_flow.py`

- 追加の種類 `kind`（`"新規"` / `"読込"` / `"貼り付け"`）を内部コード（例 `"new"` / `"load"` / `"paste"`）にし、
  78 行の題名の表もコード → 題名の関数にする。`kind` を渡している呼び出し元（keymap_panel 内・メニュー・ボタン）も合わせる。
  画面に出る文言は変えない。

### `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py`

- 418 行の `sel_key = ... or "（未選択）"` と 457 行の `key != "（未選択）"`: 表示用の文字列を判定に使わない。
  選択キーの有無は空 / None で判定し、`（未選択）` は表示の組み立てのときだけ使う。

### 上記以外で見つかったもの

- 実装時に同じ型（日本語の表示文字列との `==` / `in` / 辞書のキーでの逆引き・StringVar に日本語ラベルを入れて後で比較）を
  presentation 内で見つけたら同じ形で直し、報告に列挙する。application / domain の既定値の文言
  （例 `sequence_steps.py:48` の `"（なし）"`）は表示用なので本 task では触らない（task_06）。

### テスト

- 各対象について「判定がコードで行われる」ことを確かめるテストを足す: ラベルの関数をテスト内で別の文字列（例 英語風の
  ダミー）に差し替えても、ダイアログの値の読み取り・分岐・保存される action が日本語のときと同じになること（`unittest.mock.patch`）。
- 既存テスト（日本語の表示を assert しているもの）は変えずに通ること。テストが `SYSTEM_OPERATIONS` 等の旧名を参照していれば
  新しい関数へ直す。

## 設計メモ / 制約

- 表示順・既定値・保存される JSON の値は今と同じ。
- 新しい表を共通モジュールへ集めない（各ファイルの中に置く。`file_organization_rules.md` の局所化）。
- `tr` / i18n はまだ使わない（task_03〜05 でラベルを差し替える）。

## 読むファイル

1. `instructions/history/55_multilingual_ui.md` §3.2・§6.3
2. 編集対象（全体）: `dialogs/action_key_hold_fields.py`・`dialogs/action_control_fields.py`・`dialogs/action_mouse_scroll_fields.py`・
   `controllers/keymap_panel/keymap_add_flow.py`
3. `dialogs/action_dialog.py:250-270`・`controllers/trigger_panel/trigger_panel_controller.py:405-470`
4. 既存テストの手本: `tests_ui/test_action_dialog_key_hold.py`・`tests_ui/test_action_dialog_mouse_scroll.py`・`tests_ui/test_action_dialog_control.py`（各冒頭〜1 つ目のテストまで）

## 含まない

- 文言のキー化・`tr` の利用（task_03〜06）・アクションの種類の表示名（task_08）・英語の文言（task_08）
- application / domain の文言（task_06）

## 確認

- 追加テスト: ラベルの関数を差し替えても、key_hold（対象・押す / 離す・ボタン）・system の op と範囲外の扱い・mouse_scroll の向き・
  キーマップの追加の種類が同じ action / 同じ分岐になる / 「未選択」の判定が表示文字列に依らない
- 既存テスト全 pass（`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui`）・`-m compileall keyseq` clean・
  `-m tests.smoke_app` OK

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_12 でまとめて実施。
