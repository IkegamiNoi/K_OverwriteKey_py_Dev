# task_02_names_and_input

## 目的

暫定 38（v0.5）の §3 名前の表・§4 入力の名前の決定・§3 / §6 の名前の検査を実装する。送信（task_03）と記録（task_04）は含まない。

## 対象範囲

### domain（新規 `keyseq/domain/numpad_keys.py`）
- 表（§3）: 名前 → `(scan_code, extended)` の 16 件。`num 0`〜`num 9` = 82 / 79 / 80 / 81 / 75 / 76 / 77 / 71 / 72 / 73（非拡張）・`num decimal` 83・`num multiply` 55・`num subtract` 74・`num add` 78（非拡張）・`num divide` 53・`num enter` 28（拡張）
- `numpad_key_spec(name) -> tuple[int, bool] | None`: trim + 小文字で表を引く
- `is_numpad_key_name(name) -> bool`
- `numpad_name_from_event(scan_code, is_keypad) -> str`: `is_keypad` が真で、スキャンコードが表にあれば表の名前・それ以外は `""`（`num lock` 69・126 は `""`）。スキャンコード → 名前の逆引きは表から作る（拡張フラグはイベントに無いので、スキャンコードだけで一意に引ける 16 件である）。`scan_code` が int に変換できなければ `""`
- `is_reserved_numpad_name(name) -> bool`: trim + 小文字 + `_` を半角空白に置き換えた形が `num ` で始まり、表に無く、`num lock` でもないとき真（`num +` / `num plus` / `num del` / `num_1` / `num_plus` / `num_add` 等）。**表の名前そのもの（`num 1`）は偽**
- keyboard に依存しない

### application
- `application/input_router.py` の `_extract_key_name`（:143）と `application/key_state_manager.py` の `_extract_key_name`（:93）の**両方**で、最初に `numpad_name_from_event(getattr(event, "scan_code", None), getattr(event, "is_keypad", False))` を呼び、空でなければそれを返す（`key_state_manager` は既存の `_normalize_key` を通してよい）
- その後の `resolve_scan_code` の結果が**表の名前**（`is_numpad_key_name`）なら採用せず、イベントの `name` / `key` に進む（§4・外部レイアウトの `id` で End が `num 1` になるのを防ぐ）

### infrastructure
- `infrastructure/input_gateway.py` の `validate_key_name`（:255）: 先に `is_numpad_key_name` なら OK（return）・`is_reserved_numpad_name` なら `ValueError`（文言例「テンキーのキー名は num 0〜num 9 / num add / num subtract / num multiply / num divide / num decimal / num enter のいずれかで指定してください。」）・それ以外は従来どおり

### テスト
- `tests/test_numpad_keys.py`（新規）: 表の 16 件・大文字 / 前後空白・`numpad_name_from_event`（表の 16 件・`is_keypad` 偽は `""`・69 / 126 は `""`・不正なスキャンコード）・`is_reserved_numpad_name`（`num +` / `num plus` / `num del` / `num_1` / `NUM_ADD` / `num_plus` は真・表の名前 / `num lock` / `1` / `end` は偽）（§8-1・2・7）
- `tests/test_input_router.py`・`tests/test_key_state_manager.py`: `is_keypad` 真 + 79 で `name="end"` / `name="1"` とも `num 1`・`is_keypad` 偽の `end` は `end`・`is_keypad` 属性の無いイベントは従来どおり・`resolve_scan_code` が `num 1` を返しても `is_keypad` 偽なら `end`・NumLock をまたぐ down `1` / up `end`（どちらも `is_keypad` 真・79）で押下状態が `num 1` の対で消える（§8-2・3・7a）
- トリガー `num 1` / `1` / `end` の判定（§8-4）・重なり判定で `num 1` と `1` が重ならない（§8-5）は、既存の input_router / key_overlap のテストの形に合わせて最小限追加
- `validate_key_name`（`keyboard` を patch してよい）: 表の名前は keyboard を呼ばずに OK・予約名は `ValueError`・`num lock` は従来どおり（§8-7）

## 読むファイル

- `instructions/history/38_numpad_key_distinction.md`（§2〜§4・§6 の名前の検査・§8）
- `keyseq/application/input_router.py`（:1-160）・`keyseq/application/key_state_manager.py`（全体）・`keyseq/domain/key_identifiers.py`・`keyseq/domain/config.py`（:80-90）・`keyseq/infrastructure/input_gateway.py`（:225-262）
- `tests/test_input_router.py`・`tests/test_key_state_manager.py`・`tests/test_key_overlap.py`・`tests/test_input_gateway_send.py`（validate の既存テストがあれば）

## 含まない

- 送信・`key_identity`（task_03）・記録（task_04）・正本の改訂（task_06）。既存の拡張キー表・送信経路は変えない

## 確認

- 上記テスト + 既存テスト（実行は verifier）・reviewer（5 観点）
