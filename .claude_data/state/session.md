# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-03T20:00:00
phase: **07_hook_keys_global_default（保存系リデザイン Phase γ）**。規範 = `instructions/phase/07_hook_keys_global_default/phase.md`
last_commit_location: claude/task-03-progression-bba1a9 @ `f0f2a52` ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 07（Phase γ = hook キーの全体デフォルト化）を実施中。task_01〜06b 完了（実装は全て完了）、次は task_07（統合確認 + 実機目視）**。
mode: implementing

## last_action
ts: 2026-08-03T20:00:00
who: main
summary: |
  【task_06b（表示切替と個別値の保持）を起票 → codex-implementer 実装 → verifier 実測 → reviewer 採用で完了】
  - **実装（presentation 限定・2 ファイル）**: `App.toggle_hook_keys_individual` を拡張し、
    **ON→OFF で個別値を `App._retained_hook_keys` へ退避 → OFF→ON で復元（復元時に消費）**。
    退避は **App が持つ**（`app.data` の内部キーにしない = 保存経路・スキーマへ影響させない）。
  - **順序が重要**: `hook_keys_individual` を data へ書いた**後**に `apply_global_hook_key_defaults`
    を呼ぶ（この API はフラグが真なら何もしないため、逆順だと注入されない）。
  - **退避が無い OFF→ON は両キーを `""` にする**（全体デフォルト値を個別値として引き継がない）。
    引き継ぐと全体デフォルトが keymap_set へ焼き付く。task_03（保存時の空文字化）・
    task_02（読込時に個別値を runtime へ持ち込まない）と整合する唯一の値。
  - **破棄は `keymap_set_io` の 4 箇所**: `save_keymap_set_to` の**保存成功後** /
    `apply_loaded_data_to_ui` 先頭 / `new_config` / `restore_default`。
    保存失敗時は破棄に到達しない（「保存成功時のみ破棄」を満たす）。
  - **`_sync_control_vars_from_data` に破棄を入れてはいけない**（toggle 自身が呼ぶため退避が即消える）。
result_files:
  - keyseq/presentation/app.py（`_retained_hook_keys` / `toggle_hook_keys_individual` 拡張 / `discard_retained_hook_keys`）
  - keyseq/presentation/controllers/config_io/keymap_set_io.py（破棄の呼び出し 4 箇所）
  - tests_ui/test_app_ui_flows.py（ON→OFF 切替 / 復元と ""化 / 保存後の破棄 / 読込・新規・既定復元での破棄）
  - instructions/phase/07_hook_keys_global_default/{phase.md,tasks/task_06b_hook_keys_display_switch.md}
  - instructions/phase/current.md（phase 07 の進捗行）
  - .claude_data/state/decisions.md（「phase 07」節へ task_06b を追記）
verified:
  compile: clean
  tests: pass 168（presentation 限定のため増減なし）
  tests_ui: pass 176（173 → +3）
  smoke: pass
  manual: **未実施。phase 07 の実機目視は task_07 で実施する**（task_06b 完了で UI 挙動が一通り揃った）。
    Phase β 時点の実機目視 R1〜R11 は全 OK（ユーザー実施 2026-08-02）。
  review: reviewer（task_06b）= **完了可・指摘なし**（セッション内復活の境界 / キー解決点の 1 箇所性 /
    退避の持ち方 / 完了済みタスク範囲への非接触を個別確認）。

## next_action
- **次は task_07（統合確認）を `/task_new` で起票**。内容 = 暫定仕様 06 §7 の**受入条件 1〜8 の通し確認**。
  - 特性テストの網羅確認（解決・移行・所有者切替・空文字化・保存失敗）と `tests` / `tests_ui` / smoke の実測
  - **実機目視のシナリオを起票してユーザーへ提示する**（phase 07 で唯一の実機確認。
    全体デフォルト設定 → 新規作成で再設定不要 → ON で個別指定 → OFF 保存で空文字化 →
    再 ON で空 → config.json 保存失敗時の挙動 まで）
  - レビューは **`deep-reviewer` + Codex レビュー系**を併用する（`.claude/rules/agent_selection.md`）
- task 一覧は phase.md の「タスク」表（01〜06b は**完了** → 07 統合確認 → 08 正本反映）。
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
