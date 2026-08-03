# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-03T22:00:00
phase: **07_hook_keys_global_default（保存系リデザイン Phase γ）**。規範 = `instructions/phase/07_hook_keys_global_default/phase.md`
last_commit_location: claude/task-03-progression-bba1a9 @ `ee537cb` ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 07（Phase γ）は task_07（統合確認）を実施中。自動確認・レビュー・指摘是正（task_07b）まで完了し、残るは実機目視 G1〜G9（ユーザー実施）のみ**。
mode: pending_review

## last_action
ts: 2026-08-03T22:00:00
who: main
summary: |
  【task_07（統合確認）を起票 → verifier 実測 + deep-reviewer + Codex 敵対的レビュー →
   ユーザー判断で指摘 A〜D を採用 → task_07b で是正して完了】
  - **自動確認は全 pass**。**フック層が無変更**であることを `git diff caf41a7..HEAD` で実測確認
    （`application/input_router.py` / `hook_controller.py` / `keyboard_window.py` /
    `app.py` のフック供給部）。受入条件 1〜7 は実装・テストで充足。
  - **deep-reviewer = 条件付き完了可 / codex-adversarial-reviewer = needs-attention**。
    **両者が独立に「単一 JSON Import 経路で全体デフォルトが注入されない」を指摘**（実害あり）。
  - **ユーザー判断: 指摘 A〜D を全採用**（D は hook キーと無関係でスコープ外と提示したうえでの採用）。
  - **task_07b で是正**:
    - A: `import_config` へ `apply_global_hook_key_defaults` を 1 行追加
      （**注入点は 3 → 4 箇所**: new_config / restore_default / 空データフォールバック / Import）
    - B: `apply_global_hook_key_defaults` 先頭に `setdefault("hook_keys_individual", False)`
      （フラグ無し dict へ注入 → 保存で全体デフォルトが焼き付く構造的な穴を閉じる）
    - C: `discard_retained_hook_keys()` を保存成功後 → **`save_runtime_data` の直前**へ移動
      （keymap_set 書込後に config.json 書込が失敗すると退避が残り再 ON で復活する窓があった。
      **境界は「保存を実行した時点」**。保存中止では退避が残る挙動は維持）
    - D: `set_startup_keymap_set` で `write_startup` の成否を見て成功表明を抑止（エラーは二重に出さない）
  - **指摘 E は task_08 へ持ち越し**（実装変更せず正本で契約明記）。
result_files:
  - keyseq/application/config_service/__init__.py（B）
  - keyseq/presentation/controllers/config_io/keymap_set_io.py（A・C・D）
  - tests/test_config_service.py / tests_ui/test_app_ui_flows.py /
    tests_ui/test_config_io_characterization_keymap_set_startup.py（A〜D のテスト + スタブ dict 追従 3 箇所）
  - instructions/phase/07_hook_keys_global_default/{phase.md,tasks/task_07_integration_check.md,tasks/task_07b_review_findings_fix.md}
  - instructions/phase/current.md / .claude_data/state/decisions.md
verified:
  compile: clean
  tests: pass 169（168 → +1）
  tests_ui: pass 178（176 → +2）
  smoke: pass
  manual: **未実施 = 唯一の残作業**。task_07 の実機目視 **G1〜G9**（task_07 定義の表）をユーザーが実施し、
    結果をメインセッションへ報告する。G1（OFF 編集で dirty にならない）と
    G7（OFF 保存後は再 ON しても空）が中核。
  review: deep-reviewer（フェーズ完了判定）= 条件付き完了可 / codex-adversarial-reviewer = needs-attention
    → **指摘 A〜D を task_07b で是正済み**。reviewer（task_07b）= 完了可・指摘なし。

## next_action
- **ユーザーへ実機目視 G1〜G9 を依頼中**（`tasks/task_07_integration_check.md` の「実機目視シナリオ」）。
  結果 OK なら task_07 完了 → **task_08（正本反映・最終）**へ進む。
  異常があればフェーズを完了扱いにせず原因タスクへ戻す。
- **task_08 の内容**（`.claude/rules/task_execution.md`「フェーズ完了時」+ phase.md）:
  - 正本 `spec_detail/data_schema.md`（config.json の全体デフォルト 2 キー / keymap_set の
    `hook_keys_individual` / OFF 時の空文字化契約 / 解決順序 / 移行規則）と `key_input.md`・
    `codebase_map.md` へ昇格
  - **指摘 E の契約明記**: ① キー衝突検証はカレント keymap_set 内に閉じている
    ② 「明示 `false` + 非空個別値」は読込→保存で個別値が失われる
  - 暫定仕様 06 の凍結 / `decisions_archive/07_hook_keys_global_default.md` 作成 /
    `current.md` 更新（次採番 08）/ `/refactor_check`
- **task_04 の申し送り**: 全体デフォルトの書き込みは `StartupIo.write_global_hook_keys` の 1 本のみ。
  **config.json を別経路で read-modify-write しない**（`_startup_settings` と乖離すると次の
  `write_startup` が hook キーを消す）。task_06 は**戻り値 True のときだけ** UI / ランタイムを確定させる。
- **task_05 の申し送り**: `hook_keys_individual` の同期の入口は 2 本のみ
  （data → Var = `app._sync_control_vars_from_data` / Var → data = `App.toggle_hook_keys_individual`）。
  **compact のチェックは表示専用**（`state="disabled"`）＝**ユーザー確定済**（2026-08-03・task_07 で再確認しない）。
- **task_06 の申し送り**: hook キーへの書き込みは `SingleKeyCaptureController._apply_key` の 1 本のみ。
  **ここ以外に書き込み点を作らない**（散らすと「OFF なのに dirty」不具合の温床）。
  OFF 操作の dirty 非汚染は `capture_dirty_snapshot` / `restore_dirty_snapshot` を `try`/`finally` で使う。
- **task_06b の申し送り**: 個別値の退避は `App._retained_hook_keys`（`app.data` に持たない）。
  破棄点は `keymap_set_io` の 4 箇所（保存成功後 / `apply_loaded_data_to_ui` / `new_config` /
  `restore_default`）。**`_sync_control_vars_from_data` に破棄を入れない**（退避が即消える）。
- **task_02 の申し送り**: 解決点は `split_loading.load_global_hook_keys` と
  `ConfigService.apply_global_hook_key_defaults` の 2 本のみ。**ここ以外へ解決ロジックを書かない**。
  フック層は無変更を維持する（触ったら設計違反）。
- **task_03 の申し送り**: keymap_set への hook キー書き出しは
  `split_payloads.build_keymap_set_payload` の 1 箇所のみ。**OFF で書くのは常に `""`**
  （runtime の解決済み値を書かない）。task_06 で「OFF 保存後の保持値破棄」を実装すること。
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
