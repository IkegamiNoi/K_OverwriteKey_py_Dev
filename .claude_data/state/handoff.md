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
2. `.claude_data/state/decisions.md` があれば読む（過去の判断履歴）
3. CLAUDE.md → `instructions/phase/current.md` → `.claude/rules/` の順に必要分を読む
4. 規範計画書 `instructions/modified_proposal/04_widget_split_plan.md` を読む（1項目=1コミット、W0→W7順）
5. session.md.next_action から作業を再開する

## 現在の作業の 1 行サマリ
計画04（Widget分割・フォルダ再編・挙動不変）実行中。W0/W1完了(コミット済 e5d8653)、W1手動UI確認待ち→次はW2（メニュー/ステータス移設）着手。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ず .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
session.md.verified（compile clean / tests pass 59 / tests_ui pass 9 / smoke pass）と一致することを確認してから次のアクションへ進む。

## 次アクション（session.md.next_action より）
- （ユーザー）W1手動UI確認: フル/省略両ビューで 停止キー表示・ステータスバー更新・「常に手前」トグル。失敗時は `git revert e5d8653`。
- W2着手: codex-implementer に「W2: メニューバー(`_build_menu`→views/menu_bar.py)とステータスバー(`_build_status_area`→views/status_bar.py)の移設」を依頼 → verifier → reviewer → 1コミット。

## 注意事項・blockers
- blockers: なし（Codex実行環境は修復済み・稼働確認済み）。
- Codex実行環境の修復履歴（再発時の参考）: ①`Programs\OpenAI\Codex` 配下に codex-resources/codex-path のシンボリックリンクを補完 ②pwsh を Store版→MSI版(7.6.3)へ入替（Store版は CreateProcessAsUserW access-denied で sandbox がコマンド起動不可）。
- 分担: 実装は codex-implementer が既定。ただし Codex は sandbox junction 経由で `.venv` python を起動できないため、標準検証はメイン側/verifier が `.venv` で実行する。
- 計画書内パスの `instruction/`(単数)は実体 `instructions/`(複数)に読み替える。
- §4「やらないこと」厳守: Full/Compact間のWidget共通化禁止・文言/レイアウト値不変・後続タスク先取り禁止。W5/W7の手動確認は省略禁止。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
