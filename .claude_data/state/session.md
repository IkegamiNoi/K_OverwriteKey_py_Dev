# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-03T00:00:00
phase: **07_hook_keys_global_default（保存系リデザイン Phase γ）**。規範 = `instructions/phase/07_hook_keys_global_default/phase.md`
last_commit_location: claude/device-testing-procedures-16467e ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 07（Phase γ = hook キーの全体デフォルト化）を起票完了。次は task_01 の起票 → 実装**。
計画05（config_service / keymap_set_io の分割リファクタ）は項目 0 / 1 / 2 をすべて完了済み。
mode: in_progress

## last_action
ts: 2026-08-03T00:00:00
who: main
summary: |
  【Phase β をコミット → 計画05 を起票・承認 → 項目 0 / 1a 完了】
  - **Phase β 完了分をコミット**: `976b3da`（task_10 + 19 + 20 = 正本反映と source_path 統一）/
    `03b52d0`（フェーズ完了判定の記録）。以降 Phase β は**クローズ済み**（`decisions_archive/06` が正）。
  - **提案書 05 の実施形態をユーザー確定 = 「計画05」として実施**（フェーズにしない）。
    根拠: 提案書がそのまま確定設計として機能し、`/refactor_check` の「挙動保存が原則」で制約が閉じるため、
    フェーズが内包する「設計を確定させる工程」が不要。**フェーズ番号を消費しない**ので
    γ=phase07 / プリセット=phase08 の対応表は不変。**γ より先に実施**（全 green + 実機目視 OK 直後で
    挙動不変の基準線が最も明確・γ が触る config_service を先に分割した方が差分が小さい）。
  - **項目 0（安全網の確認）= OK・追加テスト不要**。バイト列比較 21 箇所 / `test_save_plan.py` 12 件
    （旧索引維持・書き込み順序・deferred index）/ ダイアログ駆動 46 件。移設対象の private ヘルパは
    テストから直接呼ばれていない。**発見**: `patch("keyseq.application.config_service.os.path", ntpath)` が
    4 箇所あり、クラスを `config_service/config_service.py` へ置くと壊れる →
    **クラス本体を `config_service/__init__.py` へ置く**（計画04 案A と同じ手）。
  - **抽出方式をユーザー確定**（観点 = 後で把握しやすい方）: 引数への全展開は self 依存 1〜15 個で
    シグネチャが読めなくなるため不採用。**Mixin も不採用**（定義位置が MRO 依存で把握しにくい）。
    → **`service` を第 1 引数に取るモジュール関数**（`self.X` → `service.X` の機械的置換）。
  - **項目 1a 完了・コミット `db279e3`**: `config_service.py` → `config_service/__init__.py`（内容不変で移動・
    git も rename 認識）+ `save_plan_execution.py`（A・318 行）+ `split_payloads.py`（B・407 行）。
    親 1678 → **1011 行**。公開 3 メソッドは薄い委譲として残置、private ヘルパのラッパは作らない。
    reviewer 指摘の未使用 import 6 個はメインが削除済み。
  - **項目 1 の分割範囲をユーザー確定 = A+B+C+D・2 コミット**。A+B だけでは親 982 行で完了条件
    「600 行未満」に届かないため（起票時の見積もりが甘かった）。
  - **項目 1b 完了 = 項目 1 完了**: `save_path_resolution.py`（C・213 行）+ `split_loading.py`（D・289 行）を
    新設し、親 1011 → **551 行**（完了条件 600 行未満を達成）。方式は 1a と同一。
    **parent に残した判断**: パス基盤（`canonical_path` / `is_path_within` /
    `to_config_relative_or_absolute` / `_merge_parent_ref` 等）は **ntpath パッチの 4 テストが
    `__init__` の名前空間を見ている**ため移動不可 / `_normalize_sequence_payload` と
    `_generate_keymap_id` は読込専用ではない（保存側からも使う）ため D に含めない。
    **例外 2 件**: `slugify_file_stem` は公開メソッドのため本体を C へ移し親に薄い委譲を残す /
    `_normalize_external_keyboard_layouts` は読込専用のため D へ含めた（提案書の列挙外）。
    互換ラッパを作らない方針の帰結として **tests/test_config_service.py の 2 箇所**
    （`_default_trigger_set_path` / `_is_default_trigger_set_area` の直接呼び出し）を新名へ更新した。
  - **項目 2 完了 = 計画05 完了**: `keymap_set_io._collect_child_save_plan`（130 行）を手順の並びへ分解
    （**新規ファイルは作らず**同一ファイル内の private メソッド抽出のみ）。ファイル 640 → 662 行だが
    最長メソッドは 130 → **39 行**。ループ再入は**モジュール定数 `_RETRY` センチネル**で表現
    （戻り値がキャンセル / 再試行 / 確定の 3 系統あるため `None` と区別）。
    同型だった再計算 → 上書き確認の 2 ブロックを `_recalculate_for_trigger_target` へ統合
    （1 回目は `choices` を採用・2 回目は捨てる = 以降読まないため等価）。
    reviewer 指摘（2 メソッドが 44 行で完了条件 40 行超過）はメインが是正済み。
result_files:
  - keyseq/application/config_service/{__init__.py,save_plan_execution.py,split_payloads.py}（`db279e3`）
  - keyseq/application/config_service/{save_path_resolution.py,split_loading.py}（項目 1b・新規）
  - keyseq/presentation/controllers/config_io/keymap_set_io.py（項目 2）
  - instructions/common/codebase_map.md（ConfigService 節をパッケージ構成 5 ファイルの表へ更新 +
    `_collect_child_save_plan` の手順と `_RETRY` を追記）
  - instructions/modified_proposal/05_refactor_child_file_save_dialog.md（実施形態 / 項目 0 結果 / 項目 1 完了を追記）
  - .claude_data/state/decisions.md（「計画05」節）
verified:
  compile: clean
  tests: pass 145
  tests_ui: pass 159
  smoke: pass
  manual: **実機目視 R1〜R11 全 OK**（ユーザー実施 2026-08-02・Phase β 時点。計画05 は挙動不変のため再目視不要）
  review: reviewer（項目 1b）= **完了可・指摘なし**（AST 正規化差分で機械的置換のみを確認）。
    reviewer（項目 2）= **修正して採用**。制御フロー突合（ダイアログ呼び出し順序 / 再入条件 /
    早期 return / 通知合成）は全一致。指摘は行数のみでメインが是正済み。
    項目 1a も完了可（`db279e3`）。

## next_action
- **phase 07 起票済**（`instructions/phase/07_hook_keys_global_default/phase.md`・reviewer 整合確認 = 完了可）。
  次は **`/task_new` で task_01（スキーマと移行判定）を起票 → codex-implementer へ委任**。
  task 一覧は phase.md の「タスク」表（task_01 スキーマ/移行判定 → 02 キー解決点 → 03 保存時挙動 →
  04 全体デフォルト更新 API〔成否付き〕→ 05 チェック UI → 06 所有者切替 capture → 07 統合確認 →
  08 正本反映）。task_02 と task_03 は task_01 後なら並行可。
- **暫定仕様 06 の「現状監査」の行番号は計画05 の分割で無効**。現在の所在は phase.md
  「このフェーズで読むファイル」が正（読込 = `split_loading.py:30-31` / 保存 = `split_payloads.py:331-332`）。
- 計画05 の候補送り項目は**未着手**（必要になった時点で idea 化・`current.md`「別タスク化候補」に記録済）:
  `child_save_dialog.py` 370 行 / `save_keymap_set_to` 46 行 / `dirty_tracker.trigger_set_imported` の残置 /
  slugify の stem 衝突 / M4 の子カテゴリ列挙。
  項目 2 は γ とほぼ無関係のため、**途中で止めて γ へ移ってもよい**（ユーザー確定済）。
- 計画05 完了後に **`/phase_start` で phase 07（γ）を起票**する
  （主入力 = `instructions/history/06_hook_keys_global_default.md`・ユーザー確定済）。

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
- **保存系リデザインの番号対応**: α=phase05/暫定04〔完了〕 / **β=phase06/暫定05〔完了〕** /
  γ=phase07/暫定06〔未着手・暫定仕様は確定済〕 / プリセット=phase08/暫定07〔β とカスケード除外で協調〕。
  **計画05 はフェーズではないのでこの対応表に影響しない**（`instructions/phase/` にフォルダを作らない。
  規範 = `modified_proposal/05_*.md`・判断履歴 = `decisions.md` の「計画05」節。計画04 と同じ運用）。
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
