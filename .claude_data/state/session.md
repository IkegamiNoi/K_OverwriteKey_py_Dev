# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-10T17:30:00
phase: `instructions/phase/09_per_keymap_set_presets`（**task_06 完了 / 次は task_07**。暫定仕様 08 は **v0.6・ユーザー確定済**）
last_commit_location: claude/task-05-progression-a013e2 ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 09 は task_06（Import の強制 OFF + 別名保存時の複製）まで完了し、実装タスクが全て揃った。次は task_07 = 統合確認 + 実機目視（受入条件 1〜17）**。
mode: implementing

## last_action
ts: 2026-08-10T17:30:00
who: main
summary: |
  【phase 09 task_06 = **Import での強制 OFF + 別名保存時の個別ファイル複製**
  （暫定仕様 08 §2【K】【L】【M】【B】/ §3-2 / §3-3・受入条件 7 / 12 / 16）】
  - **強制 OFF**: `ConfigService.clear_individual_hotkey_presets(runtime)` を新設
    （**キーが無くても** `hotkey_presets_individual=False` / `hotkey_presets_path=""` を設定。
    **`hotkey_presets` の内容には触らない**）。呼び出しは `import_config` の
    **`load_legacy_runtime_data` 直後・`apply_global_defaults` 直前の 1 箇所だけ**
    （**`ensure_config_compatibility` / 通常読込へ波及させない**）。以後は E5 としてグローバルが供給される。
  - **複製**: `ConfigService.relocate_individual_hotkey_presets(runtime, *, config_root, keymap_set_path)`。
    新しい保存先 stem から既定パスを再計算し、**コピー元が有効かつ実体あり かつ コピー先に実体なし**の
    ときだけ `shutil.copyfile`。コピー先に実体あり / コピー元の実体なし / コピー元が config 外 /
    同一パス → **複製せずパスだけ返す**。**元ファイルは消さず、runtime の内容も書き出さない**
    （書き手はマネージャ 1 本のまま）。
  - **起票時の判断**: 複製の起動条件を **`save_path != self._app.keymap_set_path`（＝保存先そのものの変化）**
    に限定した。`save_as` と通常保存は同じ `save_keymap_set_to` を通るため、
    「算出した既定パスと記録済みパスの不一致」で判定すると、**個別パスを手で `custom.json` 等に
    設定した構成セットで通常保存しただけで勝手に付け替えが走る**。
  - 呼び出しは `save_runtime_data` の直前・`keymap_set_path` 更新より前。返り値が非空なら
    `data["hotkey_presets_path"]` へ反映してから保存する（**新しい payload に新パスが載る**）。
  - **【M】同一 stem の無警告共有は既知の制約**として許容（上書き確認を新設しない）。
result_files:
  - instructions/phase/09_per_keymap_set_presets/tasks/task_06_import_off_and_save_as_copy.md（新規・起票）
  - keyseq/application/config_service/__init__.py
  - keyseq/presentation/controllers/config_io/keymap_set_io.py
  - tests/test_config_service.py
  - tests_ui/test_config_io_characterization_keymap_set_startup.py
verified:
  compile: clean
  tests: pass **225**（基準線 222 → +3）
  tests_ui: pass **202**（基準線 199 → +3）
  smoke: pass
  review: `reviewer` = **採用（完了可）**。強制 OFF が Import 1 箇所 / 複製が別名保存のみ /
    コピー先を上書きしない / 元ファイルを消さない / 内容を書き出さない（`shutil.copyfile`）/
    既存関数の再利用 / 読み出し側・保存先算出・マネージャ・dirty 不変 を確認。
    **参考指摘 1 件**（「コピー元とコピー先が同一パス」分岐に明示テストが無い。
    既存の exists 判定でも実質スキップされるため実害なし・非ブロッキング）

## next_action
- **task_07 を `/task_new` で起票**する（**統合確認 + 実機目視**。規範 = 暫定仕様 08 **§5 受入条件 1〜17**）。
  - **実測（テストスイート全体・smoke）は `verifier`**、**二次レビューは `deep-reviewer` +
    Codex レビュー系の 2 本立て**（`agent_selection.md` の「統合テスト・複数タスクを跨ぐ差分」）。
  - **実機目視の観点をタスク定義で列挙する**（ユーザーが実施 → 指摘の是正まで task_07）。
    最低限: ①ON/OFF の切替と保存先表示 ②フォールバック時の「グローバルを表示中」
    ③未保存 keymap_set で ON 不可 ④無効パスで既定へ寄る（v0.6【O3】）
    ⑤Import 後に個別 OFF ⑥別名保存で個別ファイルが複製される
    ⑦**手動移行の 2 段**（ファイル移動 + config.json の明示値）を実際に踏む。
  - **フェーズ完了判定の 2 本立てレビューは省略しない**（phase 08 で両者が独立に起動不能バグを検出）。
- その後 **task_08 = 正本反映（最終）**: `data_schema.md` §5.10 改訂 + §5.5 / §5.4 / §5.8.8 / §5.1 +
  `codebase_map.md` / 暫定仕様 08 を凍結 / `decisions_archive/09_per_keymap_set_presets.md` 作成 /
  `current.md` 完了更新 / `backlog/INDEX.md` の idea_08 を `INDEX_done.md` へ移動 / `/refactor_check`。
  - **v0.5 →v0.6 の反転（【O3】）と dirty 規則**、**task_05b が task_05c で置き換わった経緯**を
    decisions_archive へ集約すること。
- 以降の流れ（各タスク共通）: 実装委任（**テスト追加まで含める / 実行は依頼しない**）→
  `verifier` で実測 → `reviewer` → `/save_state` + `/task_commit`。

## blockers
- なし（task_05 で挙がった「config 外の無効な個別パスで OK したときの保存先」は
  **v0.5【O3】= 拒否 → v0.6【O3】= 既定パスへ寄せて新規作成 へ反転して決着**。実装は task_05c）。

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
