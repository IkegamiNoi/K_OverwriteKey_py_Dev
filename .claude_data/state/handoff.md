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
4. 次フェーズ着手時は `instructions/backlog/INDEX.md` の候補 idea を読み、方針をユーザーへ確認 → `/phase_start` で起票

## 現在の作業の 1 行サマリ
**フェーズ 02_hotkey_validation 完了（task_01〜05・2026-07-18）**。hotkey 検証を presentation → domain/application へ層移設（挙動不変・層の逆転を解消）。正本昇格は不要と確定・暫定仕様 01 は v1.1 で凍結。**次はアクティブなフェーズなし＝次フェーズ（03・未起票）の方針確認から**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ず .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
session.md.verified（compile clean / tests pass **77** / tests_ui pass **16** / smoke pass）と一致することを確認する。

## 次アクション（session.md.next_action より）
- **フェーズ 02 は完了**。次フェーズ（03）の方針をユーザーへ確認してから `/phase_start` で起票する。
  - 次候補: [idea_02](../../instructions/backlog/idea_02_startup_font_settings_cleanup.md)（起動設定/フォント クラスタ・初期化順序の解決が前提）。
  - 他に未着手: [idea_03](../../instructions/backlog/idea_03_action_hotkey_save_normalization.md)（アクション hotkey の保存時正規化/検証の統一・優先度低・要設計。phase 02 task_04 から分離）。

## 直前フェーズの要点（02_hotkey_validation・完了）
- 設計の正 = 暫定仕様 `instructions/history/01_hotkey_validation.md`（**v1.1・凍結**）。判断集約は `decisions_archive/02_hotkey_validation.md`。
- 成果: `domain/hotkey.py::validate_hotkey_syntax`（文法検査）/ `application/hotkey_service.py::HotkeyService`（合成 + キー名検証 DI）新設。`App.validate_hotkey` は `HotkeyService.validate` への薄い委譲へ。`ActionExecutor` の注入元を `HotkeyService.validate` に差し替え＝**層の逆転を解消**。
- 正本昇格は**不要**（spec_detail に hotkey 検証の記述なし＝担当層は `codebase_map.md` が正）。codebase_map.md のみ追従更新済。
- 実機目視で判明した「アクション hotkey は保存時に正規化されない（プリセットは正規化・実行時は正規化）」既存挙動は **idea_03 へ分離**し、暫定仕様 §6-11 を補正済（挙動不変・task_04 とは無関係）。

## 注意事項・blockers
- blockers: なし（フェーズ 02 完了・git クリーン・標準検証全緑）。
- **【罠】state ファイル（`.claude_data/`）は worktree のパスで編集する**。main リポジトリ側の絶対パスへ編集すると
  worktree の追跡ファイルに反映されず commit から漏れる（task_04/05 で複数回遭遇）。
- 分担: 実装は codex-implementer が既定。Codex は sandbox から `.venv` python を起動できないため、
  標準検証はメイン側/verifier が `.venv` で実行する。**Codex 申告のテスト結果は信用せず必ず verifier で実行**。
- **【罠】`git grep` は追跡済みファイルしか検索しない**。新規（未追跡）ファイルの確認は**直接 `grep`**。
- **app.py の行数計測は `wc -l`**（現 466 行）。PowerShell `Measure-Object -Line` は空行を数えず誤解の元。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （01_view_ref_cleanup / 02_hotkey_validation / 計画04）。ここには再掲しない。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
