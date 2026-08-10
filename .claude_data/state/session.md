# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-10T19:00:00
phase: `instructions/phase/09_per_keymap_set_presets`（**task_07b 完了 / task_07 は実機目視待ち**。暫定仕様 08 は **v0.7・ユーザー確定済**）
last_commit_location: claude/task-05-progression-a013e2 ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 09 は task_07 の 2 本立てレビューで見つかったグローバル上書き経路を task_07b で塞ぎ、自動確認は全て green。残るは task_07 の実機目視（16 項目・ユーザー実施）→ task_08 正本反映**。
mode: pending_review

## last_action
ts: 2026-08-10T19:00:00
who: main
summary: |
  【phase 09 task_07（統合確認）の 2 本立てレビュー → **task_07b = 保存先ガードの是正**
  （暫定仕様 08 **§2【G】【O4】v0.7**・受入条件 9 / 11 / 18）】
  - **`deep-reviewer` と `codex-adversarial-reviewer` が独立に同じ穴（B1）を検出**
    （phase.md が「2 本立てを省略しない」とした狙いどおり）。両者とも**設計の骨格は
    正しく実現されている**判定で、作り直しは不要。
  - **B1**: config.json が `user/hotkey_presets/` **直下**を指し、その名前が構成セットの stem と
    一致すると、**専用プリセットとグローバルが同一ファイルの別名**になり、
    **専用側の編集が全構成セットのグローバルへ漏れ続ける**（一度きりの損失ではなく継続的なエイリアス）。
    到達には config.json の手編集が要る（**アプリはこのキーを書かない**＝
    `build_startup_payload` は既存キーを引き継ぐだけ）が、**一度書かれると round-trip で永久に保持**される。
  - **ユーザー確定 = ガードを入れる**（判断根拠: 関門は予約ディレクトリ規則で**どうせ作る**ので
    **追加コストが比較 1 個**。半分だけ実装して残りを開ける動機が無い）。
  - **暫定仕様を v0.7 へ改訂**: ①**【G】に `global/` の予約規定**（グローバルはここに置く前提を明文化）
    ②**【O4】保存先ガード新設** = **`global/` 配下** または **グローバルの読み先と同一** なら**拒否**
    ③**未定義だった 3 挙動を既知の制約として明記**（N3 残置パスの初回 ON / N4 複製失敗時の成否 /
    N6 OFF 復帰時にグローバルが読めない場合）。**挙動は変えない**。
    ④§3-1 に payload 正規化（N2）/ 受入条件 18 を追加。
  - 実装: `individual_hotkey_presets_save_rejection_reason`（application・理由 2 値）+
    `hotkey_presets_io.show_save_path_rejection`（文言 2 種・**モーダルはこのファイルへ集約**）+
    `app.py` は **`write_presets` の前**に判定して `False`（`data`・dirty は完全に不変）+
    `split_payloads` の `hotkey_presets_path` を `to_config_relative_or_absolute` へ。
  - **ON → OFF の確定と OFF のままの保存は対象外**（復旧経路・通常経路を塞がない）。
  - **見送り**: symlink/junction の追随（`is_path_within` の realpath 化は canonical identity 比較
    全体へ波及・スコープ外）/ **N5**（Import は task_06 で強制 OFF・新規作成は data ごと差し替わるため
    **到達経路が残っていない**）。
  - **【運用】サブエージェントがセッション上限で 2 本とも失敗**したため、**実測はメインが直接実行**した。
result_files:
  - instructions/history/08_per_keymap_set_presets.md（**v0.7 へ改訂・【G】予約規定 +【O4】新設 + 既知の制約 3 件**）
  - instructions/phase/09_per_keymap_set_presets/phase.md（task_07 / task_07b 行）
  - instructions/phase/09_per_keymap_set_presets/tasks/task_07_integration_check.md（新規・起票）
  - instructions/phase/09_per_keymap_set_presets/tasks/task_07b_global_collision_guard.md（新規・起票）
  - keyseq/application/config_service/{__init__.py,split_loading.py,split_payloads.py}
  - keyseq/presentation/app.py / controllers/config_io/hotkey_presets_io.py
  - tests/test_config_service.py / tests_ui/test_app_ui_flows.py
verified:
  compile: clean
  tests: pass **229**（基準線 225 → +4）
  tests_ui: pass **206**（基準線 202 → +4）
  smoke: pass
  review: `reviewer` = **採用（完了可）**。グローバルが上書きされない / ON→OFF と OFF のままの保存を
    誤って拒否しない / 拒否時 data・dirty 完全不変 / `canonical_path` を比較専用に留めている /
    `"global"` を定数の dirname から導出 / `resolve_hotkey_presets_save_path` の契約不変 /
    読み出し側【O2】・`dialogs.py` 不変 / 空文字とキー順の保持 を確認。**参考指摘 2 件**
    （`split_payloads` の二重評価 / `show_save_path_rejection` が理由 2 値以外を一律 global_conflict 扱い）

## next_action
- **【ユーザー作業】task_07 の実機目視 16 項目**を実施し、結果をメインセッションへ報告する。
  観点リストは **`tasks/task_07_integration_check.md` §3 の表**が正（受入条件との対応付き）。
  **特に重要 = 項目 11**（無効パスで既定へ寄る＝v0.6【O3】）と **項目 15**（**手動移行の 2 段**）。
  **task_07b のガードが入った状態**で行うこと（`global/` 配下や config.json と同一への保存が拒否される）。
  - 目視で不具合が出たら **task_07 内で是正**（最小差分 + `reviewer` 再実施）。
  - 2 本立てレビューは**実施済み**（`deep-reviewer` + `codex-adversarial-reviewer`）。
    残った指摘の扱いは decisions.md の「task_07 レビュー」節に確定済み。
- その後 **task_08 = 正本反映（最終）**: `data_schema.md` §5.10 改訂 + §5.5 / §5.4 / §5.8.8 / §5.1 +
  `codebase_map.md` / 暫定仕様 08 を凍結 / `decisions_archive/09_per_keymap_set_presets.md` 作成 /
  `current.md` 完了更新 / `backlog/INDEX.md` の idea_08 を `INDEX_done.md` へ移動 / `/refactor_check`。
  - **task_08 の着手前に直すもの（レビュー指摘 N8）**: **暫定仕様 §7 の反映対象記述**が
    v0.3 時点の「**プリセット単独の注入が入るため**」「**トグル時の単独注入**」のままで、
    **v0.4【I 撤回】および実装（単独注入 API なし）と矛盾**する。**直さないと正本に誤記が入る**。
    `phase.md:21` の「主入力（v0.4）」表記も現行 v0.7 へ更新する。
  - **正本へ追加する項目（N9）**: 入口台帳 §5.8.8 へ **「OFF 復帰時のグローバル再読込」経路**を
    追加する（E1〜E5 のどれでもない新しい供給点。hook キー単独注入と同型の例外として列挙）。
  - **v0.5 →v0.6 の反転（【O3】）/ v0.7 の【O4】/ dirty 規則 / task_05b が task_05c で
    置き換わった経緯**を decisions_archive へ集約すること。
- その後 **task_08 = 正本反映（最終）**: `data_schema.md` §5.10 改訂 + §5.5 / §5.4 / §5.8.8 / §5.1 +
  `codebase_map.md` / 暫定仕様 08 を凍結 / `decisions_archive/09_per_keymap_set_presets.md` 作成 /
  `current.md` 完了更新 / `backlog/INDEX.md` の idea_08 を `INDEX_done.md` へ移動 / `/refactor_check`。
  - **v0.5 →v0.6 の反転（【O3】）と dirty 規則**、**task_05b が task_05c で置き換わった経緯**を
    decisions_archive へ集約すること。
- 以降の流れ（各タスク共通）: 実装委任（**テスト追加まで含める / 実行は依頼しない**）→
  `verifier` で実測 → `reviewer` → `/save_state` + `/task_commit`。

## blockers
- **task_07 の完了に実機目視（ユーザー作業）が必要**。それまでフェーズ完了判定は出せない。
- 【参考】**サブエージェントがセッション上限で失敗することがある**（19:20 リセット）。
  その場合 `verifier` の実測はメインが直接実行してよい（**必須レビューは代替不可**）。

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
