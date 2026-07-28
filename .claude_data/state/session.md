# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-28T20:30:00
phase: `instructions/phase/06_child_file_save_dialog`（保存系リデザイン **Phase β**）
last_commit_location: claude/phase-beta-bfbdd2 ※現在地はセッション開始時の git 実測値が正

## current
focus: **Phase β task_03（保存計画 SavePlan の導入と `save_runtime_data` の計画駆動化）完了。次は task_04（dirty な子の収集と §5 共有状況判定）の `/task_new` 起票**。
mode: implementing

## last_action
ts: 2026-07-28T20:30:00
who: main
summary: |
  【task_03（save_plan_execution）完了】実装は `codex-implementer` へ委任。application 限定・presentation 無変更。
  暫定仕様 05 §2 指摘②③・§8。
  - **新規 `keyseq/application/save_plan.py`**（36 行・dataclass のみ）: `ChildSaveEntry` / `SavePlan` /
    `SavePlanError` + 定数（`CHILD_*` / `ACTION_SAVE|SAVE_AS|SKIP`）。**entries に無い子の既定は保存**（＝全保存と等価）。
  - `config_service.save_runtime_data` に `save_plan=None` を追加し計画駆動へ。**§8 の 4 契約を実装**:
    ①事前検証 → 書き込みの 2 相（違反は `SavePlanError`・**1 バイトも書かない**）②依存関係の強制
    （パスが変わる子の上位を skip 不可）③粒度（skip の子は書かない・trigger_set 保存が全 sequence を巻き込まない）
    ④**書き込み順序を子 → 親 → startup へ反転**（失敗時に親索引・config.json が旧状態のまま残る）。
  - **skip の索引規則**（タスク定義で新たに決めた穴埋め）: 既存ファイルあり → 旧パス維持 /
    既存なし → 索引に載せない。keymap / sequence / trigger_set の 3 種で一貫。
  - **想定外の追加 = `INTERNAL_TRIGGER_SET_SOURCE_PATH`（runtime 内部キー）**: reviewer 判定 **採用**
    （task_02 定義が「trigger_set の source_path の書き込み先反映は task_03 の担当」と明示委譲済み。
    keymap / sequence と対称・子JSON には出力されない）。
  - **【メイン修正 1 行】** `_build_keymap_set_payload` の `trigger_set_path` 変換に空文字ガードを追加。
    空文字を `to_config_relative_or_absolute` に通すと `os.path.abspath("")` で **cwd に化ける**実バグで、
    「skip かつ既存なしは索引に載せない」規則が壊れていた（reviewer 妥当と判定）。
  - **等価性**: `save_plan=None` / 空計画の出力は現状と同じ（書き込み順序のみ変更）。
    `tests/test_config_service.py` は**未変更のまま全 pass**。
  - 【Codex 運用メモ】フォワーダが最終出力を返さないまま完了通知が来る事象が発生。**ファイル mtime の停滞監視**
    （bash バックグラウンド）で書き込み終了を判定した。**早すぎる検証で「実装途中の fail」を掴んだ**ので、
    次回も安定を確認してから verifier を回す。
result_files:
  - keyseq/application/save_plan.py（新規）
  - keyseq/application/config_service.py
  - tests/test_save_plan.py（新規・10 件）
  - instructions/phase/06_child_file_save_dialog/tasks/task_03_save_plan_execution.md（新規）
verified:
  compile: clean
  tests: pass 112（102 + 新規 10）
  tests_ui: pass 86（無変更）
  smoke: pass
  review: reviewer = **完了可**（§8 の 4 契約・等価性・責務分離・skip 索引規則の一貫性を確認。必須指摘なし）
    参考 1 件 → task_07 で `data_schema.md` に `INTERNAL_TRIGGER_SET_SOURCE_PATH` を runtime 内部キーとして明記する

## next_action
- **task_04（`dirty_children_and_share_state`）を `/task_new` で起票する**。内容は暫定仕様 05 §3-1・§4・§5:
  ① dirty な子の収集（`dirty_state.has_individual_dirty` の走査を流用。dirty な keymap / trigger_set / 各 sequence）
  ② **共有状況の判定**（`_parent_refs` の 4 状態 = **未知 / 単独 / 共有〔N 個〕/ 別の上位に属す**）と
  **既定ラジオの決定**（未知・別の上位 → **別名保存** / 単独・共有 → 保存）
  ③ 行モデル（種別 / 対象名 / 保存先パス / 共有状況 / 既定アクション）の生成。**UI は作らない**（task_05）。
  判定ロジックは純関数として置き、`SavePlan` へ変換できる形にする（application は判断を持たない＝ task_03 の前提）。
- 起票後: `codex-implementer` へ委任（テスト実行は依頼しない）→ **書き込み停止を確認してから** `verifier` 実測 →
  `reviewer` → `/save_state` + `/task_commit`。

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
- **task_02 で入った変更**: trigger_set の保存先は `_default_trigger_set_path()`（keymap_set stem 基準）。
  個別保存経路は `dirty_tracker.trigger_set_source_path` を読む（keymap / sequence と対称）。
- **`config_service.py` は 1262 行 →（task_02 で微増）**。分割是非は**フェーズ末の `/refactor_check` で判定**する
  （task 途中では触らない。reviewer からの申し送り）。
- **task_03 で入った土台**: `keyseq/application/save_plan.py`（`SavePlan` / `ChildSaveEntry` / `SavePlanError`）。
  `save_runtime_data(..., save_plan=...)` が事前検証 → 子 → 親 → startup の順で実行する。
  presentation は task_05 でこの計画を組み立てて渡す。
- **申し送り（task_04/05 で考慮 or refactor_check / task_07）**: ① slugify 後に別々の keymap_set 名が同一 stem へ
  丸まる衝突（受入条件 8 の範囲外）② `dirty_tracker.trigger_set_imported` は読み手不在の残置状態
  ③ **task_07 の正本反映で `INTERNAL_TRIGGER_SET_SOURCE_PATH` を runtime 内部キーとして `data_schema.md` に明記**。
- **【Codex 運用】フォワーダが最終出力を返さず完了通知だけ来ることがある**。その場合は worktree のファイル
  mtime が停滞するまで待ってから verifier を回す（早すぎると実装途中の fail を掴む。2026-07-28 実測）。
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
