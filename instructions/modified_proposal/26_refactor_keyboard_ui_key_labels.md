# 提案書 26: phase 69（キーボードUIのキー名の表示と最小サイズ）後のリファクタ

> 状態: **保留**（2026-10-26・ユーザー判断）。

## 判定の要約

範囲 `git diff 3b09ad7..HEAD -- keyseq/`（5 ファイル・+299 / -38）。メトリクスは verifier の実測、M2 はメインで関数の行数を裏取り。

- **M2 該当**: `presentation/keyboard_window.py:433` `KeyboardWindow.redraw` が 77 → 100 行（phase 69 で文字合わせの計測・配置を足し 80 行を超えた）
- 境界・参考（判定には使わない）: M1 = `keyboard_window.py` 658 行・+99（+100 に 1 行足りない）/ 同型の「外接 → 最小、キーが無ければ `(KEYBOARD_WINDOW_MIN_WIDTH, 210)`」が `__init__`（:95-99）と `update_layout`（:152-156）の 2 か所（M3 は 3 か所目から・M6 は既存定数との同値ではない）
- 非該当: M4（列挙の増加なし）/ M5（0 件）

## 項目 0: 安全網の確認

- 対象領域のテスト: `tests/test_keyboard_key_text.py`・`test_keyboard_window_size.py` / `tests_ui/test_keyboard_key_text.py`・`test_app_ui_flows.py`（`test_keyboard_window_*`）・`test_keyboard_window_left_right.py`・`test_make_only_key_color_ui.py`・`test_prohibited_assign_keys_ui.py`
- 完了条件: 着手前に `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` が全 pass（基準線）

## 項目 1: `redraw` からキーの文字の描画を分ける（M2）

- 対象: `keyseq/presentation/keyboard_window.py:433` `redraw`（キーごとのループ内の「`measure` の内部関数・`fit_key_text`・塊の高さ・主 / 下の `create_text`」）
- 変え方: ループ内の文字の部分をメソッド `_draw_key_text(canvas, x1, y1, x2, y2, unit, display, sub_display, text_fill, font_family)` へ、`measure` をメソッド `_measure_key_text(text_line, px, bold, font_family)` へ移す（フォントの使い回しの辞書はそのまま）。`redraw` は枠を描いて `_draw_key_text` を呼ぶだけにする
- 完了条件: `redraw` が 80 行以下・描画の結果（item の文字・フォント・座標）が不変（既存の tests_ui がそのまま pass）
- リスクと戻し方: 局所的な抽出のみ。テストが落ちたらコミットを戻す
- 依存: なし

## 項目 2（任意）: キーが無いレイアウトの大きさを 1 つの定数に（境界の M3 / 直値の重複）

- 対象: `keyboard_window.py:95-99`・`:152-156`
- 変え方: `keyboard_window_size.py` に `KEYBOARD_WINDOW_EMPTY_SIZE = (KEYBOARD_WINDOW_MIN_WIDTH, 210)` と `layout_minimum(extent) -> tuple[int, int]`（extent が None なら EMPTY_SIZE）を置き、2 か所をその呼び出しにする
- 完了条件: 直値 `210` が `keyboard_window.py` から消える・既存テスト pass
- リスクと戻し方: 低。同上
- 依存: なし（項目 1 と独立）

## 備考

- 実施タイミングはユーザー判断: (a) phase 69 の追加タスク `task_07_refactor` / (b) 次フェーズ前の独立ミニフェーズ / (c) 保留
