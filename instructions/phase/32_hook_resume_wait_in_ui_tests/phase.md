# phase.md

## フェーズ名

UI テストでのフック再開の待ち合わせ（hook_resume_wait_in_ui_tests）

## フェーズの目的

ダイアログ破棄後のフック再開は `<Destroy>` から `after(0)` で**予約**される
（`keyseq/presentation/controllers/hook_controller.py:57`）。tests_ui は `app.update()` を **1 回**呼んでから
`get_hook_pause_count()` / `resume_hook_after_dialog` の呼び出しを確かめるため、負荷下ではこの予約が拾われず
赤くなり、`setUp` のドレイン検査を通じて同クラスの後続テストへ連鎖する。
これを「**実時間の期限まで `app.update()` を回し、期待値になるまで待つ**」ヘルパへ置き換えて解消する。

**tests_ui 限定・production 不変・JSON スキーマ不変・正本（spec_detail）の改訂なし**。
正本 `key_input.md` §7.2「停止要求は閉じ方によらずちょうど 1 回解除」の検証内容は弱めない
（待った後の確認は従来どおり「ちょうど 1 回」「カウントが期待値」）。

- 起票元: [idea_33](../../backlog/idea_33_hook_resume_after_idle_flaky_test.md)（phase 28 task_05 の §8-7 判定から分離）。
- 主入力（暫定仕様）: なし（直接改訂モード。正本の改訂も無い）。
- モード: **直接改訂モード**。番号対応: phase 32 / 暫定 なし / decisions 32。

## 確定（ユーザー 2026-09-24）

- **案 A**: 期限つきで待つヘルパを tests_ui の共有ヘルパとして追加する。**期限は回数ではなく実時間**で切る。
  案 B（`setUp` のドレイン検査を緩める）・案 C（production の `after(0)` をやめる）は採らない。
- **適用範囲 = 破棄後の解除を確かめている箇所をすべて**（観測済み 5 ファイルに限らない。`get_hook_pause_count()` を使う tests_ui 8 ファイルが対象候補）。
- **原因の A/B 測定（`60372bf` 対 `08ace46`）は行わない**（仕組みはコードで特定済み・測定はノイズが大きい）。
- 事実確認（2026-09-24）: `test_dialog_escape_binding.py` の「`resume_hook_after_dialog` が 0 回」は、
  `send_escape` が破棄を待ち `assertFalse(dialog.winfo_exists())` も通った後の失敗
  （`tests_ui/test_dialog_escape_binding.py:84-89`・a1f1323 時点）。**Escape 配送（idea_18 系統）ではなく本 family**。

## スコープ

### 含む

- tests_ui の共有ヘルパ（新規モジュール。`escape_delivery.py` とは責務が違うため別ファイル）:
  期待値になるまで実時間の期限つきで `app.update()` を回す。期限切れは**現在値・期待値・経過時間つきで fail** する。
- ヘルパ自身のテスト（**決定的に**: 再開を `after(0)` より遅らせても待てる / 期限切れで診断つき fail になる）。
- 置き換え対象 = **破棄後に解除（カウント減少・`resume_hook_after_dialog` の呼び出し）が起きることを期待する確認**。
  テスト冒頭の「先行テストが残した解除予約を流す」`update()` + 0 確認も含む。
- 対象ファイル: `test_dialog_teardown_flows.py` / `test_orphan_sweep_flow.py` / `test_quarantine_manage_flow.py` /
  `test_keymap_set_history_flow.py` / `test_dialog_escape_binding.py`（観測済み）+
  `test_app_ui_flows.py` / `test_hook_controller_teardown.py` / `test_startup_font_characterization.py`（同型の残り）。

### 含まない（後送り・置き換えない）

- **破棄直後に「まだ解除されていない」ことを確かめる確認**（`after(0)` で遅延させる設計そのものを固定している。
  例 `test_hook_controller_teardown.py:52-55`）。
- **`setUp` のドレイン検査**（phase 15 task_03 の検出力を保つ。厳密なまま残す）。
- 解除が**起きないこと**を確かめる確認（期待値が変わらない側。待っても意味が無い）。
- `tearDownClass` の「破棄前に保留中の `after(0)` を流す」`update()`。
- production コード・`escape_delivery.py` の変更・原因の A/B 測定。

## このフェーズで読むファイル

1. [idea_33](../../backlog/idea_33_hook_resume_after_idle_flaky_test.md)（経緯・観測テスト一覧）
2. `keyseq/presentation/controllers/hook_controller.py:40-73`（`suspend_hook_for_dialog` / `resume_hook_after_dialog` / `get_hook_pause_count`・読むだけ）
3. `tests_ui/escape_delivery.py`（実時間期限つき待ちの手本・変更しない）
4. 対象 8 ファイルの `get_hook_pause_count()` / `resume_hook_after_dialog` 周辺のみ（`grep` で特定してから読む）
5. `instructions/common/codebase_map.md:318-330`（tests_ui ヘルパの記載位置）

## タスク

- task_01: 待つヘルパ + ヘルパ自身の決定的テスト + 観測済み 5 ファイルへの適用 — **完了**（2026-09-24）
- task_02: 残り 3 ファイル（`test_app_ui_flows.py` / `test_hook_controller_teardown.py` / `test_startup_font_characterization.py`）への適用 +
  負荷下での tests_ui 反復実行（1 回の測定で完了判定の材料にする）— **完了**（2026-09-24）
- task_03: 記録（`codebase_map.md` へヘルパを 1〜2 行 / decisions_archive/32 / current.md / idea_33 → INDEX_done / `/refactor_check`） — **完了**（2026-09-24）

## レビュー方針

- 共通観点は `.claude/rules/review.md`。
- **本フェーズ固有**:
  - **検証内容が弱まっていないか**: 待った後も「ちょうど 1 回」「期待カウント」を確かめているか。
    `assert_called_once` を `assert_called` 等へ緩めていないか。
  - **置き換えてはいけない確認を置き換えていないか**（「まだ解除されていない」の確認 / `setUp` のドレイン検査 / 解除が起きないことの確認）。
  - ヘルパが**実時間の期限**で切っているか（回数上限だけにしていないか）・期限切れの fail に診断が出るか。
  - production・`escape_delivery.py` に差分が無いか。
