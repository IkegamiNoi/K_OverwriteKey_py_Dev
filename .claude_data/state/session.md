# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-06T00:00:00
phase: **フェーズは無し（phase 07 完了）**。「**計画06**」= `instructions/modified_proposal/06_refactor_hook_key_pair_enumeration.md` も完了（**フェーズ番号は未消費**）。次フェーズ = プリセット（phase 08）は未起票
last_commit_location: claude/refactor-hook-key-pair-enum-b7cddc @ `207e879` ※現在地はセッション開始時の git 実測値が正

## current
focus: **計画06（hook キー 2 本の「対の列挙」を domain へ集約・挙動不変）は項目 0 / 1 とも完了。次フェーズ（プリセット = phase 08）は未起票**。
mode: completed

## last_action
ts: 2026-08-06T00:00:00
who: main
summary: |
  【提案書 06 の実施形態を **(b) 独立ミニ計画 =「計画06」** でユーザー確定 → 項目 0 / 1 を実施し計画06 完了】
  - 運用は**計画05 と同じ**（提案書自体が確定設計 / **フェーズ番号を消費しない** / 1 項目 = 1 コミット /
    フェーズ末の `/refactor_check` は本計画自体がその産物のため不要）。**phase 08 より先に実施**。
  - **項目 0**: 安全網の実測（`Explore`）で観点 ①解決 ②移行判定 ④OFF 編集の成否 ⑤dirty 非汚染 は**十分**、
    **③OFF 保存だけ空白**（`read_bytes()` のバイト列比較は**子ファイル専用**で、hook キーを含む keymap_set 本体は
    **キー順＝出力バイト列を誰も固定していなかった**）→ `tests/test_save_plan.py` に
    `test_saved_keymap_set_json_keeps_stable_key_order` を**追加のみ**で新設（ON / OFF 双方で 11 キーのリスト比較）。
  - **項目 1**: `domain/config.py` に `HOOK_STOP_KEY` / `HOOK_TOGGLE_KEY` / `HOOK_KEY_FIELDS` /
    `normalize_hook_key_pair()` を新設し、application 2 + presentation 4 + domain 1 の計 8 ファイルを置換
    （+58 / -32 行・**層を跨ぐが依存は presentation/application → domain の一方向**）。
  - **挙動不変を優先して案から外した 2 箇所**: `ensure_config_compatibility` と `build_keymap_set_payload` は
    `normalize_hook_key_pair` へ寄せず**キー名だけ定数化**（新関数は `str(x or "")` を挟むため、
    非文字列時に現行が送出する例外を握り潰してしまう）。
  - メインが直接是正した軽微 2 件: 上記のキー名定数化の補完 / `app.py` の追加 import を domain 層の位置へ移動。
result_files:
  - keyseq/domain/config.py / keyseq/application/config_service/{__init__.py,split_loading.py,split_payloads.py}
  - keyseq/presentation/{app.py,ui_vars.py,controllers/key_capture.py,controllers/config_io/startup_io.py}
  - tests/test_save_plan.py（テスト 1 件追加・項目 0）
  - instructions/modified_proposal/06_refactor_hook_key_pair_enumeration.md / instructions/phase/current.md
  - .claude_data/state/decisions.md（「計画06」節を新設）
verified:
  compile: clean
  tests: **170 pass**（169 + 項目 0 の追加 1）
  tests_ui: **178 pass**（変化なし）
  smoke: pass
  characterization: キー順の特性テストが**無修正 pass** / `tests` `tests_ui` は**1 ファイルも変更なし**
  review: reviewer = **採用（完了可）** × 2 回（項目 0 / 項目 1）。項目 1 は分岐・評価順序・代入順序・
    例外挙動・公開 API シグネチャ・保存 payload のキー順が不変であることを突合で確認

## next_action
- 次フェーズの着手は**ユーザー確認が先**。本命は **プリセットの config.json グローバル化 = phase 08**
  （主入力 `instructions/history/07_hotkey_presets_global.md`・確定済）。起票は `/phase_start`
  （暫定仕様先行モード。番号対応: phase 08 / 暫定 07 / decisions_archive 08）。
- 他の候補: idea_07（参照元の掃除・着手可）/ idea_09 / idea_03（いずれも `instructions/phase/current.md`）。
- **計画06 の候補送りは未着手**: 「runtime を新規化・置換する入口が 4 経路」（`new_config` / `restore_default` /
  Import / 起動時の空データフォールバック）の一本化は**設計変更を伴う**ため保留。
  **phase 08 が同じ構造を再現するなら、そこで併せて設計する**。

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
