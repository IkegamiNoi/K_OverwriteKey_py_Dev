# idea_33: フック再開の `after(0)` が負荷下で取りこぼされ tests_ui が不定期に赤くなる

## 概要

ダイアログを閉じたときのフック再開は `<Destroy>` を受けて
[hook_controller.py:57](../../keyseq/presentation/controllers/hook_controller.py) の
`self._app.after(0, self.resume_hook_after_dialog)` で**予約**される（即実行ではない）。
テストは `app.update()` を 1 回呼んでから `get_hook_pause_count()` を確かめるが、
`update()` は**今キューにあるイベントを処理して即戻る**ため、CPU 負荷下ではこのタイマー
コールバックが同じサイクルで拾われず、**カウントが 1 のまま残る**ことがある。

これらのテストクラスは `setUpClass` で `App` を共有し、各テストの `setUp` で
「カウントが 0 であること」を確認する（phase 15 task_03 のドレイン検査）ため、
**1 件の取りこぼしが後続テストへ連鎖**する（実測で 1 fail が 7 件の赤になった）。

- **production の欠陥ではなくテストのみの問題**（実使用では次のイベントループで再開される）。
- **[idea_18](idea_18_escape_delivery_flaky_test.md) とは別 family**。idea_18 は「Escape が
  フォーカス窓へ配送されず捨てられる」問題で、phase 28 task_04 で解消済み。
  本件は **Escape を使わない経路（ボタン invoke / `destroy` / ×）でも起きる**。

## 経緯・実測（2026-09-23・phase 28 task_05）

負荷下（busy loop 4 本）の測定で観測。**task_05c が原因でないことは A/B で確認済**だが、
**phase 28 全体（特に task_01）が原因でないとは言えない**（下記の補足〔2026-09-23 追記〕）。

| 測定 | 条件 | 結果 |
|---|---|---|
| 一括 | HEAD（task_05c 前）| `test_dialog_teardown_flows` 6 回中 1 fail |
| 一括 | base `60372bf` | 15 回中 0 fail |
| 一括 | HEAD（同上） | 15 回中 0 fail |
| 5 モジュール×6 | HEAD（task_05c 後）| 30 回中 9 fail（`quarantine_manage_flow` が 4/6） |
| 交互 A/B | HEAD vs `6fbeebb` | `quarantine_manage_flow` **0/10 対 0/10**（4/6 が再現せず） |
| 交互 A/B | HEAD vs `6fbeebb` | `keymap_set_history_flow` 2/6 対 0/6 |

- **最も強く出た 4/6 が再測定で 0/10** となり、**測定自体がマシン状態のノイズに支配されている**。
- `keymap_set_history_flow` の 2/6 は、当該テストが**群 A のダイアログを一切 import していない**
  （`tests_ui/test_keymap_set_history_flow.py:9-15`）ため **task_05c からの因果経路が無い**。

**補足（2026-09-23・phase 28 完了判定前の `deep-reviewer` 指摘 M3）**:

- base `60372bf`（phase 28 前）と HEAD の比較は**両方 0/15** で差が出ておらず、判別力が無い。
- 差が出た A/B の相手 `6fbeebb` は **task_01〜04 を含む**ため、無罪にできるのは **task_05c だけ**。
- task_01 は flake が出たダイアログ（隔離の管理・孤児の棚卸し・構成セットの履歴）の
  **フォーカス挙動を変えている**ため、**原因候補に残る**。着手時は **`60372bf` 対 `08ace46`（task_01）**の比較を先に行う。
- **無負荷でも観測**: phase 28 task_06 の標準検証で `tests_ui` 一括 4 回中 1 回、
  `test_quarantine_manage_flow` の `test_escape_and_window_close_keep_action_empty` が escape / window の
  両サブケースで `1 != 0`（`send_escape` の診断は出ず＝配送ではなくカウンタの型）。単体では pass。
  **subTest 間で `setUp` が走らない**ため、escape 側の残留が window 側へ連鎖した可能性がある（未確認）。

観測されたテスト（いずれも `get_hook_pause_count()` の不一致）:

- `tests_ui/test_dialog_teardown_flows.py` — `test_t2_close_paths_resume_exactly_once` /
  `test_t1_tcl_close_defers_resume_for_manager_and_action`
- `tests_ui/test_orphan_sweep_flow.py` — `test_run_empty_list_sets_result_and_resumes_hook`
- `tests_ui/test_quarantine_manage_flow.py` — `test_escape_and_window_close_keep_action_empty`
- `tests_ui/test_keymap_set_history_flow.py` — `test_chooser_returns_result_and_restores_history_grab` /
  `test_close_routes_restore_hook_and_parent_grab`
- `tests_ui/test_dialog_escape_binding.py`（**2026-09-23・phase 30 task_02 の標準検証で追加観測**）—
  `test_layout_delete_escape_destroys_and_resumes_hook` / `test_preset_manager_escape_discards_edits_and_resumes_hook`
  ほか同クラス 1 件（計 3 件・`1 != 0`）。**再実行で 532 件全 pass**。phase 30 の差分は domain の読込時正規化のみで
  ダイアログへの因果経路は無い。**Escape を使うテストのため idea_18 系統（配送）を除外しきれていない**
  （`send_escape` の診断出力の有無は未確認。着手時の切り分け対象）。
  **2026-09-24・phase 31 task_02 の標準検証で再観測**（同ファイル 2 件）: `test_layout_delete_escape_destroys_and_resumes_hook` は
  **`resume_hook_after_dialog` が 0 回呼ばれた**という形（カウンタ不一致ではなく**再開要求そのものが来ていない**）/
  `test_preset_manager_escape_discards_edits_and_resumes_hook` は `1 != 0`。再実行で全 pass。差分は runner / app の委譲 1 行で因果経路なし。
  **「再開要求が 0 回」は Escape が届かず閉じていない〔idea_18 系統〕可能性を示す**ため、着手時はこのファイルから切り分ける。

## 提案（方向性・要設計）

**案 A（推奨）: 待つヘルパを入れる** — `assertEqual(count, 0)` を
「**上限つきで `app.update()` を回しながらカウントが期待値になるまで待つ**」ヘルパに置き換える。
最終的に解除がちょうど 1 回であることは変わらず確認できるため、**検証内容は弱まらない**。
置き場は `tests_ui` の共有ヘルパ（`escape_delivery.py` と同様の位置づけ）。
**phase 28 §6.1 と同じく、回数ではなく実時間の期限で切る**。

**案 B: `setUp` のドレイン検査を緩める** — カウントを強制的に 0 へ戻す。
**採らない**（phase 15 task_03 の検出力を失う。idea_18 の案 C と同じ理由で却下済み）。

**案 C: production 側で `after(0)` をやめる** — `<Destroy>` で同期的に再開する。
**要注意**。`after(0)` は破棄処理中の再入を避けるための設計なので、変えると別の問題が出る恐れがある。
production を触るため仕様変更フローが必要。

## 状態

**完了**（[phase 32](../phase/32_hook_resume_wait_in_ui_tests/phase.md)・2026-09-24。判断は
[decisions_archive/32](../../.claude_data/state/decisions_archive/32_hook_resume_wait_in_ui_tests.md)）。
案 A = `tests_ui/hook_resume_wait.py` の `wait_for_hook_pause_count` を tests_ui 7 ファイルへ適用し、負荷下の反復実行で赤 0 件。
適用範囲は破棄後の解除を確かめる箇所すべて・原因の A/B 測定はしない〔ユーザー確定〕。`test_dialog_escape_binding.py` の「再開要求 0 回」は `send_escape` が破棄を確認した後の失敗のため
**idea_18 系統ではなく本 family**〔2026-09-24 確認〕）。
2026-09-23 起票。phase 28 task_05 の §8-7 判定から分離（ユーザー判断 2026-09-23 =
「§8-7 は Escape family に限定して判定し、本 family は idea 化する」）。
着手時は**まず負荷条件を制御できる測定手順を固める**ところから（今回の測定はノイズが大きく、
同一条件の交互実行でないと差が見えない）。

## 関連

- [idea_18](idea_18_escape_delivery_flaky_test.md)（Escape 配送 family・phase 28 で解消済）
- [暫定仕様 22](../history/22_dialog_keyboard_focus.md) §6 / §6.1 / §8-7
- `keyseq/presentation/controllers/hook_controller.py` の
  `suspend_hook_for_dialog` / `resume_hook_after_dialog`
- 正本 `instructions/common/spec_detail/key_input.md` §7.2（閉じ方によらず解除はちょうど 1 回）
