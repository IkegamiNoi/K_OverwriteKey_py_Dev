# task_01_counter_save_format

## 目的

カウンターの保存形式を加える。①構成セットの最上位キー `counter_starts`（カウンター名 → 開始値）の正規化・読込・保存・単一 JSON の Import / Export（暫定 58 §3.3）
②カウンターの行の増やす量 `amount` の判定関数（暫定 58 §3.1）。
**domain（`sequence_control.py`・`config.py`）と application の config_service（`split_loading.py`・`split_payloads.py`）限定**。実行・表示・UI は変えない（`amount` を読む実行は task_02）。

## 対象範囲（domain + config_service 限定）

### `keyseq/domain/sequence_control.py`

- 定数 `DEFAULT_COUNTER_AMOUNT: int = 1`。
- `counter_amount(action: Mapping[str, Any]) -> int | None`: `counter_inc` の行の増やす量。
  - キー `amount` が無ければ `DEFAULT_COUNTER_AMOUNT`。
  - あれば `int(action["amount"])`（`count` / `ms` と同じ緩さ。`"3"` → 3・`2.5` → 2・`True` → 1・`0` → 0・負も可）。`TypeError` / `ValueError` / `OverflowError` なら `None`（= 不正）。
  - op は見ない（呼ぶ側が `counter_inc` の行だけに使う）。
- `normalize_counter_starts(value: Any) -> dict[str, int]`: §3.3 の順序で正規化した新しい dict を返す（入力を変えない）。
  1. `value` が dict でなければ `{}`。
  2. 要素を JSON の並び順に見て、キーが str で trim 後に空でなく、値が **bool を除く int** のものだけを取る（0 を含む）。trim 後の名前で**後に現れた要素が勝つ**。
  3. 最後に値 0 の要素を除く。
  - 例: `{"n": 7, " n ": 0}` → `{}` / `{"a": 3, "b": True, "": 1, "c": "2"}` → `{"a": 3}` / `{"x": -2}` → `{"x": -2}`。
  - 大文字小文字は区別する（小文字化しない）。

### `keyseq/domain/config.py`

- `build_base_config` の dict に `"counter_starts": {}` を足す（`select_before_run` の隣）。
- `_normalize_general_settings` で `config["counter_starts"] = normalize_counter_starts(config.get("counter_starts"))`（`select_before_run` の正規化の隣）。
  これで単一 JSON の読込（Import）・`normalize_runtime_data`・Export（`export_runtime_data` は `ensure_config_compatibility` を通す）・サンプルの構成に同じ正規化がかかる。

### `keyseq/application/config_service/split_loading.py`

- `_build_runtime_data_from_keymap_set`: 構成セットに `counter_starts` があれば `runtime["counter_starts"] = normalize_counter_starts(keymap_set.get("counter_starts"))`。無ければ `new_base_data()` の `{}` のまま。

### `keyseq/application/config_service/split_payloads.py`

- `build_keymap_set_payload` の返す dict に `"counter_starts": normalize_counter_starts(runtime.get("counter_starts"))` を足す（`select_before_run` の隣・**常に出力**・空なら `{}`）。

### `keyseq/application/config_service/__init__.py`

- `apply_global_defaults` に `runtime.setdefault("counter_starts", {})`（`select_before_run` と同じ）。

### テスト（追加・修正。**テストの実行はしない**）

- `tests/test_sequence_control.py`: `counter_amount`（キー無し 1・`"3"`・`2.5`・`True`・0・負・`"abc"`・`None`・`[]`）/ `normalize_counter_starts`（上の例 3 つ・非 dict・0 の除去・後勝ち・大文字小文字の区別・入力を変えない）。
- `tests/test_domain_config.py`: 単一 JSON の正規化で `counter_starts` が正規化される・キーが無ければ `{}`・`build_base_config` に `{}`。
- `tests/test_config_service.py`: 構成セットの保存で `counter_starts` が常に出る（空 `{}` / 値あり）・分離読込で読める・キーの無い構成セットは `{}`・保存 → 読込で保たれる・Export → Import で保たれる。
  既存の「構成セットの payload のキー一覧」を完全一致で見ているテストがあれば `counter_starts` を足す。

## 設計メモ / 制約

- 手本 = `select_before_run`（`domain/config.py:43,290-293` / `split_loading.py:108-121` / `split_payloads.py:465-469` / `config_service/__init__.py:594`）。同じ置き方にする。
- 正規化は `normalize_counter_starts` の 1 関数だけを使う（分離読込・Import・保存で別の正規化を書かない・暫定 58 §3.3）。
- `domain/config.py` は `sequence_control` を import している（循環なし・既存）。
- 新しい依存・新しいファイルを足さない。既存の他のキーの扱いを変えない。
- 編集は apply_patch で行い、Python のスクリプトでファイルを書き換えない。

## 読むファイル

- `instructions/history/58_counter_expansion.md` §3.1・§3.3（主入力）
- `keyseq/domain/sequence_control.py`（全体・編集対象）
- `keyseq/domain/config.py:30-52,274-300`（`build_base_config`・`_normalize_general_settings`）
- `keyseq/application/config_service/split_loading.py:98-125`
- `keyseq/application/config_service/split_payloads.py:411-485`
- `keyseq/application/config_service/__init__.py:586-600`
- 手本のテスト: `tests/test_config_service.py` と `tests/test_domain_config.py` の `select_before_run` を扱うテスト（`grep -n select_before_run`）

## 含まない

- `amount` を使う実行・保留・戻す（task_02）
- `AppState` の開始値・実効値（task_02）
- `counter_text` の種別（task_03）
- 一覧の表示（task_04）
- 編集ダイアログ・開始値の確定・構成セットを置き換える経路での `AppState` への同期・文言（task_05）
- 正本 `spec_detail/` の更新（task_07）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_sequence_control tests.test_domain_config tests.test_config_service tests.test_config_service_contracts` 全 pass（追加分を含む）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（既存の退行なし）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視なし（保存形式のみ・task_06 でまとめて実施）。
