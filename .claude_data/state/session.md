# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-03T00:00:00
phase: **07_hook_keys_global_default（保存系リデザイン Phase γ）**。規範 = `instructions/phase/07_hook_keys_global_default/phase.md`
last_commit_location: claude/item-1b-progress-960016 @ `8904c00` ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 07（Phase γ = hook キーの全体デフォルト化）を実施中。task_01 / task_02 完了、次は task_03（保存時挙動）**。
計画05（config_service / keymap_set_io の分割リファクタ）は項目 0 / 1 / 2 をすべて完了済み。
mode: in_progress

## last_action
ts: 2026-08-03T00:00:00
who: main
summary: |
  【計画05 を完走 → phase 07（γ）を起票 → task_01 / task_02 完了】
  - **計画05 完了**（`config_service` / `keymap_set_io` の分割リファクタ・**挙動不変**）。
    - 項目 1（`c7a8bf4`）: `config_service` をパッケージ化し 5 ファイルへ分割。親 1678 → **551 行**。
      抽出関数は **`service` を第 1 引数に取るモジュール関数**（`self.X` → `service.X` の機械的置換）。
      **parent に残した判断**: パス基盤（`canonical_path` / `is_path_within` /
      `to_config_relative_or_absolute` / `_merge_parent_ref` 等）は **ntpath パッチの 4 テストが
      `__init__` の名前空間を見ている**ため移動不可。`_normalize_sequence_payload` /
      `_generate_keymap_id` は保存側からも使うため読込モジュールに含めない。
      公開メソッド（`slugify_file_stem` 等）は薄い委譲として残置、private ヘルパのラッパは作らない。
    - 項目 2（`c22e49b`）: `_collect_child_save_plan`（130 行）を手順の並びへ分解。**新規ファイルを作らず**
      同一ファイル内の private メソッド抽出のみ。最長メソッド 130 → **39 行**。
      ループ再入は**モジュール定数 `_RETRY` センチネル**（戻り値がキャンセル / 再試行 / 確定の 3 系統あるため
      `None` と区別）。同型だった再計算 → 上書き確認の 2 ブロックを 1 本へ統合。
  - **phase 07（Phase γ）を起票**（`caf41a7`）。主入力 = 暫定仕様 06（v0.2・ユーザー確定済）。
    task_01〜08 に分割。**暫定仕様 06 の「現状監査」の行番号は計画05 の分割で無効**になったため
    phase.md「このフェーズで読むファイル」で現在の所在へ差し替えた。reviewer 整合確認 = 完了可。
  - **task_01 完了**（`d596295`・domain 限定）: `DEFAULT_CONFIG` へ `hook_keys_individual: False` +
    純関数 `resolve_hook_keys_individual(source)` を新設し `ensure_config_compatibility` の
    hook キー正規化**直後**で呼ぶ。**明示フラグの有無は `in` で判定**（`.get()` の真偽で見ると
    `false` とキー無しを区別できず移行規則が壊れる）。**冪等性を要件化**（フラグ True のまま両キーが空で
    False へ落ちると「ON→OFF で個別値を内部保持」が壊れる）。
  - **task_02 完了**（`8904c00`）: キー解決点を **`split_loading.load_global_hook_keys` と
    `ConfigService.apply_global_hook_key_defaults` の 2 本**へ集約。**フック層は無変更**。
    移行判定に渡すのは**生の `keymap_set` dict**（runtime は `new_default_data()` 由来でフラグを
    常に持つため発火しない）。受入条件 2 のため**新規 runtime を生成する presentation 3 箇所**
    （`new_config` / `restore_default` / 空データフォールバック）からも注入 API を呼ぶ。
    tests_ui 3 件はスタブ dict へ空 hook キーが加わったための**テスト側追従**として期待値を更新。
result_files:
  - keyseq/application/config_service/{__init__.py,save_plan_execution.py,split_payloads.py,save_path_resolution.py,split_loading.py}
  - keyseq/presentation/controllers/config_io/{keymap_set_io.py,startup_io.py}
  - keyseq/domain/config.py（`hook_keys_individual` / `resolve_hook_keys_individual`）
  - instructions/phase/07_hook_keys_global_default/{phase.md,tasks/task_01_*.md,tasks/task_02_*.md}
  - instructions/phase/current.md（アクティブ = 07・次採番 08）
  - instructions/common/codebase_map.md（ConfigService = パッケージ構成 5 ファイル + `_collect_child_save_plan` の手順）
  - .claude_data/state/decisions.md（「計画05」節 + 「phase 07」節）
verified:
  compile: clean
  tests: pass 164（計画05 完了時 145 → task_01 で +10 → task_02 で +9）
  tests_ui: pass 159
  smoke: pass
  manual: **実機目視 R1〜R11 全 OK**（ユーザー実施 2026-08-02・Phase β 時点）。
    **phase 07 の実機目視は task_07 でまとめて実施**（task_04 まで全体デフォルトを書く手段が無いため）。
  review: reviewer（task_01 / task_02）= いずれも **完了可・指摘なし**。
    計画05 の項目 1b = 完了可・指摘なし / 項目 2 = 修正して採用（行数のみ・是正済み）。

## next_action
- **次は task_03（保存時挙動）を `/task_new` で起票 → codex-implementer へ委任**。
  内容 = `split_payloads.py` の keymap_set 保存で、ON なら個別値を保存 / **OFF なら個別値を空文字に
  クリアし `hook_keys_individual=false` を書き出す**（キー自体は残す = 既存キー削除禁止）。
  暫定仕様 06 §5 / 受入条件 3・5。**保存 JSON のバイト列比較テストが変化する初めてのタスク**になるため、
  差分が hook 関連キーのみであることを確認する。
- task 一覧は phase.md の「タスク」表（01 スキーマ/移行判定〔**完了**〕→ 02 キー解決点〔**完了**〕→
  03 保存時挙動 → 04 全体デフォルト更新 API〔成否付き〕→ 05 チェック UI → 06 所有者切替 capture →
  07 統合確認 → 08 正本反映）。
- **task_02 の申し送り**: 解決点は `split_loading.load_global_hook_keys` と
  `ConfigService.apply_global_hook_key_defaults` の 2 本のみ。**ここ以外へ解決ロジックを書かない**。
  フック層は無変更を維持する（触ったら設計違反）。
- **暫定仕様 06 の「現状監査」の行番号は計画05 の分割で無効**。現在の所在は phase.md
  「このフェーズで読むファイル」が正（読込 = `split_loading.py:30-31` / 保存 = `split_payloads.py:331-332`）。
- 計画05 の候補送り項目は**未着手**（必要になった時点で idea 化・`current.md`「別タスク化候補」に記録済）:
  `child_save_dialog.py` 370 行 / `save_keymap_set_to` 46 行 / `dirty_tracker.trigger_set_imported` の残置 /
  slugify の stem 衝突 / M4 の子カテゴリ列挙。

## blockers
- なし。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
- **Phase β の成果は正本が正**: `spec_detail/data_schema.md` **§5.8**（子ファイルの保存計画と参照元記録）+
  §5.4 / §5.6 / §5.7、`features.md` §4.6（子ファイル保存ダイアログの表示要件）、`codebase_map.md`。
  暫定仕様 05 は**凍結済み**（経緯の参照用。仕様変更は `.claude/rules/spec_change_workflow.md` に従う）。
- **【最重要・2 度踏んだ罠】パス表記の混在事故**: runtime の `source_path` 3 種は **config 配下なら相対**で
  保持される（config 外は絶対・区切りは `/` 正規化）。**相対値を `os.path.abspath` / `dirname` / `exists` /
  `join` へ解決なしで渡すと cwd 基準で解決される**。症状 = **リポジトリルートに `user/` が生成される** /
  「別名で保存」が前回の場所に開かない。解決は `ConfigService.resolve_config_path(path, config_root)`。
  `to_config_relative_or_absolute` は**入口で解決するので相対を渡してよい**（2026-08-03 に修正）。
- **不変条件（壊しやすい）**: ① `dirty_tracker.trigger_set_source_path` と
  `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致**（入口は `dirty_state` のメソッドのみ・内部キー直代入禁止）/
  ② 子の `_parent_refs` は**保存先ファイルの集合 + 現在の上位**（in-memory の旧 refs を持ち込まない）/
  ③ **canonical identity は比較専用**（`canonical_path` / `is_path_within` の 2 本を使う。
  `normcase` 済み文字列を保存値・戻り値・表示へ混入させない）。
- **【共有状況の判定名と表示文言は別物】** 仕様書・タスク定義の「共有状況が単独 / 新規作成なら〜」は
  **判定名**（`SHARE_SOLE` / `SHARE_NEW`）を指す。画面表示は `share_text_for` が持つ
  （`SHARE_SOLE` = 「この構成のみが所有・既存を上書き」）。**分岐は判定名で書き、文言で分岐しない**。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  tests_ui の 3 ファイル（`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup`）の `setUp` に **fail-fast ガード**がある。
  期待するテストは個別 patch で上書きする。新しいモーダルを増やすときは同じガードを足す
  （`askyesnocancel` はガードへ入れない）。**ハングしたら `messagebox` / `filedialog` を全遮断して単独実行**すると
  真因が一発で出る。
- **【tests_ui の罠】`_prepare_loaded_keymap_set` は `save_plan=None` で `save_runtime_data` を呼ぶため
  runtime に source_path が入らない**。source_path 前提のテストは保存後に
  `load_runtime_data_from_keymap_set_path` で読み直すこと。
- **【Codex 運用】**フォワーダが最終出力を返さず完了通知だけ来ることがある。差分 0 件で返ることもある
  （`SendMessage` で再開して回収）。**Codex 申告のテスト結果は信用せず必ず verifier で再実行**。
  **Codex は python をまったく実行できない** → 委任にテスト実行を含めない。
  手順書は `instructions/common/rules_detail/codex_operations.md`。
- **【罠】state ファイル・`instructions/` 配下・code は必ず worktree のパスで編集する**（main 側を編集すると
  commit から漏れる）。`git grep` は追跡済みファイルのみ。行数計測は `wc -l`。
- **レビュアーは 2 本立て**: `reviewer`（sonnet・単一タスクの実装差分）/ `deep-reviewer`（opus・設計文書 /
  複数タスクを跨ぐ差分 / フェーズ完了判定）。使い分けは `.claude/rules/agent_selection.md` が正。
- **保存系リデザインの番号対応**: α=phase05/暫定04〔完了〕 / β=phase06/暫定05〔完了〕 /
  **γ=phase07/暫定06〔着手中・decisions_archive は 07〕** / プリセット=phase08/暫定07〔β とカスケード除外で協調〕。
  **計画05 はフェーズ番号を消費していない**（規範 = `modified_proposal/05_*.md`・
  判断履歴 = `decisions.md` の「計画05」節。計画04 と同じ運用）。
- **【phase 07 の設計の芯】キー解決点は 1 箇所**。`split_loading.load_global_hook_keys`（config.json の
  全体デフォルト読み出し）と `ConfigService.apply_global_hook_key_defaults`（OFF のみ注入・冪等）の
  2 本のみ。**フック層（`input_router` / `hook_controller` / `keyboard_window` / `app.py`）は無変更を維持**
  （触ったら設計違反）。移行判定 `resolve_hook_keys_individual` には**生の keymap_set dict** を渡す。
- config_io は `controllers/config_io/` へ分割済（App が `app.keymap_set_io` 等で直接公開）。
  子ファイル保存の触点: `child_save_rows.py`（共有状況判定）/ `child_save_dialog.py` /
  `child_save_plan.py`（計画組み立て）/ `keymap_set_io.py`（束ね役）/ `config_service.save_runtime_data`（実行）。
- **【計画05 で変わった構造】`config_service` は単一ファイルではなく*パッケージ***
  （`keyseq/application/config_service/`）。**ConfigService 本体は `__init__.py`**（`config_service.py` ではない。
  テストが `patch("keyseq.application.config_service.os.path", ntpath)` でモジュール名前空間を差し替えるため、
  この配置を崩すと 4 テストが壊れる。同じ理由で**パス基盤メソッドを兄弟へ移さない**）。
  兄弟モジュール = `save_plan_execution.py`（保存計画の実行）/ `split_payloads.py`（payload 構築）/
  `save_path_resolution.py`（保存先解決・命名）/ `split_loading.py`（split 読込）。
  抽出関数は **`service` を第 1 引数に取る**（`service.X` で親を参照）。
  兄弟から `__init__` を import しない（循環回避）。構成の正本は `codebase_map.md` の ConfigService 節。
- 未着手 idea: idea_07（参照元の掃除・**β 完了で着手可**）/ idea_03（hotkey 保存時正規化・優先度低）/
  idea_08（keymap_set 個別プリセット）/ idea_09（レガシー settings/ フォールバック）。
  保留 idea: idea_04 / idea_06（**残る着手条件は「共通化の実需」1 つのみ**）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 04_config_io_controller_split / 05_keymap_set_new_and_default_dir /
  **06_child_file_save_dialog**。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
