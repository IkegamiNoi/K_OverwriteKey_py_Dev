# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-01T13:38:00
phase: instructions/phase/72_multilingual_ui（**アクティブ** = 画面の文言の多言語対応・暫定 55 v0.3 ユーザー確定済・decisions 72）。次採番 = phase 73 / 暫定 56 / decisions 73 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 71**（タスクバーのアイコン・`decisions_archive/71_taskbar_status_icon.md`）
last_commit_location: `claude/multilingual-support-ff44eb`（phase 72）。phase 71 一式は `claude/taskbar-app-status-indicator-f73d28` にもあり、main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 72 進行中（task_06 完了・task_07 はユーザー判断待ち）。** 画面の文言はすべてキー化済み（全層・ja.json 約 905 キー）。次は英語の表記の規則・用語・アクションの種類の表示名の確定（暫定 55 §8 Q4〜Q6）→ 英訳。
mode: blocked
presence: away（戻る予定 未定）

## last_action
ts: 2026-11-01T13:38:00
who: main
summary: |
  task_06（キー移行 4 = application / domain / infrastructure の画面に出る文）を codex-delegating-implementer（サブエージェント 3）で実装 → ja.json に 201 キー・ログ専用 31 か所は残す（reviewer が呼び出し元まで確認）・例外は作る時点で tr・旧トリガーセットの既定名は作成時の tr。reviewer 修正して採用 → 必須 1 件（sequence_control の呼び出し先ラベルの組み立て）をメインで修正。コミット 7404ae3。
  task_07 の案を暫定 55 §8 に Q4（英語の表記の規則 E1〜E6）/ Q5（用語表 A1〜A22 の英語）/ Q6（アクションの種類の表示名と表示する場所）として追記（未確定・未コミット → 本ターンでコミット）。
  /away（戻る予定 未定）のため、ユーザー判断の手前で終了処理。
result_files:
  - keyseq/application・domain・infrastructure の 34 ファイル / keyseq/shared/i18n/locales/ja.json / tests の 4 ファイル / instructions/common/codebase_map.md
  - instructions/history/55_multilingual_ui.md（§8 Q4〜Q6 の案）
verified:
  compile: pass
  tests: pass（1891・skip 7）
  tests_ui: pass（1227）
  smoke: pass

## next_action
- **【ユーザー確認待ち】暫定 55 §8 の Q4〜Q6（`instructions/history/55_multilingual_ui.md`）**。それぞれ推奨案つき:
  - Q4 英語の表記の規則 E1〜E6（推奨 = 文頭だけ大文字〔Windows 11 の作法〕・「…」は D3 と同じ・ラベルに句点なし・数は「Files: {n}」形式・Please を付けない）
  - Q5 用語の英語（主な判断点 = A1 構成セット → **Profile**〔別案 Config set〕/ A17 退避 → **Archive** / A10 記録・取得 → Record / Pick）
  - Q6 アクションの種類の表示名（ホットキー / 文字入力 / マウスのクリック / マウスのスクロール / 押下・解放 / 制御 / ファイルの行 ↔ Hotkey / Type text / Mouse click / Mouse scroll / Press / release / Control / File line）と表示する場所（推奨 = 種類のコンボボックスとマウスのボタン〔left / right / middle → 左 / 右 / 中〕は表示名・出力シーケンスの一覧の行頭 `[hotkey]` は内部名のまま〔`domain/config.py:476-478`〕。一覧も表示名にすると日本語の見た目が変わる）
- 確定したら: 暫定 55 を v0.4 へ（§2 へ移す）→ task_07 完了 → task_08（en.json の全キーの英訳・表示名の結線・test_i18n を全キーの検査に戻す）を起票 → codex-delegating-implementer → verifier + reviewer
- 以降 task_09（help_en.json）〜 task_12（実機目視・正本反映）。main へのマージはユーザー（PR は作らない）

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
