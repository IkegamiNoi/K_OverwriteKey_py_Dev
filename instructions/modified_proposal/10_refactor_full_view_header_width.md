# 提案書 10: phase 19（フル表示ヘッダの幅をウィンドウ最小幅に含める）後のリファクタ

> `/refactor_check`（`.claude/commands/refactor_check.md`）の判定 = **推奨**。
> **ユーザー承認前に実装しない**。判定の記録は
> [decisions_archive/19](../../.claude_data/state/decisions_archive/19_full_view_header_width.md)。
> 状態: **承認済・実施完了**（2026-09-17・ユーザー選択 (a) = phase 19 の **task_07** として実施。安全網は特性テストを足さず変異検査で確認。**挙動不変**）。

## 判定の要約

PHASE_BASE = `9b95192`（phase 18 完了コミット）。対象 = `keyseq/` の変更 **13 ファイル・+159 / -25**（`verifier` 実測）。

- **M3 該当（→ 項目 1）**: `controllers/pane_layout/pane_layout_controller.py:78-79` / `:123-124` / `:134-135` に
  「`self.min_widths = self.measure_min_widths()` + `self.header_window_width = measure_header_window_width(self.app)`」の **2 行の組が 3 箇所**。
  phase 19 で 3 箇所すべてに同じ 1 行を足した結果で、**片方を直せば他も直す必要がある**（測定対象が増えたら 3 箇所とも直す）。task_03 のタスク定義でも `_measure()` への集約を許容していた。
- **M3 の境界（→ 項目 2・任意）**: `pane_width_rules.py:15` と `:22` の保存幅の有効判定（`bool` を含む非 int / 1 未満）が同一文で 2 箇所。
  3 個目ではないため機械的基準には届かないが、task_05 の `deep-reviewer` 指摘 4 と同じで、**有効条件を変えるときに片方だけ直す危険**がある。項目 1 と同時なら安い。
- **M1 / M2 / M4 / M5 / M6 非該当**: M1 = 最大 `app.py` 568 行（600 未満）/ M2 = 80 行超の関数なし / M4 = `fixed_width=True` の呼び出しは 1 箇所で全モード列挙の形ではない /
  M5 = 申し送りコメント 0 件 / M6 = `KEYBOARD_LAYOUT_COMBO_WIDTH = 12` は `SASH_WIDTH = 12` と値が一致するが意味が別（文字数 vs px）で、import 関係もない。
- **提案書に入れない既知・保留**（`current.md` 別タスク化候補へ）: `KEYBOARD_LAYOUT_COMBO_WIDTH` の置き場所（文言モジュールに同居）/
  `tests_ui` の 2 モジュールで保存予約の遅延を延ばしていない（テストは本コマンドの対象外）/
  `hook_controller.py` の `register_hook_buttons` と `apply_fixed_button_widths` の 2 行の同型（2 箇所・同一ファイル内・軽微）。

## 項目 0（先行）: 安全網の確認

- **対象領域のカバー**: `tests_ui/test_full_view_header_width.py`（初回・フォント変更・省略表示中のフォント変更 → フル表示復帰の各経路でヘッダ幅と最小幅を検査）/
  `tests_ui/test_pane_drag_and_window_min.py` / `test_full_view_panes.py` / `test_pane_window_width_persistence.py`（起動時の保存値更新・切り詰め）/
  `tests/test_pane_width_rules.py`（`parse_saved_window_width` の不正値表・`startup_window_width_to_save` の 12 ケース）。
- **確認手順**: 変更前に下記「完了条件」のコマンドを実行し全 pass を記録する。上記テストが 3 経路と不正値表を覆っているため、**特性テストの追加は不要の見込み**
  （足りなければ項目 1 の前に追加する）。

## 項目 1: 測定の 2 行を private メソッドに集約する（M3）

- **対象**: `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py:78-79,123-124,134-135`
- **どう変えるか**:

  ```python
  # 変更前（3 箇所）
  self.min_widths = self.measure_min_widths()
  self.header_window_width = measure_header_window_width(self.app)

  # 変更後
  def _measure(self) -> None:
      """最小幅とヘッダ幅を同じ契機で測る（暫定仕様16 §3-4 / 暫定仕様17 §3-1）。"""
      self.min_widths = self.measure_min_widths()
      self.header_window_width = measure_header_window_width(self.app)
  # 3 箇所は self._measure() を呼ぶ
  ```

  `measure_min_widths()`（公開メソッド・テストから patch される可能性）は残す。
- **完了条件**: `../../../.venv/Scripts/python.exe -m compileall -q keyseq` clean / `-m unittest discover -s tests` 451 OK（skip 7）/
  `-m unittest discover -s tests_ui` 427 OK / `-m tests.smoke_app` SMOKE OK / `rg -n "measure_header_window_width\(self.app\)" keyseq/presentation/controllers/pane_layout/pane_layout_controller.py` が 1 件。
- **リスクと戻し方**: 挙動不変（呼び出し順も同じ）。tests_ui が `measure_min_widths` を patch していても経路は同じ。1 コミットで revert 可能。
- **依存**: 項目 0。

## 項目 2（任意）: 保存幅の有効判定を 1 箇所にする（M3 境界）

- **対象**: `keyseq/presentation/pane_width_rules.py:13-24`
- **どう変えるか**:

  ```python
  def _is_valid_saved_window_width(raw: object) -> bool:
      return not isinstance(raw, bool) and isinstance(raw, int) and raw >= 1

  def parse_saved_window_width(raw, screen_width):
      return min(raw, screen_width) if _is_valid_saved_window_width(raw) else None

  def startup_window_width_to_save(raw, applied_width):
      if not _is_valid_saved_window_width(raw):
          return None
      return applied_width if raw < applied_width else None
  ```
- **完了条件**: 項目 1 と同じコマンド + `-m unittest tests.test_pane_width_rules -v` 全 pass。
- **リスクと戻し方**: 挙動不変（真理値表が同じ）。不正値表のテストが担保。revert 可能。
- **依存**: 項目 0。項目 1 と独立。

## 実施形態（ユーザー選択）

- (a) phase 19 末の追加タスク `task_07_refactor` として実施 / (b) 次フェーズ前の独立ミニ計画（「計画11」）として実施 / 実施しない。
