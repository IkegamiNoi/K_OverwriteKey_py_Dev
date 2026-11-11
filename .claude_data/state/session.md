# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-11T23:30:00
phase: instructions/phase/75_mac_support（主入力 = 暫定 57 v0.5・ユーザー確定済）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/windows-continuation-23d400`（Mac の worktree `windows-continuation-23d400`・`Operation_check` 3ea433e から ff）。push はユーザー。main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 75 段階 ② task_07（Mac のテストの基準線 = `instructions/phase/75_mac_support/mac_test_baseline.md`）完了・コミット済み。次は task_07b（Q2 の既定の注入）。**
mode: implementing
presence: present

## last_action
ts: 2026-11-11T23:30:00
who: main
summary: |
  task_06（probe）: Mac 実機で tap・修飾キー・抑止・タイムアウト・送信・スレッド・aqua の Tk・Dock・記号キーを実測（スクリプトはスクラッチ・リポジトリ外）。暫定 57 を v0.6 へ（§4.1 結果表・§5.1 キュー 64 件/1.0 秒・修飾キーのフラグの左右別の付け直し・§5.3.1 対応表・Q1 = Tk 9.1・Q4 = 取得中に TIS で英字へ・§9 に 11・12）。Codex 敵対的レビュー 4 件を推奨どおり反映・reviewer 修正して採用（指摘 1〜4 反映済み）。
  task_05c（probe で発覚）: Tk 9 の aqua の右クリックは Button-3 → right_click_sequence を撤去し "<Button-3>" に戻す。codex-implementer・verifier（compile clean / test_tk_platform 4 pass / smoke pass / tests 1920・失敗 89・エラー 15 = 基準同数）・reviewer 採用。
result_files:
  - instructions/history/57_mac_support.md（v0.6）
  - instructions/phase/75_mac_support/tasks/task_05c_tk9_right_click.md・task_06_macos_probe.md
  - keyseq/presentation/tk_platform.py・keyboard_window.py・help/help_tab_view.py・tests/test_tk_platform.py
verified:
  mac_tests: 1920 件・失敗 89・エラー 15・skip 16（task_05c 後も基準どおり）
  mac_visual: task_05c の右クリックが届く（キーボードUI）・ヘルプのコピー OK（ユーザー）。割り当てのクリアの目視は task_09 へ（割り当てが作れないため）

## next_action
- Mac で tests_ui を流すときは `mac_test_baseline.md` の手順（モジュールごと・4 モジュール除外）。「要調査」10 件は task_07d（task_07b の後）
- task_07b: Q2 の既定の注入（決定済み・暫定 57 Q2 の詳細）
- task_09 でキーボードUIの右クリックによる割り当てのクリアを目視（task_05c の残り）
- Windows の標準検証 4 種は task_05c の分を次の機会にまとめて
- JIS の実測（§5.3.1 の文書値の確定）は JIS キーボードを用意できたとき

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
