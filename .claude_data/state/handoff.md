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
3. CLAUDE.md → `instructions/phase/current.md`（**現在: アクティブなフェーズなし = 次フェーズ未確定**）→
   `.claude/rules/` の順に必要分を読む
4. 次フェーズに着手する場合の設計の正は暫定仕様
   [05_child_file_save_dialog.md](../../instructions/history/05_child_file_save_dialog.md)（Phase β・ユーザー確定済）。
   番号対応: **α=phase05/暫定04〔完了〕 / β=phase06/暫定05 / γ=phase07/暫定06 / プリセット=phase08/暫定07**。
5. session.md.next_action から作業を再開する

## 現在の作業の 1 行サマリ
**Phase α（05_keymap_set_new_and_default_dir）完了（task_01〜06・正本昇格 + 暫定仕様 04 凍結 + refactor_check 不要）。次は Phase β（phase 06 / 暫定 05）の `/phase_start`（ユーザー確認後）**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近のベースライン（phase 05 完了時）: compile clean / tests **90** / tests_ui **85** / smoke pass。

## 次アクション（session.md.next_action より）
- **次フェーズをユーザーへ確認する**（`current.md`「作業開始時の指示」）。本命は **Phase β = phase 06 / 暫定 05**
  （子ファイル保存の確認ダイアログ・参照元記録）。**α のディレクトリ化を前提**とし、idea_05（trigger_set の
  source_path 不整合）を**内包**する。暫定仕様は起票・確定済のため `/spec_draft` は不要、`/phase_start` から入る。
- 他の候補: γ（phase 07 / 暫定 06・停止/トグルキーの config.json 既定化。**α β と独立**）/
  プリセット（phase 08 / 暫定 07）/ idea_09（α の積み残し・優先度低・小さいので β の前後どちらでも可）。

## 直前フェーズ（Phase α）の要点 — 正本は `spec_detail/data_schema.md` §5.4 配下
- **新規作成 / Import 成功 / 起動時に stored セットが読めない**の 3 経路で `keymap_set_path` が**空**になり、
  空パスの「保存」は**別名保存**へ分岐する（初期名 `keymap_set.json` / 初期 dir `config/user/keymap_sets/`）。
- **既定保存先はディレクトリ `config/user/keymap_sets/`**（固定 `default.json` を保存ターゲットにしない）。
  起動時にディレクトリ骨格を一括作成し、`config/config.json` は最初に設定が永続化された時点で作る。
- **`prompt_if_missing` は撤去**（新規出力なし）。**既存 config.json の値は残置**（`pop` しない）。
- **制約（β の課題）**: 同一 dir に複数 keymap_set を置いても trigger_set / hotkey_presets は**共通ファイルを共有・上書き**する。
- **実装未追従が 1 件**: 別名保存でレガシー `<アプリ配置>/settings/` 配下を選ぶと `default.json` へ差し替わる
  （= idea_09）。**正本が正であり実装を追従させる**立て付け（案 A〜C の選択のみユーザー判断）。
- 保存時の `config.json` 更新は `config_service.save_runtime_data`（`config_service.py:227`）が**直接**書く。
  `write_startup` は「起動時に読むJSONを設定」メニューとフォント変更のみが使う**別経路**（混同注意）。

## 注意事項・blockers
- **blockers: なし**。
- **【Codex 運用】ジョブが詰まった/ハング検知/state 手修復は `instructions/common/rules_detail/codex_operations.md`**
  （要点は `.claude/rules/agent_selection.md` 冒頭）。**Codex 申告は信用せず必ず verifier で実測**。
  Codex 投入時はジョブログ停滞の Monitor をセットで。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。編集は必ず worktree ルート配下で。
- **【罠】`git grep` は追跡済みのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。行数計測は `wc -l`。
- **【傾向】既存の特性テストが旧挙動を固定している**。挙動変更タスクの起票時は、対象メソッドを固定している
  テストを先に grep で洗い出し、更新対象としてタスク定義に明記する。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  出力の作法（応答・進捗報告・文書分量・委任量）は `.claude/rules/output_style.md`。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近: 05_keymap_set_new_and_default_dir / 04_config_io_controller_split / 03_startup_font_settings_cleanup）。
- 未着手/保留 idea: idea_03（hotkey 保存正規化・低）/ idea_04（FontSettingsController・保留）/ idea_07（参照元掃除・β後）/
  idea_08（個別プリセット・07後）/ idea_09（レガシー保存パス・α の積み残し）。idea_05→β 内包 / idea_06→β 達成見込み。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
