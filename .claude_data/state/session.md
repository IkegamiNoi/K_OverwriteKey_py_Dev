# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-22T21:00:00
phase: instructions/phase/75_mac_support（暫定 57 v0.25 は凍結・正本反映済み）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 29 / idea 67。phase 75 の判断の記録は `decisions_archive/75_mac_support.md` に追記する（decisions.md から移し済み）
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/windows-support-continuation-f235f4`（Windows の worktree・Mac の task_13b まで取り込み済み + task_13c）。push はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 75。task_14（正本反映）完了（2026-11-22）= 暫定 57 凍結・正本昇格・deep-reviewer 指摘反映・Codex 敵対的の 5 件は idea_66・ヘルプ 2 文を両 OS に。残り = task_15（提案書 28 のリファクタ・起票済み `tasks/task_15_refactor.md`）を Windows で実装・検証 → Mac の作業時に Mac の確認（task_15 の確認 3）で phase 75 を閉じる。**
next_action_override: 上の focus が正（下の next_action の Windows 検証・task_14 はすべて済み）
mode: completed

## last_action
ts: 2026-11-22T04:30:00
who: main
summary: |
  実施: task_13b を起票（reviewer 修正して採用）→ ユーザー許可で PyInstaller 6.22.3 と sdist を Mac の .venv / packaging/sources へ → codex-implementer で実装 + メインの補い → verifier（tests 2141・test_third_party 7 pass・smoke OK・ビルド成功〔Tk 9.1 同梱可〕・codesign OK・pynput 差し替え OK）→ reviewer 修正して採用（README の pynput のパス）→ 反映・再ビルド。task_12 で書かれた test_app_data_roots（Mac でエラー）を OS 別に分割（ユーザー承認）。
  ユーザー判断: 識別子 io.github.ikegaminoi.keyseq・未公証の開き方を README に（暫定 57 v0.24）・C ライブラリ（OpenSSL 等）は Mac の一覧を記録し Windows 作業時に両 OS 分を 1 本で起票・メニューの処理を after(0) で遅らせる案で起票。
  実機確認: 4 OK。3（再起動）はメニューの処理の中の wait_window が戻らず止まる（開発実行でも起きる・faulthandler で特定・after(0) で直ることを probe で確認）→ 暫定 57 v0.25（§5.4「メニューの処理」）+ task_11g 起票（reviewer 修正して採用→反映）。保存パネルの件は .app でだけ起き、未調査。
  Codex 敵対的レビュー（v0.25）: needs-attention・中 3（終了と予約の競合／チェック項目の遅延で別の構成セットに作用／tests_ui の漏れ〔反映済み〕）。
result_files:
  - packaging/requirements-build.txt・packaging/README.md・packaging/macos/（keyseq.spec・README_dist.txt）
  - keyseq/presentation/help/content/third_party/（third_party.json・pyobjc.txt・rubicon_objc.txt・python_macos.txt）・tests/test_third_party.py・tests/test_os_backend_contracts.py
  - instructions/history/57_mac_support.md（v0.24・v0.25）・instructions/phase/75_mac_support/（phase.md・tasks/task_13b_packaging_macos_build.md・tasks/task_11g_menu_command_deferral.md）・.claude_data/state/decisions.md
verified:
  tests_mac: compile clean / tests 2141・エラー 1（test_app_data_roots → 分割後のモジュール 24 件 OK・全体の再実行は未）/ smoke OK / tests_ui test_help_window OK / ビルド成功
  tests_windows: not_run（表・テスト・requirements の変更は次の Windows 作業で）
  visual_mac: task_13b 4 OK・3 NG（→ task_11g）・保存パネル NG（.app のみ）・1・2・5 未報告

## next_action
- **Windows 検証（Windows の worktree で・task_11g / task_13b の残課題）**: Windows 検証の残課題 = test_third_party・test_os_backend_contracts（test_app_data_roots の分割）・test_sample_config・requirements-build.txt・task_11g（tests と tests_ui）・Windows の `.spec` の `dist/sources` の空にし方とアーカイブの照合（Mac と同じ修正）・テンキーのサンプル（A / G / T）の実機・C ライブラリ（OpenSSL 等）の洗い出しと両 OS 分の起票。Windows の worktree へこのブランチ（`claude/task-13b-72ac5c`）を取り込むのはユーザーの判断（push / merge はユーザー）。
- その後 task_14（正本反映 = 暫定 57 の昇格・凍結・`decisions_archive/75_mac_support.md`・current.md の完了記載・`/refactor_check`）を起票。
- 保留中: 2 枚目のモニタの目視・中クリック（ユーザー判断）。idea_45（キー名の入力用 / 出力用の整理を追記）・idea_59〜64 は検討段階。

## blockers
- **Mac で tests_ui を通しで走らせない**（task_08・09 まではスタブがキー検証できずモーダルで止まる。verifier にも明記）。Mac の python は `../../../.venv/bin/python`
- **【解消・2026-11-22】Codex の書き込み実行（2026-10-14 以降の不具合）**: ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `elevated` に戻し、Codex 0.171.0 で書き込みのテスト OK（`setup refresh ... errors=[]`）。再発したら `unelevated` に変えて回避（ユーザー操作・常駐の broker〔`app-server-broker.mjs`〕と app-server を止めないと効かない）

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
