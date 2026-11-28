# task_07_spec_promotion_and_phase_close

## 目的

暫定仕様 [63](../../../history/63_help_follows_front_dialog.md) v0.6 を正本 `instructions/common/spec_detail/` へ昇格して凍結し、フェーズ 83 を完了する（`.claude/rules/task_execution.md`「フェーズ完了時」）。
**文書のみ・コードは変えない**（目視用の一時スクリプト `spike/` の削除を除く）。

## 対象範囲（文書限定）

### 正本の昇格（暫定 63 §9・task_06 の deep-reviewer の Q2・Q4・M6）

- `features.md` §4.6「ヘルプの窓」:
  - 1054 行: 「モーダルにも `transient` にもしない」は残す。「同時に 1 つだけ」に付け替えの間の例外を、「開いた直後のフォーカス先は Notebook」に作り直しでは入れない例外を、「位置と大きさは記録しない」に引き継ぎとの関係（保存しないの意味）を足す
  - 1061 行（「?」の項）: 「メニューから開いたヘルプ窓は、モーダルのダイアログが開いている間は操作できない（ダイアログの「?」がこれを補う）」・「既に別の窓の子として開いたヘルプがあれば閉じてから開き直す」・「ダイアログを閉じると子のヘルプも閉じる」・「ヘルプを前面化するときは最小化を解除して前面へ出す」を、暫定 63 §3（持ち主・知らせる口・付け替える条件・開く / 閉じるとき・重なりとフォーカス・前面化と最小化からの復帰）と §4（引き継ぐ状態・戻す順・控えと窓の消え方）の規則へ置き換える。macOS の例外（task_01 で追加）の相手を「その時点の持ち主」へ直す
  - Welcome（1042・1044 行付近）: メニューから開き直した Welcome のヘルプは、Welcome を閉じても残る（持ち主の子へ移る）。初回の Welcome は今どおり
- `features.md` §4.6「モーダルダイアログの作法」:
  - 1140 行付近の「他のウィンドウは操作できない」にヘルプの例外を、1146 行「開いた時点では、窓の前面化・フォーカス強制は行わない」と 1155 行「閉じた後のキーボードフォーカスの戻り先は規定しない」に、ヘルプの付け替えで入力先を戻す例外（暫定 63 §3.6）を足す
  - 台帳の末尾の変化を知らせる口・grab の持ち主がヘルプならその親とみなす（§5）・台帳の窓ごとの最後の入力先（§3.2）・`grab_modal` の `help_follow`（カーソルグリッドの編集窓）
  - 最小化の項（1191〜1202 行付近）: 1191〜1195 の「メイン窓が前面のときだけ強制」は変えず、付け替えには使わない旨を書く。1198〜1202 のヘルプに関わる残存リスク・「「?」から開いたヘルプ窓はダイアログの子で、grab を取らない…」「メニューからヘルプを開いたとき、既存のダイアログの子のヘルプ窓を再利用しうる」を本書の規則に合わせて書き直す
- `key_input.md` 28〜29 行: 付け替え（古い窓の破棄）で絞り込み欄のフックの停止が解除される旨を 1 文足す（再開はちょうど 1 回のまま）
- `codebase_map.md`: help の節（`help_window_controller.py` の付け替え・控え・窓の消え方・Tk の対策 / `grab_handoff.py` / `help_window.py` と `help_tab_view.py` の `export_state` / `apply_state` / `restore_scroll` / 知らせ 2 つ）・modal の節（`set_modal_front_listener`・`front_modal`・`last_input`・`mark_grab_delegate`・`resolve_grab_holder`・`is_own_process_foreground`・`is_app_foreground` の公開）・`WindowBackend.hands_grab_to_active_child_window`（macOS = True / Windows = False）・`choice_dialog._grab_holder`・`grid_editor_window` の `help_follow=False`
- `ui_terms.md`: 足さない（画面の文言は変えていない）

### 凍結と後片付け

- 暫定 63 のヘッダを「凍結（2026-11-28・正本反映済）」へ。`instructions/history/README.md` の 63 の行を「v0.6・凍結」へ
- `instructions/phase/83_help_input_during_modal/spike/`（目視用の一時スクリプト 2 本）を削除する（`task01_measurement.md` の参照は「削除済み」と書き添える）

### 記録

- `.claude_data/state/decisions_archive/83_help_input_during_modal.md` を作り、`decisions.md` の phase 83 の節を移して「アーカイブ索引」に 1 行
- `instructions/phase/current.md`: アクティブなフェーズ = なし・直前の完了フェーズ = phase 83（完了フェーズのリンクは直近 3 件）・直近の領域の数行（残件 = 残存リスクと idea）・次採番（phase 84 / 暫定 64 / decisions 84 / 提案書 30 / idea 72 のまま）
- `instructions/backlog/INDEX.md` の idea_60 の行を完了にして `INDEX_done.md` へ移す
- 残存リスク（decisions_archive に書く）: 開いた順と違う順で閉じると grab が戻らない（既存・正本の作法どおり）/ 選択ダイアログの親と前面維持の相手が同じ（既存）/ メッセージボックス・OS のファイルの窓・カーソルグリッドの編集窓の間はヘルプを操作できない / Tk 9.1（macOS）の deiconify の不具合への回避（Tk の版が変わると要らなくなる・効かなくなる恐れ）/ `<<NotebookTabChanged>>` の経路（task_06a の reviewer の参考 ①・実機で落ちない）/ Cmd+H で隠している間の付け替え（L5）
- `/refactor_check`（メトリクスは verifier）を実行し、判定を完了報告に書く

## 読むファイル

- `instructions/history/63_help_follows_front_dialog.md`（全体）
- `instructions/common/spec_detail/features.md:1030-1062, 1138-1205`
- `instructions/common/spec_detail/key_input.md:20-35`
- `instructions/common/codebase_map.md` の help・modal・os_backend の節
- phase 82 の完了時の書き方（`decisions_archive/82_scroll_direction_setting.md`・current.md の完了記載）

## 含まない

- コードの変更

## 確認

- 正本の書き換えが暫定 63 v0.6 と食い違わない（完了判定前レビューで確認）
- リンク・番号の実在
- `/refactor_check` の判定

## 完了条件

- 完了判定前レビュー（`deep-reviewer` + Codex 敵対的レビュー）の指摘の採否がユーザーで決まり、採用分を反映済み・**reviewer 採用**（本タスクの差分の整合確認）
- 実機目視は不要（task_06 で完了済み）

## 結果

- 正本の昇格（`features.md` §4.6「ヘルプの窓」の新しい項「ダイアログとの関係」・Welcome・「モーダルダイアログの作法」の台帳と外への口・最小化の項 / `key_input.md` / `codebase_map.md`）・暫定 63 v0.6 の凍結・spike の削除・decisions_archive/83・current.md・idea_60 を INDEX_done へ（2026-11-28）
- 完了判定前レビュー: deep-reviewer = 修正要（必須 3 = codebase_map の古い行・付け替えのときだけの除外・refactor_check の記録）/ Codex 敵対的 = needs-attention 4 → ユーザー判断で推奨どおり（コード 2 件 = task_07a・文書の採用分を本タスクで反映・Codex 1 は残存リスク）
- `/refactor_check` = **不要**（M1〜M6 該当なし・help_window_controller.py の責務の境界を別タスク化候補へ）
- reviewer（task_07a と本タスク）= **修正して採用** → `codebase_map.md` の `is_own_process_foreground` の行を task_07a の判定に直し、decisions_archive に deep 6 の細目を明記
- **完了**（2026-11-28）・**phase 83 完了**
