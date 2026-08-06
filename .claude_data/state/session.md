# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-06T00:00:00
phase: `instructions/phase/08_hotkey_presets_global`（**task_01 完了 / 次は task_02**）
last_commit_location: claude/refactor-hook-key-pair-enum-b7cddc @ `675c7a7` ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 08（プリセットの config.json グローバル化）は task_01（グローバルプリセットパスの読み出し API）まで完了。次は task_02（読込元の切替）**。
mode: implementing

## last_action
ts: 2026-08-06T00:00:00
who: main
summary: |
  【phase 08 の task_01 を起票（`/task_new`）→ 実装 → 完了】
  - `split_loading.load_global_hotkey_presets_path(service, *, config_root)` を新設（+22 行）。
    `load_global_hook_keys` と同じ骨格で、**保存されている表記をそのまま返し・パス解決はしない**
    （解決は `load_named_list` 側。相対値を `os.path` 系へ直接渡さない不変条件を守るため）。
    **runtime への配線は task_02**（本タスクは読み手を足すだけで挙動は変わらない）。
  - **起票時の確定**: 「明示的な空文字」も既定 `HOTKEY_PRESETS_RELATIVE_PATH` へ縮退させる
    （暫定仕様 §3 が空文字を未定義に残していたため。根拠 = §2「プリセットの置き場は常に 1 つ」）。
    **hook キーとの非対称は意図的**（`load_global_hook_keys` は `config_root` 空で `("","")` へ縮退するが、
    本 API は常に既定パスを返す）。**task_08 の正本反映でこの契約を明記する**。
  - **タスク定義の記述ミスを実装側が是正**: `str(x or "").strip()` 一本では**数値 `42` が `"42"` になり**
    「非文字列は既定へ縮退」の要件と矛盾する → `isinstance(..., str)` の型ガードを追加（**修正して採用**）。
  - reviewer の軽微指摘（型ガード後の `str()` が冗長）はメインが 1 行へ整理し再実測。
result_files:
  - keyseq/application/config_service/split_loading.py / tests/test_config_service.py（テスト 5 件追加）
  - instructions/phase/08_hotkey_presets_global/tasks/task_01_global_presets_path_reader.md（新規）
  - .claude_data/state/decisions.md（phase 08 節へ task_01 を追記）/ .claude_data/state/session.md
verified:
  compile: clean
  tests: **175 pass**（170 + 追加 5）
  tests_ui: **178 pass**（**無修正**。本タスクは presentation を触らない）
  smoke: pass
  scope: 差分は `split_loading.py` と `tests/test_config_service.py` の **2 ファイルのみ**
  review: reviewer = **採用（完了可）**。5 経路すべての既定縮退 / パス解決をしていないこと /
    既定値の定義元が 1 箇所であること / 「含まない」への未踏み込みを確認

## next_action
- **task_02 を `/task_new` で起票 → 実装委任**する。内容 = **プリセットの読込元を config.json へ切替**
  （`build_runtime_data_from_split:82-87` の `keymap_set.get("hotkey_presets_path")` を
  task_01 の `load_global_hotkey_presets_path(service, config_root=...)` の戻り値へ差し替え）+
  **keymap_set 側の同キーは読込時に無視**（能動削除はしない）。
  受入条件 1・2（読込側）・5 が対象。**payload 生成停止とカスケード除外は task_05**（混ぜない）。
- 以降の流れ（各タスク共通）: 実装委任（**テストコードの追加まで含める / 実行は依頼しない**）→
  `verifier` で実測 → `reviewer` → `/save_state` + `/task_commit`。
- **task_03（設計確定）の前に task_04 へ着手しない**。task_03 は暫定仕様 07 §4 検討事項 A を
  ユーザー確定し **v0.4 へ改訂**するタスクで、レビューは `codex-adversarial-reviewer`（縮退時 `deep-reviewer`）。

## blockers
- なし。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
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
