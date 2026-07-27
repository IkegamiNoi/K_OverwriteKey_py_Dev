# handoff.md

過去の会話履歴は参照しないでください。
このファイルと `.claude_data/state/session.md` を起点に作業を再開してください。

## プロジェクト概要
- 言語/実行: Python（tkinter GUI）。オニオン構成（presentation / application / domain / infrastructure）。
- 対象アプリ: keyseq（キー割り当て/オーバーライドツール）。全体仕様は `instructions/common/`（`app_overview.md` / `codebase_map.md`）参照。
- **python は作業ツリー直下の `.venv` を使う**（worktree なら `.\.venv\Scripts\python.exe`）。
  依存 keyboard/pyautogui/pynput は `requirements.txt`。グローバル `py` は使わない（tests_ui/smoke が落ちる）。
  **worktree に `.venv` が無ければ最初に作成する**（手順は `.claude/rules/python_rules.md`。`.venv` は .gitignore 済み）。
  ツリー外の venv（`..\..\..\.venv`）は Codex のサンドボックスが実行を拒否するため使わない。

## 再開手順
1. `.claude_data/state/session.md` を読む（最重要・最新状態）
2. `.claude_data/state/decisions.md` を読む（判断履歴。完了フェーズは「アーカイブ索引」→ `decisions_archive/<phase>.md`）
3. CLAUDE.md → `instructions/phase/current.md`（**現在: phase 05 = Phase α 進行中**）→ `.claude/rules/` の順に必要分を読む
4. **設計の正は暫定仕様 [04_keymap_set_new_and_default_dir.md](../../instructions/history/04_keymap_set_new_and_default_dir.md)**
   （v0.3・ユーザー確定済）。フェーズ定義は
   [phase 05](../../instructions/phase/05_keymap_set_new_and_default_dir/phase.md)（タスク表 task_01〜06）。
   番号対応: **α=phase05/暫定04 / β=phase06/暫定05 / γ=phase07/暫定06 / プリセット=phase08/暫定07**。
5. session.md.next_action から作業を再開する

## 現在の作業の 1 行サマリ
**Phase α の task_01（起動時ディレクトリ骨格作成）完了（verifier 全緑・reviewer 完了可・指摘なし）。次は task_02（new_config_empty_path）を `/task_new` で起票し codex-implementer へ委任**。

## 最初に確認するコマンド（作業ツリー直下の .venv 必須）
```bash
# 作業ツリーのルートで実行
./.venv/Scripts/python.exe -m compileall -q keyseq main.py tests_ui
./.venv/Scripts/python.exe -m unittest discover -s tests
./.venv/Scripts/python.exe -m unittest discover -s tests_ui
./.venv/Scripts/python.exe -m tests.smoke_app
```
直近のベースライン（phase 05 task_01 完了時）: compile clean / tests **87** / tests_ui **76** / smoke pass。
※ Phase α は**挙動変更フェーズ**。以降のタスクでも新挙動の特性テスト追加で件数が増える（暫定 04 §8）。

## 次アクション（session.md.next_action より）
- **task_02（`new_config_empty_path`）を `/task_new` で起票**し、`codex-implementer` へ委任する
  （暫定 04 §3・§4・§7-1 / **受入条件 1**）。内容: `keymap_set_io.py` の `new_config` で `keymap_set_path` を空に /
  `save_keymap_set` の先頭で空パスなら `save_as` へ委譲 / `save_as` の `initialfile` を **`keymap_set.json`** に。
  `confirm_save_if_dirty` と `save_keymap_set_to` は**変更しない**。
- 以降 task_03〜06 は phase.md「タスク」表の順で進める（各タスクで `reviewer` 必須。
  task_05 統合とフェーズ完了判定前は Codex レビュー + `deep-reviewer` を併用）。
- β/γ/プリセットは α 完了後に順次 `/phase_start`（暫定 05/06/07 が設計の正）。

## 現フェーズ（Phase α）の設計要点（暫定 04 §2 確定事項）
- **新規作成は「ファイルなし」**（`new_config` で `keymap_set_path=""`）。**保存は空パスなら別名保存へ分岐**
  （ボタン名は「保存」のまま）。**Import 成功時は無条件で空**。**空起動時も空**。
- **既定保存先は固定 `default.json` ではなくディレクトリ `config/user/keymap_sets/`**。
  `default.json` への自動保存・自動フォールバックを廃止。別名保存の初期ファイル名は **`keymap_set.json`**。
- **起動時にディレクトリ骨格を一括作成**（config.json 本体の作成は従来どおり初回保存時）。← task_01 で実装済
- **`prompt_if_missing` は新規出力を止める。既存値は残置許容**（未知キー保持契約のため能動削除しない）。
- **制約**: 複数の独立 keymap_set の完全対応はしない（同一 dir では子ファイルを共有・上書きする現挙動が残る）。
  子ファイルのセット別分離は **Phase β + プリセット案2**。
- 後続フェーズの設計は `instructions/history/05〜07`（すべてユーザー確定済・未実装）。

## 注意事項・blockers
- **blockers: なし**。
- **保存系の実コード把握（設計時に確認済）**: keymap_set 保存 = `KeymapSetIo.save_keymap_set_to`→`config_service.save_runtime_data`
  （全子を無条件上書き・config_root 内は trigger_set/presets を固定 default.json へ）。config.json=起動エントリ
  （`preferred_startup_path`=`_startup_entry_path`）。hook キーは keymap_set に保存・`InputRouter` が `app.data` 直読み。
  プリセットは keymap_set の `hotkey_presets_path`→固定 default.json。dirty は子単位（`INTERNAL_*_DIRTY`/`trigger_set_dirty`）。
- **【Codex 運用】ジョブが詰まった/ハング検知/state 手修復は `instructions/common/rules_detail/codex_operations.md`**
  （要点は `.claude/rules/agent_selection.md` 冒頭）。**Codex 申告のテスト結果は信用せず必ず verifier で再実行**。
  Codex のサンドボックスは**作業ツリー配下しか実行できない**ため venv は worktree 内に置く（§0）。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。編集は必ず worktree ルート配下で。
- **【罠】`git grep` は追跡済みのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。行数計測は `wc -l`。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  出力の作法（応答・進捗報告・文書分量・委任量）は `.claude/rules/output_style.md`。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近: 04_config_io_controller_split / 03_startup_font_settings_cleanup / 02_hotkey_validation）。
- 未着手/保留 idea: idea_03（hotkey 保存正規化・低）/ idea_04（FontSettingsController・保留）/ idea_07（参照元掃除・β後）/
  idea_08（個別プリセット・07後）。idea_05→β 内包 / idea_06→β 達成見込み。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
