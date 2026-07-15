# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-15T23:20:00
phase: instructions/modified_proposal/04_widget_split_plan.md（フェーズ番号は未確定 / current.md 参照）
last_commit_location: refactor/04-widget-split（worktree: template-merge-cleanup-52e942）※最終コミット場所。現在地はセッション開始時の git 実測値が正

## current
focus: 計画04 Widget分割リファクタ実行中。W0完了・W1完了(コミット済)、W1手動UI確認待ち→次はW2着手。
mode: pending_review             # W1はreviewer完了可済。残るは W1 のユーザー手動UI確認のみ。

## last_action
ts: 2026-07-15T23:20:00
who: main
summary: |
  計画04 を開始。W0前提確認: git clean / plan03完了(grep 2/0, V9済) / 標準検証は .venv python で全緑。
  重要発見: 計画書は `py` ランチャ前提だが実環境の依存(keyboard/pyautogui/pynput)はリポジトリルート
  `.venv` にのみ導入済み。python_rules.md の EDIT REQUIRED 節を .venv に確定しコミット(6db24c2)。
  Codex実行環境の障害を段階修復(ユーザー実施): ①codex-resources/codex-path のシンボリックリンク補完
  ②pwsh を Store版→MSI版(7.6.3)へ入替(CreateProcessAsUserW access-denied 解消)。以降 codex-implementer 稼働。
  W1(UiVars導入)を codex-implementer で実装→verifier全緑→reviewer「完了可」→コミット(e5d8653)。
  App直下の共有Tk変数12件を新規 ui_vars.py の UiVars へ集約、全参照を app.ui_vars.<var> へ機械置換。
result_files:
  - keyseq/presentation/ui_vars.py（新規）
  - keyseq/presentation/app.py
  - keyseq/presentation/key_capture.py
  - keyseq/presentation/layout_controller.py
  - keyseq/presentation/trigger_panel_controller.py
  - keyseq/presentation/views.py
  - tests_ui/test_app_ui_flows.py
  - .claude/rules/python_rules.md（W1とは別コミット 6db24c2）
verified:
  compile: clean
  test(tests): pass 59
  test(tests_ui): pass 9
  smoke: pass

## next_action
- （ユーザー）W1手動UI確認: フル/省略両ビューで 停止キー表示・ステータスバー更新・「常に手前」トグルが機能するか確認。失敗時は `git revert e5d8653`。
- W2に着手: codex-implementer に計画04「W2: メニューバーとステータスバーの移設」を依頼（`App._build_menu`→`views/menu_bar.py::build_menu_bar(app)`、`App._build_status_area`→`views/status_bar.py::build_status_area(app,parent)`。views/ フォルダ新規作成。`_bind_menu_shortcuts` の扱いは現物確認して報告）。実装環境: python=`..\..\..\.venv\Scripts\python.exe`、コミットはメイン側。
- W2実装後: verifier で標準検証4項目 → reviewer(5観点) → メイン判定 → 1コミット。

## blockers
- なし（Codex実行環境は修復済み・稼働確認済み）。

## resume_hints
- **python は必ず `..\..\..\.venv\Scripts\python.exe`（worktree相対）を使う。グローバル `py` は依存欠落で tests_ui/smoke が落ちる。**
- 実装は codex-implementer が既定（agent_selection.md）。Codexは .venv python を sandbox junction 経由で起動できないため、標準検証はメイン側/verifier が .venv で実行する分担。
- 計画書 instructions/modified_proposal/04_widget_split_plan.md が規範。1項目=1コミット、W0→W7順。§4「やらないこと」厳守（Full/Compact間のWidget共通化禁止・文言/レイアウト値不変・後続先取り禁止）。
- 計画書内パスの `instruction/`(単数)は実体 `instructions/`(複数)に読み替える。
- W5(生やし解消)とW7(フック手動6項目)の手動確認は計画上省略禁止。確認前に停止キー設定。
- 済コミット: 6db24c2(python_rules) / e5d8653(W1 UiVars)。ブランチ refactor/04-widget-split。
