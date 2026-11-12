# task_07c_pane_initial_apply

## 目的

Mac（Tk 9.1 aqua）で、フル表示のペインの初期幅・最小幅の適用（`PaneLayoutController.apply_initial_widths`）が一度も走らない（2026-11-11 実測）。
適用は `panes` の `<Configure>`（幅 > 1）を契機にしているが、Mac では `install()`（`app.py:357`）の時点で `panes` が既に表示済み（幅 756）で、その後 `panes` に `<Configure>` が届かない。そのため `min_widths` / `desired` / `_auto_window_width` が None のままになる。
tests_ui の `'NoneType' object has no attribute 'keymap'` 22 件と `bad geometry specifier "Nonex820"` 2 件は、これが起点（task_07 の基準線の前に直す）。

**レイヤ制約**: presentation のみ。domain / application / infrastructure 不変・JSON スキーマ不変。
Windows では従来どおり `<Configure>` で適用される（後述の確認は `_applied` で二重に走らない）。

## 対象範囲（presentation 限定）

### `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py`

- `install()` の最後（`self._installed = True` の後）で `self.app.after_idle(self._apply_if_already_sized)` を 1 回予約する。
- `_apply_if_already_sized(self) -> None` を追加する: `if not self._applied and self.app.full_view.panes.winfo_width() > 1:` なら `self._applied = True` → `self.apply_initial_widths()`。`_on_configure` と同じ条件・同じ手順にする（docstring に「aqua では install 前に panes の大きさが確定し `<Configure>` が届かないため」と書く）。
- `_on_configure` の条件と処理は変えない。

### テスト

- `tests/` に、`PaneLayoutController` の単体テストを追加する（既存の同コントローラのテストがあればそこへ。無ければ `tests/test_pane_layout_initial_apply.py` を新規）。Mock の app（`full_view.panes.winfo_width`・`after_idle`・`bind`）で:
  - `install()` が `after_idle` に `_apply_if_already_sized` を 1 回予約する
  - 幅 > 1・未適用 → `apply_initial_widths` が 1 回呼ばれ `_applied` が True
  - 幅 ≤ 1 → 呼ばれない
  - 適用済み（`_applied` True）→ 呼ばれない
  - `apply_initial_widths` は `patch.object` で差し替える

## 読むファイル

- `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py:30-100`
- `keyseq/presentation/app.py:350-360`（`install` の呼び出し）
- `tests/` で `PaneLayoutController` を参照しているテスト（`grep -rln PaneLayoutController tests`）の Mock の作り方

## 含まない

- `test_minimize_grab_custody` の 25 件（aqua では入れ子の transient が最小化で隠れない。別系統・task_07 の基準線に記録し扱いを決める）
- tests_ui を通しで流したときの Tk の Segmentation fault（`test_grid_editor_window`・実行順依存。task_07 で記録）
- コンパクト表示の `compact_pane_layout`（同じ症状が出るかは task_07 の基準線で確認する）
- tests_ui の sashwidth 4 か所・skip・基準線の記録（task_07）

## 確認

**Mac**（`../../../.venv/bin/python`）:

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- 追加した単体テストが pass
- `-m unittest discover -s tests` の失敗・エラーが基準（失敗 89・エラー 15）から増えない
- `-m tests.smoke_app` が pass
- tests_ui の `test_pane_widths_persistence`・`test_pane_drag_and_window_min`・`test_full_view_header_width`・`test_pane_window_width_persistence` をモジュールごとに実行し、`'NoneType' object has no attribute 'keymap'` と `Nonex820` が 0 件（残る失敗は列挙して報告）
- `main.py` を起動し、フル表示の 3 つのペインの幅が初期幅で並び、ペインの境界をドラッグすると最小幅で止まること（ユーザー目視）
  - 2026-11-11 実施: verifier = compile clean・追加 4 件 pass・tests 1924 件 失敗 89 / エラー 15（基準同数）・smoke OK・tests_ui の pane 系 3 モジュール全件 pass・`test_pane_window_width_persistence` は失敗 4（窓幅の数値。task_07 の基準線へ）・`keymap` / `Nonex820` 0 件。目視 OK（ユーザー）。reviewer 採用（参考: `_apply_if_already_sized` の TclError 吸収は見送り）

**Windows**: 次に Windows で標準検証 4 種を行う機会にまとめて実施する（tests_ui の pane 系が従来どおり pass すること）。
- 2026-11-13 実施（M1）: compile clean・tests 1997 件 失敗 0 / エラー 0 / skip 7・tests_ui 1271 件 失敗 0 / エラー 0・smoke OK（verifier）。目視 OK（ユーザー）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視: Mac のペインの初期幅は本タスクで実施（ユーザー）。
