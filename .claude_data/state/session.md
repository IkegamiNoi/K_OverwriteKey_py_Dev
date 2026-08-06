# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-06T00:00:00
phase: `instructions/phase/08_hotkey_presets_global`（**task_03 完了 / 次は task_04 = 実装**。暫定仕様 07 は **v0.5・確定済**）
last_commit_location: claude/refactor-hook-key-pair-enum-b7cddc @ `654d2ef` ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 08 は task_03（入口一本化の設計確定・暫定仕様 v0.5）まで完了。次は task_04 = `apply_global_defaults` の実装と入口台帳 E1〜E5 への配線**。
mode: implementing

## last_action
ts: 2026-08-06T00:00:00
who: main
summary: |
  【phase 08 task_03 = **入口一本化の設計確定**（文書のみ・コード無変更）→ 暫定仕様 07 を **v0.5** へ】
  - **ユーザー確定: 案B = 注入 API を 1 本に束ねる**。`ConfigService.apply_global_defaults(runtime, *, config_root)`
    が hook キー注入 + グローバルプリセット供給を担う。**`app.py:77` も新方式へ寄せる**。
    却下は案A（供給済みファクトリ・通常読込が条件付き注入のため入口は 1 つにならない）と案C（現状維持）。
  - **例外 1 つ**: `toggle_hook_keys_individual` の **ON→OFF は従来どおり単独注入**
    （束ねるとキー切替だけでプリセットが再読込され編集中の内容を取りこぼす）。
  - **敵対的レビュー = needs-attention → 指摘 2 件ともユーザー採用**（実コードで裏取り済み）:
    ① **空リスト縮退が §2 を破る** → 読み出しを **`list | None`** へ。**読めたら空でも採用 /
    読めなければ置き換えない**。**通常読込も同規則へ統一**（task_02 のテスト 1 件は task_04 で更新）
    ② **入口台帳が不完全** → `app.data` 置換の**実測 9 箇所**を **E1〜E5 / L1〜L3 / N1** として台帳化し、
    受入条件 7 を全経路へ拡張・受入条件 9 を追加。
  - **実測で判明**: Import（`keymap_set_io.py:561`）は**レガシー単一 JSON 経路**で
    `build_runtime_data_from_split` を通らない → インラインの `hotkey_presets` は
    **グローバルが読めれば置き換わる**（読めないときだけ残る）。
result_files:
  - instructions/history/07_hotkey_presets_global.md（**v0.5**・§3-2 と入口台帳を新設 / 受入条件 7〜9）
  - instructions/phase/08_hotkey_presets_global/tasks/task_03_entry_point_design.md（新規）
  - .claude_data/state/decisions.md（phase 08 節へ task_03 を追記）/ .claude_data/state/session.md
verified:
  code_unchanged: 本タスクは**文書のみ**（`keyseq` / `tests` / `tests_ui` に差分なし）
  compile / tests / tests_ui / smoke: task_02 完了時の実測が最新（clean / **180** / **178** / pass）
  review: codex-adversarial-reviewer = **needs-attention** → 指摘 2 件を**ユーザー採用**し v0.5 へ反映済み

## next_action
- **task_04 を `/task_new` で起票 → 実装委任**する（規範 = 暫定仕様 07 **§3-2**・**v0.5**）。内容:
  1. **`list | None` を返すグローバルプリセット読み出し**を新設（`load_named_list` は使わない。
     読めた＝`list`〔空を含む〕/ 不存在・破損・根キーが list でない＝`None`）
  2. **`ConfigService.apply_global_defaults(runtime, *, config_root)`** を新設
     （既存 `apply_global_hook_key_defaults` を呼ぶ + プリセット供給。冪等・例外を投げない）
  3. **入口台帳 E1〜E5 へ配線**（`app.py:77` / `keymap_set_io.py:53,561,599` / `startup_io.py:35`。
     既存の `apply_global_hook_key_defaults` 呼び出しを置き換える）
  4. **通常読込（`build_runtime_data_from_split`）も同じ供給規則へ統一**
     → **task_02 で追加したテスト「不存在・破損 → `[]`」を「置き換えない＝組込 8 件」へ更新する**
  5. **`toggle_hook_keys_individual` の ON→OFF は変更しない**（単独注入のまま。受入条件 8）
- 受入条件 7・8・9 を特性テストで固定する。**L1〜L3（通常読込）と N1（再正規化）は配線対象外**。
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
