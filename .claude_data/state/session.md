# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-09T10:40:00
phase: **なし（phase 08 完了・次フェーズ未確定）**。直前 = `08_hotkey_presets_global`（暫定仕様 07 は **v0.6・凍結済**。正本 = `data_schema.md` §5.10）
last_commit_location: claude/task-04-progression-dbaaef ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 08（プリセットの config.json グローバル化）は 2026-08-09 完了。次フェーズは未確定で、着手前にユーザーへ方針確認する**。
mode: completed

## last_action
ts: 2026-08-09T10:05:00
who: main
summary: |
  【phase 08 task_07 実機目視 OK → **task_08（正本反映）** → 完了レビューの High を **task_08b** で是正】
  - **実機目視 = OK**（観点 1〜6・ユーザー実施）→ 受入条件 1〜6 の充足を確認。
  - **task_08（文書のみ）**: 正本 `data_schema.md` へ **§5.10 新設** + **§5.8.8 に入口台帳** +
    §5.1 に**「削除禁止の例外＝生成停止」** + §5.4 / §5.5 / §5.9.2 を改訂。`codebase_map.md` へ
    注入 5 経路 / プリセットの解決点 3 つ / `HotkeyPresetsIo`（config_io = 7 クラス）/ dirty 非汚染 /
    カスケードが書かないこと。暫定仕様 07 を**凍結**し `decisions_archive/08` を作成、
    `decisions.md` は索引 1 行へ。`current.md` を完了状態（次採番 `09_<topic>` / 暫定仕様 `08_<topic>`）、
    `backlog/INDEX.md` の **idea_08 を着手可**へ。
  - **完了レビュー = `codex-adversarial-reviewer` needs-attention + `deep-reviewer` 修正要**。
    **両者が独立に同じ High** を指摘（実測で再現）: `normalize_hotkey_presets` が非文字列 `label`/`value` で
    `AttributeError` → **E1 が捕捉せず起動不能**（phase 08 前は空データ起動へ縮退していた）。
  - **ユーザー確定 = 要素単位で除去** → 正本 §5.10.2 を先に確定 → **task_08b で実装**。
    `None` / キー無しは従来どおり空文字（除去しない）。
  - 文書指摘も修正: §5.10.4 の `None` 時内訳へ **E5 ＝インライン値** / §5.10.1 に
    **「手編集はアプリ終了中に」** / `codebase_map` のツリーへ `hotkey_presets_io.py` /
    `current.md` の古い対応表 / archive の区切り重複。低 3 件は保留・1 件は除外。
result_files:
  - instructions/common/spec_detail/data_schema.md / instructions/common/codebase_map.md（**正本**）
  - instructions/history/07_hotkey_presets_global.md（**凍結**）
  - .claude_data/state/decisions_archive/08_hotkey_presets_global.md（新規）/ .claude_data/state/decisions.md（索引 1 行）
  - instructions/phase/current.md / instructions/backlog/INDEX.md / phase.md
  - instructions/phase/08_hotkey_presets_global/tasks/task_08_promote_to_spec.md・task_08b_*.md（新規）
  - keyseq/domain/config.py / tests/test_domain_config.py / tests/test_config_service.py（task_08b）
verified:
  compile: clean
  tests: pass **203**（基準線 198 → +5）
  tests_ui: pass **186**（増減なし）
  smoke: pass
  note: **サブエージェントがセッション上限（19:00 JST リセット）で落ちたため実測はメインで代行**（`verifier` 縮退）
  review: フェーズ完了 = `codex-adversarial-reviewer` **needs-attention** + `deep-reviewer` **修正要**
    （→ 正本改訂 + task_08b で解決）/ task_08b = `reviewer` **採用（完了可・指摘なし）**
  refactor_check: **不要**（M1〜M6 該当なし。候補送り 2 件は `current.md`「別タスク化候補」）

## next_action
- **次フェーズの方針をユーザーへ確認する**（未確定。勝手に着手しない）。候補は
  `instructions/phase/current.md`「次フェーズ候補」:
  - **[idea_08] keymap_set ごとの個別プリセット**（phase 08 完了で**着手可**。停止/トグルキーの
    個別指定〔正本 §5.9〕と同型で、前提の正本は **§5.10**。保存系リデザインの自然な続き）
  - [idea_07] 参照元の掃除（孤児 trigger_set と陳腐化した `_parent_refs` の回収・着手可）
  - [idea_09] レガシー `settings/` 保存パスのフォールバック / [idea_03] アクション hotkey の
    保存時正規化（いずれも優先度低）
  - 未承認の提案書 2 本（[05_refactor_child_file_save_dialog] / [06_refactor_hook_key_pair_enumeration]
    ※06 は実施済み）と、`current.md`「別タスク化候補」に溜めた項目
- 決まったら `/phase_start` で `instructions/phase/09_<topic>/` を起票する
  （**次採番は `09_<topic>` / 暫定仕様は `08_<topic>`**）。
- 着手前に `instructions/phase/current.md` と `.claude/rules/` を読み直すこと。

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
