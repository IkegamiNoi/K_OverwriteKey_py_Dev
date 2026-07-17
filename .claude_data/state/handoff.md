# handoff.md

過去の会話履歴は参照しないでください。
このファイルと `.claude_data/state/session.md` を起点に作業を再開してください。

## プロジェクト概要
- 言語/実行: Python（tkinter GUI）。オニオン構成（presentation / application / domain / infrastructure）。
- 対象アプリ: keyseq（キー割り当て/オーバーライドツール）。全体仕様は `instructions/common/`（`app_overview.md` / `codebase_map.md`）参照。
- **python 実行は必ずリポジトリルートの `.venv` を使う**（worktree相対 `..\..\..\.venv\Scripts\python.exe`）。
  依存 keyboard/pyautogui/pynput はこの `.venv` にのみ導入済み。グローバル `py` は使わない（tests_ui/smoke が落ちる）。

## 再開手順
1. `.claude_data/state/session.md` を読む（最重要・最新状態）
2. `.claude_data/state/decisions.md` を読む（判断履歴。完了フェーズは「アーカイブ索引」→ `decisions_archive/<phase>.md`）
3. CLAUDE.md → `instructions/phase/current.md` → `.claude/rules/` の順に必要分を読む
4. **主入力（設計の正）`instructions/history/01_hotkey_validation.md`（v1.0・ユーザー確定済）を読む**
   → 次に `instructions/phase/02_hotkey_validation/phase.md`
5. session.md.next_action から作業を再開する

## 現在の作業の 1 行サマリ
フェーズ 02_hotkey_validation 実行中（hotkey 検証を presentation → domain/application へ移設・挙動不変）。task_01〜03 完了・コミット済。**次は task_04（配線の差し替え＝山場・初めて実挙動に影響）**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ず .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
session.md.verified（compile clean / tests pass **77** / tests_ui pass **16** / smoke pass）と一致することを確認してから次のアクションへ進む。

## 次アクション（session.md.next_action より）
- **task_04_presentation_delegation に着手**（暫定仕様 §4.3 が正）。`/task_new` で起票 →
  codex-implementer → verifier → reviewer → **codex-reviewer で二次レビュー** → コミット → **実機目視**。
  1. `app.py` の `input_gateway` 生成後・`ActionExecutor` 生成前に `HotkeyService` を生成
  2. `app.py:71` の注入元を `self.hotkey_service.validate` へ差し替え ＝**層の逆転が解消**
  3. `App.validate_hotkey` を薄い委譲へ（dialogs 契約のため削除しない）
  4. `application/action_executor.py` は**変更しない**
  - 検証の主役は **task_01 の特性テスト7件が無変更で pass** すること（挙動不変の証明）
- その後 task_05_finalize_records（正本反映・記録。暫定仕様の昇格/凍結・idea_01 の INDEX_done 移動含む）

## 注意事項・blockers
- blockers: なし（git クリーン・標準検証全緑）。
- **設計の正は暫定仕様 `instructions/history/01_hotkey_validation.md`（v1.0）**。phase.md は設計を再定義していない（参照のみ）。
  番号対応: phase 02 / 暫定 01 / decisions `decisions_archive/02_hotkey_validation.md`（暫定仕様は独立採番）。
- 分担: 実装は codex-implementer が既定。ただし Codex は sandbox から `.venv` python を起動できないため、
  標準検証はメイン側/verifier が `.venv` で実行する。**Codex 申告のテスト結果は信用せず必ず verifier で実行する**。
- **【罠】`git grep` は追跡済みファイルしか検索しない**。新規ファイル（未追跡）の確認には**直接 `grep`** を使う
  （git grep だと「0件」と出るが実は検索されていない）。
- **【罠】キー名検証ループは明示的な `for` で書く**。内包表記/map/any だと Python 3 ではループ変数が
  外側へ漏れず `except` 内の `p` が NameError になり挙動が変わる。
- **app.py の行数計測は `wc -l` を使う**（489行）。PowerShell `Measure-Object -Line` は空行を数えず誤解の元。
- 完了済: 計画04（Widget分割・W0〜W7）/ フェーズ 01_view_ref_cleanup（2026-07-17）。
  詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正（ここには再掲しない）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
