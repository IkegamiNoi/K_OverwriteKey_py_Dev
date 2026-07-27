# handoff.md

過去の会話履歴は参照しないでください。
このファイルと `.claude_data/state/session.md` を起点に作業を再開してください。

## プロジェクト概要
- 言語/実行: Python（tkinter GUI）。オニオン構成（presentation / application / domain / infrastructure）。
- 対象アプリ: keyseq（キー割り当て/オーバーライドツール）。全体仕様は `instructions/common/`（`app_overview.md` / `codebase_map.md`）参照。
- **python 実行は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  依存 keyboard/pyautogui/pynput はこの `.venv` にのみ導入済み。グローバル `py` は使わない（tests_ui/smoke が落ちる）。
- **Codex は python を一切実行できない**（サンドボックス制約・回避不能）。実装委任にテスト実行を含めず、
  実測は `verifier` が行う（理由と検討した 3 案は `instructions/common/rules_detail/codex_operations.md` §0）。

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
**Phase α の task_03（Import 後の無条件クリア + 空起動時 path の空化）完了（verifier 全緑・reviewer 完了可・指摘なし）。次は task_04（remove_prompt_if_missing）を `/task_new` で起票し codex-implementer へ委任**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近のベースライン（phase 05 task_03 完了時）: compile clean / tests **87** / tests_ui **82** / smoke pass。
※ Phase α は**挙動変更フェーズ**。以降のタスクでも新挙動の特性テスト追加で件数が増える（暫定 04 §8）。

## 次アクション（session.md.next_action より）
- **task_04（`remove_prompt_if_missing`）を `/task_new` で起票**し、`codex-implementer` へ委任する
  （暫定 04 §6 / **受入条件 5・6**）。除去対象は 4 箇所: `config_service.py` の正規化行 /
  `startup_settings.py` の型ガード / `startup_io.write_startup` の base 既定 /
  `keymap_set_io.set_startup_keymap_set` が書く辞書。
  **既存 config.json に残る値は能動削除しない**（未知キー保持契約。受入は「**新規作成される**
  config.json に含まれない」で判定）。application 層に触れる唯一のタスク。
  既存テストで config.json のキー集合を固定している箇所（例
  `test_write_startup_merges_defaults_current_and_arg`）の更新が必要。起票時に grep で洗い出す。
- 以降 task_05（統合退行・実機目視をまとめて依頼）→ task_06（正本反映・凍結・`/refactor_check`）。
  各タスクで `reviewer` 必須。task_05 とフェーズ完了判定前は Codex レビュー + `deep-reviewer` を併用。
- β/γ/プリセットは α 完了後に順次 `/phase_start`（暫定 05/06/07 が設計の正）。

## 現フェーズ（Phase α）の設計要点（暫定 04 §2 確定事項）
- **新規作成は「ファイルなし」**（`new_config` で `keymap_set_path=""`）。**保存は空パスなら別名保存へ分岐**
  （ボタン名は「保存」のまま）。**Import 成功時は無条件で空**。**空起動時も空**。← task_02・03 で実装済
- **既定保存先は固定 `default.json` ではなくディレクトリ `config/user/keymap_sets/`**。
  別名保存の初期ファイル名は空パス時のみ **`keymap_set.json`**（非空時は現在ファイル名）。← task_02 で実装済
- **起動時にディレクトリ骨格を一括作成**（config.json 本体の作成は初回保存時のまま）。← task_01 で実装済
- **`prompt_if_missing` は新規出力を止める。既存値は残置許容**（未知キー保持契約のため能動削除しない）。← task_04
- **制約**: 複数の独立 keymap_set の完全対応はしない（同一 dir では子ファイルを共有・上書きする現挙動が残る）。
  子ファイルのセット別分離は **Phase β + プリセット案2**。
- `config_paths.py` は Phase α では**変更しない**（監査済: `save_keymap_set_to` に空パスが渡る経路がないため、
  `normalize_keymap_set_save_path("")` の `default.json` フォールバックは保存経路から到達しない）。
- 後続フェーズの設計は `instructions/history/05〜07`（すべてユーザー確定済・未実装）。

## 注意事項・blockers
- **blockers: なし**。
- **保存系の実コード把握（設計時に確認済）**: keymap_set 保存 = `KeymapSetIo.save_keymap_set_to`→`config_service.save_runtime_data`
  （全子を無条件上書き・config_root 内は trigger_set/presets を固定 default.json へ）。config.json=起動エントリ
  （`preferred_startup_path`=`_startup_entry_path`）。hook キーは keymap_set に保存・`InputRouter` が `app.data` 直読み。
  プリセットは keymap_set の `hotkey_presets_path`→固定 default.json。dirty は子単位（`INTERNAL_*_DIRTY`/`trigger_set_dirty`）。
- **【Codex 運用】ジョブが詰まった/ハング検知/state 手修復は `instructions/common/rules_detail/codex_operations.md`**
  （要点は `.claude/rules/agent_selection.md` 冒頭）。**Codex 申告は信用せず必ず verifier で実測**。
  Codex 投入時はジョブログ停滞の Monitor をセットで。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。編集は必ず worktree ルート配下で。
- **【罠】`git grep` は追跡済みのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。行数計測は `wc -l`。
- **【傾向】既存の特性テストが旧挙動を固定している**（phase 04 で作成）。挙動変更タスクの起票時は、
  対象メソッドを固定しているテストを先に grep で洗い出し、更新対象としてタスク定義に明記する。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  出力の作法（応答・進捗報告・文書分量・委任量）は `.claude/rules/output_style.md`。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近: 04_config_io_controller_split / 03_startup_font_settings_cleanup / 02_hotkey_validation）。
- 未着手/保留 idea: idea_03（hotkey 保存正規化・低）/ idea_04（FontSettingsController・保留）/ idea_07（参照元掃除・β後）/
  idea_08（個別プリセット・07後）。idea_05→β 内包 / idea_06→β 達成見込み。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
