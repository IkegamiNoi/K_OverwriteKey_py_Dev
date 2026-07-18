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
4. **主入力（設計の正）`instructions/history/02_startup_font_settings_cleanup.md`（v1.0・ユーザー確定済）を読む**
   → 次に `instructions/phase/03_startup_font_settings_cleanup/phase.md`
5. session.md.next_action から作業を再開する（次は task_01 安全網）

## 現在の作業の 1 行サマリ
**フェーズ 03_startup_font_settings_cleanup 起票済・実装未着手**。起動設定/フォント 3 メソッド
（`_coerce_font_delta` / `_load_startup_settings` / `set_ui_font_delta`）を整理（presentation 内再編・挙動不変）。
暫定仕様 02 は v1.0 でユーザー確定済。**次は task_01（安全網の特性テスト）の起票・実装から**。

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
- **task_01_characterization_test（安全網）に着手**: `/task_new` で起票 → 現行 3 メソッドの特性テストを新規追加
  （coerce 純関数 / startup ローダの真理値表〔欠損・例外・非dict・正常〕+ `on_read_error` 呼出/文言 /
   **未知キー保持** / フォント変更フロー〔差分なし早期 return・`build_menu_bar` のみ〕）。**実装は変更しない**。
- 以降 task_02（`theme.coerce_font_delta`）→ task_03（`startup_settings.py`）→ task_04（font apply/uivars・二次レビュー併用）→
  task_05（正本反映・記録）。実装は codex-implementer 既定・標準検証は verifier・コミットはメイン。

## 直前フェーズの要点（03_startup_font_settings_cleanup・実装着手前）
- 設計の正 = 暫定仕様 `instructions/history/02_startup_font_settings_cleanup.md`（**v1.0・ユーザー確定済**）。phase.md は設計を再定義しない（参照のみ）。
- 確定設計（§2）: ①coerce_font_delta→`theme.py` の純関数 ②起動設定ローダ→新規 `presentation/startup_settings.py`（`config_service` 直依存）
  ③フォント設定は**案A（最小抽出）確定・案B〔FontSettingsController〕は今フェーズ見送り** ④エラー通知は `on_read_error(exc)` 注入 ⑤未知キー全保持契約。
- **要注意（挙動不変の要）**: ①**未知キー全保持**（`keymap_set_path` 消失防止・最優先の後方互換）
  ②**エラー通知の真理値表**（欠損=無警告 / 例外=警告1回〔title「startup.json 読込失敗」〕/ 非dict=無警告・文言1文字一致）
  ③**初期化順序**（ローダは `config_service`〔app.py:43〕のみ依存・`config_io`〔:127〕に依存しない・:57 の実行位置を保つ）
  ④**メニュー再構築**は `build_menu_bar` のみ（`bind_menu_shortcuts` を呼ばない副作用を保持）⑤**案B は実装しない**。
- 番号対応: phase 03 / 暫定 02 / decisions `decisions_archive/03_startup_font_settings_cleanup.md`。

## 注意事項・blockers
- blockers: なし（phase 03 起票完了・暫定仕様 v1.0 確定・git クリーン・標準検証全緑）。
- **【罠】state ファイル（`.claude_data/`）は worktree のパスで編集する**。main リポジトリ側の絶対パスへ編集すると
  worktree の追跡ファイルに反映されず commit から漏れる（phase 02 で複数回遭遇）。
- 分担: 実装は codex-implementer が既定。Codex は sandbox から `.venv` python を起動できないため、
  標準検証はメイン側/verifier が `.venv` で実行する。**Codex 申告のテスト結果は信用せず必ず verifier で実行**。
- **【罠】`git grep` は追跡済みファイルしか検索しない**。新規（未追跡）ファイルの確認は**直接 `grep`**。
- **app.py の行数計測は `wc -l`**（現 466 行）。PowerShell `Measure-Object -Line` は空行を数えず誤解の元。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （01_view_ref_cleanup / 02_hotkey_validation / 計画04）。ここには再掲しない。
- 未着手 idea: [idea_03](../../instructions/backlog/idea_03_action_hotkey_save_normalization.md)（アクション hotkey の保存時正規化・優先度低）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
