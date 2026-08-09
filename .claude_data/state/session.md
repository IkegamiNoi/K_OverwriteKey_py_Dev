# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-09T08:20:00
phase: `instructions/phase/08_hotkey_presets_global`（**task_07b 完了 / task_07 は実機目視のみ未了**。暫定仕様 07 は **v0.6・確定済**）
last_commit_location: claude/task-04-progression-dbaaef ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 08 は task_07b（横断レビュー指摘の是正）まで完了。残るは task_07 の実機目視のみで、その後 task_08（正本反映）**。
mode: pending_review

## last_action
ts: 2026-08-09T08:20:00
who: main
summary: |
  【phase 08 task_07（統合確認）→ 指摘を受けて暫定仕様 **v0.6** 確定 → **task_07b で是正**】
  - **自動確認は全 pass**。`codex-reviewer` = 指摘なし。**`deep-reviewer` = 修正要**（実測付き）。
  - **ユーザー確定（4 件）**:
    ① **H1 = 読み出し側で正規化**（注入経路 E1/E3/E4/E5 が非正規化のままで、非 dict 要素が
    runtime に残り `AttributeError` の破綻面だった）→ v0.6 §3-2 へ規則追加 + task_07b で実装
    ② **受入条件 7 を「グローバルが読めた場合」へ限定**（`None` 時の経路差と条項間矛盾していた）
    ③ **M3（`None` 時の上書き内容が入口経路で割れる）は現状を制約として明文化**（実装は変えない）
    ④ task_07b へ **M1（死にコード `load_named_list` 削除）/ M2（E1 の特性テスト）/ L3（deepcopy）** を同梱
  - **task_07b の実装**: `normalize_hotkey_presets` を **domain の純関数へ切り出し**
    （`ensure_config_compatibility` は呼ぶだけ・既定値縮退は元の場所に残す = 挙動不変）→
    `load_global_hotkey_presets` が**正規化済みを返す**（**`None` 判定は正規化の前**）。
    `load_named_list` 削除 / `save_hotkey_presets` を `safe_deepcopy` 代入へ。
  - **L1 / L2 / L4（旧「別ディレクトリ保存」の孤児プリセット / Export のデッドデータ /
    `hotkey_presets_path` はアプリが書かない）は task_08 で正本へ文書化**（暫定仕様 §7 へ列挙済）。
result_files:
  - instructions/history/07_hotkey_presets_global.md（**v0.6**）
  - instructions/phase/08_hotkey_presets_global/tasks/task_07_integration_and_manual_check.md（新規・実施記録付き）
  - instructions/phase/08_hotkey_presets_global/tasks/task_07b_normalize_presets_on_read.md（新規）
  - instructions/phase/08_hotkey_presets_global/phase.md（task_07b を 1 行追記）
  - keyseq/domain/config.py / keyseq/application/config_service/split_loading.py / keyseq/presentation/app.py
  - tests/test_domain_config.py / tests/test_config_service.py / tests_ui/test_app_ui_flows.py
verified:
  compile: clean
  tests: pass **198**（基準線 193 → +5）
  tests_ui: pass **186**（基準線 185 → +1）
  smoke: pass
  review: task_07 横断 = `codex-reviewer` **指摘なし** + `deep-reviewer` **修正要**（→ v0.6 + task_07b で解決）/
    task_07b = `reviewer` **採用（完了可・指摘なし）**

## next_action
- **task_07 の実機目視を実施**（ユーザー担当。結果を task_07 定義の「実施記録」へ追記する）。観点 6 件:
  ①全 keymap_set で共通 ②編集が即時にファイルへ入る（keymap_set 未保存で再起動）
  ③保存失敗時に編集内容が残る（ファイルを読み取り専用にする。**属性は必ず戻す**）
  ④keymap_set 保存でプリセットが書かれない（更新日時 / 別名保存先に `hotkey_presets/` が出来ない）
  ⑤既存 `hotkey_presets_path` 付き keymap_set の後方互換（再保存で当該キーが消える）
  ⑥**【task_07b の確認】破損 JSON / 非 dict 要素を含むプリセットファイル**で起動・編集しても落ちない
- その後 **task_08（最終）**: 正本 `spec_detail/data_schema.md` + `codebase_map.md` へ昇格
  （**反映する具体項目は暫定仕様 07 §7 の「v0.6 追記」に列挙済み**。L1 / L2 / L4 の文書化を含む）/
  暫定仕様 07 を凍結 / `decisions_archive/08_hotkey_presets_global.md` 作成 /
  `current.md` 完了更新 / `backlog/INDEX.md` の **idea_08** 行を着手可へ更新 / `/refactor_check` 実行。

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
