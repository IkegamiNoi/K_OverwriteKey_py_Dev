# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-30T06:05:00
phase: `instructions/phase/06_child_file_save_dialog`（保存系リデザイン **Phase β**）
last_commit_location: claude/save-dialog-ui-improvements-c0189a ※現在地はセッション開始時の git 実測値が正

## current
focus: **Phase β は task_13 まで完了（実装は全て完了）。残りは実機目視（ユーザー実施）→ task_10（正本反映）**。
mode: pending_review

## last_action
ts: 2026-07-30T06:05:00
who: main
summary: |
  【task_13（`data` 置換時の trigger_set 状態リセット）完了 = **Phase β の実装タスクが全て完了**】
  `codex-implementer` へ委任（presentation 限定）。
  - `dirty_state.DirtyStateTracker.reset_trigger_set_state()` を新設し、**リセットの入口を 1 本に集約**。
    `set_trigger_set_source_path("")` で tracker を空にし、`data` からは
    `INTERNAL_TRIGGER_SET_SOURCE_PATH` を **pop**（`new_default_data()` と同じ「キー無し」の形に揃える）。
    `trigger_set_dirty` / `trigger_set_imported` も False。`set_trigger_set_source_path()` 自体は無変更。
  - `keymap_set_io.new_config` / `restore_default` が `data` 差し替え直後・`set_dirty(True)` の前に呼ぶ。
    **`apply_loaded_data_to_ui`（読込 / Import / 起動設定変更）は無変更**（既に同期済み）。
  - 実測で**既存の特性テスト 1 件が回帰**（`test_restore_default_yes` が `data` に空の内部キーを検出）→
    **テストを緩めず実装側を「新品と同じ形」に揃えて**解消（キー無しと `""` は読み出し時に等価）。
  - これで **task_01〜09・11〜13 が完了**。**残るは実機目視（ユーザー実施）→ task_10（正本反映）**のみ。
result_files（**未コミット**。直近 3 コミット = `01c656e` v0.4 改訂と起票 / `8d8262c` task_11 / `97f2e39` task_12）:
  - instructions/phase/06_child_file_save_dialog/tasks/task_13_data_replace_state_reset.md（新規）
  - keyseq/presentation/controllers/dirty_state.py（`reset_trigger_set_state`）
  - keyseq/presentation/controllers/config_io/keymap_set_io.py（`new_config` / `restore_default` から呼ぶ）
  - tests_ui/test_config_io_characterization_keymap_set_startup.py（5 件追加）
verified:
  compile: clean
  tests: pass 138
  tests_ui: pass 136（+5・skip 0・完走）
  smoke: pass
  review: reviewer（task_13 差分）= **完了可**（指摘なし。リセット入口の集約・呼び出し位置・
    対象外ファイル無変更・fail-fast ガードの維持を確認。テスト 3・4 は
    `trigger_set_file_io.save_trigger_set_file()` の旧パス即保存分岐と整合し、**修正前なら失敗する**
    実効的な回帰テストであることも確認済み）

## next_action
- **実機目視をユーザーへ依頼する**（残る唯一の未完了項目。起動は `<repo>\.venv\Scripts\python.exe main.py`。
  **③④の確認は VS Code の ▶ 実行〔小文字ドライブ〕で行う**）。確認項目は
  (a) 2026-07-29 の①③④⑤ + (b) 2026-07-30 の⑥（最小サイズでボタンとラジオが見える / 幅で省略量が変わる）・
  ⑦（単独所有なら依存確認が出ない / 共有時は 4 択・「保存しない」で索引が旧パスのまま残り次回保存で追随）+
  (c) **新規作成 / 例の設定に戻す の直後に個別「トリガー一覧を保存」で前の構成が書き換わらない**（task_13）+
  (d) task_06 定義「対象範囲 4」の 9 項目の退行が無いこと。
  結果は `instructions/phase/06_child_file_save_dialog/integration_result.md` §3 へ記録する。
- 目視 OK 後: **task_10（`finalize_records`）を `/task_new` で起票**。正本反映で**必ず明記**する項目は
  `SHARE_NEW` / 非 dirty 子の SKIP 規則 / SKIP した子の索引規則 / 依存確認ダイアログと既定ボタン /
  SKIP 子の dirty 保持 / `data_schema.md` §5.4 の「trigger_set は全セット共通」記述の更新 /
  §5.6 のフォールバック名の経路差（一括 = `default` / 個別 = `trigger_set.json`）/
  個別「トリガー一覧を保存」が全 sequence を書く点と §8 の関係 / **v0.3 追加分**（A: 再表示しない /
  A2: 再計算先の上書き確認 / B: canonical identity / C: ダイアログ要件 / 変更なし保存でも親は書かれる）/
  **v0.4 追加分**（D/E: 依存確認の提示条件と 4 択・deferred index 例外と上位の dirty 化 / F: A2 維持 /
  G: 既定保存先は既存ファイルを避けない / I: 新規子が既存ファイルへ当たるときは既定を別名保存
  〔**keymap / sequence 限定・元判定が単独 / 共有中のときだけ**〕/ H: `data` 置換時の trigger_set 状態リセット /
  受入条件 15 の「依存が発生しない経路では事後通知を出さない」）。
  併せて暫定仕様 05 の凍結・`decisions_archive/06` 作成・`current.md` 完了記載・
  `backlog/INDEX.md`（idea_05 クローズ・idea_06 / idea_07 の条件更新）・`/refactor_check`。

## blockers
- なし。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
- **Phase β の設計の正は暫定仕様 [05](../../instructions/history/05_child_file_save_dialog.md)（**v0.4**・ユーザー確定済 2026-07-30）**。
  フェーズ中は正本 `spec_detail/` を直接改訂せず、**task_10** で昇格＋凍結する。
  v0.3 の追加分は §2「v0.3 の変更」A / A2 / B / C と §3-3・§3-5・§6 末尾・受入条件 12〜14。
  **v0.4 の追加分は §2「v0.4 の変更」D / E / F / G / H / I と §3-3・§3-5 末尾・§5 末尾・§6・§7・§8・
  受入条件 14b / 15 / 16 / 16b / 17 / 17b / 18**（敵対的レビュー 5 件を全採用して反映済み）。
- **Phase β の勘所**（暫定仕様の指摘①〜④由来。実装時に後退しやすい）:
  ① 未知の参照元・別の上位に属す子は**別名保存が既定**（安全側）。**v0.4-I**: `source_path` を持たない子の
  保存先に既存ファイルがあれば共有状況にかかわらず既定は別名保存 / ② 保存計画は
  **presentation が決定・application が実行**（application に tkinter 依存を持ち込まない）/
  ③ パスが変わる子の上位は**保存必須**・失敗時は**旧索引維持**・**行ごとの粒度**（他 sequence を巻き込まない）。
  **v0.4-E の唯一の例外 = deferred index**（ユーザーが 4 択で「保存しない」を明示選択したときのみ。
  親索引は旧パス維持・上位を強制 dirty 化・`_validate_save_plan:786` の必須依存をこの場合だけ通す）/
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
- **task_11 で入った土台**: `child_save_dialog.py` は**表示専用の補助メソッド**
  （`_add_text_cell` / `_configure_columns` / `_bind_content_width` / `_set_minimum_size`）と
  純関数 `_fit_text(text, measure, max_px, ellipsize)` を持つ。**省略は px 幅ベース**で
  Canvas の `<Configure>` 時に再計算し、**同幅なら早期 return**（再入・無限ループ防止）。
  `_ellipsize` / `_ellipsize_path` は無変更のまま `_fit_text` から再利用（`limit=1` で
  `_ellipsize_path` が非単調になるため探索は `low=2` から・`limit=1` は個別候補として扱う）。
  ツールチップは**常時バインド + 省略中のみ表示**。`minsize` は要求幅から算出（px 決め打ち禁止）。
- **task_12 で入った土台**: `SavePlan.allow_deferred_index`（既定 False。**presentation が 4 択で
  「保存しない」を選んだときだけ立てる**フラグで、application は `_validate_save_plan` の必須依存チェックを
  通すためだけに使う）/ `child_save_rows.SHARE_NEW_COLLIDES` + `build_row(has_source_path=...)`
  （**keymap / sequence 限定・元判定が単独 / 共有中のときだけ置き換え**）/ 依存確認は `messagebox` から
  **自前の 4 択 `Toplevel`** へ（既定フォーカス=別名保存・Escape と閉じるはキャンセル）/
  提示条件は上位が `SHARE_SOLE` / `SHARE_NEW` なら確認なし自動保存＋事後通知 /
  `save_keymap_set_to` が保存成功後に `mark_trigger_set_dirty()` を無条件で呼ぶ（deferred index の追随）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  テスト内の `AssertionError` も `save_keymap_set_to` の広い `except Exception` に捕まるため、
  **失敗が「ハング」に化けて原因が見えなくなる**（2026-07-30 に 3 回発生）。
  対策として tests_ui の 3 ファイル（`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup`）の `setUp` に **fail-fast ガード**を入れてある:
  `messagebox.showerror` / `confirm_recalculated_overwrite`(A2) / `confirm_trigger_set_dependency` を
  「呼ばれたら `AssertionError`」に patch。**期待するテストは個別 patch で上書きし、内容をアサーションする**。
  新しいモーダルを増やすときは**同じガードを足す**こと。
- **【教訓】ハングしたら `messagebox` / `filedialog` を全遮断して単独実行する**と真因が一発で出る
  （`python -c` で `mb.showerror` 等を差し替えて `unittest.main(module=..., argv=[...])`。2026-07-30 実測で 0.6 秒）。
- **申し送り（refactor_check / task_10）**: ⓪ `child_save_dialog.py` が **324 行**（目安 300 超）+
  `_add_text_cell` の戻り値が素の dict（型注釈なし。dataclass 化は task_11 では過剰と判断・reviewer 非ブロッキング）
  ① slugify 後に別々の keymap_set 名が同一 stem へ
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
