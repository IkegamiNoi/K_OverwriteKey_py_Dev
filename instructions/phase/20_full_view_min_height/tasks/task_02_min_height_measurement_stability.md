# task_02_min_height_measurement_stability

## 目的

task_01 で入れた最小の高さの測定が、測る瞬間の表示内容で揺れないようにする（暫定仕様 18 §2-7・§3-4）。
①ステータスバーの一時メッセージは表示の有無・行数によらず **1 行分として測る** ②フル表示へ戻るときは、ステータス欄をフル表示の文言（1 行）に更新**してから**測る。
受け入れ条件は暫定 §5-2（後半）・§5-4。

**presentation 限定・domain / application / infrastructure 不変・JSON 不変**。最小の高さの再計算の契機（起動時・フォント変更・フル表示へ戻る）は変えない（一時メッセージの設定・消去では測り直さない）。

## 対象範囲（presentation 限定・既存 2 ファイル + tests_ui 1 ファイル）

### `keyseq/presentation/controllers/pane_layout/pane_measure.py`

- `measure_window_min_height(app)` を、**一時メッセージが 1 行のときの要求高さ**を返すように変える:
  - `app.update_idletasks()` の後、`app.winfo_reqheight()` から「一時メッセージのラベルが 1 行を超えて押し上げている分」を引く。
  - 押し上げ分 = `max(0, 一時メッセージのラベルの要求高さ − 同じ親〔ステータスバー〕の他のラベルの要求高さの最大)`。
    ステータスバーの行の高さはラベルの要求高さの最大で決まり、左のファイル状態のラベルは常に 1 行（`app.py` の `_update_file_status`）のため。
  - 一時メッセージのラベルは **`app` 配下のウィジェットを辿り、`textvariable` が `str(app.ui_vars.flash_message_var)` と一致する `ttk.Label`** として見つける
    （private なヘルパー関数に分ける）。見つからない・同じ親に他のラベルが無い場合は押し上げ分 0。
  - docstring に「一時メッセージは 1 行分として測る（暫定仕様18 §2-7）」を明記。

### `keyseq/presentation/app.py`

- `show_full_view` の `self.pane_layout.on_full_view_shown()` の呼び出しを、`self.trigger_panel.update_status()` の**後**（メソッドの末尾）へ移す。
  他の呼び出し（`_restore_full_geometry` / `sync_trigger_selection_to_views` / `refresh_actions` / `update_status`）の順序は変えない。

### `tests_ui/test_full_view_min_height.py`（task_01 で新規作成済みのファイルへ追加）

既存の setUp / `_restore` を使い、一時メッセージを使うテストでは**後始末で `app._set_flash_message("", auto_clear=False)` 相当により消し、予約された消去 `after` を残さない**。追加テスト:

1. **フォント変更時に複数行の一時メッセージが表示中でも同じ値**（暫定 §5-2 後半）: 一時メッセージ無しで ＋3 にしたときの `window_min_height` を記録 → 0 へ戻す →
   `app._set_flash_message("1行目\n2行目\n3行目", auto_clear=False)` → ＋3 → `window_min_height` が記録値と一致。
   前提確認として、一時メッセージ表示中の `app.winfo_reqheight()` が表示前より大きいこと（テストが空振りしていないこと）も assert する。
2. **一時メッセージを表示したまま省略表示を往復しても同じ値**（暫定 §5-2 後半）: フル表示で一時メッセージ無しの `window_min_height` を記録 → 複数行の一時メッセージを表示 →
   `show_compact_view()` → `show_full_view()` → `window_min_height` が記録値と一致。
3. **省略表示中のフォント変更後に戻った値が、ステータス欄 1 行で測った値と一致**（暫定 §5-2・§3-4）: `show_compact_view()` → ＋3 → `show_full_view()` → 値を記録 →
   `update()` 後に `layout.apply_layout()` を呼び直した値と一致（フル表示の状態で測り直しても変わらない）。
4. **戻った高さが最小未満なら広がる**（暫定 §5-4 後半）: フォント 0 で高さを最小ちょうどにする → `show_compact_view()` → ＋3 → `show_full_view()` →
   `app.winfo_height() == layout.window_min_height` かつ ＋3 の最小がフォント 0 の最小より大きい。

### 設計メモ / 制約

- **App に属性を足さない**（`app.status_bar` 等は phase 01 で「生やし」として解消済み = `decisions_archive/01_view_ref_cleanup.md`。`views/status_bar.py` も変えない）。ラベルは測定側で辿って見つける。
- 一時メッセージの値を一時的に書き換えて測る方式は採らない（表示を揺らす・消去予約と競合するため）。
- 複数行の一時メッセージの表示中に最小付近で下側が切れるのは受容（暫定 §2-7）。それを検出・回避する処理は入れない。
- 既存テストの期待値は変えない。落ちたら**期待値を弱めず**原因を報告する。

## 読むファイル

1. `instructions/history/18_full_view_min_height.md` §2-7・§3-4・§5-2・§5-4
2. `keyseq/presentation/controllers/pane_layout/pane_measure.py`（全体・編集対象）
3. `keyseq/presentation/views/status_bar.py`（全体・ステータスバーのラベル構成。編集しない）
4. `keyseq/presentation/app.py` の `show_full_view`・`_set_flash_message`・`_clear_flash_message`・`_update_file_status`（`rg -n` で位置特定。編集は `show_full_view` のみ）
5. `tests_ui/test_full_view_min_height.py`（全体・追加先）
6. `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py` の `apply_layout`・`on_font_changed`・`on_full_view_shown`（呼び出し関係の確認のみ）

## 含まない

- 統合確認（`tests` / `tests_ui` 全体・`smoke_app`）・二次レビュー・実機目視（**task_03**）。
- `features.md` §4.6 / `codebase_map.md` の更新・暫定仕様の凍結（**task_04**）。
- 一時メッセージの表示形式の変更（1 行にまとめる等）・一時メッセージの設定 / 消去での測り直し（不採用・暫定 §2-7）。
- 省略表示の最小サイズ（スコープ外）。

## 確認

実行は `verifier`。python は `..\..\..\.venv\Scripts\python.exe`。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest tests_ui.test_full_view_min_height -v` の 10 項目（task_01 の 6 + 本タスクの 4）が pass。
3. 関連既存テストが pass: `tests_ui.test_pane_drag_and_window_min` / `tests_ui.test_full_view_header_width` / `tests_ui.test_full_view_panes` /
   `tests_ui.test_pane_widths_persistence` / `tests_ui.test_pane_window_width_persistence`、および `show_full_view` を通る既存テスト（`rg -ln "show_full_view" tests_ui` の全ファイル）。
4. `-m unittest discover -s tests` が全 pass。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は **task_03** でまとめて実施。
