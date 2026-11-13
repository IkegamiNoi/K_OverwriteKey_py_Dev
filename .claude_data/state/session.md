# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-13T18:30:00
phase: instructions/phase/75_mac_support（主入力 = 暫定 57 v0.7・ユーザー確定済）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/task-08-progression-2214c7`（Windows の worktree `task-08-progression-2214c7`・task_08 のコミット）。Mac の worktree は `claude/task-06-progression-a047bd`。push はユーザー。main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 75 段階 ③。task_08（フックのディスパッチャ・暫定 57 §5.1.1）完了（Windows 検証 pass・reviewer 採用・Windows 目視 OK）。task_08b（CGEventTap・受信の vk の表・CapsLock は素通し）を起票済み。次は task_08b の実装を **Mac で**行う（2026-11-13 ユーザー判断: Quartz を実物で検証し、probe の実測・目視と同じ場で回すため）。**
mode: implementing

## last_action
ts: 2026-11-13T18:00:00
who: main
summary: |
  実施: task_08 = `presentation/hook_dispatcher.py`（即時版 / キュー版・上限 64・期限 1 秒・世代・優先）・`OsBackend.queued_hook_dispatch`（macOS True）・HookController（稼働番号・切替の予約番号・過負荷の印と 1 回の停止・`hook.overload.*` の警告・stop_hook で invalidate）・KeyCaptureHook（dispatch 注入・素通し中の集合）・App の配線。infrastructure（os_backend の項目 1 つ）と presentation を跨ぐ。codex-delegating-implementer（Sol + Luna サブエージェント使用）。新契約で壊れる既存テスト（tests_ui 3・tests 1）の最小追従をメイン判断で許可。
  reviewer: 採用（参考 1 = 解除と競合した素通し中の残留 → メインで `_handle is not None` のときだけ追加に修正・対象テスト再実行 OK / 参考 2 = 排出中のモーダルで排出が止まる → 08b の Mac 実機で確認 / 参考 3 = 予約番号の加算の競合は実害小 / hook_controller.py 404 → 459 行・分割はしていない〔報告のみ〕）。
  codebase_map の hook_controller・key_capture_hook・hook_dispatcher・os_backend 節を追従（メイン）。
  完了判定: Windows の検証 pass・reviewer 採用・Windows 目視 OK（ユーザー）→ task_08 完了。
result_files:
  - keyseq/presentation/hook_dispatcher.py（新規）・app.py・controllers/hook_controller.py・key_capture_hook.py
  - keyseq/infrastructure/os_backend/contracts.py・windows/backend.py・macos/backend.py
  - keyseq/shared/i18n/locales/ja.json・en.json
  - tests/test_hook_dispatcher.py（新規）・test_hook_coordinator.py・test_key_capture_hook.py・test_os_backend_contracts.py・test_call_link_lifecycle.py
  - tests_ui/test_app_ime_shutdown.py・test_hook_controller_reserved_actions.py・test_sequence_control_review_fixes.py
  - instructions/common/codebase_map.md
verified:
  compile: clean
  tests: pass 2022（失敗 0・エラー 0・skip 7・+25）
  tests_ui: pass 1271（失敗 0・エラー 0）
  smoke: pass
  visual_windows: OK（ユーザー）

## next_action
- 前提（ユーザー作業）: Windows のブランチ `claude/task-08-progression-2214c7` を push → Mac の worktree（`claude/task-06-progression-a047bd`）へ取り込む（task_08 と 08b の起票が入っていること = `git log` に `task_08b(phase 75): 起票` があるか確認）
- 次（**Mac で**）: まず task_08 の取り込み後の退行確認（tests が基準線〔失敗 6・エラー 10〕から増えない・smoke pass。tests_ui は通しで走らせない）→ task_08b の実装（`instructions/phase/75_mac_support/tasks/task_08b_macos_event_tap.md`・codex 実装 → verifier〔Mac の `../../../.venv/bin/python` で tests・smoke・対象モジュール〕→ reviewer）→ probe の実測（暫定 57 §4.1 へ追記）→ 目視 ①〜⑥ → 最後に Windows で tests・smoke を 1 回（08b は `macos/` の中だけなので影響確認のみ）
- task_08 のキュー版の実機確認（reviewer 参考 2 = 排出中のモーダル）は task_09 の目視でまとめて
- `test_keymap_list_operations` の合成マウスイベントの 2 件は要調査（task_09 で）
- task_09 でキーボードUIの右クリックによる割り当てのクリアを目視（task_05c の残り）
- JIS の実測（§5.3.1 の文書値の確定）は JIS キーボードを用意できたとき
- Mac で tests_ui を流すときは `mac_test_baseline.md` の手順（モジュールごと・4 モジュール除外）

## blockers
- **Mac で tests_ui を通しで走らせない**（task_08・09 まではスタブがキー検証できずモーダルで止まる。verifier にも明記）。Mac の python は `../../../.venv/bin/python`
- **【回避中】Codex の書き込み実行（2026-10-14 18:24 以降の不具合）**: `~/.codex/.sandbox/sandbox.2026-10-14.log` に `setup refresh had errors`（node_repl.exe の ACL 更新が失敗）。**2026-10-15 ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `unelevated` に変更 → 常駐の broker・app-server を止めて再実行で書き込み可**。Codex の更新で直ったら `elevated` に戻す（ユーザー操作）。設定を変えたら常駐の broker（`app-server-broker.mjs`）と app-server を止めないと効かない

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **画面の文言（phase 72 以降）**: 新しい文言は `keyseq/shared/i18n/locales/ja.json` と `en.json` の両方にキーを足し、ソースに日本語を書かない（静的テスト）。`tr` はモジュール定数・import 時に評価しない。`App(` を作る / 文言を assert する新しいテストモジュールは import 直後に `fix_language("ja")`。英語は `ui_terms.md` §2・§3（E1〜E7）に従う。
- **phase 73**: 報告された不具合のうち、キー名の記号表記は別セッションの提案カードに出してある（本フェーズ外）。tests_ui の窓の大きさのテスト（`test_compact_window.py:298`・`test_pane_window_width_persistence.py:236,275` の `pending`）が負荷で落ちることがある。**tests_ui の App() は worktree の `config/config.json`（ユーザーの手元の設定・gitignore）を読む**ので結果が手元の設定に左右される（task_05 の Welcome を出さない入口で考える）。Codex は python を実行できずテスト修正が手探りになる → 失敗はメインがトレースを読んで原因を絞ってから委任する。
- **phase 71**: タスクバーのアイコンは AppUserModelID（`main.py`）が無いと出ない。`App()` を直接作る tests_ui / smoke では設定されない。
- **`__version__`** はユーザーが直接またはユーザーの指示でだけ変更する（Claude が独断で上げない）。
- **Codex は Python で既存ファイルを編集しようとして失敗することがある** → 依頼文に「apply_patch で編集・Python を使わない」と書く（phase 71）。
- **素の `python` を Bash で呼ばない**（必ず `..\..\..\.venv\Scripts\python.exe`）。Bash の heredoc の前に `cat > file` を単独で書かない（stdin 待ちでハングする）。
- **Codex は互換の工夫・テストの期待値の推測を足すことがある**。差分を直読みしてから verifier / reviewer へ。Codex は LF を混ぜることがある（コミットは git が正規化）。
- カーソルグリッドの地図 = `codebase_map.md`「カーソルグリッド（phase 56・57）」。
- **【罠・phase 57】Windows の Tk で位置の反映の保留中に `wm_attributes("-topmost", True)` を呼ぶと窓が `0,0` へ戻る**（`geometry` の直後に `update_idletasks()`）。Tk の測り直しは after_idle だと配置の計算より先に走ることがある・`<Configure>` で configure し返すと無限ループになり得る。
- **プロセスは pyautogui の import でシステム DPI 対応**。検証は本番の起動経路で
- `tests_ui/test_action_dialog_control.py` の 2 件は Tk ルートを作るモジュールの後に同じプロセスで走らせると落ちる（既存の実行順依存・current.md「テスト負債」）。
- 過去の判断は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜46・48〜55）の条項を実装の根拠に引かない。
- **【Codex のプロセス】** companion は作業フォルダごとに `app-server-broker.mjs serve` を常駐させ、`codex app-server` は呼び出し後も残る。worktree を多く使うと codex.exe が溜まる。
- **【罠・phase 58】ttk.LabelFrame の `labelwidget` に既定の ttk.Label を使うと枠の要求高さが 4px 増える**（`style="TLabelframe.Label"` なら同じ）
