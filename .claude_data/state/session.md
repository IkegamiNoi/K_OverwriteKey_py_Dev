# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-19T01:05:00
phase: `instructions/phase/63_make_only_keys`（phase 63・暫定 46 v0.3 ユーザー確定済・decisions 63）。次採番 = phase 64 / 暫定 47 / decisions 64 / 提案書 25
直前の完了フェーズ = **phase 62**（`decisions_archive/62_special_keys_from_layout_only.md`）
last_commit_location: `claude/idea-49-50-execution-c565e4`（phase 62 完了・phase 63 の task_01〜03）。phase 60・61 = `claude/idea-46-3c4cb6` / phase 57 = `claude/crosshair-selection-frame-f4b464` / phase 58・59 = `claude/physical-device-visual-check-79fcd3`。main へのマージはユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 63（idea_52・押下だけが続けて届くキー）: task_01〜03 実装・検証・レビュー済。task_03 の実機目視待ち → task_04（正本反映）。**
mode: blocked

## last_action
ts: 2026-10-19T01:05:00
who: main
summary: |
  実測（2026-10-18・生のフック）: 無変換 = DOWN vk 0x1A scan 241・変換 = DOWN vk 0x16 scan 242（ext・UP なし）。1 回押す = 押した瞬間 1 回 + 離したとき約 11〜13 ms 間隔の 2 回組 / 押し続ける = 約 0.5 秒後から約 33 ms ごと（21〜46 ms）+ 離したとき 2 回組。
  ユーザー判断: 241 / 242 の表で見分ける・案 B（16 ms 以下の 2 回組 = 離した）・リピートあり（直接置換で別キーに置き換えるため）・名前は extra_scan_codes。暫定 46 v0.3 確定（deep 14 件・Codex 4 件を反映）→ phase 63 起票。タスクの連続実行はユーザー許可済み。
  task_01 = extra_scan_codes（phase 62 で戻した 722a1e9 の当て直し）/ task_02 = domain の表 + application の状態機械 MakeOnlyKeyFilter（単体 22 件）/ task_03 = DelayedCallWorker（application）・hook_controller の分岐・世代つきの予約・開始 / 停止での消去・app.py の組み立て（presentation）。いずれも Codex 実装・reviewer 採用。
verified:
  compile clean / tests 1743 pass / tests_ui 1117 pass / smoke OK

## next_action
- **【ユーザー確認待ち・最優先】task_03 の実機目視**（`instructions/phase/63_make_only_keys/tasks/task_03_hook_integration.md` の「確認」節・JIS 外付けキーボード・jis.json を選ぶ）
  1. キーボードUI で無変換を BackSpace に置き換える → 1 回押すと 1 文字消える / 押し続けると続けて消える / 離すと止まる
  2. 変換を別のキー（例: Enter）に置き換えて押す → IME が切り替わらない / 1 回だけ入る
  3. 無変換を押したまま Shift を押し、無変換を離す → 余計な出力が出ない
  - NG なら、何を押して何が起きたかを聞き、状態機械（`keyseq/application/make_only_keys.py`）の遷移（暫定 46 §3.2）と照らして切り分ける
- 目視 OK なら task_04 を `/task_new` で起票: 暫定 46 §8 の正本反映（key_input.md §7.1 :16-17 の受容の書き換え・§7.2・§7.3・§7.7 / features.md §4.6 の `extra_scan_codes` と :711 の受容の書き換え / codebase_map）・暫定 46 凍結・decisions_archive/63・decisions.md 索引・current.md 完了記載・idea_52 を INDEX_done へ・`/refactor_check`・完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）
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
