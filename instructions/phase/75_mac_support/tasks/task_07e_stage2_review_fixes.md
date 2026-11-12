# task_07e_stage2_review_fixes

## 目的

段階 ② の区切りレビュー（deep-reviewer・2026-11-12）の M2・M3 を直す（ユーザー判断 2026-11-13・decisions「段階 ② の区切り」）。
- M2: `listbox_range_drag.py:107-110` が aqua では封じたい操作を封じていない。aqua の実測（Tk 9.1）: `<<SelectAll>>` = `<Mod1-Key-a>`（Command+A）で `<Command-slash>` は全選択にならない・Listbox のクラスバインドは aqua でも `<Control-Shift-Key-Home>` / `<Control-Shift-Key-End>`・`<<SelectNone>>` もクラスバインドあり。task_05 の `primary_modifier` への置き換えで、Mac では Command+A の全選択と Control+Shift+Home / End の範囲選択が素通りする。
- M3: task_07d の起動時の既定の高さ（`max(820, fit)`・画面の高さで頭打ち）が aqua に限定されておらず、Windows でもフォントの増分・低い画面で高さが変わる → **aqua のときだけ**適用する（ユーザー判断「aqua だけに限る」）。

**レイヤ制約**: presentation とテストのみ。domain / application / infrastructure 不変・JSON スキーマ不変。
**Windows の動作不変**: M2 の Windows の封じる組は従来（task_05 以前）と同じ `Control` の組 + 仮想イベント 2 つ（Windows の `<<SelectAll>>` / `<<SelectNone>>` は `Control-slash` / `Control-backslash` 等で、従来の封じと同じ操作）。M3 は Windows では 820 のまま（task_07d 以前と同じ）。

## 対象範囲

### M2: `keyseq/presentation/listbox_range_drag.py:107-110`

- 封じる組を OS によらず次にする（`primary_modifier` を使わない）:
  `"<Control-slash>"`・`"<Control-backslash>"`・`"<Shift-Control-Home>"`・`"<Shift-Control-End>"`・`"<Shift-Home>"`・`"<Shift-End>"`・`"<<SelectAll>>"`・`"<<SelectNone>>"`（いずれも `self._break_event`）。
- 使わなくなった `primary_modifier` の import を外す。

### M3: `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py:105-108`

- `if self.app.wm_state() == "normal":` を `if is_aqua(self.app) and self.app.wm_state() == "normal":` にする（`keyseq.presentation.tk_platform.is_aqua`）。他は変えない。

### テスト

- `tests/test_pane_layout_initial_apply.py`: 既存の高さのテスト 2 件は `is_aqua` を True に patch する。aqua でないときは `geometry` で高さを変えない（`measure_window_fit_height` を呼ばない）テストを 1 件足す。
- `tests_ui/test_listbox_range_drag.py`: listbox に上記 8 つのシーケンスが束ねられていること（`bind(seq)` が空でない）、`event_generate("<<SelectAll>>")` で選択が変わらないこと（selectmode が extended の箱で、事前の選択が保たれる）を足す。既存のテストが `primary_modifier` で組を作っていれば直す。
- `tests_ui/test_keymap_list_operations.py`・`test_trigger_list_operations.py`・`test_preset_manager_range_drag.py` で封じる組を `primary_modifier` から作っている箇所があれば、上記の固定の組に合わせる（task_07 の A2 で入れた `<Control-x>` 等の**クリップボード**のショートカットは対象外。変えない）。

## 読むファイル

- `keyseq/presentation/listbox_range_drag.py:1-15,85-115`
- `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py:1-30,92-115`・`keyseq/presentation/tk_platform.py`
- `tests/test_pane_layout_initial_apply.py`
- `tests_ui/test_listbox_range_drag.py`・`grep -n "primary_modifier\|slash\|Home>\|End>" tests_ui/test_keymap_list_operations.py tests_ui/test_trigger_list_operations.py tests_ui/test_preset_manager_range_drag.py`

## 含まない

- 他の `Control` 系のバインドの全件点検（レビューの残存リスク。task_09 の目視で見つかれば対応）
- L4〜L6・L9（参考）・文書の修正（M4・L2・L3 はメインが本タスクのコミットで行う）

## 確認

**Mac**（`../../../.venv/bin/python`。tests_ui は通しで流さない）:

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` の失敗・エラーが基準線（失敗 6・エラー 10）から増えない
- `-m tests.smoke_app` が pass
- tests_ui の `test_listbox_range_drag`・`test_preset_manager_range_drag`・`test_keymap_list_operations`・`test_trigger_list_operations`・`test_full_view_scroll_areas`・`test_pane_window_width_persistence`・`test_full_view_panes` を 1 モジュールずつ流し、基準線より悪化しない（`test_keymap_list_operations` の失敗 3 は task_09 の基準線）
- `main.py` で一覧（キーマップ管理等）にフォーカスして Command+A・Control+Shift+Home / End を押しても選択が広がらない（ユーザー目視）

**Windows**: 段階 ② の区切りの Windows 検証（M1）でまとめて実施する（既定の高さ 820・一覧の Control+/・Control+Shift+Home が従来どおり封じられる）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
  - 2026-11-13 実施: compile clean・tests 1940 件 失敗 6 / エラー 10 / skip 28（基準線どおり）・smoke OK・tests_ui 11 モジュールは `test_keymap_list_operations` の失敗 3 以外 0（3 件は HEAD でも同じ・既存）（verifier）。reviewer 採用（参考: import の並び）。目視 OK（Command+A・Control+Shift+Home / End で一覧の選択が広がらない・ユーザー）。
- 実機目視: Mac は本タスクで実施（ユーザー）。
