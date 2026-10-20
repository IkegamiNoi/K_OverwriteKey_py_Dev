# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-20T09:00:00
phase: `instructions/phase/63_make_only_keys`（phase 63・暫定 46 v0.5 ユーザー確定済 2026-10-20・decisions 63）。次採番 = phase 64 / 暫定 47 / decisions 64 / 提案書 25 / idea 55
直前の完了フェーズ = **phase 62**（`decisions_archive/62_special_keys_from_layout_only.md`）
last_commit_location: `claude/ime-switch-color-adjust-ac5df9`（暫定 46 v0.5・task_03f）。task_01〜03e = `claude/phase62-trace-file-empty-ddc0c0`（Operation_check へ早送り済み = ff61938）。main へのマージはユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 63（idea_52）: 暫定 46 v0.5（離した直後の押下は押し続けの続き）で task_03f を実装・検証・レビュー済み。ユーザーの実機目視（§6 #6）OK（2026-10-20）。色の最終判断・§9 #7 の判断待ち → task_04。**
mode: waiting_user
presence: present

## last_action
ts: 2026-10-20T08:43:00
who: main
summary: |
  実機目視（v0.4）: 123 で届いたのはリモート実行のため（普通のキー）と切り分け。241/242 の計測で、長押しの途中のフックの詰まり（約 30 ms）による「離した」の取り違え → 案 A と連鎖してリピートのように出続ける、を特定。IME の切り替えは未特定（ユーザーが操作を後で伝える）。
  暫定 46 v0.5 確定（ce89b3a）: 「長押しの途中の 2 回組」「案 A の片方」の「離した」から 16 ms 超〜60 ms 以内の押下は続き・続きで「押した」の時刻を置き直す。Codex 敵対的 2 回（high 2・medium 1）反映。decisions 記録・task_03f 起票。
  task_03f（application 限定・codex-implementer）: `CONTINUATION_WINDOW_S`・`released_continuable`・続きの分岐・実の up で消去・テスト 10 件 + 結合 1 件。既存 1 件の期待値が「押した」→「続き」（注 5 どおり・テスト名を直した）。reviewer 完了可。
result_files:
  - keyseq/application/make_only_keys.py
  - tests/test_make_only_keys.py
  - tests/test_make_only_keys_integration.py
verified:
  compile clean / tests 1759 pass / tests_ui 1122 pass / smoke OK

## next_action
- **【ユーザー・実機目視（暫定 46 §6 #6）】** Operation_check を本ブランチ（`claude/ime-switch-color-adjust-ac5df9`）へ早送り → `.venv\Scripts\python.exe main.py`（`phase62.json` の `debug_jis_special_key_events` は true のまま）→ jis.json・無変換 / 変換 → BackSpace・**241 / 242 で届く環境（リモートでない）**で: 1 回押す / 2 秒以上の長押しを 3 回以上（途中で消え続けない・`released` の後に `down accept` が続かない）/ 約 0.1 秒の連打（回数どおり）/ IME が切り替わらない
- 目視の後: 色の最終判断（灰色がかった緑のまま / 緑に戻す＝暫定 46 の改訂）→ IME の切り替えの操作をユーザーから聞いて §9 #7 を判断 → task_04（正本反映〔§8〕・暫定 46 の凍結・decisions_archive/63・decisions.md の phase 63 節を索引へ・idea_52 を INDEX_done へ・`/refactor_check`・完了判定前レビュー〔deep-reviewer + codex-adversarial-reviewer〕）
- 別件: external_keyboard_layouts のパスが入れ子に増える件は idea_13 に追記済み（別セッション・ブランチ `claude/lucid-wiles-a6c8d3`・未マージ）
- main へのマージはユーザー

## blockers
- **【回避中】Codex の書き込み実行（2026-10-14 18:24 以降の不具合）**: Codex の更新（0.162.x・cua_node runtime a9ba…・17:22〜18:25）以降、`~/.codex/.sandbox/sandbox.2026-10-14.log` に `setup refresh had errors`（node_repl.exe の ACL 更新が「別のプロセスが使用中」で失敗）。読み取り専用（レビュー・調査）は通る。再起動では直らない。**2026-10-15 ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `unelevated` に変更 → 常駐の broker・app-server を止めて再実行で書き込み可**。Codex の更新で直ったら `elevated` に戻す（ユーザー操作）。設定を変えたら常駐の broker（`app-server-broker.mjs`）と app-server を止めないと効かない

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **素の `python` を Bash で呼ばない**（必ず `..\..\..\.venv\Scripts\python.exe`）。Bash の heredoc の前に `cat > file` を単独で書かない（stdin 待ちでハングする）。
- **Codex は互換の工夫・テストの期待値の推測を足すことがある**。差分を直読みしてから verifier / reviewer へ。Codex は LF を混ぜることがある（コミットは git が正規化）。
- 画面の枠（phase 56・57）の地図 = `codebase_map.md`「画面の枠（phase 56・57）」。振り分けは `suppress_keys` 1 本（`screen_grid_session._publish_snapshot`）/ 操作キーは `domain/screen_grid/ops.py`。
- **【罠・phase 57 で実証】Windows の Tk で位置の反映の保留中に `wm_attributes("-topmost", True)` を呼ぶと窓が `0,0` へ戻る**（`geometry` の直後に `update_idletasks()`）。**Tk の測り直しは after_idle だと配置の計算より先に走ることがある**（測る前に `update_idletasks()`）・`<Configure>` で configure し返すと無限ループになり得る（値が変わったときだけ・結び付けは 1 つ）。
- **プロセスは pyautogui の import でシステム DPI 対応**（`.venv/Lib/site-packages/pyautogui/_pyautogui_win.py:17`）。検証は本番の起動経路で
- `tests_ui/test_action_dialog_control.py` の 2 件は Tk ルートを作るモジュールの後に同じプロセスで走らせると落ちる（既存の実行順依存・current.md「テスト負債」）。
- 過去の判断は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜41）の条項を実装の根拠に引かない。
- **【Codex のプロセス・2026-10-14 実測】** companion は作業フォルダ（cwd）ごとに `app-server-broker.mjs serve` を常駐させ、その下の `codex app-server`（+ sandbox の runner・node）は**呼び出し後も残る（再利用のための設計）**。
  worktree ごとに 1 組ずつ増えるため、worktree を多く使うと codex.exe が溜まる。Codex デスクトップアプリ（ChatGPT.exe）配下の codex.exe は別物。2026-10-14 の不調はプロセスの溜まりではなく Codex の更新が原因（blockers 参照・再起動では直らない）
- **【罠・phase 58 task_02 で実測】ttk.LabelFrame の `labelwidget` に既定の ttk.Label を使うと枠の要求高さが 4px 増える**（vista・58 → 62px。矢印の字形とは無関係）。`style="TLabelframe.Label"` なら元と同じ 58px・同じ見た目
