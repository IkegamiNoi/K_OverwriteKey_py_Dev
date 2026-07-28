# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-28T07:05:00
phase: `instructions/phase/06_child_file_save_dialog`（保存系リデザイン **Phase β**）
last_commit_location: claude/phase-beta-bfbdd2 ※現在地はセッション開始時の git 実測値が正

## current
focus: **Phase β task_01（参照元記録 `_parent_refs` の読み書き基盤）完了。次は task_02（trigger_set の source_path 接続＝idea_05 内包 + 既定命名の keymap_set stem 基準化）の `/task_new` 起票**。
mode: implementing

## last_action
ts: 2026-07-28T07:05:00
who: main
summary: |
  【task_01（parent_refs_schema）完了】実装は `codex-implementer` へ委任。application 限定 + presentation は引数配線のみ。
  - `config_service.py`: 定数 4 種（ファイル側 `_parent_refs` / runtime 側 keymap・sequence・trigger_set トップレベル）+
    純関数ヘルパ `_normalize_parent_refs` / `_merge_parent_ref` を追加。読込・保存・split 保存の全経路へ親参照を伝搬。
    `_sanitize_runtime_for_storage` で新内部キーを除去（レガシー export へ漏らさない）。
  - **`None`（キー無し＝未知）と `[]`（既知・参照元ゼロ）の区別を全経路で維持**（§5 の「未知→別名保存」既定の前提）。
    reviewer が `or []` 等での握りつぶし無しを確認。
  - **後方互換**: 親未指定なら出力 JSON 不変。既存の完全一致アサート（`tests/test_config_service.py:125`）を
    **書き換えずに pass**。
  - presentation 3 ファイルは `parent_ref` / `config_root` を渡す引数追加のみ（判定・分岐なし）。
  - **【メイン修正】tests_ui のハング解消**: `_keymap_save_patches` 等の `fake_save` が新キーワード引数を受けられず
    TypeError → 未patch の `messagebox.showerror` がモーダル表示でハングしていた。モック署名に
    `parent_ref` / `config_root` を追加（3 行・検証意図は不変）。
  - domain `ensure_config_compatibility` の keymap ホワイトリスト再構築で内部キーが落ちる件は、application 側で
    明示復元して回避（reviewer 確認済）。
result_files:
  - keyseq/application/config_service.py
  - keyseq/presentation/controllers/config_io/{keymap_file_io,sequence_file_io,trigger_set_file_io}.py
  - tests/test_config_service.py（`ParentRefsSchemaTest` 7 件追加）
  - tests_ui/test_config_io_characterization.py（モック署名 3 行）
  - instructions/phase/06_child_file_save_dialog/tasks/task_01_parent_refs_schema.md（新規）
verified:
  compile: clean
  tests: pass 97（ベースライン 90 + 新規 7）
  tests_ui: pass 85（ハング解消後・再実測）
  smoke: pass
  review: reviewer = **完了可**（5 観点 + 重点 6 点すべて OK。指摘は参考 2 件〔到達不能ガード分岐 /
    `config_service.py` が 1262 行 → `/refactor_check` へ送る〕）

## next_action
- **task_02（`trigger_set_source_and_naming`）を `/task_new` で起票する**。内容は暫定仕様 05 §6・§7:
  ① trigger_set の source_path 分断を接続（**案1＝`dirty_tracker.trigger_set_source_path` へ寄せる**軸。
  読み手が未定義 App 属性を見ている現状を解消 = idea_05 内包。旧「別名で保存しますか？」個別ダイアログは復活させない）/
  ② config_root 内の trigger_set 既定パスを固定 `user/trigger_sets/default.json`
  （`config_service.py:468-471`）から **keymap_set の stem 基準**へ変更（§10 受入 8）。
  既存の特性テストが旧挙動を固定しているため、**起票前に対象テストを grep で洗い出してタスク定義へ明記**する。
- 起票後: `codex-implementer` へ委任（テスト実行は依頼しない）→ `verifier` 実測 → `reviewer` → `/save_state` + `/task_commit`。

## blockers
- なし。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
- **Phase β の設計の正は暫定仕様 [05](../../instructions/history/05_child_file_save_dialog.md)（v0.2・ユーザー確定済）**。
  フェーズ中は正本 `spec_detail/` を直接改訂せず、task_07 で昇格＋凍結する。
- **Phase β の勘所**（暫定仕様の指摘①〜④由来。実装時に後退しやすい）:
  ① 未知の参照元・別の上位に属す子は**別名保存が既定**（安全側）/ ② 保存計画は
  **presentation が決定・application が実行**（application に tkinter 依存を持ち込まない）/
  ③ パスが変わる子の上位は**保存必須**・失敗時は**旧索引維持**・**行ごとの粒度**（他 sequence を巻き込まない）/
  ④ 既定命名の変更は **trigger_set のみ**（keymap_set stem 基準。現状は固定 `user/trigger_sets/default.json`）。
- **task_01 で入った土台**（後続はこれを使う): `PARENT_REFS_KEY = "_parent_refs"`（子JSON 側）/
  `INTERNAL_{KEYMAP,SEQUENCE,TRIGGER_SET}_PARENT_REFS`（runtime 側。trigger_set のみ `data` トップレベル）/
  `_normalize_parent_refs`（**未知は `None`・既知ゼロは `[]`**）/ `_merge_parent_ref`（重複排除・順序保持）。
- **`config_service.py` は 1262 行**（task_01 で +269）。分割是非は**フェーズ末の `/refactor_check` で判定**する
  （task 途中では触らない。reviewer からの申し送り）。
- Phase β の主な触点: `config_service.save_runtime_data`(200-252) / `_build_split_save_payloads`(456-) /
  `config_io/keymap_set_io.py`(`save_keymap_set_to`:78-102) / `controllers/dirty_state.py`（idea_05 の当事者）/
  `config_io/io_dialogs.py`（`choose_save_path_with_collision`）。
- **保存系リデザインの番号対応**: α=phase05/暫定04〔完了〕 / **β=phase06/暫定05〔進行中〕** /
  γ=phase07/暫定06〔独立・未着手〕 / プリセット=phase08/暫定07〔β とカスケード除外で協調〕。
- **Phase α の成果は正本 `spec_detail/data_schema.md` §5.4 配下が正**（新規/Import/空起動で keymap_set パスが空 →
  保存は別名保存 / 既定はディレクトリ `config/user/keymap_sets/` / 子ファイルは全セット共有〔β の課題〕/
  レガシー `settings/` 経路のみ実装未追従 = idea_09）。
- config_io は `controllers/config_io/` の 6 クラスへ分割済（App が `app.keymap_set_io` 等で直接公開）。
- **レビュアーは 2 本立て**: `reviewer`（sonnet・単一タスクの実装差分）/ `deep-reviewer`（opus・設計文書 /
  複数タスクを跨ぐ差分 / フェーズ完了判定）。使い分けは `.claude/rules/agent_selection.md` のレビュー表が正。
  出力の作法は `.claude/rules/output_style.md`。
- **【Codex 運用の手順書】ジョブが詰まった / cancel が効かない / ハング検知 / state 手修復は
  `instructions/common/rules_detail/codex_operations.md` を読む**。**Codex 申告のテスト結果は信用せず必ず verifier で再実行**。
  **Codex は python をまったく実行できない**（サンドボックス制約・回避不能）→ 委任にテスト実行を含めない。
- **【罠】state ファイル・`instructions/` 配下・code は必ず worktree のパスで編集する**（main 側を編集すると commit から漏れる）。
- **【罠】`git grep` は追跡済みファイルしか検索しない**。新規（未追跡）ファイルの確認には**直接 `grep`** を使う。
  行数計測は `wc -l`（PowerShell `Measure-Object -Line` は空行を数えない）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 03_startup_font_settings_cleanup / 04_config_io_controller_split / 05_keymap_set_new_and_default_dir。
- 未着手 idea: idea_03（hotkey 保存時正規化・優先度低）/ idea_07（参照元の掃除・**β 完了後**）/
  idea_08（keymap_set 個別プリセット・プリセット案2 完了後）/ idea_09（レガシー settings/ フォールバック・α の積み残し）。
  保留 idea: idea_04（FontSettingsController）/ idea_06（D/E/F 共通化・**β で達成見込み**）。idea_05 は β が内包（着手中）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
