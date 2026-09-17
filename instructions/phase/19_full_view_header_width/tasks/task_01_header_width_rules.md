# task_01_header_width_rules

## 目的

暫定仕様 17（v0.3）の**純関数部分**を追加する。①`resolve_layout` にヘッダから算出したウィンドウ幅を入力として足す（§3-2: ウィンドウ最小幅 = max・画面超過の縮小目標 = max(画面幅, ヘッダ幅)）
②ドラッグ後のウィンドウ最小幅（§3-2: 縮小規則を通さない）③文言が切り替わるボタンの固定幅（§3-3: `ceil(max(measure)/measure("0"))`）。
**presentation 直下の tkinter 非依存モジュールのみ。UI へは未結線**（呼び出し側の変更は task_02・task_03）。スキーマ不変。

## 対象範囲（presentation の純関数 2 ファイル + tests 2 ファイル）

### `keyseq/presentation/pane_width_rules.py`

1. **`resolve_layout` にキーワード引数 `header_window_width: int = 0` を追加**（既存の位置引数 6 つと順序・既定の結果は不変）:
   - `required`（メイン）は従来どおり算出。
   - 縮小目標 `target = max(screen_width, header_window_width)`。**`required > target` のときだけ**、従来と同じ順（出力シーケンス → キーマップ管理、最小幅まで）で `required` を `target` 以下へ縮める。
   - `window_min_width = max(required, header_window_width)` / `window_width = max(current_window_width, window_min_width)`。
   - `header_window_width=0` のとき結果は現行と完全に同じ（`target = screen_width`）。
   - docstring の参照を「暫定仕様16 §3-7 / 暫定仕様17 §3-2」にする。
2. **新規 `window_min_width_after_drag(displayed: PaneWidths, mins: MinWidths, sash_total: int, window_extra: int, header_window_width: int = 0) -> int`**（暫定仕様17 §3-2）:
   `max(displayed.keymap + displayed.sequence + mins.trigger + sash_total + window_extra, header_window_width)`。画面幅は受け取らない（縮小規則を通さない）。
3. 既存の他の関数・定数・データクラスは変えない。

### `keyseq/presentation/button_width_rules.py`（新規）

- **`fixed_button_width_chars(text_widths: Sequence[int], zero_width: int) -> int`**（暫定仕様17 §3-3）:
  `ceil(max(text_widths) / zero_width)`。`text_widths` が空、または `zero_width <= 0` なら `ValueError`。整数演算で求める（浮動小数の誤差を持ち込まない）。
- モジュール docstring に「文言が切り替わるボタンを最大文言幅で固定する幅（ttk の文字数単位）」と暫定仕様 17 §3-3 を書く。tkinter を import しない。

### `tests/test_pane_width_rules.py`（追記）

- 既存 `test_resolve_layout_all_required_boundaries` は**変えない**（`header_window_width` 省略時の不変を担保）。
- **新規 `test_resolve_layout_with_header_width`**（`mins = MinWidths(100, 80, 120)`・`sash_total=24`・`window_extra=16`。メイン必要幅は `PaneWidths(200, 300)` で 620）:

  | ケース | desired | current | screen | header | 期待 `LayoutPlan` |
  |---|---|---|---|---|---|
  | main_wins | (200, 300) | 700 | 1000 | 500 | (200, 300, 620, 700) |
  | header_wins | (200, 300) | 700 | 1000 | 800 | (200, 300, 800, 800) |
  | equal | (200, 300) | 500 | 1000 | 620 | (200, 300, 620, 620) |
  | header_only_over_screen | (200, 300) | 700 | 1000 | 1100 | (200, 300, 1100, 1100) |
  | main_only_over_screen | (200, 300) | 500 | 600 | 500 | (200, 280, 600, 600) |
  | both_over_screen | (500, 580) | 900 | 1000 | 1100 | (500, 480, 1100, 1100) |
  | zero_header_same_as_omitted | (200, 300) | 500 | 619 | 0 | 省略時の結果と等しい |

  いずれも `desired` を変更しないこと（既存テストと同じ確認）。
- **新規 `test_window_min_width_after_drag`**: displayed (300, 400)・同じ mins/sash/extra → header 省略 820 / header 700 → 820 / header 900 → 900 /
  displayed の和が画面幅より大きい値（例 (900, 900) → 1920）でも縮めずそのまま返す。

### `tests/test_button_width_rules.py`（新規）

- `[85, 130]`, 7 → 19 / `[140]`, 7 → 20（割り切れる）/ `[141]`, 7 → 21 / 順序に依存しない（`[130, 85]` → 19）/
  `[]` → `ValueError` / `zero_width` 0・−1 → `ValueError`。

### 設計メモ / 制約

- `resolve_layout` の既存呼び出し（`controllers/pane_layout/pane_layout_controller.py` の `_plan`）は本タスクでは変えない（キーワード既定値で不変）。
- `button_width_rules.py` を `pane_width_rules.py` に入れない（ボタン幅は枠の幅配分ではなく、task_02 で HookController / SingleKeyCaptureController が使う）。
- 関数 30 行以内。`MinWidths` にヘッダ幅を足さない（暫定仕様17 §3-2）。

## 読むファイル

- 編集対象（全体）: `keyseq/presentation/pane_width_rules.py` / `tests/test_pane_width_rules.py`
- 仕様: `instructions/history/17_full_view_header_width.md` の §3-2・§3-3・§5-2〜§5-4（`rg -n "§3-2|§3-3|^[234]\. " ` で位置特定）

## 含まない

- ヘッダの測定・保持・`_plan` / `_update_window_min_size` への結線（**task_03**）
- 文言定数・ボタンへの幅の適用・`_apply_font_delta` の順序・ドロップダウン幅（**task_02**）
- 起動時の保存値更新（**task_04**）/ 正本反映（**task_06**）

## 確認

python は `../../../.venv/Scripts/python.exe`。実測は `verifier`。

1. `-m compileall -q keyseq tests` が clean。
2. `-m unittest tests.test_pane_width_rules tests.test_button_width_rules -v` が全 pass（既存 `test_resolve_layout_all_required_boundaries` を含む）。
3. `-m unittest discover -s tests` が 445 + 追加分 OK（skip 7）。`tests_ui` は変更なしのため `-m unittest tests_ui.test_full_view_panes tests_ui.test_pane_drag_and_window_min tests_ui.test_pane_widths_persistence tests_ui.test_pane_window_width_persistence` が pass（結線していないので不変）。
4. `rg -n "import tkinter|from tkinter" keyseq/presentation/pane_width_rules.py keyseq/presentation/button_width_rules.py` が 0 件。
5. `git diff --stat` が上記 4 ファイル（+ 本タスク文書）のみ。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。
- 実機目視は不要（UI 未結線。task_05 でまとめて実施）。

## 完了記録（2026-09-17）

- 実装は `codex-implementer`（4 ファイル）。
- `verifier`: compileall clean / 対象 2 モジュール 33 OK / `tests` 450 OK（skip 7・+5）/ `tests_ui` pane 系 4 モジュール 59 OK（不変）/ tkinter import 0 件 / 差分 4 ファイルのみ。
- `reviewer` = 完了可（`header_window_width` 省略時の不変・縮小目標 max(画面幅, ヘッダ幅)・表の期待値を式で照合・整数演算を確認。指摘なし）。
