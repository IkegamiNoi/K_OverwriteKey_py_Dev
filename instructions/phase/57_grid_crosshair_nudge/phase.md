# phase.md

## フェーズ名

画面の枠の十字マーク・矢印でクリック位置の微調整・操作キーの任意化（grid_crosshair_nudge）

## フェーズの目的

画面の枠（phase 56）で選んだ枠に十字マーク（クリック点）を出し、矢印キーでクリック点をずらしてクリックできるようにする。
あわせて枠の操作キー（Space / BackSpace / Enter / Tab / 矢印）を keymap ごとに付け替えられるようにし（Esc = 戻る・num enter = クリックは固定）、
編集の窓では境界のドラッグ中に関係する枠の中心へ十字マークを出す。
**domain（`grid.ops` の正規化・保存・読み出し・固定の予約キーの縮小・自動割当 / 検査）/ application（操作キーによる振り分け・実効の suppress 集合・クリック点の移動）/ presentation（十字の描画・編集の窓の操作キーの欄・取り込み）に跨る。JSON スキーマ変更あり（`grid` に任意キー `ops`・既定と同じなら書かない・後方互換）。**

- 起票元: ユーザー要望（2026-10-13）。
- 主入力（暫定仕様）: [41_grid_crosshair_nudge.md](../../history/41_grid_crosshair_nudge.md)（v0.4・ユーザー確定済 2026-10-14）
- モード: **暫定仕様先行モード**。番号対応: phase 57 / 暫定 41 / decisions 57。

## 確定（ユーザー 2026-10-13〜14）

暫定 41 §2 が正（本書に再掲しない）。要点: 選んだ枠に十字（中央表示ではキーの文字を置き換え）/ 矢印で min(16px, 枠の 1/8)・Shift で 1px・枠の中だけ・覚えない・カーソルも動かす /
矢印は選択中だけ suppress / 操作キーは各 1 つで付け替え可・Esc と num enter は固定・右クリックは Shift + click のキー /
OK では重なりを拒否・既存 / 手編集の重なりは枠のキーを優先 / 編集の窓はドラッグ中に関係する枠の中心へ十字。

## スコープ

### 含む

- 暫定 41 §4〜§8 の実装とテスト
- 実機目視（暫定 41 §9 の 1〜4・6・8）
- 正本反映（暫定 41 §11）

### 含まない（後送り）

- 暫定 41 §10 のとおり（右クリック専用キー / 移動量・十字の設定化 / クリック点の記憶 / テンキーの矢印の既定化 / 細分化のボタンの並びの十字 / キーボード表示に操作キーを出すこと）

## このフェーズで読むファイル

1. `instructions/history/41_grid_crosshair_nudge.md`（全体）
2. domain: `keyseq/domain/screen_grid/`（`normalize.py`・`models.py`・`assignment.py`・`editing.py`・`geometry.py`）
3. application: `keyseq/application/screen_grid_session.py`（全体）・`keyseq/application/input_router.py`（:153-179 `_route_grid_key`）
4. presentation: `keyseq/presentation/screen_grid/`（`grid_overlay_window.py`・`cell_label.py`・`grid_editor_panel.py`・`screen_grid_controller.py`）・
   `keyseq/presentation/dialogs/grid_editor_window.py`・`keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`（:490-515 `new_grid_shapes` の取り込み）・`keyseq/presentation/dialogs/keymap_edit_dialog.py`（下書き）
5. 正本: `features.md` §4.7 / `data_schema/5_06_01_keymap_grid.md` / `key_input.md` §7.3・§7.4 / `codebase_map.md`「画面の枠（phase 56）」
6. テスト: `tests/test_screen_grid*.py`・`tests/test_input_router.py`・`tests_ui/test_screen_grid_overlay.py`・`tests_ui/test_grid_editor_window.py`・`tests_ui/test_task06_keymap_management_ui.py`

## タスク

- task_01: domain の `grid.ops`（正規化・既定と同じなら書かない・`ops_of`）・固定の予約キーを修飾キーだけに・自動割当 / 振り直しが操作キーを飛ばす・操作キーの検査（重なり・固定・予約）の純関数（暫定 41 §4・§8 の検査）と単体テスト（既存の固定予約のテストの書き換えを含む）
- task_02: application の振り分け（枠のキー > 操作キー・操作キーの引き当て・Shift の扱い・実効の suppress 集合を `suppress_keys` 1 本で公開・router の esc 固定分岐の廃止）とクリック点の移動（暫定 41 §5・§6）と単体テスト
- task_03: 枠の窓の十字マーク（中央表示ではキーの文字を置き換え・腕の切り詰め・暫定 41 §7 枠の窓）と UI テスト。**実装後にユーザーの実機目視**
- task_04: 編集の窓の操作キーの欄（ボタン・既定に戻す・Esc / 選択の解除・OK の検査）と結果の取り込み（`ops` の写し・消し）（暫定 41 §4 取り込み・§8）と UI テスト。**実装後にユーザーの実機目視**
- task_05: 編集の窓の境界のドラッグ中の十字マーク（暫定 41 §7 編集の窓）と UI テスト。**実装後にユーザーの実機目視**
- task_06: 統合確認（tests / tests_ui / smoke・deep-reviewer + codex-reviewer）
- task_06a: 統合レビューの指摘（OK の検査で固定の esc / num enter と未編集の今つながる画面の枠のキーの重なり）の修正 + §5 のテストの抜け 2 件
- task_06b: 完了判定前レビュー（Codex 敵対的 medium）の対応 = 編集の窓のパネルの 2 列化とスクロール（OK / キャンセルは常に見える）。**実装後にユーザーの実機目視**
- task_07: 正本反映（暫定 41 §11 の昇格・凍結・`codebase_map.md`「画面の枠」節の更新）・`decisions_archive/57_grid_crosshair_nudge.md`・decisions.md の索引・current.md の完了記載・`/refactor_check`
- task_08_refactor: 提案書 23 の実施（矢印の操作キーの集合を 1 か所に・選択の解除を 1 つの呼び出しに・パネルのボタンの色を定数に）
- task_09_fix: 完了後のユーザー報告 = 「枠を編集…」の窓を閉じた後にキーマップ変更のダイアログが Esc で閉じない（入力フォーカスが戻らない）の修正。**実機目視あり**

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: **最上段の Esc・選択なしの矢印が素通しを保つ**（実効の suppress 集合）/ 枠のキー > 操作キーの優先順位が session と router で揃う /
  `ops` の無い・既定と同じ `grid` に差分が出ない（4 経路 + 編集の窓の取り込み）/ クリック点が枠の外へ出ない（0px の枠を含む）/
  domain に tkinter・Win32 を持ち込まない / フックのスレッドでの判定が UI スレッドの状態に依存しない（集合 1 本で判定）
- 統合確認（task_06）: `deep-reviewer` + `codex-reviewer` / 完了判定前（task_07）: `deep-reviewer` + `codex-adversarial-reviewer`
- 実機（ユーザー）: task_03・task_04・task_05
