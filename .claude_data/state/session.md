# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-04T12:00:00
phase: なし（アクティブなフェーズなし）。次採番 = phase 73 / 暫定 56 / decisions 73 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 72**（画面の文言の多言語対応・`decisions_archive/72_multilingual_ui.md`）
last_commit_location: `claude/ui-text-length-english-style-f5ba4e`（phase 72 task_11b〜12）。それ以前の phase 72 は `claude/multilingual-support-ff44eb`、phase 71 一式は `claude/taskbar-app-status-indicator-f73d28`。main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 72 完了（2026-11-04）。** 日英の切り替え（メニュー「Language」・次回起動から反映・「今すぐ再起動」）・全層の文言のキー化・英語の表記 E1〜E7・一覧の行頭の印の統一まで入り、正本反映・暫定 55 凍結・refactor_check 不要。次フェーズはユーザー判断（予定 = Mac 対応）。
mode: completed

## last_action
ts: 2026-11-04T12:00:00
who: main
summary: |
  ユーザー報告: task_11d の実機目視 OK → task_12（正本反映）を実施。features §4.6「言語」「一覧の表示形式」「ヘルプの窓」/ data_schema §5.4 ui_language / ui_terms §1〜§3（多言語の扱い・英語の列・表示名・E1〜E7）/ architecture §3.2 shared / codebase_map「画面の文言の多言語対応」。暫定 55 凍結・decisions_archive/72・current.md 完了記載。
  完了判定前レビュー: Codex 敵対的 needs-attention 1・deep-reviewer 修正して完了可 11 件 → ユーザー = 推奨どおり反映（保留 1 = 一覧に無い言語が保存されているときの比較）。refactor_check = 不要（境界 2 件を別タスク化候補へ）。
result_files:
  - instructions/common/spec_detail/{features,data_schema,ui_terms,architecture}.md / instructions/common/codebase_map.md
  - instructions/history/55_multilingual_ui.md / instructions/phase/current.md / instructions/phase/72_multilingual_ui/phase.md
  - .claude_data/state/decisions.md / .claude_data/state/decisions_archive/72_multilingual_ui.md
verified:
  compile: pass（HEAD 18cf3f7・以後は文書のみ）
  tests: pass（1909・skip 7）
  tests_ui: pass（1238）
  smoke: pass

## next_action
- 次フェーズはユーザー判断（`/phase_start`。予定 = Mac 対応 / 3 言語目以降は idea_56）
- main へのマージはユーザー（PR は作らない）

## blockers
- **【回避中】Codex の書き込み実行（2026-10-14 18:24 以降の不具合）**: `~/.codex/.sandbox/sandbox.2026-10-14.log` に `setup refresh had errors`（node_repl.exe の ACL 更新が失敗）。**2026-10-15 ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `unelevated` に変更 → 常駐の broker・app-server を止めて再実行で書き込み可**。Codex の更新で直ったら `elevated` に戻す（ユーザー操作）。設定を変えたら常駐の broker（`app-server-broker.mjs`）と app-server を止めないと効かない

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **画面の文言（phase 72 以降）**: 新しい文言は `keyseq/shared/i18n/locales/ja.json` と `en.json` の両方にキーを足し、ソースに日本語を書かない（静的テスト）。`tr` はモジュール定数・import 時に評価しない。`App(` を作る / 文言を assert する新しいテストモジュールは import 直後に `fix_language("ja")`。英語は `ui_terms.md` §2・§3（E1〜E7）に従う。
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
