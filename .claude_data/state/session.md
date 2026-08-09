# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-09T07:10:00
phase: `instructions/phase/08_hotkey_presets_global`（**task_06 完了 / 次は task_07 = 統合確認 + 実機目視**。暫定仕様 07 は **v0.5・確定済**）
last_commit_location: claude/task-04-progression-dbaaef ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 08 は task_06（プリセットマネージャの即時保存）まで完了し、実装タスクは全て終了。次は task_07 = 統合確認 + 実機目視（受入条件 1〜6）**。
mode: implementing

## last_action
ts: 2026-08-09T07:10:00
who: main
summary: |
  【phase 08 task_06 = **プリセットマネージャの即時保存**（暫定仕様 07 §2 指摘③ / 受入条件 3）】
  - **application**: `ConfigService.save_global_hotkey_presets(presets, *, config_root)` を新設。
    保存先は `load_global_hotkey_presets_path` → **`resolve_config_path` で解決**、
    形は読み出しと対称の `{"hotkey_presets": ...}`。**例外は握り潰さず送出**（成否判定は presentation の責務）。
  - **presentation（新規モジュール）**: `controllers/config_io/hotkey_presets_io.py` の
    `HotkeyPresetsIo.write_global_presets(presets) -> bool`（失敗は `messagebox.showerror` + `False`）。
    `config_io/__init__.py` へ追加。**`config_io` はファイル種別ごとの IO モジュール構成**に沿わせた。
  - **確定点**: `App.save_hotkey_presets` は**成功時だけ** `data["hotkey_presets"]` を反映。
    `PresetManagerDialog.on_ok` は**成功時だけ `destroy()`**（失敗時は閉じず `_temp` 保持 = 受入条件 3）。
  - **`open_preset_manager` から `set_dirty(True)` を削除**（プリセットは keymap_set の一部ではない）。
    flash message は維持。
  - **verifier 初回で tests_ui fail 1 件** → 原因は**テストの作り**（`AppUiFlowsTest` は
    `setUpClass` で App を共有し、`has_unsaved_changes()` が他テストの残した個別 dirty も拾う）。
    `set_dirty` 未呼出 + dirty 状態の不変を見る形へ差し戻し修正 → 再実測で全 green。
result_files:
  - instructions/phase/08_hotkey_presets_global/tasks/task_06_preset_manager_immediate_save.md（新規・起票）
  - keyseq/application/config_service/__init__.py
  - keyseq/presentation/controllers/config_io/hotkey_presets_io.py（新規）/ config_io/__init__.py
  - keyseq/presentation/app.py / keyseq/presentation/dialogs.py
  - tests/test_config_service.py / tests_ui/test_app_ui_flows.py
verified:
  compile: clean
  tests: pass **193**（基準線 190 → +3）
  tests_ui: pass **185**（基準線 181 → +4）
  smoke: pass
  review: `reviewer` = **採用（完了可・指摘なし）**。受入条件 3 / 書き手の一本化 / 例外の扱い /
    依存方向（dialog → App → controller → application）/ dirty 非汚染を確認

## next_action
- **task_07 を `/task_new` で起票 → 実施**する（受入条件 **1〜6** の通し確認）。内容:
  1. `verifier` で通しの再実測（compile / `tests` / `tests_ui` / smoke）
  2. **実機目視の観点をタスク定義で列挙**（ユーザーが実施 → 結果をメインへ報告）。最低限:
     ①プリセットが全 keymap_set で共通に見える ②マネージャの編集が即時にファイルへ入る
     ③保存失敗時に編集内容が残る（書込不可の状況を作る）④keymap_set 保存でプリセットが書かれない
     ⑤既存 `hotkey_presets_path` 付き keymap_set でも起動・保存が正常
  3. 指摘が出たら是正タスクを起票（枝番）
- その後 **task_08（最終）**: 正本 `spec_detail/data_schema.md` + `codebase_map.md` へ昇格
  （**§3-2 の注入契約 = `apply_global_defaults` を呼ぶ 5 経路 / ON→OFF は単独注入 / 通常読込は
  経由しない / 空リストでは置き換えない** も含める）/ 暫定仕様 07 を凍結 /
  `decisions_archive/08_hotkey_presets_global.md` 作成 / `current.md` 完了更新 /
  `backlog/INDEX.md` の **idea_08** 行を着手可へ更新 / `/refactor_check` 実行。

## blockers
- なし。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
- **【phase 08 で確定したプリセットの経路】書き手は
  `PresetManagerDialog.on_ok` → `App.save_hotkey_presets` → `HotkeyPresetsIo.write_global_presets`
  → `ConfigService.save_global_hotkey_presets` の 1 本のみ**（保存カスケードは書かない）。
  読み手は `load_global_hotkey_presets`（`list | None`）。**保存失敗時はダイアログを閉じず
  runtime も更新しない**。プリセット編集は **dirty を汚さない**。
- **【tests_ui の罠・追加】`AppUiFlowsTest` は `setUpClass` で App を 1 つ共有する**ため、
  `has_unsaved_changes()` は他テストが残した個別 dirty も拾う。**絶対値で assert せず、
  前後の変化 / `set_dirty` の呼出有無で見る**こと（task_06 で 1 度踏んだ）。
- **【phase 08 task_04 で入った契約】runtime を新規化・置換したら
  `ConfigService.apply_global_defaults(runtime, *, config_root)` を呼ぶ**（入口台帳 E1〜E5）。
  通常読込は経由しない（`build_runtime_data_from_split` が同じ供給規則を持つ）。
  **プリセットは `list | None`**（読めたら空でも採用 / `None` は置き換えない）。
  **ON→OFF の hook キー単独注入だけは `apply_global_hook_key_defaults` を直呼び**（受入条件 8）。
  台帳は暫定仕様 07 §3-2 が正。**正本 `codebase_map.md` への反映は task_08**。
- **hook キー（Phase γ の成果）は正本が正**: `spec_detail/data_schema.md` **§5.9** +
  `key_input.md` **§7.6** + `codebase_map.md`。暫定仕様 06 は**凍結済**（経緯の参照用）。
  要点だけ再掲 = **解決の分岐点は 4 つ**（`load_global_hook_keys` 読み出し /
  `build_runtime_data_from_split` 通常読込の選択 / `apply_global_hook_key_defaults` 新規化・置換経路
  〔**通常読込は経由しない**〕/ `build_keymap_set_payload` 保存側）。**フック層は無変更**が設計の芯。
- **【計画06 で変わった構造】hook キー名の定義元は `keyseq/domain/config.py` の `HOOK_STOP_KEY` /
  `HOOK_TOGGLE_KEY` / `HOOK_KEY_FIELDS`（対のタプル）+ `normalize_hook_key_pair()`**。新たに触る箇所は
  リテラルを書かずこれを使う（**添字参照 `HOOK_KEY_FIELDS[0]` は禁止**。反復・zip でのみタプルを使う）。
  意図的にリテラルのまま残した 3 箇所 = `DEFAULT_CONFIG` の既定値表 / `split_payloads` の返却 dict キー /
  `startup_io` の保存 dict キー。**保存 JSON のキー順は
  `tests/test_save_plan.py::test_saved_keymap_set_json_keeps_stable_key_order` が固定している**。
  `ensure_config_compatibility` と `build_keymap_set_payload` が `normalize_key_name` 直呼びのままなのは
  **非文字列時の例外を握り潰さないため**（`normalize_hook_key_pair` は `str()` を挟む）。
- **Phase β の成果も正本が正**: `data_schema.md` **§5.8**（子ファイルの保存計画と参照元記録）+
  §5.4 / §5.6 / §5.7、`features.md` §4.6、`codebase_map.md`。暫定仕様 05 は凍結済。
- **【最重要・2 度踏んだ罠】パス表記の混在事故**: runtime の `source_path` 3 種は **config 配下なら相対**で
  保持される（config 外は絶対・区切りは `/` 正規化）。**相対値を `os.path.abspath` / `dirname` / `exists` /
  `join` へ解決なしで渡すと cwd 基準で解決される**。症状 = **リポジトリルートに `user/` が生成される** /
  「別名で保存」が前回の場所に開かない。解決は `ConfigService.resolve_config_path(path, config_root)`。
  `to_config_relative_or_absolute` は**入口で解決するので相対を渡してよい**。
- **不変条件（壊しやすい）**: ① `dirty_tracker.trigger_set_source_path` と
  `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致**（入口は `dirty_state` のメソッドのみ）/
  ② 子の `_parent_refs` は**保存先ファイルの集合 + 現在の上位**（in-memory の旧 refs を持ち込まない）/
  ③ **canonical identity は比較専用**（`canonical_path` / `is_path_within` の 2 本。
  `normcase` 済み文字列を保存値・戻り値・表示へ混入させない）。
- **【共有状況の判定名と表示文言は別物】** 仕様書・タスク定義の「共有状況が単独 / 新規作成なら〜」は
  **判定名**（`SHARE_SOLE` / `SHARE_NEW`）を指す。**分岐は判定名で書き、文言で分岐しない**。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  tests_ui の 3 ファイル（`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup`）の `setUp` に **fail-fast ガード**がある。
  新しいモーダルを増やすときは同じガードを足す。**ハングしたら `messagebox` / `filedialog` を全遮断して
  単独実行**すると真因が一発で出る。
- **【tests_ui の罠】`_prepare_loaded_keymap_set` は `save_plan=None` で `save_runtime_data` を呼ぶため
  runtime に source_path が入らない**。source_path 前提のテストは保存後に
  `load_runtime_data_from_keymap_set_path` で読み直すこと。
- **【Codex 運用】**フォワーダが最終出力を返さず完了通知だけ来ることがある（`SendMessage` で再開して回収）。
  **Codex 申告のテスト結果は信用せず必ず verifier で再実行**。**Codex は python をまったく実行できない**
  → 委任にテスト実行を含めない。手順書は `instructions/common/rules_detail/codex_operations.md`。
- **【罠】state ファイル・`instructions/` 配下・code は必ず worktree のパスで編集する**（main 側を編集すると
  commit から漏れる）。`git grep` は追跡済みファイルのみ。行数計測は `wc -l`。
- **レビュアーは 2 本立て**: `reviewer`（sonnet・単一タスクの実装差分）/ `deep-reviewer`（opus・設計文書 /
  複数タスクを跨ぐ差分 / フェーズ完了判定）。使い分けは `.claude/rules/agent_selection.md` が正。
- **保存系リデザインの番号対応**: α=phase05/暫定04〔完了〕 / β=phase06/暫定05〔完了〕 /
  γ=phase07/暫定06〔**完了**・decisions_archive 07〕 / **プリセット=phase08/暫定07〔次・未起票〕**。
  **計画05 はフェーズ番号を消費していない**（規範 = `modified_proposal/05_*.md`）。
- **【計画05 で変わった構造】`config_service` は単一ファイルではなく*パッケージ***
  （`keyseq/application/config_service/`）。**ConfigService 本体は `__init__.py`**
  （テストが `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため、
  この配置を崩すと 4 テストが壊れる。同じ理由で**パス基盤メソッドを兄弟へ移さない**）。
  兄弟 = `save_plan_execution.py` / `split_payloads.py` / `save_path_resolution.py` / `split_loading.py`。
  抽出関数は **`service` を第 1 引数に取る**。兄弟から `__init__` を import しない（循環回避）。
- config_io は `controllers/config_io/` へ分割済（App が `app.keymap_set_io` 等で直接公開）。
- 未着手 idea: idea_07（参照元の掃除・**着手可**）/ idea_03（hotkey 保存時正規化・優先度低）/
  idea_08（keymap_set 個別プリセット）/ idea_09（レガシー settings/ フォールバック）。
  保留 idea: idea_04 / idea_06（**残る着手条件は「共通化の実需」1 つのみ**）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 05_keymap_set_new_and_default_dir / 06_child_file_save_dialog /
  **07_hook_keys_global_default**。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
