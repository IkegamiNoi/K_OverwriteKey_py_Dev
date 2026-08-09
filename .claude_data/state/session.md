# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-09T00:00:00
phase: `instructions/phase/08_hotkey_presets_global`（**task_04 完了 / 次は task_05**。暫定仕様 07 は **v0.5・確定済**）
last_commit_location: claude/task-04-progression-dbaaef ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 08 は task_04（`apply_global_defaults` 新設 + 入口台帳 E1〜E5 配線）まで完了。次は task_05 = keymap_set payload からの `hotkey_presets_path` 生成停止 + 保存カスケードからのプリセット除外**。
mode: implementing

## last_action
ts: 2026-08-09T00:00:00
who: main
summary: |
  【phase 08 task_04 = **注入入口の一本化を実装**（暫定仕様 07 §3-2・v0.5 の実装）】
  - **application**: `split_loading.load_global_hotkey_presets(service, *, config_root) -> list | None` を新設
    （読めた＝`list`〔空含む〕/ 不存在・破損・非 dict・根キー非 list＝`None`。`load_named_list` は不使用）。
    `ConfigService.apply_global_defaults(runtime, *, config_root)` を新設し、既存
    `apply_global_hook_key_defaults` をそのまま呼んだ上でプリセットを供給（`list` なら置換・`None` なら非置換）。
  - **通常読込も同規則へ統一**: `build_runtime_data_from_split` は `load_global_hotkey_presets` の結果を使い、
    `None` なら組込 8 件を維持（`apply_global_defaults` は経由しない）。
  - **presentation（層跨ぎの配線変更）**: 入口台帳 **E1〜E5** を `apply_global_defaults` へ置換
    （`app.py:77` は**新規に 1 行追加**して順序依存の穴を塞いだ / `keymap_set_io.py:54,562,600` /
    `startup_io.py:36`）。**L1〜L3・N1 は無配線**、`toggle_hook_keys_individual` の ON→OFF は
    **単独注入のまま**（受入条件 8）。
  - **既存テスト 2 件を期待値更新**（緩和ではなく値比較）: `test_missing_or_invalid_global_presets_file_*` /
    `test_legacy_keymap_set_presets_path_loads_without_error` → 読めないときは**組込 8 件が残る**。
result_files:
  - instructions/phase/08_hotkey_presets_global/tasks/task_04_apply_global_defaults.md（新規・起票）
  - keyseq/application/config_service/split_loading.py / keyseq/application/config_service/__init__.py
  - keyseq/presentation/app.py / controllers/config_io/keymap_set_io.py / controllers/config_io/startup_io.py
  - tests/test_config_service.py / tests_ui/test_app_ui_flows.py /
    tests_ui/test_config_io_characterization_keymap_set_startup.py
verified:
  compile: clean
  tests: pass **186**（基準線 180 → +6）
  tests_ui: pass **181**（基準線 178 → +3）
  smoke: pass
  review: `reviewer` = **採用（完了可・指摘なし）**。5 観点 + §3-2 適合・台帳網羅・受入条件 7/8/9 を確認

## next_action
- **task_05 を `/task_new` で起票 → 実装委任**する（規範 = 暫定仕様 07 **§2 指摘②・④** / 受入条件 **2・4**）。内容:
  1. **keymap_set payload から `hotkey_presets_path` の生成を停止**
     （`split_payloads.py:39-42 / :102 / :299 / :337` が対象。既存キーの**能動削除はしない**）
  2. **保存カスケードからプリセット書出を除外**（`save_plan_execution.py:135-136`。
     `save_runtime_data` はプリセットファイルを書かない）
  3. 影響を受ける既存テストの期待値更新（`tests/test_save_plan.py` に
     `hotkey_presets_path` / プリセットファイル生成を前提とした箇所あり。**保存 JSON のキー順を固定する
     `test_saved_keymap_set_json_keeps_stable_key_order` に注意**）
- 以降の流れ（各タスク共通）: 実装委任（**テストコードの追加まで含める / 実行は依頼しない**）→
  `verifier` で実測 → `reviewer` → `/save_state` + `/task_commit`。
- 残タスク: task_05（保存側）→ task_06（プリセットマネージャの即時保存）→ task_07（統合 + 実機目視）→
  task_08（正本反映・凍結・`/refactor_check`）。

## blockers
- なし。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
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
