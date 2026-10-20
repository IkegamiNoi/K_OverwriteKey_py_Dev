# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-21T15:30:00
phase: instructions/phase/65_layout_snapshot_for_hook（進行中・暫定仕様先行・暫定 48 v0.3 確定 / decisions 65）。次採番 = phase 66 / 暫定 49 / decisions 66 / 提案書 25 / idea 55
直前の完了フェーズ = **phase 64**（`decisions_archive/64_external_layout_path_base.md`）
last_commit_location: `claude/external-key-layout-persistence-a9eaa2`。main へのマージはユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 65 進行中（受け取りと送信が同じレイアウトの写しを使う・idea_51）。task_01・task_02 済 → task_03 の実機目視待ち。**
mode: pending_review
presence: present

## last_action
ts: 2026-10-21T09:30:00
who: main
summary: |
  task_02（押したままのキーを押したときの送り方で送る）: Codex の利用上限の回復後に codex-implementer で再実行（ユーザー判断 案 A）。input_gateway に KeySend / resolve_send / press_send / release_send / identity_of・held_inputs が送り方を記録し離し・一時的な離し・押し直し・リピート・補償に使う・key_repeat の callback を send(identity, key) に。infrastructure + application（application は KeySend を import しない）。
  reviewer 完了可（低 1 を修正）・verifier 1 回目は既存テスト 11 件の期待のずれ（実装は正しい）→ テスト修正 → 全 pass。
result_files:
  - keyseq/infrastructure/input_gateway.py
  - keyseq/application/held_inputs.py
  - keyseq/application/key_repeat.py
  - tests/test_held_inputs.py
  - tests/test_held_inputs_repeat.py
  - tests/test_key_repeat.py
  - tests/test_input_gateway_send.py
  - tests/test_action_executor_key_hold.py
  - tests/test_sequence_runner_key_hold.py
  - tests_ui/test_key_hold_presentation.py
  - tests_ui/test_task06_keymap_management_ui.py
verified:
  compile: clean
  tests: pass 1778（skipped 7）
  tests_ui: pass 1122
  smoke: pass

## next_action
- ユーザーの実機目視（暫定 48 §7-7）: ① jis.json を選んだまま JSON の `muhenkan` の `scan_code` を書き換え → 選び直す（同じ jis.json をドロップダウンで選び直す / 別のレイアウトを経由して戻す）・再起動するまではキーボードUI の表示も受け取りも変わらず、選び直した後は変わる ② jis.json の `muhenkan` を key_hold で押したまま別のレイアウトへ選び直すと離れる
- 目視 OK 後 task_03 を `/task_new` で起票して実施（正本反映〔暫定 48 §9〕・暫定 48 凍結・decisions_archive/65・decisions.md 索引・current.md 完了・idea_51 を INDEX_done へ・/refactor_check・完了判定前レビュー〔deep-reviewer + codex-adversarial-reviewer〕）

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
