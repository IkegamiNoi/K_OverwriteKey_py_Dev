# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-18T15:00:00
phase: `instructions/phase/62_special_keys_from_layout_only`（phase 62・暫定 45 v0.3 ユーザー確定済・decisions 62）。次採番 = phase 63 / 暫定 46 / decisions 63 / 提案書 25
直前の完了フェーズ = **phase 61**（`decisions_archive/61_keyboard_ui_vk_to_scan_code.md`）
last_commit_location: `claude/idea-49-50-execution-c565e4`（phase 62 の task_01〜03）。phase 60・61 = `claude/idea-46-3c4cb6` / phase 57 = `claude/crosshair-selection-frame-f4b464` / phase 58・59 = `claude/physical-device-visual-check-79fcd3`。main へのマージはユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 62（idea_49）: task_01〜03 済。実機目視の 1 で「半角/全角」「かな」OK・「変換」「無変換」NG（フックに走査コード 0 → keyboard が -VK を渡す疑い・未確認）。確認用スクリプトでの実測待ち。**
mode: blocked

## last_action
ts: 2026-10-18T18:30:00
who: main
summary: |
  ユーザー判断（2026-10-18）: 受け取り・送信ともレイアウトの scan_code・既知の表を削除・後方互換不要・レイアウトが変わる前に離す = 案 B（案 A は idea_51）。暫定 45 v0.3 確定 → phase 62 起票。
  task_01 = フック・画面の枠の編集の窓の名前をレイアウトだけで引く（presentation）。
  task_02 = 送信・検査・同じキーの判定を テンキー→拡張→keyboard→レイアウト に一本化し、レイアウトのキーは SendInput の走査コードで送る（今まで muhenkan は送れていなかった）・domain の既知の表を削除（domain・presentation・infrastructure。infrastructure は関数の注入のみで presentation を import しない）。
  task_03 = レイアウトの読み直し・選ぶ id の変更の前に held_inputs.release_all（presentation）。
  いずれも Codex（codex-implementer）実装・reviewer 採用・tests のスタブ / 期待値の不備 2 件をメインが修正。タスクの連続実行はユーザー許可済み。
result_files:
  - keyseq/domain/key_identifiers.py / keyseq/infrastructure/input_gateway.py / keyseq/presentation/{app.py,keyboard_layouts.py,controllers/layout_controller.py}
  - tests/test_input_gateway_send.py / tests/test_keyboard_layout_files.py / tests/test_layout_controller_scan_code.py（新規）/ tests/test_key_identifiers.py（削除）
  - instructions/history/45_special_keys_from_layout_only.md / instructions/phase/62_special_keys_from_layout_only/ / instructions/backlog/idea_51_layout_snapshot_for_hook.md
verified:
  compile clean / tests 1706 pass（task_03 の修正後に対象モジュール 13 件 OK）/ tests_ui 1111 pass / smoke OK

## next_action
- **【ユーザー確認待ち・最優先】「変換」「無変換」が受け取りで効かない件の実測**（実機目視 1 で 半角/全角・かな OK / 変換・無変換 NG）
  - 依頼: アプリを止めた状態で `..\..\..\.venv\Scripts\python.exe .claude_data\state\probe_hook_keys.py`（フックの down の name・scan_code・is_keypad を 20 秒表示・抑止しない）を実行し、無変換・変換・半角/全角・かな を 1 回ずつ押して出力を貼ってもらう（スクリプトは確認後に削除する一時ファイル）
  - 見立て（未確認）: 今回の変更による退行ではない（jis.json 選択時の受け取りの値は変更前と同じ 123 / 121）。MS-IME の設定で無変換 = `VK_IME_OFF`（0x1A）・変換 = `VK_IME_ON`（0x16）になり（phase 61 の Tk での実測）、フックに走査コード 0 で届くと keyboard が `scan_code or -vk`（`.venv/Lib/site-packages/keyboard/_winkeyboard.py:529`）で -26 / -22 を渡し、jis.json の 123 / 121 と一致しない
  - 結果が -26 / -22 なら: 仕様フラグ（暫定 45 の前提の誤り = 走査コードで物理キーが分からないキーがある）としてユーザーへ報告し、対処を決める。案（下調べのみ・未判断）:
    - 案 1（推奨候補）: 暫定 45 の範囲外として受容し idea_50 と合わせて別 idea へ（IME の設定に依存する VK しか来ないため、レイアウトの走査コードでは決められない）
    - 案 2: レイアウトの `scan_code` に負の値（-26 / -22 = keyboard の -VK）を書けるようにして jis.json に別 id の行を足す（受け取りだけ。IME の設定に依存・送信は 1〜255 の制限のまま）
    - 案 3: VK_IME_OFF / ON を `muhenkan` / `henkan` へ写す表をアプリに持つ（既知の表の削除〔§2〕と矛盾。不採用候補）
  - 結果が 123 / 121 なら: 別の原因（`input_router` / キーマップの照合 等）を切り分ける
- 残りの実機目視（task_03 の確認節: JIS キーボード・jis.json で 無変換のトリガー / 出力の `muhenkan`・`zenkaku_hankaku` が物理キーと同じ動き / 任意で US TKL での検査エラー）
- 目視 OK なら task_04 を `/task_new` で起票: 暫定 45 §9 の正本反映（key_input.md §7.1/§7.4/§7.7/§7.8・features.md §4.6・codebase_map）・暫定 45 凍結・decisions_archive/62・decisions.md 索引・current.md 完了記載・idea_49 を INDEX_done へ・`/refactor_check`・完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）
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
