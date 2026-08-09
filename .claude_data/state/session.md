# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-10T09:30:00
phase: `instructions/phase/09_per_keymap_set_presets`（**task_04 完了 / 次は task_05**。暫定仕様 08 は **v0.4・ユーザー確定済**）
last_commit_location: claude/task-04-progression-dbaaef ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 09 は task_04（保存先の算出と書込先の切替）まで完了し、読み書き両方が個別／グローバルへ分岐するようになった。次は task_05 = 切替 UI（マネージャ内のチェック・保存先表示・OK/キャンセルの契約）**。
mode: implementing

## last_action
ts: 2026-08-10T09:30:00
who: main
summary: |
  【phase 09 task_04 = **保存先の算出と書込先の切替**（暫定仕様 08 §2【G】【B】【H】【O】/ §3-3）】
  - `save_path_resolution.default_individual_hotkey_presets_path` を追加
    （trigger_set と同じ流儀・`slugify_file_stem`・フォールバック `default`・衝突回避しない）。
    **グローバル既定は `global/` 配下なので stem が `default` でも衝突しない**（task_01 の狙い）。
  - `ConfigService.save_hotkey_presets(presets, *, config_root, stored_path)` を新設し
    `save_global_hotkey_presets` を**薄いラッパ**へ（**読み出し側と対称**）。
  - 書込先の決定は `split_loading.resolve_hotkey_presets_save_path` に集約し、
    **task_03 の `resolve_individual_hotkey_presets_path` を再利用**（判定を二重化しない）。
    分岐 = ON+有効パス → そのパス / ON+パス未設定 → 既定パス（保存表記へ変換）/
    **ON+config 外 → 空文字（グローバル）** / OFF・フラグ無し・`config_root` 空 → 空文字。
  - presentation: `write_global_presets` → **`write_presets(presets, *, stored_path)`** へ改名
    （旧名の残存ゼロ）。`App.save_hotkey_presets` は **成功時のみ**
    `data["hotkey_presets_path"]` を確定値へ反映（**フラグは変えない**）。
  - **【H】ON にした時点ではファイルを作らない**（実体は保存時に初めて作られる）。
  - **【Codex 運用インシデント】** フォワーダがハング復旧中に `taskkill /PID <pid> /T /F` を実行し、
    **PID 再利用により無関係な `node_repl` 約 22 個を巻き込んで終了**させた。
    → **以後 taskkill /T は使わない**。詰まったら `codex_operations.md` §4 の **state 手修復**へ倒す。
result_files:
  - instructions/phase/09_per_keymap_set_presets/tasks/task_04_individual_save_target.md（新規・起票）
  - keyseq/application/config_service/{__init__.py,save_path_resolution.py,split_loading.py}
  - keyseq/presentation/app.py / controllers/config_io/hotkey_presets_io.py
  - tests/test_config_service.py / tests_ui/test_app_ui_flows.py
verified:
  compile: clean
  tests: pass **220**（基準線 216 → +4）
  tests_ui: pass **189**（基準線 186 → +3）
  smoke: pass
  review: `reviewer` = **採用（完了可）**。全分岐の追跡 / 判定の非二重化 / 【H】/ 失敗時に data 不変 /
    保存側で正規化なし / 改名の追随を確認。**参考指摘 1 件**（既定ディレクトリを
    `dirname` 二重適用で導いており定数の階層変更で黙って壊れる。非ブロッキング）

## next_action
- **task_05 を `/task_new` で起票 → 実装委任**する（規範 = 暫定仕様 08 **§2【D】【E】【F】【J】【Q】【R】/ §3-4**）。内容:
  1. **プリセットマネージャ内に「この構成セット専用にする」チェック**を置く
  2. **トグルは保存先の切替だけ**（**一覧は差し替えない**。【I】は撤回済み）。保存先パス表示は追従
  3. **OK で確定・キャンセルで何も変えない**（フラグ・dirty・ファイルのいずれも）
  4. **OK の挙動**: ON なら個別へ書いて runtime 反映 /
     **OFF へ戻したら書かずにグローバルを読み直す**（グローバルを上書きしない）
  5. **切替の確定は keymap_set を dirty にする**（内容編集は dirty にしない）
  6. **keymap_set 未保存なら ON 不可**（UI で無効化し理由表示。保存/読込/新規作成の後に再評価）
  7. **保存先表示の出し分け**（個別 / フォールバック中「グローバルを表示中」/
     両方読めない「読み込めませんでした（既定を表示中）」/ config 外で無効）
  - **tests_ui から操作できる形か**を実装前に確認（`PresetManagerDialog` は `wait_window` を使うため、
    既存テストは `on_ok` 直呼び等で回避している）
- 以降の流れ（各タスク共通）: 実装委任（**テスト追加まで含める / 実行は依頼しない**）→
  `verifier` で実測 → `reviewer` → `/save_state` + `/task_commit`。

## blockers
- なし。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
- **【phase 08 の成果は正本が正】** `spec_detail/data_schema.md` **§5.10**（プリセットの全体ライブラリ）
  + **§5.8.8**（**全体デフォルトの入口台帳 E1〜E5 / L1〜L3 / N1**）+ §5.1 の例外 + `codebase_map.md`。
  暫定仕様 07 は**凍結済**。要点だけ再掲 = ①runtime を新規化・置換したら
  **`apply_global_defaults` を呼ぶ**（通常読込は経由しないが供給規則は共通 /
  **ON→OFF の hook キー単独注入だけ `apply_global_hook_key_defaults` を直呼び**）
  ②プリセットの読み出しは **`list | None`**（読めたら空でも採用 / `None` は置き換えない）で
  **読み出し側で正規化**（**非文字列 `label`/`value` の要素は除去**。ここを緩めると起動不能が再発する）
  ③**書き手は `PresetManagerDialog.on_ok` → `App.save_hotkey_presets` →
  `HotkeyPresetsIo` → `ConfigService.save_global_hotkey_presets` の 1 本のみ**
  （カスケードは書かない / 失敗時は確定せずダイアログを閉じない / dirty を汚さない）。
- **【tests_ui の罠・追加】`AppUiFlowsTest` は `setUpClass` で App を 1 つ共有する**ため、
  `has_unsaved_changes()` は他テストが残した個別 dirty も拾う。**絶対値で assert せず、
  前後の変化 / `set_dirty` の呼出有無で見る**こと（task_06 で 1 度踏んだ）。
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
  tests_ui の 4 ファイル（`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup` / `test_app_ui_flows`）の
  `setUp` に **fail-fast ガード**がある。
  新しいモーダルを増やすときは同じガードを足す。**ハングしたら `messagebox` / `filedialog` を全遮断して
  単独実行**すると真因が一発で出る。
- **【tests_ui の罠】`_prepare_loaded_keymap_set` は `save_plan=None` で `save_runtime_data` を呼ぶため
  runtime に source_path が入らない**。source_path 前提のテストは保存後に
  `load_runtime_data_from_keymap_set_path` で読み直すこと。
- **【Codex 運用・重要】詰まったジョブに `taskkill /T` を使わない**（PID 再利用で**無関係な
  プロセスを巻き込む**。phase 09 task_04 で `node_repl` 約 22 個を巻き込んだ実害あり）。
  **`codex_operations.md` §4 の state 手修復**（backup してから `cancelled` へ書換・`.log` は保全）に倒す。
- **【Codex 運用】**フォワーダが最終出力を返さず完了通知だけ来ることがある（`SendMessage` で再開して回収）。
  **Codex 申告のテスト結果は信用せず必ず verifier で再実行**。**Codex は python をまったく実行できない**
  → 委任にテスト実行を含めない。手順書は `instructions/common/rules_detail/codex_operations.md`。
- **【罠】state ファイル・`instructions/` 配下・code は必ず worktree のパスで編集する**（main 側を編集すると
  commit から漏れる）。`git grep` は追跡済みファイルのみ。行数計測は `wc -l`。
- **レビュアーは 2 本立て**: `reviewer`（sonnet・単一タスクの実装差分）/ `deep-reviewer`（opus・設計文書 /
  複数タスクを跨ぐ差分 / フェーズ完了判定）。使い分けは `.claude/rules/agent_selection.md` が正。
- **保存系リデザインの番号対応**: α=phase05/暫定04〔完了〕 / β=phase06/暫定05〔完了〕 /
  γ=phase07/暫定06〔完了〕 / プリセット=phase08/暫定07〔**完了**・decisions_archive 08〕 /
  **個別プリセット=phase09/暫定08〔着手中〕**。
  **計画05・計画06 はフェーズ番号を消費していない**（規範 = `modified_proposal/05_*.md` / `06_*.md`）。
- **【計画05 で変わった構造】`config_service` は単一ファイルではなく*パッケージ***
  （`keyseq/application/config_service/`）。**ConfigService 本体は `__init__.py`**
  （テストが `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため、
  この配置を崩すと 4 テストが壊れる。同じ理由で**パス基盤メソッドを兄弟へ移さない**）。
  兄弟 = `save_plan_execution.py` / `split_payloads.py` / `save_path_resolution.py` / `split_loading.py`。
  抽出関数は **`service` を第 1 引数に取る**。兄弟から `__init__` を import しない（循環回避）。
- config_io は `controllers/config_io/` へ分割済（App が `app.keymap_set_io` 等で直接公開）。
- 未着手 idea: idea_07（参照元の掃除・**着手可**）/ idea_03（hotkey 保存時正規化・優先度低）/
  idea_09（レガシー settings/ フォールバック・優先度低）。**idea_08 は phase 09 で着手中**。
  保留 idea: idea_04 / idea_06（**残る着手条件は「共通化の実需」1 つのみ**）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 06_child_file_save_dialog / 07_hook_keys_global_default /
  **08_hotkey_presets_global**。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
