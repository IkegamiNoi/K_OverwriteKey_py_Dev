# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-06T00:00:00
phase: `instructions/phase/08_hotkey_presets_global`（**起票済・task_01 未着手**。計画06 は完了・フェーズ番号は未消費）
last_commit_location: claude/refactor-hook-key-pair-enum-b7cddc @ `432f071` ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 08（プリセットの config.json グローバル化）を起票済み。task_01（config.json への `hotkey_presets_path` 追加と既定補完）から着手する**。
mode: implementing

## last_action
ts: 2026-08-06T00:00:00
who: main
summary: |
  【計画06（項目 0 / 1）を完了 → **phase 08 を起票**（`/phase_start`・コード変更なし）】
  - **phase 08 = プリセットの config.json グローバル化**（主入力 = 暫定仕様 07・**v0.3** へ改訂）。
    `instructions/phase/08_hotkey_presets_global/phase.md` を新設し、task_01〜08 を定義
    （最終 task_08 = 正本反映）。`current.md` の現在の参照先・次採番（次フェーズ = 09）も更新。
  - **ユーザー判断: 計画06 の候補送り（runtime を新規化・置換する入口の一本化）を phase 08 が引き取る**。
    暫定仕様 07 **§4 検討事項 A（未確定）** として起票し、**task_03 で確定 → v0.4 → task_04 で実装**の順とした
    （プリセットが 2 例目を作るため。放置すると 4 経路 × 2 種類の規約になる）。
  - 起票の整合チェック（`reviewer`・整合確認限定）= **修正して採用**。指摘 2 件（`app.py` の行番号 405→406 /
    受入条件 6 の回収先が読めない）を反映済み。
  - 前段の計画06 は**完了・コミット済**（`207e879` 項目0 / `4fa12a6` 項目1 / `432f071` handoff。
    経緯は `decisions.md`「計画06」節と提案書 `modified_proposal/06_*` が正）。
result_files:
  - instructions/phase/08_hotkey_presets_global/phase.md（新規）
  - instructions/history/07_hotkey_presets_global.md（v0.3・§4 検討事項 A を追加）
  - instructions/phase/current.md（現在の参照先 / 次採番 / 候補送りの引き取り）
  - .claude_data/state/decisions.md（phase 08 の節を新設）/ .claude_data/state/session.md
verified:
  code_unchanged: 本ターンは**文書のみ**（`keyseq` / `tests` / `tests_ui` に差分なし）
  compile / tests / tests_ui / smoke: 計画06 完了時の実測が最新（clean / **170** / **178** / pass）
  review: reviewer（起票の整合確認・1 回）= **修正して採用** → 指摘 2 件を反映済み

## next_action
- **task_01 を `/task_new` で起票 → `codex-implementer` へ委任**する。内容 = config.json の
  `hotkey_presets_path` をスキーマへ追加し、**未設定時の既定補完**（`user/hotkey_presets/default.json`）付きの
  読み出し API を新設。**同型の先行実装 `split_loading.load_global_hook_keys` をそのまま参考にする**
  （読めない / 未設定なら既定へ縮退・正規化はパス解決側）。
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
