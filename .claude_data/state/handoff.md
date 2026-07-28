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
3. CLAUDE.md → `instructions/phase/current.md`（**現在: `instructions/phase/06_child_file_save_dialog/phase.md` = Phase β**）→
   `.claude/rules/` の順に必要分を読む
4. **このフェーズの設計の正は暫定仕様 [05_child_file_save_dialog.md](../../instructions/history/05_child_file_save_dialog.md)**
   （v0.2・ユーザー確定済）。フェーズ中は正本 `spec_detail/` を直接改訂しない（task_07 で昇格＋凍結）。
   番号対応: **α=phase05/暫定04〔完了〕 / β=phase06/暫定05〔進行中〕 / γ=phase07/暫定06 / プリセット=phase08/暫定07**。
5. session.md.next_action から作業を再開する

## 現在の作業の 1 行サマリ
**Phase β（06_child_file_save_dialog）起票完了（phase.md + current.md + INDEX.md）。次は task_01（参照元キーの読み書き基盤）の `/task_new` 起票 → 実装委任**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近のベースライン（phase 05 完了時）: compile clean / tests **90** / tests_ui **85** / smoke pass。
Phase β 起票時点はコード差分ゼロのため未再測（verified: compile/pytest = not_run）。

## 次アクション（session.md.next_action より）
- **task_01（`parent_refs_schema`）を `/task_new` で起票**（`instructions/phase/06_child_file_save_dialog/tasks/`）。
  子JSON の参照元キー（例 `_parent_refs`）を `keyseq/application/config_service.py` で読み書き
  （keymap / trigger_set → keymap_set、sequence → trigger_set。パスは `to_config_relative_or_absolute`）。
  **キー無し＝「未知」として区別できる形**にする。追加のみ・既存キー削除禁止。
- 起票後: `codex-implementer` へ委任（テストコード追加まで・**実行は依頼しない**）→ `verifier` で実測 →
  `reviewer` で差分レビュー → `/save_state` + `/task_commit`。

## 現フェーズ（Phase β）の要点 — 設計の正は暫定仕様 05
- keymap_set の「保存」を、**変更（dirty）のある子ファイルごとに 保存 / 別名保存 / 保存しない を選べる
  確認ダイアログ**へ置き換える。**親 keymap_set.json は常に保存**（ラジオ対象外・索引として最後）。
  変更のある子が無ければダイアログを出さない。
- **参照元記録（案A・軽量）**: 子JSON に直接の上位ファイルパス集合を記録し、共有状況を可視化する。
- **実装で後退しやすい 4 点**（暫定仕様の敵対レビュー指摘①〜④）:
  ① 未知の参照元・別の上位に属す子は**別名保存が既定**（安全側）/
  ② 保存計画は **presentation が決定・application が実行**（application に tkinter 依存を持ち込まない）/
  ③ パスが変わる子の上位は**保存必須**・失敗時は**旧索引維持**・**行ごとの粒度**（他 sequence を巻き込まない）/
  ④ 既定命名の変更は **trigger_set のみ**（keymap_set stem 基準。現状は固定 `user/trigger_sets/default.json`）。
- タスク: 01 参照元スキーマ → 02 trigger_set source_path 接続＋既定命名（idea_05 内包）→ 03 保存計画の実行契約 →
  04 dirty 収集＋共有状況判定 → 05 ダイアログ → 06 統合退行 → 07 正本反映。
  **task_03 はダイアログ導入前に既存挙動と等価**であることを確認してから 05 へ進む。
- 主な触点: `config_service.save_runtime_data`(200-252) / `_build_split_save_payloads`(456-) /
  `config_io/keymap_set_io.py`(`save_keymap_set_to`:78-102) / `controllers/dirty_state.py` / `config_io/io_dialogs.py`。

## 注意事項・blockers
- **blockers: なし**。
- **【Codex 運用】ジョブが詰まった/ハング検知/state 手修復は `instructions/common/rules_detail/codex_operations.md`**
  （要点は `.claude/rules/agent_selection.md` 冒頭）。**Codex 申告は信用せず必ず verifier で実測**。
  Codex 投入時はジョブログ停滞の Monitor をセットで。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。編集は必ず worktree ルート配下で。
- **【罠】`git grep` は追跡済みのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。行数計測は `wc -l`。
- **【傾向】既存の特性テストが旧挙動を固定している**。β は挙動変更フェーズのため、各タスク起票時に
  対象メソッドを固定しているテスト（`tests/test_config_service.py` / `tests_ui/test_config_io_characterization*.py` 等）を
  先に grep で洗い出し、更新対象としてタスク定義に明記する。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  出力の作法（応答・進捗報告・文書分量・委任量）は `.claude/rules/output_style.md`。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近: 05_keymap_set_new_and_default_dir / 04_config_io_controller_split / 03_startup_font_settings_cleanup）。
- 未着手/保留 idea: idea_03（hotkey 保存正規化・低）/ idea_04（FontSettingsController・保留）/ idea_07（参照元掃除・β後）/
  idea_08（個別プリセット・07後）/ idea_09（レガシー保存パス・α の積み残し）。idea_05→β 内包（着手中）/ idea_06→β 達成見込み。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
