# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-09T06:30:00
phase: `instructions/phase/08_hotkey_presets_global`（**task_05 完了 / 次は task_06**。暫定仕様 07 は **v0.5・確定済**）
last_commit_location: claude/task-04-progression-dbaaef ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 08 は task_05（保存側からのプリセット切り離し）まで完了。次は task_06 = プリセットマネージャの編集をグローバルファイルへ即時保存（成否付き）**。
mode: implementing

## last_action
ts: 2026-08-09T06:30:00
who: main
summary: |
  【phase 08 task_05 = **保存側からプリセットを切り離す**（暫定仕様 07 §2 指摘②・④ / 受入条件 2・4）】
  - **application 限定**（`split_payloads.py` / `save_plan_execution.py`。差分は削除のみ）:
    `build_keymap_set_payload` から `hotkey_presets_path` 引数と返却キーを削除 /
    `build_split_save_payloads` からプリセットパス算出・payload 生成・返却 2 キーを削除 /
    保存カスケードのプリセット書込を削除。**残りのキー順・書込順は不変**。
  - **既存キーの能動削除はしていない**（生成停止による自然消滅。`test_resaving_legacy_keymap_set_*` で固定）。
  - **【中間状態・意図的】task_06 までプリセットの書き手が居ない**（保存では書かず、マネージャは未対応）。
  - **verifier 初回で tests fail（190 中 ERROR 1 / FAIL 1）** → `tests/test_config_service.py` の追随漏れ
    2 件（`build_keymap_set_payload` への廃止引数 / round-trip のプリセットファイル存在前提）を
    Codex へ差し戻して修正 → 再実測で全 green。**reviewer は tests_ui しか見ておらず拾えなかった**。
result_files:
  - instructions/phase/08_hotkey_presets_global/tasks/task_05_stop_writing_presets_on_save.md（新規・起票）
  - keyseq/application/config_service/split_payloads.py / keyseq/application/config_service/save_plan_execution.py
  - tests/test_save_plan.py / tests/test_config_service.py
verified:
  compile: clean
  tests: pass **190**（基準線 186 → +4）
  tests_ui: pass **181**（増減なし）
  smoke: pass
  review: `reviewer` = **採用（完了可・指摘なし）**。受入条件 2・4 / 能動削除なし / キー順・書込順の保持を確認
    （※実測の失敗 2 件はレビュー範囲外だったため、修正後にメインで差分を直接確認した）

## next_action
- **task_06 を `/task_new` で起票 → 実装委任**する（規範 = 暫定仕様 07 **§2 指摘③ / §3** / 受入条件 **3**）。内容:
  1. **`PresetManagerDialog` の編集確定（`dialogs.py:507` 付近）を、config.json が指すグローバル
     プリセットファイルへの即時保存へ変更**（書き手はプリセットマネージャのみ）
  2. **成否付き**（phase 07 の `write_global_hook_keys` と同じ契約）。
     **保存失敗時は編集内容を失わず・確定もしない**
  3. dirty を汚さない（keymap_set の保存状態と独立）
  4. 保存先パスは `load_global_hotkey_presets_path`（task_01）を使う。**presentation から
     `os.path` 系へ生の相対値を渡さない**（`resolve_config_path` の罠）
  5. tests_ui の modal ガード（`.claude_data/state/session.md` の罠メモ）に従い、新しい
     `messagebox` を増やすなら fail-fast ガードを足す
- 以降の流れ（各タスク共通）: 実装委任（**テスト追加まで含める / 実行は依頼しない**）→
  `verifier` で実測 → `reviewer` → `/save_state` + `/task_commit`。
- 残タスク: task_06（マネージャの即時保存）→ task_07（統合 + 実機目視・受入条件 1〜6）→
  task_08（正本反映・凍結・`decisions_archive/08` 作成・`current.md` 完了更新・`/refactor_check`）。

## blockers
- なし。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
- **【phase 08 task_05 の中間状態】保存側はもうプリセットを書かない**（`save_runtime_data` /
  カスケードから除外済・keymap_set payload にも `hotkey_presets_path` を生成しない）。
  **task_06 が完了するまで「プリセットの書き手が居ない」**。これは設計どおりの中間状態。
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
