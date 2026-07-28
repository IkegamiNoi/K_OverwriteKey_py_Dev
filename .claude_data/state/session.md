# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-28T21:10:00
phase: `instructions/phase/06_child_file_save_dialog`（保存系リデザイン **Phase β**）
last_commit_location: claude/phase-beta-bfbdd2 ※現在地はセッション開始時の git 実測値が正

## current
focus: **Phase β task_04（dirty な子の収集・保存先解決・共有状況判定・既定アクション）完了。次は task_05（保存確認ダイアログ UI と保存経路への挟み込み）の `/task_new` 起票**。
mode: implementing

## last_action
ts: 2026-07-28T21:10:00
who: main
summary: |
  【task_04（dirty_children_and_share_state）完了】実装は `codex-implementer` へ委任。暫定仕様 05 §3・§4・§5。
  - **新規 `keyseq/presentation/controllers/config_io/child_save_rows.py`**（209 行・**tkinter を import しない**
    純ロジック・App ではなく値を引数で受ける）: `SHARE_*` / `ChildSaveRow` / `judge_share_state` /
    `share_text_for` / `default_action_for` / `collect_child_save_rows`。行順は keymap → trigger_set → sequence。
  - **application へ公開 API 2 本**: `resolve_child_save_targets()`（**空 `SavePlan()` で task_03 の解決経路を
    そのまま再利用**・書き込みなし）/ `read_parent_refs(path)`（無い・壊れ・キー無しは `None`・例外なし）。
  - **§5 の判定は `target_path`（これから上書きする相手のファイル）から読む**（runtime の refs は使わない。
    別名保存・既定命名変更で書き込み先が変わると誤判定するため）。
  - **`SHARE_NEW` を 1 状態追加**（§5 の表に無い判断）: 保存先ファイルが存在しない → 既定は**保存**。
    未知に倒すと新規の子すべてで別名保存ダイアログが出て実用に耐えないため。**task_07 で正本に明記する**。
  - 安全側の既定を維持: `_parent_refs` が **None も空リストも UNKNOWN**、`current_parent` が空文字も UNKNOWN →
    いずれも **別名保存**。`SHARE_OTHER_PARENT` も別名保存。
  - **【メイン修正 1 行】** `_build_split_save_payloads` の `serialized_keymaps` に `"resolved_path"` を追加
    （新 API が参照するキーが欠けており `KeyError` で新規テスト 5 件が error。sequences 側は既に露出済みで対称化）。
result_files:
  - keyseq/presentation/controllers/config_io/child_save_rows.py（新規）
  - keyseq/application/config_service.py（公開 API 2 本 + resolved_path 露出）
  - tests/test_child_save_rows.py（新規・7 件）
  - instructions/phase/06_child_file_save_dialog/tasks/task_04_dirty_children_and_share_state.md（新規）
verified:
  compile: clean
  tests: pass 119（112 + 新規 7）
  tests_ui: pass 86（無変更）
  smoke: pass
  review: reviewer = **完了可**（§5 の安全側既定・target_path から読む・二重実装なし・依存方向を確認。必須指摘なし）
    参考 2 件（任意）: ① keymap の display_name フォールバックが生 id ではなく正規化キー
    ② `collect_child_save_rows` が `keymap_service.get_keymaps` を経由せず `data["keymaps"]` を直接走査（挙動差なし）

## next_action
- **task_05（`save_dialog_ui`）を `/task_new` で起票する**。内容は暫定仕様 05 §3:
  ① 子ファイル保存確認ダイアログ（一覧・列 = 種別 / 対象名 / 保存先パス / 共有状況 / **ラジオ 3 択**。
  既定は task_04 の `default_action`）② 別名保存を選んだ行の保存先を `asksaveasfilename` で決める
  ③ 選択結果を **`SavePlan` へ変換**して `save_runtime_data` へ渡す（task_03 の実行契約に乗せる）
  ④ `keymap_set_io.save_keymap_set_to` への挟み込み（**dirty な子が無ければダイアログを出さない**）。
  依存関係（パスが変わる子の上位は skip 不可）は **UI 側でも選べないようにする**か、`SavePlanError` を
  ユーザー向けメッセージに変換するかを設計で決める。tests_ui は monkeypatch でダイアログ選択を駆動する。
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
- **task_04 で入った土台**: `config_io/child_save_rows.py` の `collect_child_save_rows(...)` が行モデル
  （`ChildSaveRow`: kind / key / display_name / target_path / share_state / share_text / default_action）を返す。
  task_05 のダイアログはこれを並べ、選択結果を `SavePlan` へ変換するだけでよい。
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
