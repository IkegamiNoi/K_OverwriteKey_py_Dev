# task_01_pane_width_rules

## 目的

フル表示メイン領域の幅に関する**計算規則を tkinter 非依存の純関数**として実装し、`tests/` で境界値を固定する。
根拠は暫定仕様 16（v0.3）の §3-2（可動範囲）/ §3-4（最小幅）/ §3-5（希望幅の更新）/ §3-6（保存値の検証・既定幅）/
§3-7（収まらない場合の最終値計算）。**UI へは結線しない**（task_02〜04 が使う）。

**presentation 直下の新規モジュール 1 つ + 新規テスト 1 つのみ。既存ファイル不変・tkinter を import しない・スキーマ不変。**

## 対象範囲（新規 2 ファイル限定）

### 1. `keyseq/presentation/pane_width_rules.py`（新規）

前例: `presentation/reference_cleanup_text.py`（presentation 直下の純関数モジュール）。
**import は標準ライブラリのみ**（`dataclasses` / `typing`）。

**定数**

- `PANE_WIDTHS_KEY = "full_view_pane_widths"`（config.json のキー名・§3-6）
- `MIN_LIST_CHARS = 10`（一覧の最小文字数・§2-5）/ `DEFAULT_LIST_CHARS = 26`（既定幅の算出に使う現状値・§3-6）

**データ型**（`@dataclass(frozen=True)`）

- `PaneWidths(keymap: int, sequence: int)` — 両端の枠の幅（希望幅 / 表示幅のどちらにも使う）
- `MinWidths(keymap: int, trigger: int, sequence: int)` — 3 枠の最小幅
- `LayoutPlan(keymap: int, sequence: int, window_min_width: int, window_width: int)` — §3-7 の計算結果

**関数**

1. `parse_saved_pane_widths(raw: object) -> PaneWidths | None`（§3-6 の検証）
   - `raw` が dict で、`"keymap"` / `"sequence"` の両方があり、**どちらも `bool` ではない `int` で 1 以上**なら `PaneWidths`。
   - それ以外（dict でない / 欠け / `bool` / `float` / 文字列 / 0 以下）は `None`。**例外を出さない**。
   - 最小幅によるクランプはしない（希望幅は保存値のまま保持する・§3-6）。
2. `list_row_width(char_width: int, chars: int, list_chrome: int, scrollbar_width: int) -> int`
   - `char_width * chars + list_chrome + scrollbar_width`（一覧 1 行分の幅・§3-4）。
3. `stacked_min_width(list_row: int, other_widths: Sequence[int], frame_chrome: int, title_width: int) -> int`（§3-4・縦並び）
   - `max(max(list_row, *other_widths) + frame_chrome, title_width)`。`other_widths` は空でもよい。
   - `title_width` は呼び出し側が「見出しの要求幅 + 左右の枠線・余白」を渡す。
4. `side_by_side_min_width(list_row: int, buttons_width: int, gap: int, frame_chrome: int, title_width: int) -> int`（§3-4・横並び）
   - `max(list_row + buttons_width + gap + frame_chrome, title_width)`。
5. `default_pane_widths(main_width: int, keymap_req: int, trigger_req: int, sash_total: int, mins: MinWidths) -> PaneWidths`（§3-6）
   - `keymap = max(keymap_req, mins.keymap)`
   - `sequence = max(main_width - keymap_req - trigger_req - sash_total, mins.sequence)`
   - `sash_total` は境界線 2 本分の占有幅。
6. `drag_limits(total_width: int, own_min: int, other_side_width: int, trigger_min: int, sash_total: int) -> tuple[int, int]`（§3-2）
   - ドラッグ中の枠の幅の範囲 `(lo, hi)`。`lo = own_min`、`hi = max(lo, total_width - other_side_width - trigger_min - sash_total)`。
   - `total_width` = PanedWindow の幅。サッシュ 0（キーマップ管理）/ サッシュ 1（出力シーケンス）で共通に使う。
7. `clamp(value: int, lo: int, hi: int) -> int` — `hi < lo` の場合は `lo` を返す。
8. `update_desired_after_drag(desired: PaneWidths, side: str, width_before: int, width_after: int) -> PaneWidths`（§3-5）
   - `side` は `"keymap"` / `"sequence"`（それ以外は `ValueError`）。
   - **`width_before == width_after` なら `desired` をそのまま返す**（v0.3・無効ドラッグで希望幅を変えない）。
   - 変わっていれば、`side` 側だけ `width_after` にした新しい `PaneWidths` を返す（もう一方は変えない）。
   - 保存の要否は呼び出し側が「戻り値 != 引数の `desired`」で判定する（関数は増やさない）。
9. `resolve_layout(desired: PaneWidths, mins: MinWidths, sash_total: int, window_extra: int, current_window_width: int, screen_width: int) -> LayoutPlan`（§3-7）
   - `window_extra` = ウィンドウ幅のうちメイン領域の 3 枠 + 境界線以外の部分（外側の余白等）。
   - 手順:
     1. `keymap = max(desired.keymap, mins.keymap)` / `sequence = max(desired.sequence, mins.sequence)`
     2. `required = keymap + sequence + mins.trigger + sash_total + window_extra`
     3. `required > screen_width` なら、超過分を**出力シーケンス → キーマップ管理の順に最小幅まで**差し引いて `required` を再計算する。
        両端とも最小幅になっても超える場合はそこで止める。
     4. `window_width = max(current_window_width, required)`（**縮めない**）
     5. `window_min_width = required`
   - **途中の値を返さない**（最終値の `LayoutPlan` 1 つだけ・v0.3）。

各関数に 1〜2 行の docstring（暫定仕様の § を付す）。**関数はおおむね 30 行以内**。

### 2. `tests/test_pane_width_rules.py`（新規・`unittest`）

前例: `tests/test_reference_cleanup_text.py`。最低限以下を固定する:

- `parse_saved_pane_widths`: 正常 / 非 dict（`None`・list・str）/ 片方欠け / `True`・`False` / `1.0` / `"100"` / `0` / 負数 / 余分なキーがあっても正常値なら採用。
- `list_row_width` / `stacked_min_width`（`other_widths` 空・一覧が最大・他の子が最大〔suppress チェック相当〕・見出しが最大）/
  `side_by_side_min_width`（合計が最大・見出しが最大）。
  **「他の子が一覧行より広いとき、最小幅がその子の幅 + frame_chrome 未満にならない」**を明示的に固定（v0.3 の穴の回帰）。
- `default_pane_widths`: 通常 / `keymap_req < mins.keymap` / 残り幅が `mins.sequence` 未満（負になるケースを含む）。
- `drag_limits` + `clamp`: 通常 / 上限が下限を下回る（`hi == lo`）/ `clamp` の `hi < lo`。
- `update_desired_after_drag`: 変化なし（同一オブジェクト相当の値）/ keymap 側だけ変わる / sequence 側だけ変わる / 不正な `side` で `ValueError`。
- `resolve_layout`: ①そのまま収まる（`window_width == current`）②ウィンドウを広げる ③**ちょうど画面幅** ④**画面幅を 1px 超過 → 出力シーケンスが 1px 縮む**
  ⑤出力シーケンスが最小幅まで縮んでも超過 → キーマップ管理が縮む ⑥**両端とも最小幅でも超過 → 最小幅で止まり `required > screen_width`**
  ⑦希望幅が最小幅未満 → 表示は最小幅 ⑧現在のウィンドウ幅が画面幅より広くても `window_width` は縮まない。

## 設計メモ / 制約

- **tkinter / keyseq の他モジュールを import しない**（`tests/` で GUI なしに走らせるため）。
- 測定値（`winfo_reqwidth` 等）の取得・PanedWindow の操作は**本タスクでは書かない**。
- 名前・シグネチャは上記のとおり実装する。実装都合で変えたくなった場合は変えずに報告する（task_02〜04 の前提になる）。

## 含まない

- `full_view.py` / `keymap_box.py` / `trigger_box.py` の変更・PanedWindow 化（**task_02**）
- 幅コントローラ・ドラッグのバインド・`wm minsize`・フォント変更 / 省略表示との結線（**task_03**）
- `write_startup` による保存・起動時の復元（**task_04**）
- `codebase_map.md` 等の正本 / 文書更新（**task_06**）

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `../../../.venv/Scripts/python.exe`）。実測は `verifier`。

1. `../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui` が clean。
2. `../../../.venv/Scripts/python.exe -m unittest tests.test_pane_width_rules -v` が全 pass（上記ケースがすべて存在）。
3. `../../../.venv/Scripts/python.exe -m unittest discover -s tests` が **pass 417 + 追加件数**（skip 7 のまま）。
4. `git grep -n "import tkinter\|from tkinter" keyseq/presentation/pane_width_rules.py` が 0 件。
5. `git diff --stat` が新規 2 ファイルのみ（既存ファイルの差分なし）。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。
- 実機目視は**なし**（UI 未結線。task_05 でまとめて実施）。
