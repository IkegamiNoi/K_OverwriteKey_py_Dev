# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-01T13:20:00
phase: instructions/phase/72_multilingual_ui（**アクティブ** = 画面の文言の多言語対応・暫定 55 v0.3 ユーザー確定済・decisions 72）。次採番 = phase 73 / 暫定 56 / decisions 73 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 71**（タスクバーのアイコン・`decisions_archive/71_taskbar_status_icon.md`）
last_commit_location: `claude/multilingual-support-ff44eb`（phase 72）。phase 71 一式は `claude/taskbar-app-status-indicator-f73d28` にもあり、main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 72 進行中（task_02 完了・次 task_03）。** i18n 基盤（task_01）と、表示文字列を内部値に使う箇所の内部コード化（task_02）まで済み。既存の文言のキー化は task_03〜06。
mode: implementing
presence: away（戻る予定 未定）

## last_action
ts: 2026-11-01T13:20:00
who: main
summary: |
  task_02（表示文字列の内部値の分離）を codex-implementer（3 回に分けて実行）で実装。presentation 6 ファイル: key_hold（対象・押す / 離す・ボタン）/ system の op・範囲外 / mouse_scroll の向き / キーマップの追加の種類（new / load / paste）/ 「（未選択）」の判定を、呼び出し時に作るコード → ラベルの表で持ちコードで判定する形へ。旧名 SYSTEM_OPERATIONS 等は 0 件。
  メインで修正: 行の種類の列に内部コードが出る退行（`_kind_row_labels`）/ ステータス欄の「（未選択）」が空になる退行（`sel_text`）/ 新テストの入力エラーの modal で tests_ui が止まった件（入力を足し showerror を patch・止まったプロセス 2 本だけ Stop-Process）/ レビュー指摘でボタンの表を `_button_labels()` へ・「（未選択）」の表示のテストを test_app_ui_flows に追加。
  reviewer 採用（任意 1 = 反映 / テスト補強の推奨 2 = 反映・3 = 未反映〔edit モードのループ除外・load 経路・題名の差し替え等。既存テストで間接的に押さえ済み〕）。
result_files:
  - keyseq/presentation/dialogs/{action_key_hold_fields,action_control_fields,action_mouse_scroll_fields,action_dialog}.py
  - keyseq/presentation/controllers/keymap_panel/keymap_add_flow.py / controllers/trigger_panel/trigger_panel_controller.py
  - tests_ui/test_internal_value_codes.py（新規）/ tests_ui/test_task06_keymap_management_ui.py / tests_ui/test_app_ui_flows.py
  - instructions/phase/72_multilingual_ui/tasks/task_02_internal_values.md / instructions/phase/current.md
verified:
  compile: pass
  tests: pass（1888・skip 7）
  tests_ui: pass（1222〔レビュー後の小修正の前〕・修正後に該当 3 ファイル 126 件 pass）
  smoke: pass

## next_action
- task_03（キー移行 1 = 主画面・メニュー・views・controllers・モジュール定数の文言表 `*_text.py` 等）を `/task_new` で `instructions/phase/72_multilingual_ui/tasks/task_03_keys_main_views.md` に起票 → codex-delegating-implementer → verifier（tests / tests_ui 全体 / smoke）→ reviewer。日本語の文言は 1 文字も変えない・キーは `ja.json` に追加・`en.json` は task_08（ただし en.json の欠けはフォールバックで ja が出るため本 task ではキーを足さない）。task_02 で作ったラベルの関数も対象ファイルなら `tr` へ
- 以降 phase.md の順に task_04〜12。task_07（英語の用語・アクションの種類の表示名）と task_12（実機目視）はユーザー判断が要る
- main へのマージはユーザー（PR は作らない）

## blockers
- **【回避中】Codex の書き込み実行（2026-10-14 18:24 以降の不具合）**: Codex の更新（0.162.x・cua_node runtime a9ba…・17:22〜18:25）以降、`~/.codex/.sandbox/sandbox.2026-10-14.log` に `setup refresh had errors`（node_repl.exe の ACL 更新が「別のプロセスが使用中」で失敗）。読み取り専用（レビュー・調査）は通る。再起動では直らない。**2026-10-15 ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `unelevated` に変更 → 常駐の broker・app-server を止めて再実行で書き込み可**。Codex の更新で直ったら `elevated` に戻す（ユーザー操作）。設定を変えたら常駐の broker（`app-server-broker.mjs`）と app-server を止めないと効かない

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **phase 72**: `App(` を作る / 画面の文言を assert する新しいテストモジュールは import 直後に `fix_language("ja")` を書く（無いと `ui_language` 未設定の環境で英語になり落ちる・静的テストが検出）。`tr` はモジュール定数・import 時に評価しない。
- **phase 71**: タスクバーのアイコンは AppUserModelID（`main.py`）が無いと出ない。`App()` を直接作る tests_ui / smoke では設定されない。保留 2 件は current.md「別タスク化候補」。
- **`__version__`** はユーザーが直接またはユーザーの指示でだけ変更する（Claude が独断で上げない）。
- **Codex は Python で既存ファイルを編集しようとして失敗することがある** → 依頼文に「apply_patch で編集・Python を使わない」と書く（phase 71）。
- **素の `python` を Bash で呼ばない**（必ず `..\..\..\.venv\Scripts\python.exe`）。Bash の heredoc の前に `cat > file` を単独で書かない（stdin 待ちでハングする）。
- **Codex は互換の工夫・テストの期待値の推測を足すことがある**。差分を直読みしてから verifier / reviewer へ。Codex は LF を混ぜることがある（コミットは git が正規化）。
- カーソルグリッド（旧称「画面の枠」・phase 56・57）の地図 = `codebase_map.md`「カーソルグリッド（phase 56・57）」。振り分けは `suppress_keys` 1 本（`screen_grid_session._publish_snapshot`）/ 操作キーは `domain/screen_grid/ops.py`。
- **【罠・phase 57 で実証】Windows の Tk で位置の反映の保留中に `wm_attributes("-topmost", True)` を呼ぶと窓が `0,0` へ戻る**（`geometry` の直後に `update_idletasks()`）。**Tk の測り直しは after_idle だと配置の計算より先に走ることがある**（測る前に `update_idletasks()`）・`<Configure>` で configure し返すと無限ループになり得る（値が変わったときだけ・結び付けは 1 つ）。
- **プロセスは pyautogui の import でシステム DPI 対応**（`.venv/Lib/site-packages/pyautogui/_pyautogui_win.py:17`）。検証は本番の起動経路で
- `tests_ui/test_action_dialog_control.py` の 2 件は Tk ルートを作るモジュールの後に同じプロセスで走らせると落ちる（既存の実行順依存・current.md「テスト負債」）。
- 過去の判断は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜41）の条項を実装の根拠に引かない。
- **【Codex のプロセス・2026-10-14 実測】** companion は作業フォルダ（cwd）ごとに `app-server-broker.mjs serve` を常駐させ、その下の `codex app-server`（+ sandbox の runner・node）は**呼び出し後も残る（再利用のための設計）**。
  worktree ごとに 1 組ずつ増えるため、worktree を多く使うと codex.exe が溜まる。Codex デスクトップアプリ（ChatGPT.exe）配下の codex.exe は別物。2026-10-14 の不調はプロセスの溜まりではなく Codex の更新が原因（blockers 参照・再起動では直らない）
- **【罠・phase 58 task_02 で実測】ttk.LabelFrame の `labelwidget` に既定の ttk.Label を使うと枠の要求高さが 4px 増える**（vista・58 → 62px。矢印の字形とは無関係）。`style="TLabelframe.Label"` なら元と同じ 58px・同じ見た目
