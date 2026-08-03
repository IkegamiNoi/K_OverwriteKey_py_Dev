# handoff.md

過去の会話履歴は参照しないでください。
このファイルと `.claude_data/state/session.md` を起点に作業を再開してください。

## プロジェクト概要
- 言語/実行: Python（tkinter GUI）。オニオン構成（presentation / application / domain / infrastructure）。
- 対象アプリ: keyseq（キー割り当て/オーバーライドツール）。全体仕様は `instructions/common/`（`app_overview.md` / `codebase_map.md`）参照。
- **python 実行は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  依存 keyboard/pyautogui/pynput はこの `.venv` にのみ導入済み。グローバル `py` は使わない（tests_ui/smoke が落ちる）。
- **Codex は python を一切実行できない**（サンドボックス制約・回避不能）。実装委任にテスト実行を含めず、
  実測は `verifier`（またはメイン）が行う（理由は `instructions/common/rules_detail/codex_operations.md` §0）。

## 再開手順
1. `.claude_data/state/session.md` を読む（最重要・最新状態）
2. `.claude_data/state/decisions.md` を読む（判断履歴。**末尾の「計画05」節が現在の作業**。
   完了フェーズは「アーカイブ索引」→ `decisions_archive/<phase>.md`）
3. CLAUDE.md → `.claude/rules/` の順に必要分を読む
4. **現在の作業はフェーズではなく「計画05」**（計画04 と同じ運用）。
   **規範 = [modified_proposal/05_refactor_child_file_save_dialog.md](../../instructions/modified_proposal/05_refactor_child_file_save_dialog.md)**
   （ユーザー承認済 2026-08-03。**挙動不変のリファクタ**）。`instructions/phase/` にフォルダは作らない。
   `instructions/phase/current.md` は **Phase β = phase 06 完了**の記載が正で、次フェーズ γ は未起票。
   番号対応: **α=phase05/暫定04〔完了〕 / β=phase06/暫定05〔完了〕 / γ=phase07/暫定06〔未着手・暫定仕様は確定済〕 /
   プリセット=phase08/暫定07**（**計画05 はフェーズ番号を消費しないのでこの表に影響しない**）。
5. session.md.next_action から作業を再開する（**項目 1b から**）

## 現在の作業の 1 行サマリ
**計画05（config_service 等の分割リファクタ・挙動不変）を実施中。項目 0 / 1a 完了、次は項目 1b**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（項目 1a 完了時・コミット `db279e3`）: compile **clean** / tests **145** / tests_ui **159** / smoke **pass**。
**計画05 は挙動不変なので、この件数は全項目を通じて変わらないはず**（テストの追加・削除をしない）。
変わったら退行を疑う。実行後に worktree ルートへ `user/` が生成されていないことも確認する。

## 次アクション（session.md.next_action より）
- **項目 1b**: C（保存先の解決・命名 = `_resolve_sequence_save_path` / `_default_trigger_set_path` /
  `_allocate_unique_*` / `slugify_file_stem` 等・約 180 行）→ `save_path_resolution.py`、
  D（split 読込 = `_build_runtime_data_from_split` / `_load_keymap_entry` /
  `_load_triggers_from_trigger_set` 等・約 204 行）→ `split_loading.py` へ抽出。
  **1a と同じ方式**（`service` を第 1 引数に取るモジュール関数 / 互換ラッパを作らない）。
  完了条件は親 `__init__.py` が **600 行未満**（`wc -l` で確認・現在 1011 行）。
  流れ: codex-implementer へ委任 → **verifier で実測** → reviewer → `/task_commit`。
- そのあと**項目 2**（`_collect_child_save_plan` の分割）。**項目 2 は γ とほぼ無関係のため、
  途中で止めて γ へ移ってもよい**（ユーザー確定済）。
- 計画05 完了後に **`/phase_start` で phase 07（γ）を起票**する
  （主入力 = `instructions/history/06_hook_keys_global_default.md`・ユーザー確定済）。

## 計画05 の要点（規範 = modified_proposal/05）
- **唯一の合格条件は「挙動不変」**。挙動・エラーメッセージ・**保存 JSON のバイト列**を変えない。
  変更が必要になったら `/refactor_check` の範囲外 → 止めてユーザーへ報告する。
- **1 項目 = 1 コミット**（項目 1 のみ 1a / 1b の 2 コミット）。各段階で**フル検証 + reviewer**を通す。
- **【最重要・構造】`config_service` はパッケージ**（`keyseq/application/config_service/`）で、
  **ConfigService 本体は `__init__.py`**（`config_service/config_service.py` **ではない**）。
  理由: テスト 4 箇所が `patch("keyseq.application.config_service.os.path", ntpath)` で
  **モジュール名前空間の `os.path` を差し替えている**ため、この配置を崩すと壊れる
  （`tests/test_config_service.py:429` / `:789` / `tests/test_config_paths.py:113` /
  `tests/test_child_save_rows.py:201`）。
- 兄弟モジュール（1a 完了分）: `save_plan_execution.py`（保存計画の実行・検証・適用・依存判定）/
  `split_payloads.py`（payload 構築）。抽出関数は **`service` を第 1 引数に取り**、本文は
  `self.X` → `service.X` の機械的置換のみ。**兄弟から `__init__` を import しない**（循環回避）。
  公開メソッド（`save_runtime_data` / `resolve_child_save_targets` / `find_dependency_blocked_sequences`）は
  **薄い委譲として親に残す**。private ヘルパの**互換ラッパは作らない**。
- 安全網（項目 0 で実測・追加テスト不要）: 保存 JSON のバイト列比較 **21 箇所** /
  `tests/test_save_plan.py` **12 件**（失敗時の旧索引維持・**子 → 親 → 起動設定の書き込み順序**・
  deferred index・SKIP の索引規則）/ `tests_ui/test_child_save_dialog.py` **46 件**。

## 直前フェーズ（Phase β = phase 06）の要点
- **完了済み**（コミット `976b3da` / `03b52d0`）。**設計の正は正本**:
  `spec_detail/data_schema.md` **§5.8**（子ファイルの保存計画と参照元記録）+ §5.4 / §5.6 / §5.7、
  `features.md` **§4.6**（子ファイル保存ダイアログの表示要件）、`codebase_map.md`。
  暫定仕様 05 は**凍結済み**（経緯の参照用）。判断履歴は `decisions_archive/06_child_file_save_dialog.md`。
- 成果: keymap_set の「保存」を**子ファイルごとに 保存 / 別名保存 / 保存しない を選ぶ確認ダイアログ**へ置換。
  **責務分担 = 保存計画の決定は presentation・実行は application**。
- 子ファイル保存の触点: `child_save_rows.py`（共有状況判定）/ `child_save_dialog.py`（一覧 UI + 依存確認）/
  `child_save_plan.py`（選択 → 計画の純変換）/ `keymap_set_io.py`（一括経路）/
  `trigger_set_file_io.py`（個別経路）/ `config_service.save_runtime_data`（実行）。

## 注意事項・blockers
- **blockers: なし**。
- **【最重要・2 度踏んだ罠】パス表記の混在事故**: runtime の `source_path` 3 種は **config 配下なら相対**で
  保持される（config 外は絶対・区切りは `/` 正規化）。**相対値を `os.path.abspath` / `dirname` / `exists` /
  `join` へ解決なしで渡すと cwd 基準で解決される**。症状 = **リポジトリルートに `user/` が生成される** /
  「別名で保存」が前回の場所に開かない。解決は `ConfigService.resolve_config_path(path, config_root)`。
  `to_config_relative_or_absolute` は**入口で解決するので相対を渡してよい**（2026-08-03 に修正）。
- **不変条件（壊しやすい）**: ① `dirty_tracker.trigger_set_source_path` と
  `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致**（入口は `dirty_state` のメソッドのみ・内部キー直代入禁止）/
  ② 子の `_parent_refs` は**保存先ファイルの集合 + 現在の上位**（in-memory の旧 refs を持ち込まない）/
  ③ **canonical identity は比較専用**（`canonical_path` / `is_path_within` を使い、`normcase` 済み文字列を
  保存値・戻り値・表示へ混入させない）/ ④ **共有状況は判定名で分岐する**（`SHARE_SOLE` / `SHARE_NEW`。
  表示文言 `share_text_for` で分岐しない）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  テスト内の `AssertionError` も広い `except Exception` に捕まり、**失敗が「ハング」に化ける**。
  tests_ui の 3 ファイル（`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup`）の `setUp` に **fail-fast ガード**がある。
  期待するテストは個別 patch で上書きする。新しいモーダルを増やすときは同じガードを足す
  （`askyesnocancel` はガードへ入れない）。**ハングしたら `messagebox` / `filedialog` を全遮断して単独実行**すると
  真因が一発で出る（実測 1 秒以下）。
- **【tests_ui の罠】`_prepare_loaded_keymap_set` は `save_plan=None` で `save_runtime_data` を呼ぶため
  runtime に source_path が入らない**。source_path 前提のテストは保存後に
  `load_runtime_data_from_keymap_set_path` → `apply_loaded_data_to_ui` で読み直すこと。
  怠ると個別保存が「保存先を選ぶ」分岐へ落ち、**実リポジトリの `config/` にモーダルを開いてハングする**。
- **【教訓・UI】tkinter の「初期表示だけ崩れる」系は one-shot の再計算（`after_idle` 1 回）では直らない**。
  **対象ウィジェット自身の `<Configure>` で自己修復させる**（同幅早期 return を必ず併設）。
- **【Codex 運用】フォワーダが最終出力を返さないまま完了通知だけ来る / 差分 0 件で返る**ことがある
  → `SendMessage` で同じフォワーダを再開して回収する。**Codex 申告のテスト結果は信用せず必ず verifier で再実測**。
  手順書は `instructions/common/rules_detail/codex_operations.md`。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。編集は必ず worktree ルート配下で。
- **【罠】Bash ツールは Git Bash**。PowerShell の here-string（`@'...'@`）はコミットメッセージに `@` が混入する。
  複数行は heredoc（`git commit -F - <<'EOF'`）を使う。
- **【罠】`git grep` は追跡済みのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。行数計測は `wc -l`。
- **【傾向】reviewer が「完了可」でも実測で落ちることがある**。**判定はテストの実測が優先**。
  fail が出たら**まず production か test かを切り分ける**（既知の期待値誤り: `slugify_file_stem` は
  大文字小文字を変換しない / `source_path` は config_root 相対）。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  Codex レビュー系との併用は `.claude/rules/agent_selection.md` のレビュー表が正。出力の作法は
  `.claude/rules/output_style.md`。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **06_child_file_save_dialog** / 05_keymap_set_new_and_default_dir / 04_config_io_controller_split）。
- 未着手/保留 idea: idea_07（参照元の掃除・**β 完了で着手可**）/ idea_03（hotkey 保存正規化・低）/
  idea_08（個別プリセット）/ idea_09（レガシー保存パス）/ idea_04・idea_06（保留）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
