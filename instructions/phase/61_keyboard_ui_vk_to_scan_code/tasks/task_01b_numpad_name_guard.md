# task_01b_numpad_name_guard

## 目的

phase 61 の完了判定前の Codex 敵対的レビュー（中・ユーザー採用 2026-10-17）への対応。`KeyboardWindow._normalize_tk_key` で、走査コードからレイアウトを引いた結果が**テンキーのキー名**なら採らず keysym へ落とす（フックの実行時 `application/input_router.py:190-193` の `is_numpad_key_name` のガードと同じ）。
外部レイアウトにテンキーの id（例 `num 0`）と `scan_code` 82 を書いた場合に、拡張キーの Insert（VK 45 → 走査コード 82）が `num 0` に化けるのを防ぐ（テンキーは先頭の `numpad_name_from_tk_event` が拡張ビットで判定する）。
**presentation 限定（`keyboard_window.py` 1 か所 + テスト）。他は不変。**

## 対象範囲

### `keyseq/presentation/keyboard_window.py`

* `_normalize_tk_key`: `resolve_layout_key_id_from_scan_code` の結果を `normalize_key_name` した名前が `is_numpad_key_name`（`keyseq.domain.numpad_keys`）に当たるときは採らず、keysym の小文字へ進む

### `tests_ui/test_keyboard_window_scan_code.py`（追加）

* `id = "num 0"`・`scan_code = 82` のキーを持つレイアウト（`KeyboardLayout` / `KeySpec` を直接作るか `keyboard_layout_from_dict`）で、拡張の Insert（keysym `Insert`・keycode 45・state に拡張ビット 0x40000・変換後 82）→ `insert`（`num 0` にならない）
* 同じレイアウトでテンキーの 0（keycode 96）→ `num 0`（先頭のテンキー判定で決まる・既存どおり）

## 読むファイル

1. `keyseq/presentation/keyboard_window.py`（import と `_normalize_tk_key`）
2. `keyseq/application/input_router.py:184-198`（手本のガード）/ `keyseq/domain/numpad_keys.py:30-40`（`is_numpad_key_name`）
3. `tests_ui/test_keyboard_window_scan_code.py`（追加先）・`keyseq/presentation/keyboard_layouts.py:11-35`（`KeySpec` / `KeyboardLayout`）

## 含まない

* 文書（task_02 で反映）/ 他の取得の入口・フックの実行時

## 確認

* compileall clean・`tests_ui.test_keyboard_window_scan_code` と `tests.test_keyboard_layout_files` が全 pass・既存の tests / tests_ui / smoke が全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。実機目視は不要（同梱のレイアウトでは起きない経路・自動テストで固定）。
