# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-17T12:00:00
phase: instructions/phase/02_hotkey_validation/phase.md（主入力＝暫定仕様 instructions/history/01_hotkey_validation.md v1.0）
last_commit_location: claude/w1-physical-verification-647a57（worktree: w1-physical-verification-647a57）※現在地はセッション開始時の git 実測値が正

## current
focus: フェーズ 02_hotkey_validation 実行中（hotkey 検証を presentation → domain/application へ移設・挙動不変）。task_01〜03 完了・コミット済。**次は task_04（配線の差し替え＝このフェーズの山場・初めて実挙動に影響）**。
mode: ready                      # git クリーン・標準検証全緑。task_04 のタスク定義起票から。

## last_action
ts: 2026-07-17T12:00:00
who: main
summary: |
  【フェーズ 02_hotkey_validation・task_01〜03 完了】設計は暫定仕様 01（v1.0・ユーザー確定済）が正。
  task_01(5ca5799) 安全網: 現行 App.validate_hotkey の特性テストを tests_ui へ7件追加（実装無変更）。
    移設後も無変更で pass することが挙動不変の証明になる。「不明なキー名」は {e}（keyboard 由来）を
    完全一致で固定せず startswith で前半のみ固定。
  task_02(2e0efa7) domain: keyseq/domain/hotkey.py::validate_hotkey_syntax 新規（①〜⑥の文法検査を
    1文字一致で移設。⑦キー名検証は含まない）+ tests/test_hotkey.py 9件。tk.Tk もモックも不要で pass
    ＝テスト容易性を達成。標準ライブラリのみ・注入なし・クラスなし（既存 domain スタイル準拠）。
  task_03(c0b782a) application: keyseq/application/hotkey_service.py::HotkeyService 新規
    （domain の文法検査を呼び、文法エラーは即 return＝現行の順序。domain の parts をそのまま使い
    再 split しない。⑦を担当。validate_key_name を Callable で DI）+ tests/test_hotkey_service.py 9件。
  **この時点で新モジュールは誰からも呼ばれていない**（現行 App.validate_hotkey がそのまま動作中）。
  差し替えは task_04。全タスクで verifier 全緑 + reviewer「完了可」。
result_files:
  - keyseq/domain/hotkey.py（新規）/ tests/test_hotkey.py（新規9件）
  - keyseq/application/hotkey_service.py（新規）/ tests/test_hotkey_service.py（新規9件）
  - tests_ui/test_app_ui_flows.py（特性テスト7件を追加。既存は無変更）
verified:
  compile: clean
  test(tests): pass 77          # 59(基準) + 9(test_hotkey) + 9(test_hotkey_service)
  test(tests_ui): pass 16       # 9(基準) + 7(特性テスト)
  smoke: pass

## next_action
- **task_04_presentation_delegation に着手**（フェーズの山場・初めて実挙動に影響する）。
  `/task_new` でタスク定義を起票 → codex-implementer → verifier → reviewer → **codex-reviewer で二次レビュー** →
  コミット → **実機目視**。内容（暫定仕様 §4.3 が正）:
  1. `app.py` の `input_gateway` 生成後・`ActionExecutor` 生成前に
     `self.hotkey_service = HotkeyService(validate_key_name=self.input_gateway.validate_key_name)` を生成
  2. **`app.py:71` の注入元を差し替え**: `validate_hotkey=self.validate_hotkey`
     → `validate_hotkey=self.hotkey_service.validate` ＝**層の逆転が解消**
  3. `App.validate_hotkey` を薄い委譲へ（`return self.hotkey_service.validate(hotkey)`。
     dialogs 契約のため**削除しない**。docstring は現行維持）
  4. **`application/action_executor.py` は変更しない**（シグネチャ不変・注入元が変わるだけ）
  - 検証の主役は **task_01 の特性テスト7件が無変更で pass** すること（挙動不変の証明）
  - 実機目視: アクション編集ダイアログで不正 hotkey（空 / `ctrl++c` / `ctrl+ctrl+c` / 不明キー）の
    エラー表示・正常 hotkey の正規化保存・hotkey アクションの実行（暫定仕様 §6-11）
- その後 task_05_finalize_records（正本反映・記録）: 暫定仕様の**正本昇格 + 凍結** /
  `codebase_map.md` 更新 / `decisions_archive/02_hotkey_validation.md` / `decisions.md` 索引 /
  `current.md` 完了記載・次採番 / **`backlog/INDEX.md` の idea_01 を完了にして `INDEX_done.md` へ移動** /
  `/refactor_check`。

## blockers
- なし（git クリーン・標準検証全緑）。

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
