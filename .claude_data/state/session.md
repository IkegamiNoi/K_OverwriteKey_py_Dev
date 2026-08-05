# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-05T00:00:00
phase: **なし（phase 07 完了）**。次フェーズは未起票 = 着手前にユーザーへ方針確認（`instructions/phase/current.md`）
last_commit_location: claude/task-08-proceed-84c4a5 @ `3176954` ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 07（保存系リデザイン Phase γ・hook キーの全体デフォルト化）は task_08 まで完了しフェーズ完了。次フェーズ（プリセット = phase 08）は未起票**。
mode: completed

## last_action
ts: 2026-08-05T00:00:00
who: main
summary: |
  【実機目視 G1〜G9 OK を受けて task_07 を完了 → task_08（正本反映・最終）を起票して実施 → phase 07 完了】
  - **正本昇格**（文書のみ・コード無変更）: `spec_detail/data_schema.md` **§5.9**（データモデル /
    解決順序 / 移行規則 / 編集と保存の契約 / 既知の制約）+ `spec_detail/key_input.md` **§7.6**
    （供給源とフック挙動）+ `codebase_map.md`（責務）。**既存節は無改変**（追記のみ・節番号を動かさない）。
  - **暫定仕様 06 を凍結** / `decisions_archive/07_hook_keys_global_default.md` を作成し
    `decisions.md` は索引 1 行へ / `current.md`・`phase.md` を完了状態へ更新。
  - **指摘 E は実装を変えず契約として明記**（§5.9.5: キー衝突検証はカレントセット内に閉じる /
    「明示 false + 非空個別値」は個別値が失われる）。
  - レビュー = **deep-reviewer（修正要・軽微）+ codex-adversarial-reviewer（needs-attention）**。
    **ユーザー判断: 指摘 A〜H を採用 / I の 3 件は保留**。最重要は **A**（§5.9.2 の「未設定なら注入」が
    §5.9.3 の移行規則と矛盾＝後方互換回帰の種）と **B**（codebase_map が通常読込の分岐点を隠していた）。
  - **`/refactor_check` = 推奨**（M4 のみ該当）→ 提案書 `06_refactor_hook_key_pair_enumeration.md` を
    起票（**未承認**・実施形態はユーザー判断待ち）。
result_files:
  - instructions/common/spec_detail/{data_schema.md,key_input.md} / instructions/common/codebase_map.md
  - instructions/history/06_hook_keys_global_default.md（凍結）
  - instructions/phase/07_hook_keys_global_default/{phase.md,tasks/task_08_spec_promotion.md}
  - instructions/phase/current.md / instructions/modified_proposal/06_refactor_hook_key_pair_enumeration.md
  - .claude_data/state/decisions.md / .claude_data/state/decisions_archive/07_hook_keys_global_default.md
verified:
  code_unchanged: `git diff -- keyseq tests tests_ui` が**空**（文書のみの変更）
  compile / tests / tests_ui / smoke: task_07b 実測値が最終（clean / 169 pass / 178 pass / pass）。本タスクでは再実行しない
  manual: **実機目視 G1〜G9 すべて OK**（ユーザー実施・2026-08-05）
  review: deep-reviewer = 修正要（軽微・A〜H 反映で完了可）/ codex-adversarial-reviewer = needs-attention
    → **採用分をすべて反映済み**

## next_action
- **`/task_commit` で task_08 の成果をコミットする**（対象は上記 result_files。コード差分なし）。
- 次フェーズの着手は**ユーザー確認が先**。候補は `instructions/phase/current.md`「次フェーズ候補」:
  - **本命: プリセットの config.json グローバル化 = phase 08**
    （主入力 = `instructions/history/07_hotkey_presets_global.md`・確定済）。起票は `/phase_start`。
  - 他: idea_07（参照元の掃除・着手可）/ idea_09 / idea_03。
- **未承認の提案書**: `instructions/modified_proposal/06_refactor_hook_key_pair_enumeration.md`
  （Phase γ の `/refactor_check` = 推奨・M4）。実施形態は (a) 追加タスク / (b) ミニフェーズ /
  **(c) 見送り**（推奨は (c) または (b)。phase 08 で 2 例目が出てから共通化する方針なら見送り）。

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
