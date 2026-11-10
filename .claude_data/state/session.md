# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-11T01:00:00
phase: instructions/phase/75_mac_support（主入力 = 暫定 57 v0.5・ユーザー確定済）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/windows-continuation-23d400`（Mac の worktree `windows-continuation-23d400`・`Operation_check` 3ea433e から ff）。push はユーザー。main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 75 段階 ② task_05・task_05b を Mac で実装・確認済み（reviewer 採用・Mac 起動目視 OK）。Windows の標準検証 4 種待ち（未実施のため完了判定は保留）。次は task_06（probe）。**
mode: implementing
presence: present

## last_action
ts: 2026-11-11T01:00:00
who: main
summary: |
  task_05（macOS で起動）: os_backend/macos/ のスタブ・darwin の分岐・requirements の環境マーカー（keyboard は win32・pyobjc は darwin）・presentation/tk_platform.py（Control→Command・右クリック・accelerator）・契約テストの windows import の分離（M5）。codex-implementer（途中で止まり resume 1 回）・メインが 2 件修正（Option- / キャッシュのテストの patch 先を macos へ）・reviewer 採用。
  task_05b（Tk 9 の長さ）: Tk 9 は Canvas の width/height 既定を '10c'/'7c'・sashwidth を '2.25p' で返す（probe）→ tk_platform.screen_distance（winfo_pixels）で 8 か所を置換。codex-implementer・reviewer 採用。
  Mac の .venv は Homebrew の Python 3.13.18 + python-tk@3.13（Tk 9.1.0）に作り直し（Q1 から変更・decisions.md）。
result_files:
  - keyseq/infrastructure/os_backend/macos/
  - keyseq/presentation/tk_platform.py
  - instructions/phase/75_mac_support/tasks/task_05_macos_startup.md・task_05b_tk9_screen_distance.md
verified:
  mac_compile: clean
  mac_tests: 1920 件・失敗 89・エラー 15・skip 16（Windows 前提のパス約 55・テンキー約 22・スタブ約 15 等。基準線の確定は task_07）
  mac_smoke: pass（stderr の Traceback 0）
  mac_tests_ui: 実行しない（スタブのキー検証で「不明なキー名」のモーダルが出て止まる。task_07 で対処）
  mac_visual: 起動・メニュー・キーボードUI・フック開始のエラー・フル表示の大きさ OK（ユーザー）
  windows: 未実施（標準検証 4 種・tests 1971+新規分 / tests_ui 1270 / smoke）

## next_action
- push（ユーザー）→ Windows で task_05・05b の標準検証 4 種 → 通れば完了判定 → Mac で task_06（probe・Tk 9 の差を含む・暫定 57 の Q1 の文言改訂）
- task_07 で Mac の tests_ui のモーダル対処と `tests_ui/test_compact_sequence_view.py` の sashwidth 4 か所（phase.md 追記済み）
- 別件: ブランチ `claude/gracious-brahmagupta-2e05b1` と `claude/welcome-popup-first-launch-2b70d9` の main へのマージ（ユーザー）

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
