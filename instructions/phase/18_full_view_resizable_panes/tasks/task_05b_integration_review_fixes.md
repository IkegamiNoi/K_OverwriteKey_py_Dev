# task_05b_integration_review_fixes

## 目的

task_05 の二次レビュー（`deep-reviewer` F1・F2・F4・F5 / `codex-reviewer` P2）のうち、ユーザーが採用した 4 件を直す
（ユーザー判断 2026-09-17）。根拠は暫定仕様 16 §3-4（ウィンドウ最小幅 = 両端の**表示幅** + トリガー一覧の最小幅）・§3-2・§5-10・§5-14。
**presentation 限定**。`pane_width_rules.py` / `app.py` / domain / application / infrastructure は変更しない。

## 対象範囲（presentation 1 ファイル + tests_ui 3 ファイル）

### `keyseq/presentation/controllers/pane_layout_controller.py`

1. **F1（ドラッグ後の最小幅を表示幅から出す）**: `_update_window_min_size()` が `resolve_layout` に渡す幅を、
   希望幅 `desired` ではなく**現在の表示幅** `PaneWidths(keymap_box.winfo_width(), sequence_box.winfo_width())` にする。
   - 実現は `_plan()` に省略可能な幅引数（既定は `self.desired`）を足す形でよい。計算は `resolve_layout` に一本化したまま（独自式を書かない）。
   - `apply_layout()` の計算（希望幅から）は変えない。ドラッグを離したとき `apply_layout()` を呼ぶ形にはしない（反対側の枠が変わるため）。
2. **F5（取り残されたドラッグ状態を消す）**: `_on_press` で、準備前またはサッシュ以外の押下のときも `self._drag = None` にしてから戻る。

### `tests_ui/test_full_view_panes.py` / `tests_ui/test_pane_drag_and_window_min.py` / `tests_ui/test_pane_widths_persistence.py`

3. **F2（実際の config に左右されない）**: 3 モジュールの `setUpClass` で `App()` を作る間だけ
   `patch.object(app_module.ConfigService, "load_startup", return_value={})` を当てる
   （前例 `tests_ui/test_startup_font_characterization.py:11-28`。`App` の import 形は各ファイルに合わせる）。
   **既存のアサーション・期待値は変えない**。
4. **F1 のテスト**（`test_pane_drag_and_window_min.py` に 1 件追加）: `app.winfo_screenwidth` を小さい値に patch し、
   出力シーケンスの表示幅が希望幅より縮められた状態を作る → サッシュ 0 を左へドラッグして離す →
   `app.wm_minsize()[0] == self._expected_window_min()`（既存ヘルパ = 表示幅の合計から算出）。
   修正前の実装なら失敗する条件になっていること（縮められていない状態では差が出ない）。
5. **F4（本物の起動経路で復元）**（`test_pane_widths_persistence.py` に**別の TestCase クラス**で 1 件追加）:
   `load_startup` が `{PANE_WIDTHS_KEY: {"keymap": K, "sequence": S}}` を返す状態で `App()` を作り `update()` →
   `pane_layout.desired == PaneWidths(K, S)` かつ両端の `winfo_width()` が K / S。K / S は最小幅以上で既定幅と異なる値
   （例: 既定の keymap 要求幅 + 40 / 出力シーケンスの最小幅 + 30 程度。定数で置けない場合は最小幅から算出してよい）。
   `write_startup` / `save_startup` が呼ばれないこと。App は classCleanup で `update()` → `destroy()`。

### 設計メモ / 制約

- 変更は上記だけ。既存テストのアサーションを弱めない。
- F2 の patch は `App()` 構築の間だけ（`start` → 構築 → `finally: stop`）。以後のテストで `write_startup` の実呼び出しが必要な箇所（persistence test_05 の `save_startup` patch）は変えない。
- F4 のクラスは既存クラスの共有 App と同時に 2 つの App を持たない（クラス単位で作って破棄する）。

## 含まない

- F3（見出しの切れ）/ F6（縦方向の見た目）→ **task_05 の実機目視項目**で確認
- F7（動かしていない側の既定幅も保存）→ 仕様どおり・除外。task_06 の正本反映で §3-6 の文言を残す
- 正本反映（**task_06**）

## 確認

python は `../../../.venv/Scripts/python.exe`。実測は `verifier`。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest tests_ui.test_full_view_panes tests_ui.test_pane_drag_and_window_min tests_ui.test_pane_widths_persistence -v` が全 pass（6 / 12 / 13）。
3. F1 テストが「表示幅 ≠ 希望幅」の状態を作っていること（= 修正前の実装なら失敗する条件）を `reviewer` がテストコードで確認する。
4. `-m unittest discover -s tests` が 441 OK（skip 7）/ `-m unittest discover -s tests_ui` が 382 OK。
5. `-m tests.smoke_app` が SMOKE OK。`git status --short config` が空。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。
- 実機目視は **task_05 で実施**（本タスク完了後）。

## 完了記録（2026-09-17）

- 実装は `codex-implementer`。F1 = `_plan(widths=None)` + `_update_window_min_size` が表示幅を渡す / F5 = `_on_press` 冒頭で `_drag = None` /
  F2 = 3 モジュールの `App()` 構築中だけ `load_startup` → `{}` / F1 テスト `test_12_drag_after_screen_shrink_uses_displayed_window_min` /
  F4 テスト = 別クラス `PaneWidthsStartupRestoreTest`。
- `verifier`: compileall clean / 3 モジュール 6・12・13 OK / `tests` 441 OK（skip 7）/ `tests_ui` 382 OK / smoke OK / config 差分なし。
- `reviewer` = 採用（指摘なし。F1 テストは修正前実装なら 30px ずれて失敗することを計算で確認）。
