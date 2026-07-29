# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-30T00:05:00
phase: `instructions/phase/06_child_file_save_dialog`（保存系リデザイン **Phase β**）
last_commit_location: claude/file-label-save-issues-3b04cf ※現在地はセッション開始時の git 実測値が正

## current
focus: **Phase β 実機目視 5 件を暫定仕様 05 v0.3 へ反映（task_07〜09 を追加・旧 07 は task_10 へ）。task_07・task_08 完了。次は task_09（ダイアログのレイアウト）**。
mode: implementing

## last_action
ts: 2026-07-30T00:05:00
who: main
summary: |
  【task_08（save_dialog_no_recheck）完了】`codex-implementer` へ委任（presentation 限定）。
  - `_collect_child_save_plan` から**再計算を理由とする自動再表示を廃止**し、その場で `targets` を
    再解決して計画を組み直す形へ（v0.3-A）。**依存確認の「選び直す」だけがループへ戻る唯一の経路**。
    戻り値を `tuple[SavePlan | None, str]` にし、再計算の事後通知を flash と保存完了ダイアログへ追記。
  - `confirm_recalculated_overwrite` を追加（v0.3-A2）。対象は「一覧で保存を選んだ行 × 保存先が
    提示と変わった × 新パスに既存ファイルがあり `SHARE_SOLE` 以外」の 3 条件を満たす行のみ。
    0 件なら出さない。既定ボタンは `messagebox.NO`。はい=上書き / いいえ=行ごとに別名保存 /
    キャンセル=保存中止。`show_recalculation_notice` は廃止。
  - **【メイン修正 2 件・いずれもテスト側の不具合】** ①新規テストが既存ファイルへ非 JSON を書いた直後に
    `_parent_refs` を差し込んで `load_json` が落ちていた ②`INTERNAL_SEQUENCE_SOURCE_PATH` は
    config_root 内なら相対で入るのに `os.path.exists` へ直接渡していた（既知の罠）。production は無修正。
  - **申し送り（`/refactor_check` へ）**: `_collect_child_save_plan` が約 116 行で、trigger_entry 変化時と
    confirmed 変化時の「再解決 → 通知 → A2 確認」がほぼ重複（reviewer 提案）。
    `_confirm_recalculated_overwrites` の 0 件分岐の `build_save_plan` 呼び直しも冗長（実害なし）。

result_files:
  - instructions/phase/06_child_file_save_dialog/tasks/task_08_save_dialog_no_recheck.md（新規）
  - keyseq/presentation/controllers/config_io/keymap_set_io.py（再表示廃止・再解決・A2 の呼び出し）
  - keyseq/presentation/controllers/config_io/child_save_dialog.py（`confirm_recalculated_overwrite` 追加・注記削除）
  - tests_ui/test_child_save_dialog.py（期待値更新 + A2 のテスト 3 系統）
  - tests_ui/test_config_io_characterization.py（戻り値タプル化への機械的追従 4 行）
verified:
  compile: clean
  tests: pass 136
  tests_ui: pass 110（+3）
  smoke: pass
  review: reviewer（task_08 差分）= **完了可**（非ブロッキング 2 件 = 関数肥大と重複・冗長な計画再構築。
    いずれも `/refactor_check` へ申し送り）

## next_action
- **task_09（`save_dialog_layout`）を `/task_new` で起票**する。設計の正は暫定仕様 05 v0.3 の
  §3-5【v0.3-C】と受入条件 14。対象は `config_io/child_save_dialog.py` の `_create_action_dialog` /
  `_add_headers` / `_add_rows`。**初期 geometry・最小幅・試験用の行数/文字数をタスク定義で数値化**する
  （受入条件 14 が「数値はタスク定義で確定」としているため）。構造テスト（`resizable` / 縦スクロール領域 /
  ツールチップ全文）は `tests_ui/test_child_save_dialog.py` へ、実表示のはみ出しは実機目視へ分ける。
- 起票後は `codex-implementer` へ委任（テスト実行は依頼しない）→ `verifier` で `.venv` 実測 → `reviewer`。
- その後 **実機目視（ユーザー実施）** → task_10（`finalize_records`）。目視では実機フィードバック
  ①③④⑤の解消を確認する（②は仕様どおりで修正なし）。

## blockers
- なし。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
- **Phase β の設計の正は暫定仕様 [05](../../instructions/history/05_child_file_save_dialog.md)（**v0.3**・ユーザー確定済 2026-07-29）**。
  フェーズ中は正本 `spec_detail/` を直接改訂せず、**task_10**（旧 task_07）で昇格＋凍結する。
  v0.3 の追加分は §2 末尾「v0.3 の変更」A / A2 / B / C と §3-3・§3-5・§6 末尾・受入条件 12〜14。
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
- **`config_service.py` は 1600 行超（task_07 で微増）**。分割是非は**フェーズ末の `/refactor_check` で判定**する
  （task 途中では触らない。reviewer からの申し送り）。
- **task_03 で入った土台**: `keyseq/application/save_plan.py`（`SavePlan` / `ChildSaveEntry` / `SavePlanError`）。
  `save_runtime_data(..., save_plan=...)` が事前検証 → 子 → 親 → startup の順で実行する。
  presentation は task_05 でこの計画を組み立てて渡す。
- **task_04 で入った土台**: `config_io/child_save_rows.py` の `collect_child_save_rows(...)` が行モデル
  （`ChildSaveRow`: kind / key / display_name / target_path / share_state / share_text / default_action）を返す。
- **task_05 で入った土台**: `config_io/child_save_dialog.py`（UI）+ `child_save_plan.py`（選択 → `SavePlan` の純変換）+
  `keymap_set_io._collect_child_save_plan`（**再解決ループ**）。**不変条件**:
  ① 提示した保存先と実際に書く先を一致させる → **v0.3-A で緩和（task_08 で一覧再表示を廃止）**。
  代わりに **v0.3-A2**（再計算先が既存ファイル〔単独所有以外〕の「保存」行だけ行単位で上書き確認）が安全弁
  ② 未知・別の上位に属す保存先を明示操作なしに上書きしない（一覧の既定 + 依存確認の既定ボタン両方）＝**維持**。
- **task_06b で入った不変条件（壊しやすい）**: ③ `dirty_tracker.trigger_set_source_path` と
  `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致**させる（変更の入口は `dirty_state` の
  `set_trigger_set_source_path` / `sync_trigger_set_source_path_from_data` の 2 本のみ。直接代入を復活させない）
  ④ 子の `_parent_refs` は**保存先ファイルの集合 + 現在の上位**（保存元 in-memory の旧参照元は足さない）
  ⑤ アクションの優先順位は `child_save_plan.build_save_plan` の 1 箇所（一覧の選択 > confirmed > 非 dirty 既定）。
- **task_07 で入った土台（壊しやすい）**: `ConfigService.canonical_path(path, config_root)` /
  `is_path_within(path, ancestor_dir, config_root)`。パスの同一性判定は**必ずこの 2 本を使う**
  （`commonpath` の素の文字列一致・`startswith` の前方一致を復活させない）。
  ⑥ **canonical identity は比較専用**。`normcase` 済み文字列を保存値（`_parent_refs` / keymap_set の索引 /
  起動設定）・戻り値・表示文字列へ混入させない。保存表記は config_root 内=相対 / 外=絶対のまま。
  `to_config_relative_or_absolute` は canonical で内外判定し、**相対化は元の絶対パスから `relpath`** で作る。
- **申し送り（refactor_check / task_10）**: ① slugify 後に別々の keymap_set 名が同一 stem へ
  丸まる衝突（受入条件 8 の範囲外）② `dirty_tracker.trigger_set_imported` は読み手不在の残置状態
  ③ **task_10 の正本反映で `INTERNAL_TRIGGER_SET_SOURCE_PATH` を runtime 内部キーとして `data_schema.md` に明記**。
  ④ 実機の `config/` には**絶対パスで記録済みの `_parent_refs` / 起動設定**が残るが、比較時に解決して
  照合するため**移行処理は不要**（次回保存で自然に相対へ戻る）。
- **【Codex 運用】フォワーダが最終出力を返さず完了通知だけ来ることがある**。その場合は worktree のファイル
  mtime が停滞するまで待ってから verifier を回す（早すぎると実装途中の fail を掴む。2026-07-28 実測）。
  **差分が 0 件のまま返ることもある**（ジョブ未起動 or 早期リターン）。その場合は `SendMessage` で
  同じフォワーダを再開し、ジョブ状態の確認と最終出力の回収を依頼する（2026-07-29 実測。再開で回収できた）。
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
