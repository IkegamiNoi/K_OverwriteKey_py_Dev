# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-16T14:00:00
phase: **phase 60**（キーの取得中は IME を OFF にする・`instructions/phase/60_ime_off_during_key_capture/phase.md`・主入力 = 暫定 44 v0.4 ユーザー確定済）。次採番 = phase 61 / 暫定 45 / decisions 61 / 提案書 25
直前の完了フェーズ = **phase 59**（`decisions_archive/59_keyboard_ui_left_right_modifiers.md`）
last_commit_location: `claude/idea-46-3c4cb6`（phase 60）。phase 57 = `claude/crosshair-selection-frame-f4b464` / phase 58・59 = `claude/physical-device-visual-check-79fcd3`。main へのマージはユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 60 task_03 実装・検証・レビュー済（コミット済）・ユーザーの実機目視待ち（task_03 の確認 a〜d）。目視 OK 後に task_04（統合確認）。**
mode: active

## last_action
ts: 2026-10-16T14:00:00
who: main
summary: |
  idea_46 から暫定 44 を起票（codex-explorer の監査 → v0.1 → deep-reviewer 修正要〔H1 は Tk の全 HWND が同じ入力コンテキストを共有することを probe で実測し解消〕→ v0.2 → Codex 敵対的 needs-attention → v0.3）。
  ユーザーが §7 の 1〜4 を提案どおり確定（v0.4）。取得中のフック再開を idea_48 に分離。/phase_start で phase 60 を起票（reviewer の整合チェック = 採用・任意指摘 (a) を反映）。
verified:
  文書のみ（コード不変）

## next_action
- `/task_new` で task_01 を起票 → codex-implementer へ委任
- 残件 = idea_47（キーボードUI の取得で F キーが kana 等になる見込み）・idea_48（取得中のフック再開）
- main へのマージはユーザー（phase 57 = `claude/crosshair-selection-frame-f4b464` / phase 58・59 = `claude/physical-device-visual-check-79fcd3`）

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
