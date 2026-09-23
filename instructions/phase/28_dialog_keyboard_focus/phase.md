# phase.md

## フェーズ名

ダイアログの初期キーボードフォーカス（dialog_keyboard_focus）

## フェーズの目的

モーダルダイアログを開いた時点で**キーボードフォーカスをダイアログ内へ入れる責務を
`grab_modal` へ集約**し、Escape が親の App へ抜ける不具合を構造的に解消する。あわせて
**群 C の 5 経路へ Escape を追加**し、**Escape 依存テストの flaky（idea_18）**を解消する。

- **対象レイヤ = presentation のみ**。**データスキーマ・domain / application の変更は無い**。
- 起票元: [idea_26](../../backlog/idea_26_dialog_keyboard_focus.md)（主・phase 27 task_04 の実機目視由来）
  + [idea_18](../../backlog/idea_18_escape_delivery_flaky_test.md)（同梱）。
- 主入力（暫定仕様）: [22_dialog_keyboard_focus.md](../../history/22_dialog_keyboard_focus.md)
  （**v0.4・ユーザー確定済・実装着手可**）。
- モード: **暫定仕様先行モード**。番号対応: phase 28 / 暫定 22 / decisions 28。

## 確定（ユーザー 2026-09-22）

- **案 B = `grab_modal` へフォーカス責務を集約**（個別修正の案 A は不採用）。
  実装方式は**明示引数**（`grab_modal(window, parent=None, *, focus=None)`）。
  推測型（`focus_lastfor()` / `after_idle`）は**実測で反証済**（暫定仕様 §1.2）。
- **idea_18 を同梱**。ただし idea_18 の案 B（配送後に待つ）では直らないことが実測で判明したため、
  **「フォーカスを確保してから送る + 診断を先に採る」**へ設計変更（暫定仕様 §6）。
- **群 C（Escape bind なし 5 経路）にフォーカスが入る挙動変化を受容**し、
  **正本へ Escape 条項も追加して 5 経路へ Escape を実装する**（暫定仕様 §2.1-2・§2.1-3・§3.5）。
- **フォーカスの復帰（閉じた後・最小化復帰後）はスコープ外**。実機目視のついでに**再現確認のみ**行う。
- **同型スケルトンの共通化は合流させない**（`current.md`「別タスク化候補」に残置）。

## 確定（ユーザー 2026-09-23・スコープ拡大）

- **群 A の 4 経路（`ActionDialog` / `KeymapEditDialog` / `PresetDialog` / `TriggerDialog`）へも
  Escape を追加する**（task_05c）。これで `grab_modal` を通る 15 経路すべてが Escape で閉じ、
  正本の Escape 条項を例外なしで昇格できる。
- **Esc に別用途がある状態（記録中・取得中）では、その用途を優先して閉じない**。
  実現形は**単一の `<Escape>` ハンドラ + 状態分岐**（暫定仕様 v0.5 §3.6。Tk の bind 解決を実測済み）。
- **実機目視は実装がすべて終わってから 1 回**にまとめる。

## スコープ

### 含む

- `modal.grab_modal` のフォーカス適用（`focus` 引数 + `_apply_initial_focus`）
- 群 A（6 経路）・A'（1 経路）の `focus_set` を引数へ移す機械的な移行
- 群 B（3 経路）の欠落解消の確認、群 C（5 経路）への Escape 結線
- テストの検出力強化（決定論的な単体テスト + 実 Tk 検査 + 偽 Toplevel 2 クラスへの `focus_set` 追加）
- idea_18 の診断・Escape ヘルパ・対象 4 テストの移行
- 正本 `features.md` への 3 条項追記 + `codebase_map.md` の署名更新と件数訂正（13 → 15）

### 含まない（後送り）

- **フォーカスの復帰**の規定（再現確認のみ行い、再現したら idea 起票）
- **同型スケルトンの共通化**（`suspend_hook_for_dialog` / `Escape` + `WM_DELETE_WINDOW`）
- ダイアログの初期フォーカス位置の UX 設計の全面見直し
- [idea_32](../../backlog/idea_32_grab_modal_static_check_discovery.md)（静的検査の発見ベース化）

## このフェーズで読むファイル

1. `instructions/history/22_dialog_keyboard_focus.md`（**主入力**。v0.4）
2. `keyseq/presentation/modal.py`（実装の中心）
3. 群 A・A': `dialogs/action_dialog.py` / `keymap_edit_dialog.py` / `keymap_set_history_dialog.py` /
   `preset_dialog.py` / `trigger_dialog.py` / `controllers/config_io/child_save_dialog.py`
4. 群 B: `dialogs/orphan_sweep_dialog.py` / `quarantine_manage_dialog.py` / `reference_cleanup_dialog.py`
5. 群 C: `dialogs/layout_delete_dialog.py` / `preset_manager.py` /
   `controllers/config_io/io_dialogs.py` / `hotkey_presets_io.py` / `child_save_dialog.py`
6. `tests_ui/test_nested_modal_grab.py`（静的検査）/ `test_dialog_teardown_flows.py` /
   `test_orphan_sweep_flow.py` / `test_quarantine_manage_flow.py` / `test_keymap_set_history_flow.py` /
   `test_child_save_dialog.py` / `test_config_io_characterization.py`（偽 Toplevel 2 クラス）
7. 正本: `instructions/common/spec_detail/features.md`「モーダルダイアログの作法」/
   `key_input.md` §7.2 / `instructions/common/codebase_map.md:303`〜

## タスク

**進捗（2026-09-23）**: task_01〜06・05b〜05e は**完了**。**task_07（提案書 11 のリファクタ）** が残り。

- **task_01**: `grab_modal` へフォーカス責務を集約（`focus` 引数 + `_apply_initial_focus`）+
  群 A・A' の 7 経路を引数へ移行 + 偽 Toplevel 2 クラスへ `focus_set` 追加 + 決定論的な単体テスト。
  **既存の静的検査 `tests_ui/test_nested_modal_grab.py:260`
  `test_grab_modal_is_last_initialization_statement` が引き続き green であることを本タスクで確認する**
  （暫定仕様 §8-5）
- **task_02**: 実 Tk の検出力（群 B の 3 件の修正確認 + 群 A・A' の回帰確認 + skip ガード）
- **task_03**: 群 C の 5 経路へ Escape を結線（暫定仕様 §3.5 の表）+ フック解除 1 回の固定
- **task_04**: idea_18 = 診断 → Escape ヘルパ導入 → 対象 4 テストの移行（案 A 併用の採否判断を含む）
- **task_05**: 統合確認（`verifier`・負荷下の再現確認）+ 実機目視の依頼 → **完了**（2026-09-23・C② 再現 → idea_34）
  （群 B の Escape / フォーカス復帰の再現確認）
- **task_05b**: テストの検出力補強（`deep-reviewer` 指摘 M1・M3。暫定仕様 §8-13）。tests_ui 限定
- **task_05c**: **群 A の 4 経路へ Escape を追加**（暫定仕様 v0.5 §3.6。Esc の別用途は状態分岐で優先）。
  **スコープ拡大**（ユーザー確定 2026-09-23・§2.2）
- **task_05d**: `send_escape` の確保ループを deadline 方式へ（暫定仕様 v0.6 §6.1。`deep-reviewer` M2）。
  tests_ui 限定
- **task_05e**: **Esc の押しっぱなしで閉じない**（暫定仕様 v0.7 §3.6.1。フェーズ完了判定前レビュー L3・task_05c の退行）+
  群 A の「閉じない」検査の送り方を期限つきのフォーカス確保へ揃える（M2）。**追加**（ユーザー確定 2026-09-23・§2.3）
- **task_06**: 正本反映（`features.md` 3 条項 + `codebase_map.md` 署名更新・件数訂正）+
  暫定仕様 22 の凍結 + `decisions_archive/28` 作成 + `current.md` 更新 +
  idea_26 / idea_18 を `backlog/INDEX_done.md` へ移動
- **task_07**: `/refactor_check`（推奨・M3）の [提案書 11](../../modified_proposal/11_refactor_dialog_escape_secondary_use.md) を実施 =
  Esc の別用途つき閉じ処理（3 ダイアログの複製）を `dialogs/escape_close.py` の `bind_escape_close` へ寄せる。**挙動不変**。
  **追加**（ユーザー選択 (a)・2026-09-23）

## レビュー方針

- 各タスクの必須レビュー = `reviewer`。
- **task_01 と task_03 は「既存の意図を壊していないか」を重点観点にする**
  （フォーカス先の移行 / 閉じ方の意味づけ）。
- 統合確認（task_05）= `deep-reviewer` + `codex-reviewer`。
- **Codex に python 実行を伴う検証を依頼しない**（実測は `verifier` またはメイン）。
- **暫定仕様 §8 の受け入れ条件 14 件（v0.7）が完了判定の基準**。特に §8-2（群 A・A' の挙動不変）・
  §8-7（負荷下の再現確認）・§8-8（実機目視と skip 件数の報告）を省略しない。
