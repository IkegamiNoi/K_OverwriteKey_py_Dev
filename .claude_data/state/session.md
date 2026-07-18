# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-18T00:00:00
phase: instructions/phase/02_hotkey_validation/phase.md（主入力＝暫定仕様 instructions/history/01_hotkey_validation.md v1.0）
last_commit_location: claude/task-04-progression-dc2eeb（worktree: worktree-state-tracking-da2833）※現在地はセッション開始時の git 実測値が正

## current
focus: フェーズ 02_hotkey_validation 実行中。**task_01〜04 完了・コミット済（task_04 は実機目視までユーザー確認済＝挙動不変を確認）**。次は最終タスク task_05_finalize_records（正本反映・記録）。
mode: ready                      # task_04 完了。task_05 の起票から。

## last_action
ts: 2026-07-18T00:00:00
who: main
summary: |
  【フェーズ 02_hotkey_validation・task_04 完了（実機目視までユーザー確認済）】設計は暫定仕様 01（v1.0）が正。
  実機目視結果（ユーザー）: プリセットダイアログの正規化保存 OK / hotkey アクションの実行 OK。挙動不変を確認。
  実機目視中に判明（task_04 とは無関係の既存非対称）: アクション（シーケンス）の hotkey は
  ActionDialog.on_ok が生値のまま保存（プリセットは normalized 保存・実行時は正規化される）。
  → ユーザー判断: (A) 今フェーズでは触らず idea_03 として起票済（優先度低・要設計・挙動変更を伴う）。
    (B) 暫定仕様 §6-11 の文言は「プリセット＝保存時正規化／アクション＝実行時正規化・アクション保存時
    正規化は idea_03 で対応予定」と補正する（idea_03 実施を前提とした文言）＝ task_05 で実施。
  --- 以下 task_04 の実装内容 ---
  task_04 presentation 配線差し替え（暫定仕様 §4.3）を codex-implementer で実装。差分は
  keyseq/presentation/app.py のみ（+4/-27）:
    1. import 追加 `from keyseq.application.hotkey_service import HotkeyService`
    2. __init__ で input_gateway 生成後・ActionExecutor 生成前に
       `self.hotkey_service = HotkeyService(validate_key_name=self.input_gateway.validate_key_name)`
    3. ActionExecutor 注入元を `self.validate_hotkey` → `self.hotkey_service.validate`（＝層の逆転が解消）
    4. App.validate_hotkey を `return self.hotkey_service.validate(hotkey)` の薄い委譲へ（docstring 維持・削除せず）
  対象外（action_executor.py / hotkey_service.py / hotkey.py / dialogs.py）は無変更を確認。
  自動ゲート全通過: verifier 全緑（77/16/smoke。特性テスト7件が無変更で pass＝挙動不変の証明）/
  reviewer「完了可・指摘なし」/ codex-reviewer「指摘なし」。
result_files:
  - keyseq/presentation/app.py（委譲化・HotkeyService 生成・注入元差し替え）
  - instructions/phase/02_hotkey_validation/tasks/task_04_presentation_delegation.md（タスク定義・新規起票）
verified:
  compile: clean
  test(tests): pass 77          # 変化なし
  test(tests_ui): pass 16       # 特性テスト7件を含め無変更で pass（挙動不変の証明）
  smoke: pass

## next_action
- **task_05_finalize_records（正本反映・記録・最終タスク）に着手**: `/task_new` で起票 →
  暫定仕様の**正本昇格 + 凍結**（§8。hotkey 検証の仕様節が spec_detail にあるか要調査。無ければ昇格不要） /
  **暫定仕様 §6-11 の文言補正**（プリセット＝保存時正規化／アクション＝実行時正規化。アクション保存時
    正規化は idea_03 で対応予定と明記。ユーザー承認済＝上記 last_action の (B)） /
  `codebase_map.md` 更新（HotkeyService / domain/hotkey.py 追記・App 責務を薄い委譲へ整理） /
  `decisions_archive/02_hotkey_validation.md` 作成（idea_03 分離・§6-11 補正の判断も集約） / `decisions.md` アーカイブ索引 /
  `current.md` 完了記載・次採番（次フェーズ 03） /
  **`backlog/INDEX.md` の idea_01 を完了にして `INDEX_done.md` へ移動** / `/refactor_check` 実行と判定記載。
- 派生 idea: [idea_03](../../instructions/backlog/idea_03_action_hotkey_save_normalization.md)（アクション hotkey
  の保存時正規化/検証の統一・未着手・優先度低）。

## blockers
- なし（task_04 完了・git クリーン想定・標準検証全緑）。

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
