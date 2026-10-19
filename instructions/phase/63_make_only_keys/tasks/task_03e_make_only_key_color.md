# task_03e_make_only_key_color

## 目的

キーボードUI で、押下だけのキー（走査コード 241 / 242）に直接置換を割り当てた枠を、リピートしないことが分かるように**灰色がかった緑**で出す（暫定 46 v0.4 §3.4・§9 #1 / #2・ユーザー確定 2026-10-20）。

**presentation 限定**（`keyboard_window.py` とその UI テスト）。domain の表は参照のみ（変えない）。application・infrastructure・JSON スキーマは変えない。

## 対象範囲（presentation 限定）

### `keyseq/presentation/keyboard_window.py`

- 枠の描画（:376-392 付近・`kind = self._kind_map.get(lookup_key, "normal")` の後）で、次の両方に当たる枠の kind を新しい種類（例: `keymap_make_only`）にする
  - 割り当て禁止の判定（:386-387）の後で、kind が `keymap` のまま
  - その枠の `KeySpec`（`spec`）の `scan_code` か `extra_scan_codes` のどれかが、domain の `is_make_only_scan_code`（`keyseq/domain/make_only_keys.py`）で真
- `set_key_color` に新しい種類を足す: 地 `#e4ebe1`・枠 `#7f9a74`・文字 `#2f4429`（§3.4 の案）
- トリガー・停止 / トグル・直接切替キー・割り当て禁止の kind はそのまま（この色にしない）。割り当ての無い枠（`normal`）も白のまま

### `tests_ui/test_make_only_key_color_ui.py`（新規）

手本は `tests_ui/test_prohibited_assign_keys_ui.py`（`_rectangle_fill` で枠の地の色を読む形）。

- jis.json（または `extra_scan_codes: [241]` / `[242]` を持つ行のあるレイアウト）で:
  - `muhenkan` に直接置換 → 地が `#e4ebe1`
  - `henkan` に直接置換 → 地が `#e4ebe1`
  - `muhenkan` に割り当てなし → 白（`set_key_color("normal")[0]`）
  - `muhenkan` をトリガーのキーにする → `set_key_color("trigger")[0]`（青のまま）
  - 押下だけの走査コードを持たない行（例: `kana`・`a`）の直接置換 → `set_key_color("keymap")[0]`（緑のまま）

### 設計メモ / 制約

- 判定は描画の場で `KeySpec` から行う（`_kind_map` の作り方〔:150-200 付近〕は変えない。kind_map はキー名で引くので、走査コードを持つのは `KeySpec` 側）
- 新しい走査コードの表を作らない（domain の `is_make_only_scan_code` を使う）
- 凡例・案内の文言は足さない（§3.4）

## 読むファイル

1. `instructions/history/46_make_only_keys.md` の §3.4・§9
2. `keyseq/presentation/keyboard_window.py:355-445`
3. `keyseq/presentation/keyboard_layouts.py:10-30`（`KeySpec`）
4. `keyseq/domain/make_only_keys.py`（全体）
5. `tests_ui/test_prohibited_assign_keys_ui.py:1-92`（手本）

## 含まない

- 状態機械の変更（task_03d）
- 正本反映（`features.md` §4.6・`codebase_map.md` の色の値は task_04）
- 内蔵と外付けのキーボードの見分け（§9 #1 で受容）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests_ui.test_make_only_key_color_ui tests_ui.test_prohibited_assign_keys_ui` が全 pass
- 既存テストが全 pass（`unittest discover -s tests` / `unittest discover -s tests_ui` / `-m tests.smoke_app`）

## 完了条件

- 上記の確認が pass し、**reviewer が採用**していること
- 本タスクの後に、task_03d と合わせてユーザーの実機目視（暫定 46 §6 #6）。色の最終の値は実機目視で決める
