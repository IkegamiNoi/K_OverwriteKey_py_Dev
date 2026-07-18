# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-18T02:00:00
phase: （アクティブなフェーズなし）02_hotkey_validation 完了。次フェーズ 03 未起票
last_commit_location: claude/task-04-progression-dc2eeb（worktree: worktree-state-tracking-da2833）※現在地はセッション開始時の git 実測値が正

## current
focus: **フェーズ 02_hotkey_validation 完了（task_01〜05・2026-07-18）**。hotkey 検証を presentation → domain/application へ層移設（挙動不変・層の逆転を解消）。正本昇格は不要と確定・暫定仕様 01 は v1.1 で凍結。次は次フェーズ（03・未起票）の方針確認。
mode: phase_done                 # 02 完了・記録済。次フェーズ着手はユーザー方針確認から。

## last_action
ts: 2026-07-18T02:00:00
who: main
summary: |
  【フェーズ 02_hotkey_validation・task_05（正本反映・記録）完了 → フェーズ完了】
  設計の正 = 暫定仕様 01（v1.1・凍結）。判断履歴の集約は decisions_archive/02_hotkey_validation.md が正。
  task_05 は文書作業のみ（keyseq/ 実装・テストは無変更＝git diff 空を確認）:
    - 正本昇格: **不要**（Explore 調査で spec_detail に hotkey 検証の記述なし＝担当層は codebase_map.md が正）。
    - 暫定仕様 history/01 を **v1.1 で凍結**（§6-11 の文言をユーザー承認どおり補正: プリセット＝保存時正規化／
      アクション＝実行時正規化・アクション保存時正規化は idea_03 で対応予定）。
    - codebase_map.md: App.validate_hotkey を「HotkeyService への薄い委譲」と整理 + 「HotkeyService / domain/hotkey.py」節を新設。
    - decisions_archive/02_hotkey_validation.md 作成 + decisions.md アーカイブ索引に 1 行追加。
    - current.md: 02 完了記載・次採番 03。backlog: idea_01 を INDEX_done へ移動（idea_03 は INDEX に残置）。
    - /refactor_check: **不要**（M1〜M6 該当なし。対象 6 ファイル・app.py 466 行/正味+4・旧ロジックは移動でコピー増殖なし）。
  【注意・自分用】task_05 中に .claude_data 配下（session.md / decisions_archive/02）を worktree ではなく
    main リポジトリ側の絶対パスへ誤保存 → 都度 worktree へ移送・main を復元して解消。**.claude_data は worktree パスで編集**。
verified:
  compile: clean                 # task_05 はコード無変更（git diff -- keyseq tests tests_ui = 空）
  test(tests): pass 77
  test(tests_ui): pass 16
  smoke: pass

## next_action
- **フェーズ 02 は完了**。次フェーズ（03）の方針をユーザーへ確認してから `/phase_start` で起票する。
  次候補: [idea_02](../../instructions/backlog/idea_02_startup_font_settings_cleanup.md)（起動設定/フォント クラスタ・
  初期化順序の解決が前提）。他に未着手 [idea_03](../../instructions/backlog/idea_03_action_hotkey_save_normalization.md)
  （アクション hotkey の保存時正規化・優先度低・要設計）。
- 本タスク（task_05）のコミットはメインで作成（task_commit）。

## blockers
- なし（フェーズ 02 完了・標準検証全緑・コードは task_04 で確定済）。

## resume_hints
- **python は必ず `..\..\..\.venv\Scripts\python.exe`（worktree相対）を使う。グローバル `py` は依存欠落で tests_ui/smoke が落ちる。**
- **設計の正は暫定仕様 `instructions/history/01_hotkey_validation.md`（v1.0）**。phase.md は設計を再定義していない（参照のみ）。
  番号対応: phase 02 / 暫定 01 / decisions `decisions_archive/02_hotkey_validation.md`（暫定仕様は独立採番）。
- 実装は codex-implementer が既定（agent_selection.md）。Codex は sandbox から `.venv` python を起動できないため、
  標準検証はメイン側/verifier が `.venv` で実行する分担。**Codex 申告のテスト結果は信用せず必ず verifier で実行する**。
- **【罠】`git grep` は追跡済みファイルしか検索しない**。新規ファイル（未追跡）の確認には**直接 `grep`** を使う
  （git grep だと「0件」と出るが実は検索されていない。task_02 で遭遇）。
- **【罠】キー名検証ループは明示的な `for` で書く**。内包表記/map/any だと Python 3 ではループ変数が
  外側へ漏れず `except` 内の `p` が NameError になり挙動が変わる（task_03 の最大の事故ポイント）。
- **app.py の行数計測は `wc -l` を使う**（489行）。PowerShell `Measure-Object -Line` は空行を数えず誤解の元（過去に誤報告あり）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引あり）+ `decisions_archive/<phase>.md`。
  計画04（Widget分割・完了）とフェーズ 01_view_ref_cleanup（完了）の詳細はそちらが正。
- 完了済: 計画04（W0〜W7・全手動確認済）/ フェーズ 01_view_ref_cleanup（2026-07-17）。
  次フェーズ候補: [idea_02](../../instructions/backlog/idea_02_startup_font_settings_cleanup.md)（起動設定/フォント。初期化順序の解決が前提）。
- 据え置き中: `action_list` alias（`full_view.py`）。production が使う生きたパスのため（decisions_archive/01 参照）。
