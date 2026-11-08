# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-09T06:00:00
phase: instructions/phase/73_welcome_first_launch（主入力 = 暫定 56 v0.4・ユーザー確定済）。次採番 = phase 74 / 暫定 57 / decisions 74 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 72**（画面の文言の多言語対応・`decisions_archive/72_multilingual_ui.md`）
last_commit_location: `claude/welcome-popup-first-launch-2b70d9`（phase 73 起票・task_01）。main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 73（初回起動の Welcome とサンプルの作り直し）実装中。** task_01〜07 完了（実装は全部入った）・次は task_08（統合確認）→ task_09（実機目視・正本反映）。
mode: implementing

## last_action
ts: 2026-11-09T06:00:00
who: main
summary: |
  task_07 完了: ヘルプのメニューに「Welcome を表示」（`open_welcome_again`: フックの停止・再開を try/finally・窓は reopen=True〔配列と始め方なし・サンプル設定の案内・閉じる〕・ヘルプは open_for_dialog・言語が変わったら set_ui_language〔再起動の知らせ〕・全体の言語は変えない）。
  実装 = codex-implementer（Luna high）。reviewer = 修正要（案内の一文にメニュー名「ファイル」を入れる・重複 import）→ メインが修正。テスト 2 か所（open_welcome_again の窓の差し替え・ヘルプのメニューの並び）をメインが追従。
result_files:
  - keyseq/presentation/welcome/{welcome_window,first_launch}.py / keyseq/presentation/views/menu_bar.py / keyseq/shared/i18n/locales/{ja,en}.json
  - tests_ui/{test_welcome_window,test_help_window}.py
  - instructions/phase/73_welcome_first_launch/tasks/task_07_welcome_reopen.md
verified:
  compile: pass
  tests: pass（1934・skip 7）
  tests_ui: pass（1262）
  smoke: pass（修正前の実行）

## next_action
- task_08（統合確認）: verifier で tests / tests_ui / smoke 一式・二次レビュー（deep-reviewer + codex-reviewer。phase 73 の task_01〜07 の差分 = `git diff 108bbe7..HEAD`）→ 指摘の採否はユーザー → task_09（実機目視 → 正本反映）
- 以降 task_03〜09 は phase.md の順（ユーザーはタスクの連続実行を許可済 2026-11-08）
- main へのマージはユーザー（PR は作らない）

## blockers
- **【回避中】Codex の書き込み実行（2026-10-14 18:24 以降の不具合）**: `~/.codex/.sandbox/sandbox.2026-10-14.log` に `setup refresh had errors`（node_repl.exe の ACL 更新が失敗）。**2026-10-15 ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `unelevated` に変更 → 常駐の broker・app-server を止めて再実行で書き込み可**。Codex の更新で直ったら `elevated` に戻す（ユーザー操作）。設定を変えたら常駐の broker（`app-server-broker.mjs`）と app-server を止めないと効かない

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **画面の文言（phase 72 以降）**: 新しい文言は `keyseq/shared/i18n/locales/ja.json` と `en.json` の両方にキーを足し、ソースに日本語を書かない（静的テスト）。`tr` はモジュール定数・import 時に評価しない。`App(` を作る / 文言を assert する新しいテストモジュールは import 直後に `fix_language("ja")`。英語は `ui_terms.md` §2・§3（E1〜E7）に従う。
- **phase 73**: 報告された不具合 2 件（プリセットが編集で開くまで表示されない / キー名の記号表記）は別セッションの提案カードに出してある（本フェーズ外）。tests_ui の窓の大きさのテスト（`test_compact_window.py:298`・`test_pane_window_width_persistence.py:236,275` の `pending`）が負荷で落ちることがある。**tests_ui の App() は worktree の `config/config.json`（ユーザーの手元の設定・gitignore）を読む**ので結果が手元の設定に左右される（task_05 の Welcome を出さない入口で考える）。Codex は python を実行できずテスト修正が手探りになる → 失敗はメインがトレースを読んで原因を絞ってから委任する。
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
