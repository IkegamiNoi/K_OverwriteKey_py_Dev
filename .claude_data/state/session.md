# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-03T00:00:00
phase: なし（**Phase β = phase 06 完了**。次フェーズ未確定 → `instructions/phase/current.md` を参照）
last_commit_location: claude/device-testing-procedures-16467e ※現在地はセッション開始時の git 実測値が正

## current
focus: **Phase β（phase 06）完了。次フェーズ（γ = phase 07 / 暫定仕様 06）は未着手・未起票**。
mode: completed

## last_action
ts: 2026-08-03T00:00:00
who: main
summary: |
  【task_10（正本反映）→ フェーズ完了レビュー → task_19 / 20 → Phase β 完了】
  - **task_10（正本反映）**: 正本 `data_schema.md` に **§5.8 を新設**（参照元記録 / runtime 内部キー /
    保存計画と既定規則 / 共有状況と既定選択 / 確認ダイアログ / 依存と索引 / 個別保存 / データ置換の入口）+
    §5.4・§5.6・§5.7 を更新。`features.md` §4.6 に「子ファイル保存ダイアログ」を新設（レイアウト要件の昇格）。
    `codebase_map.md` に責務分担（**presentation が保存計画を決定・application が実行**）を反映。
    暫定仕様 05 を**凍結**、`decisions_archive/06` を作成し decisions.md は索引 1 行へ。
    backlog: idea_05 を `INDEX_done.md` へ / idea_06 の条件②充足 / idea_07 着手可。
  - **`/refactor_check` = 推奨**（M1/M2/M3/M4 該当・M5/M6 なし）→ 提案書
    `modified_proposal/05_refactor_child_file_save_dialog.md`（**未承認**）。M3 は idea_06 がカバーする既知領域、
    M4 ほか 3 件は `current.md` の別タスク化候補へ。
  - **deep-reviewer（フェーズ完了判定）= 修正要 → 高 2 + 中 5 + 低 5 を反映**。特に ①ダイアログの
    レイアウト要件がどこにも昇格していなかった ②§5.8.8 が「読込も**リセット**」と実装と逆の誤記
    （正本が正の原則で実装が誤って直される危険）。
  - **Codex 敵対的レビュー**が正本 §5.7 と実装の乖離を検出 → ユーザー選択で**実装修正**を採用し
    **task_19（個別保存）→ task_20（個別読込）** で source_path を **config 相対へ統一**。
    実装中に**同じ事故を 2 度**踏んだ（`to_config_relative_or_absolute` が入力を **cwd 基準**で
    `abspath` していたため、config 相対を渡すと cwd 基準の絶対へ化ける → リポジトリルートに `user/` 生成）。
    **入口で `_resolve_config_relative_path` を通す根本修正** + `_merge_parent_ref` の `abspath` 削除 +
    `config_paths.json_dialog_initial_dir` の解決漏れ修正（メインが直接修正）で解消。
  - **レイヤ跨ぎ**: application（`config_service`・パス正規化と loader 契約）+ presentation
    （`config_paths` / `config_io` の 3 コントローラ）。domain 不変・スキーマ不変・**保存 JSON のバイト列不変**。
result_files（**未コミット**）:
  - keyseq/application/config_service.py / keyseq/presentation/config_paths.py
  - keyseq/presentation/controllers/config_io/{keymap_file_io,sequence_file_io,trigger_set_file_io}.py
  - tests/test_config_paths.py / tests/test_config_service.py / tests_ui/test_config_io_characterization.py
  - instructions/common/spec_detail/data_schema.md / features.md / instructions/common/codebase_map.md
  - instructions/history/05_child_file_save_dialog.md（凍結）
  - instructions/phase/06_child_file_save_dialog/{phase.md,integration_result.md,manual_check_plan.md}
  - instructions/phase/06_child_file_save_dialog/tasks/{task_10,task_19,task_20}_*.md（新規）
  - instructions/phase/current.md / instructions/backlog/{INDEX.md,INDEX_done.md}
  - instructions/modified_proposal/05_refactor_child_file_save_dialog.md（新規・**未承認**）
  - .claude_data/state/decisions.md / decisions_archive/06_child_file_save_dialog.md（新規）
verified:
  compile: clean
  tests: pass 145
  tests_ui: pass 159
  smoke: pass
  manual: **実機目視 R1〜R11 全 OK**（ユーザー実施 2026-08-02。手順は `manual_check_plan.md`）
  review: reviewer（task_19 / task_20 差分）= **完了可**。deep-reviewer（フェーズ完了判定）= 修正要 →
    指摘を全反映済み。**codex-adversarial-reviewer の最終確認（3 回目）= approve・指摘ゼロ**
    （前回指摘 2 件の解消と、stored 相対パスの cwd 解決が残存しないことを網羅検索で確認）

## next_action
- **未コミット**。`/task_commit` で「task_10 + 19 + 20（Phase β 完了）」を 1 コミットにする
  （state 更新済み・コード 8 ファイル + 文書）。
- 次フェーズに着手する場合は **`/phase_start` で phase 07（γ）を起票**する
  （主入力 = `instructions/history/06_hook_keys_global_default.md`・ユーザー確定済）。
- 提案書 `modified_proposal/05_refactor_child_file_save_dialog.md` は**未承認**。
  実施するなら「独立ミニフェーズ」か「次フェーズ前」かをユーザーへ確認してから。
- **フェーズ完了レビューは完了**（Codex 最終確認 = approve・指摘ゼロ）。追加のレビューは不要。

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
- config_io は `controllers/config_io/` へ分割済（App が `app.keymap_set_io` 等で直接公開）。
  子ファイル保存の触点: `child_save_rows.py`（共有状況判定）/ `child_save_dialog.py` /
  `child_save_plan.py`（計画組み立て）/ `keymap_set_io.py`（束ね役）/ `config_service.save_runtime_data`（実行）。
- 未着手 idea: idea_07（参照元の掃除・**β 完了で着手可**）/ idea_03（hotkey 保存時正規化・優先度低）/
  idea_08（keymap_set 個別プリセット）/ idea_09（レガシー settings/ フォールバック）。
  保留 idea: idea_04 / idea_06（**残る着手条件は「共通化の実需」1 つのみ**）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 04_config_io_controller_split / 05_keymap_set_new_and_default_dir /
  **06_child_file_save_dialog**。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
