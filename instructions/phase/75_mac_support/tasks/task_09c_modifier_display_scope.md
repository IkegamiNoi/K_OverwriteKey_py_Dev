# task_09c_modifier_display_scope

## 目的

修飾キーの表示名（macOS で `windows` → `Command`・`alt` → `Option`）を、暫定 57 v0.10 §5.3.3 の表の「本節で追加」の箇所へ広げる。保存するキー名・JSON は変えない。Windows は差し替え表が空のため表示が変わらない。

- 前提: task_09a（`key_symbols.set_modifier_display_names` / `display_key_name` / `display_modifier_names`・`OsBackend.modifier_display_names` の注入）が済んでいる。
- 変更は presentation の表示箇所・文言へ渡す値（application の文言の候補は対象範囲 4 の判定による）と、必要なら `domain/key_symbols.py` の公開関数に限る。業務処理・検査・JSON スキーマは不変。OS を判定しない（差し替え表を通すだけ）。

## 対象範囲（§5.3.3 の表）

1. **キーマップ一覧の切替キー**: `keymap_panel_controller.py` の `format_keymap_list_entry` が `tr("keymap_panel.entry", switch_key=…)` へ渡す値（`"-"` はそのまま）。重なりの判定（`overlap.keymap_switch_conflict`）には元のキー名を渡す。
2. **停止 / トグルキーの欄**（`views/full_view/hook_frame.py:33,42`・`views/compact_view/hook_frame.py:39,44` の読み取り専用の Entry）と **キーマップ編集・まとめて設定の切替キーの欄**（`dialogs/keymap_edit_dialog.py:65-67`・`dialogs/keymap_switch_batch_dialog.py:126-128`）: 記録専用の欄。**保存値を持つ今の StringVar（`ui_vars.stop_key_var` / `toggle_key_var`・ダイアログの `key_var` / 行ごとの `key_vars[i]`）はそのまま**にし、Entry の `textvariable` だけを表示用の StringVar に替える。表示用は保存値の変数の `trace_add("write")` で追従する（初期値も同じ）。保存・検査・重なりの判定・取り消しは今どおり保存値の変数を読む（書く側 = `key_capture.py:116,128` の `_apply_key` と `app.py:762-763` はどちらも保存値の変数への `.set()` だけ）。
   - **停止 / トグルキーの表示用の変数は `ui_vars.py` に 1 回だけ作り**（例 `stop_key_display_var` / `toggle_key_display_var`）、保存値の変数への trace もそこで張る。FullView / CompactView は `textvariable` に表示用を指定するだけ（View の作り直しで trace を残さない）。ダイアログはダイアログごと（まとめて設定は行ごとに 1 組）に作る。
   - 表示値は共通の純関数 1 つ（`display_modifier_names` を呼ぶだけでよい）で作り、Tk なしでテストできるようにする。修飾キーの語だけで、記号の置き換えは §4.6 のとおりこれらの欄に入れない（切替キーの一覧・タイトル・文言も同じく修飾キーの語だけ）。
3. **キーボードUIのタイトル**: `keyboard_window.py:666` の `keyboard_window_title` へ渡す編集中のキー名を `display_modifier_names` で置き換える（`_editing_source_key` 自体は変えない）。
4. **キー名を差し込むすべての文言**（§5.3.3 の文言の行）: `tr(…)` へ渡す**キー名の値**（`key` / `source` / `target` / `existing_switch_key` 等）だけを `display_modifier_names` で置き換える。**検査・比較（例 `keymap_panel_controller.py:213,215,229` の `key != excluded_key`）・ログ・例外の文字列（`error`）は元のキー名のまま**。文言そのもの・`keymap_id`・ラベル・名前は変えない。
   - 対象（キー名を渡していることを実測済み）: `controllers/keymap_panel/keymap_panel_controller.py:188,194,199,204,209,219,232,240`（切替キー）・`:648,651,654,660`（置換元・置換先の検査）・`:667,669,680,683`（割り当て / クリアの通知の `source` / `target`）・`controllers/key_capture.py:173,182`・`controllers/trigger_panel/trigger_row_edit.py:36,40,43,46,49,88,91,94,97,100,164`・`controllers/trigger_panel/trigger_list_edit.py:56`・`controllers/trigger_panel/effective_row_transition.py:30`・`controllers/hook_controller.py:262,306,307`・`controllers/keymap_panel/keymap_add_flow.py:132`。
   - 判定して報告する候補（`key=` 等を渡すが値がキー名か未確認）: `presentation/keyboard_layouts.py:180-244`（レイアウトの id の見込み = 対象外）・`presentation/dialogs/action_control_fields.py:311,320,345`・`application/keymap_switch_batch.py:36,108-119`（まとめて設定の検査の文言 = 切替キーなら対象。application から `domain.key_symbols` を使うのは依存方向として可）・`application/config_service/save_plan_execution.py:427-468`・`application/call_context.py`・`application/hotkey_service.py:23`・`application/sequence_steps.py:59`・`application/sequence_runner/input_acceptance.py:215`。**値が保存されたキー名のときだけ**置き換え、変数名・カウンタ名・レイアウトの id 等は置き換えない。判定結果を 1 行ずつ報告する。
5. 適用済みの箇所（トリガー一覧・`key_hold`・キーボードUIの枠・アクション一覧の `hotkey`）が `key_symbols` の 3 関数（`set_modifier_display_names` / `display_key_name` / `display_modifier_names`）を通っていることを確かめる（変更は不要の見込み）。

## 含まない

- 手で打てる入力欄（トリガーのキー・`key_hold` のキー・`hotkey` の値・アクションの値）・ホットキーのラベル・プリセットの表示・ヘルプの本文（§5.3.3「適用しない箇所」）
- 割り当て禁止の文言の Mac 向けの言い換え（task_11）
- 置換先に修飾キーを記録すること（idea_57）
- 正本 `features.md` §4.6 の訂正（フェーズ末の正本反映）

## 読むファイル

- `instructions/history/57_mac_support.md` §5.3.3
- `keyseq/domain/key_symbols.py`
- 上の対象範囲に挙げた各ファイルの該当行と、`ui_vars.py`・`app.py:255-280,374-375,760-765`（停止 / トグルキーの変数の使われ方）

## テスト

- `tests/test_key_symbols.py`（必要なら）: `display_modifier_names` の既存のテストで足りるか確認。
- キーマップ一覧の切替キーの表示（差し替え表を設定したとき `Command+…` / 空のとき不変）。
- 記録専用の欄: 保存値の変数を `left windows` にすると表示用の変数が `left Command` になり、保存値は `left windows` のまま（差し替え表が空なら同じ文字列）。Tk を使うテストは tests_ui、使わずに済む部分（表示値を作る関数）は tests。
- 文言に差し込む値の置き換え（代表 = `key_capture.py:173`〔取得の重複〕と `keymap_panel_controller.py:188`〔切替キーの禁止〕・`tr` は日本語固定〔`fix_language("ja")`〕）。
- 保存値が変わらないこと: 停止キーを `_apply_key` 経由で `left windows` に変えたとき、`data["hook_stop_key"]`（実際のキー名は `HOOK_STOP_KEY` の値）が `left windows` のまま・表示用の変数は `left Command`。
- 差し替え表を設定するテストは `tearDown` で空へ戻す。Mac で tests_ui の App を作ると `app.py:118` が macOS の表を注入するため、**表の有無で結果が変わる既存の tests_ui が無いか**を確認する（あれば表示の期待値を表に合わせるか、テストの中で表を空にする）。

## 確認

Mac（`../../../.venv/bin/python`・verifier）: compile clean・`tests` が基準線（失敗 6・エラー 10）から増えない・smoke pass・tests_ui は触れたモジュールに関係するものを 1 本ずつ。
Windows（task_09 / 09a と合わせて verifier）: compile clean・`tests` 失敗 0・`tests_ui` 失敗 0（1 本ずつ）・smoke pass。
実機目視（Mac・ユーザー）: キーマップ一覧・停止 / トグルキーの欄・キーマップ編集の切替キーの欄・キーボードUIのタイトル・切替キーの重複のエラーで `Command` / `Option` と出る。停止 / トグルキーの欄（幅 8 文字）で `left Command` が欠けて読めなくならないか（欠けるなら報告・幅の変更は別途判断）。保存した設定のキー名は `windows` / `alt` のまま。

## 完了条件

- 上記の確認 pass・**reviewer 採用**・実機目視（Mac）OK。
- `instructions/common/codebase_map.md` の記号キーの表示の行（`key_symbols`）に適用箇所・`ui_vars` の表示用の変数を追従（メイン）。

## 起票レビュー

reviewer「修正して採用」（2026-11-14）: 中 3 件（文言の対象の列挙漏れ → §5.3.3 の文言の行を「すべて」へ改訂・キー名の変数名と比較は元の値・停止 / トグルの表示用の変数は `ui_vars` に 1 回）・低 3 件（欄の幅の目視・保存値のテスト・tests_ui の表の有無）を反映（ユーザー「推奨どおり反映」）。
