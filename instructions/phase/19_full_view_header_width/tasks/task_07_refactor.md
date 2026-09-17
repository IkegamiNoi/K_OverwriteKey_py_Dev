# task_07_refactor

## 目的

`/refactor_check` の判定「推奨」で起票した提案書 [10](../../../modified_proposal/10_refactor_full_view_header_width.md) を、phase 19 末の追加タスクとして実施する（ユーザー選択 (a)・2026-09-17）。
**挙動不変**。項目 1 = 最小幅とヘッダ幅の測定の 2 行（3 箇所）を private メソッドへ集約（M3）/ 項目 2 = 保存幅の有効判定の重複を 1 箇所へ（M3 境界）。
安全網は新規の特性テストを足さず、**変異検査**で既存テストが崩れを検出できることを確かめる（ユーザー承認）。

## 対象範囲（presentation 2 ファイル・テスト変更なし）

### 項目 1: `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py`

- private メソッド `_measure(self) -> None` を追加: `self.min_widths = self.measure_min_widths()` と `self.header_window_width = measure_header_window_width(self.app)` をこの順で行う（docstring に暫定仕様16 §3-4 / 暫定仕様17 §3-1）。
- `apply_initial_widths` / `on_font_changed`（非省略表示経路）/ `on_full_view_shown`（再測定経路）の 2 行を `self._measure()` に置き換える。呼び出し順・条件分岐は変えない。
- 公開メソッド `measure_min_widths()` は残す。

### 項目 2: `keyseq/presentation/pane_width_rules.py`

- モジュール内 private 関数 `_is_valid_saved_window_width(raw: object) -> bool`（`not isinstance(raw, bool) and isinstance(raw, int) and raw >= 1`）を追加し、
  `parse_saved_window_width` と `startup_window_width_to_save` の判定をこれに置き換える。戻り値・docstring の意味は変えない。

## 読むファイル

- 編集対象（全体）: 上記 2 ファイル
- 提案書: `instructions/modified_proposal/10_refactor_full_view_header_width.md`（項目 1・2）

## 含まない

- テストの変更 / 保留候補（`KEYBOARD_LAYOUT_COMBO_WIDTH` の置き場所・tests_ui の保存予約遅延・`hook_controller.py` の 2 行の同型）
- 正本の変更（`codebase_map.md` に private メソッドは載せない）

## 確認

python は `../../../.venv/Scripts/python.exe`。

0. **安全網（基準）**: 変更前の全 pass は task_05 の統合確認（`tests` 451 / `tests_ui` 427 / smoke OK）を基準とする（以降の差分は文書のみ）。
1. `verifier`: compileall clean / `tests` 451 OK（skip 7）/ `tests_ui` 427 OK / smoke OK / config mtime 不変 /
   `rg -n "measure_header_window_width\(self.app\)" keyseq/presentation/controllers/pane_layout/pane_layout_controller.py` が 1 件 /
   `rg -n "isinstance\(raw, bool\)" keyseq/presentation/pane_width_rules.py` が 1 件。
2. **変異検査**（メインが一時的にコードを壊して実行し、必ず元に戻す。戻した後に `git diff` が本タスクの差分のままであることを確認）:
   - 項目 1: `_measure()` から `header_window_width` の測定行を消す → `-m unittest tests_ui.test_full_view_header_width tests_ui.test_full_view_panes` のいずれかが**落ちる**こと。
   - 項目 2: `_is_valid_saved_window_width` の `raw >= 1` を `raw >= 0` にする → `-m unittest tests.test_pane_width_rules` が**落ちる**こと。
   - 落ちなかった場合は実施を止めてユーザーへ報告する（特性テストの追加を先に行う）。
3. `reviewer` が挙動不変（呼び出し順・分岐・真理値表）を確認。

## 完了条件

- 上記確認 pass・変異検査で両方とも検出・**`reviewer` 採用**。実機目視は不要（挙動不変）。

## 完了記録（2026-09-17）

- 実装は `codex-implementer`（2 ファイル・+14 / -8）。
- 変異検査（メイン）: ヘッダ測定行の削除 → `test_header_and_each_frame_fit_at_minimum_width` 4 件失敗 / `raw >= 0` → `test_parse_invalid_window_width`・`test_startup_window_width_to_save` の `raw=0` で 2 件失敗。いずれも検出。実施後に元へ戻し md5 一致を確認。
- `verifier`: compileall clean / `tests` 451 OK（skip 7）/ `tests_ui` 427 OK / smoke OK / config mtime 不変 / rg 2 件とも 1 件。
- `reviewer` = 完了可（呼び出し順・分岐・`_remeasure_pending` の位置不変・真理値表一致・指摘なし）。
