# decisions_archive / phase 32: UI テストでのフック再開の待ち合わせ

対応表: phase 32 / 暫定なし（直接改訂モード）/ decisions 32。
起票元: [idea_33](../../../instructions/backlog/idea_33_hook_resume_after_idle_flaky_test.md)（phase 28 task_05 の §8-7 判定から分離）。
完了 2026-09-24。**tests_ui 限定・production 不変・スキーマ不変・正本 `spec_detail/` の改訂なし**。
記録先 = `codebase_map.md` の HookController 節（テストで破棄後の解除を確かめるときのヘルパ）。

## 問題

ダイアログ破棄後のフック再開は `<Destroy>` から `after(0)` で**予約**される（`hook_controller.py:57`）。
tests_ui は `app.update()` を 1 回呼んでから `get_hook_pause_count()` / `resume_hook_after_dialog` の呼び出しを確かめていたため、
負荷下ではタイマーが同じ `update()` で拾われずカウントが 1 のまま残り、`setUp` のドレイン検査を通じて同クラスの後続テストへ連鎖した
（phase 28〜31 の標準検証で繰り返し観測。再実行では pass）。

## 確定した設計判断（ユーザー 2026-09-24）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | **案 A = 実時間の期限つきで待つヘルパ**（`tests_ui/hook_resume_wait.py`）。**先に必ず `update()` を 1 回呼ぶ**（置き換え前より弱くしない）・`time.monotonic` の期限（既定 2 秒）・期限切れは期待値 / 現在値 / 経過 / timeout つきで fail | 案 B（`setUp` のドレイン検査を緩める）= phase 15 task_03 の検出力を失う / 案 C（production の `after(0)` をやめる）= 破棄中の再入を避ける設計を崩す・仕様変更フローが要る |
| 2 | **適用範囲 = 破棄後の解除を確かめる箇所すべて**（観測済み 5 ファイルに限らない） | 観測済みのみ = 同じ形の箇所が後から個別に flaky になる |
| 3 | **原因の A/B 測定（`60372bf` 対 `08ace46`）は行わない** | 仕組みはコードで特定済み・直すのはテスト側・測定はマシン状態のノイズが大きい（idea_33 の実測表） |
| 4 | `test_dialog_escape_binding.py` の「`resume_hook_after_dialog` が 0 回」は**本 family**（Escape 配送 = idea_18 系統ではない） | `send_escape` が破棄を待ち `assertFalse(dialog.winfo_exists())` も通った後の失敗（`:84-89`）で、閉じたが `after(0)` が未処理だった（行番号は `a1f1323` 時点。現在は `:85-88`） |

**置き換えない確認**（task 定義で行単位に列挙）: ①破棄直後の「まだ解除されていない」（`after(0)` 遅延の設計そのもの）
②解除が起きないこと（子の破棄・`window` 省略・`PresetDialog`・Escape で閉じない側）③同期解除（t4b・`messagebox` 前後・`resume_hook_after_dialog()` の直接呼び出し）
④`setUp` のドレイン検査・`tearDownClass` ⑤`update()` を伴わないテスト / subTest 冒頭の `== 0`。
⑤の例外 = `test_keymap_set_history_flow.py` の chooser を開いた直後の `== 1`（task_01 で明示的に置換対象とした。観測済みテストで、先行テストの予約が残ると 2 になる）。
否定確認が再開に依存する箇所（t4a の「再開しない」）は**待機の後**に置く（先に置くと素通りする）。

## 実施結果

- task_01（`9eff5ee`）: ヘルパ + `tests_ui/test_hook_resume_wait.py`（決定的 3 件・実 App 不使用）+ 観測済み 5 ファイル
  （teardown_flows / orphan_sweep / quarantine_manage / keymap_set_history / dialog_escape_binding）。
  `keymap_set_history` は `before` の取得前にも待つ（先行テストの予約が残ったまま基準値を取らない）。reviewer = 完了可・指摘なし。
- task_02（`6754290`）: `test_app_ui_flows.py`（3 箇所）/ `test_hook_controller_teardown.py`（素の `tk.Tk` のため `wait_pause_count` で
  `SimpleNamespace(update, hook)` を渡す・二重予約の検査は中間値 1 を待つ）。`test_startup_font_characterization.py` は同期解除のみで**変更なし**。
  reviewer = 完了可・指摘なし。
- task_03: `codebase_map.md`（HookController 節に 3 行。task 定義では tests_ui ヘルパの記載〔`escape_delivery.py` の説明〕の近くとしていたが、
  `after(0)` 予約の説明と一緒に読まれる HookController 節の方が適切と判断して置き場を変えた）/ 本アーカイブ / current.md / idea_33 → INDEX_done。
- 実測: compile clean / `tests` **577**（skip 7・不変）/ `tests_ui` **535**（+3）/ smoke OK。
  **負荷下**（`.venv` python の busy loop × 4）: 9 モジュール一括 × 6 回（各 172 件 OK）+ tests_ui 全体 × 1 回（535 OK）= **本 family の赤 0 件・他の fail 0 件**。
- 実機目視: 不要（テストのみ）。

## 残るリスク（記録のみ）

- `update()` を伴わずテスト冒頭でカウントを確かめる箇所（`test_app_ui_flows.py:249` の `== 0` / `:2290` の `== 1`〔phase 32 完了時点〕・
  `test_dialog_escape_binding.py` のテスト冒頭〔`:77` / `:93` / `:259`〕と subTest 冒頭の `== 0`）は、
  直前のテストが解除予約を残したまま終わると同じ形で赤くなり得る。今回の適用で主な発生源（閉じた後の確認）は待つようになり、観測も無い。
  再び観測されたら、そのテストの冒頭にヘルパ（0）を入れる。

## 完了判定前レビュー（2026-09-24）

- `codex-adversarial-reviewer` = **approve**（指摘なし。静的確認のみ）。
- `deep-reviewer` = **完了可**（high なし・medium 2・low 6。いずれも文書のみ）。**ユーザー確認のうえ反映**:
  - **M1**: `handoff.md` の「数える前に `app.update()` を挟む」は本フェーズの結論と逆 → `wait_for_hook_pause_count` を使う旨へ書き換え（session.md の同趣旨の hint も更新）。
  - **M2**: 本節と `decisions.md` 索引行の refactor_check 結果を記入。
  - **L3〜L6**: codebase_map の置き場の変更理由 / ⑤の例外（chooser 直後の `== 1`）/ 残るリスクへ `escape_binding:77/93/259` を追加 / 起票時点の行番号の注記。
  - 保留: L7（ヘルパのテストが期限切れメッセージの `elapsed=` / `timeout=` を確かめていない。出力はしており実害なし）。
  - 見送り: L8（`keymap_set_history` の `before` が常に 0 で冗長 / ヘルパ引数を `update` と `get_count` に分ける案）。
- 補足（deep-reviewer の確認）: 「再開が大きく遅れる」退行は `test_hook_controller_teardown.py` の `after.assert_called_once_with(0, ...)` が単体で固定するため待機で隠れない。
  「再開が 2 回に分かれる」退行はカウントでは見えず mock の呼び出し回数でのみ捕まる（置き換え前と同条件で、今回弱めてはいない）。

## refactor_check

- **スキップ**（PHASE_BASE `ef2e97d`・`git diff --stat ef2e97d..HEAD -- keyseq/` が空＝判定対象の変更ファイル 0 件。
  変更は tests_ui のみで、テストは判定対象外）。`hook_resume_wait.py` は 21 行・新規テスト 47 行で実装目安内。
