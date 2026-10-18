# task_03b_extra_scan_codes

## 目的

レイアウトの JSON の行に、受け取り専用の任意キー `extra_scan_codes`（整数の配列）を書けるようにする（暫定 45 §3.1・v0.4）。
受け取る側（フックの実行時・画面の枠の編集の窓・キーボードUI の取得・デバッグ出力の判定）は、`scan_code` か `extra_scan_codes` のどちらかに一致する最初の行の `id` を名前にする。
送る側（§4）は変えない。

背景: 2026-10-18 の実測で、この PC の無変換は 241、変換は 242 でフックに届くと分かった（IME の割り当てで走査コードが変わる）。

**presentation 限定**（`keyboard_layouts.py`・`layout_controller.py`）＋ 見本の `config/user/keylayout/jis.json`。
domain・application・infrastructure は不変。設定・キーマップの JSON は不変。

## 対象範囲（presentation 限定 + 見本 JSON）

### `keyseq/presentation/keyboard_layouts.py`

- `KeySpec` に `extra_scan_codes: tuple[int, ...] = ()` を足す（最後のフィールド。組み込みの US TKL は変えない）
- `validate_layout_json` の行ごとの検証に `extra_scan_codes` を足す
  - 無い・`None` → `()`
  - `list` でなければ `ValueError(f"{key_prefix}.extra_scan_codes は整数の配列である必要があります。")`
  - 要素は `_coerce_int(value, f"{key_prefix}.extra_scan_codes[{j}]")` で整数にする（範囲は問わない）
  - 正規化後の dict に `"extra_scan_codes": tuple(...)` を入れる
- `keyboard_layout_from_dict` で `KeySpec(extra_scan_codes=key_data.get("extra_scan_codes", ()))` を渡す
- `resolve_layout_key_id_from_scan_code`
  - 行の順に見て、行ごとに `scan_code`（`None` でなければ）→ `extra_scan_codes` の順に照合する
  - 一致した最初の行の `id` を返す
- `resolve_layout_scan_code_from_key_name`（送信用）は**変えない**（`extra_scan_codes` を使わない）

### `keyseq/presentation/controllers/layout_controller.py`

- `should_debug_special_key_event`: 行の `scan_code` に加え、`extra_scan_codes` のどれかと一致しても真にする
  - `getattr(key_spec, "extra_scan_codes", ())` で読む
  - それ以外の条件（設定・`down`・整数化）は今と同じ

### `config/user/keylayout/jis.json`

- `muhenkan` の行に `"extra_scan_codes": [241]`、`henkan` の行に `"extra_scan_codes": [242]` を足す
  - `scan_code` 123 / 121 はそのまま
  - 行の書き方（1 行 1 キー・キーの順）は今の形に合わせる

### テスト

- `tests/test_keyboard_layout_files.py`（または新規 `tests/test_layout_extra_scan_codes.py`）に追加する
  - 読込:
    - 無い → `()`
    - `null` → `()`
    - `[241, "242"]` → `(241, 242)`
    - `"241"`（配列でない）→ `ValueError`
    - `["x"]` → `ValueError`
    - 負の値 `[-26]` は通る
  - 受け取り:
    - jis.json で 241 → `muhenkan`、242 → `henkan`、123 / 121 も従来どおり
    - 自作レイアウトで、`scan_code` なし・`extra_scan_codes` だけの行が当たる
    - 2 行が同じ走査コードを持つ（`scan_code` と別の行の `extra_scan_codes`）とき、行の順で最初の行
  - 送信: jis.json で `resolve_layout_scan_code_from_key_name(layout, "muhenkan") == 123`（`extra` を使わない）
    - `scan_code` なし・`extra_scan_codes` だけの行の `id` → `None`
  - 見本の検査（既存の `test_layouts_have_unique_non_overlapping_keys` 等）が jis.json の変更後も通る
- `tests/test_layout_controller_scan_code.py` に追加する
  - jis.json で `resolve_key_name_from_scan_code(241)` → `muhenkan`
  - `should_debug_special_key_event` が走査コード 242 の `down` で真

### 設計メモ / 制約

- 修飾キー・Caps Lock・Windows・AltGr の行に書かない規定（§3.1）は規定のみ。コードで防がない
- 同じ走査コードを複数の行が持っても、読込で拒否しない（最初の行を採る）
- テンキーの名前を採らないガードは呼び出し側（`input_router` / `key_state_manager` / `keyboard_window`）にあるので変更不要

## 読むファイル

1. `instructions/history/45_special_keys_from_layout_only.md` §3.1
2. `keyseq/presentation/keyboard_layouts.py`（編集対象。:1-30・:150-260・:300-365）
3. `keyseq/presentation/controllers/layout_controller.py:385-406`
4. `config/user/keylayout/jis.json`
5. `tests/test_keyboard_layout_files.py`・`tests/test_layout_controller_scan_code.py`（手本）

## 含まない

- 送信・検査・同じキーの判定の変更（§4 は不変）
- 正本反映（`features.md` §4.6 の `extra_scan_codes` の記載・`data_schema.md` の追従は task_04）
- de.json の変更

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_keyboard_layout_files tests.test_layout_controller_scan_code`（新規ファイルを作ったならそれも）が全 pass
- 既存テストが全 pass: `unittest discover -s tests` / `unittest discover -s tests_ui` / `-m tests.smoke_app`
- **実機目視（ユーザー・JIS キーボード・jis.json を選ぶ）**
  1. キーボードUI で「無変換」「変換」の枠に `a` 等を割り当て、フックの開始後に押して反応する
  2. レイアウトの一覧で jis.json を選び直す（外部レイアウトの読込エラーが出ない）

## 完了条件

- 上記の確認（自動テスト）が pass し、**reviewer が採用**していること。
- 実機目視は本タスクで行う（ユーザー）。
