# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-02T00:00:00
phase: `instructions/phase/06_child_file_save_dialog`（保存系リデザイン **Phase β**）
last_commit_location: claude/keymap-set-overwrite-issue-18de5d ※現在地はセッション開始時の git 実測値が正

## current
focus: **task_17 完了（v0.6 の実装も完了）。残るは task_10（正本反映）のみ**。
mode: pending_review

## last_action
ts: 2026-08-02T00:00:00
who: main
summary: |
  【4 回目の実機目視フィードバック → 暫定仕様 05 を **v0.6** へ改訂 → task_17 起票・実装・完了】
  - **報告**: 読込済みの keymap_set から「例を復元」→ 保存すると**旧 keymap_set へ上書き**。
    トリガー一覧・出力シーケンスは同名ファイルがあると上書きされないが、例のシーケンスのファイルが
    無い状態だとトリガー一覧は上書きされる。
  - **切り分け（コードで確定）**: 例のデータ（`DEFAULT_CONFIG`・trigger 2 件〔f1/f2〕・keymap 0 件）は
    **子 dirty フラグを持たない** → **一覧ダイアログが出ない** → 各子は `child_save_plan._entry_for` の
    **既定規則（実体があれば SKIP / 無ければ SAVE）だけ**で決まる。
    ＝「同名なら上書きされない」の正体は **v0.4-I ではなくこの既定規則**（当初 v0.4-I と誤認 → 訂正済み）。
    例の sequence の保存先が実在しないときだけ SAVE ＝ パスが変わる子が発生し、§8 の依存 →
    **v0.4-D の確認なし自動保存**で旧トリガー一覧が上書きされる。
  - **v0.6 の 3 条項（ユーザー確定 2026-08-02）**: **O** = `restore_default` が `keymap_set_path` を
    クリアしない実バグ → **「中身のある新規作成」として扱う**（保存は別名保存へ落ちる。
    `config/example/` 案は不採用）/ **P** = `restore_default` だけ `confirm_save_if_dirty` 未呼び出し →
    未保存確認を追加 / **Q** = 例の子（trigger_set / 各 sequence）を **dirty 扱い**にし、
    一覧ダイアログと v0.4-I の保護を通す（O だけだと既存 `user/sequences/f1.json` が SKIP され
    新セットが旧セットの子を索引する ＝ 例の中身が保存されない）。受入条件 24 / 24b / 25 / 26 を追加。
  - **敵対的レビュー 2 回**: 1 回目 high 1 + medium 1 を**全採用**（同名 keymap_set 選択時に
    stem 由来 trigger_set が上書きされる点の明記 + 24b / 受入条件 25 を 3 分岐まで検証可能に）。
    2 回目 high 1（陳腐化 `_parent_refs` による孤児 trigger_set 上書き）は**除外**
    （2026-07-30 に許容と確定した露出範囲・Q により一覧へ可視化される・対策は v0.4-D の空振りを再発させる）。
  - **task_17 実装**（`codex-implementer` へ委任）: `restore_default` を `new_config` と同形へ。
    順序 = 未保存確認 → askyesno → data 置換 → `reset_trigger_set_state()` → `keymap_set_path = ""` →
    子 dirty 化（`mark_sequence_dirty` / `mark_trigger_set_dirty` / `mark_keymap_dirty`）→ UI 更新 → `set_dirty(True)`。
    **presentation 限定・既存 API のみ使用**（`dirty_state.py` は無変更）。
    tests_ui に 6 件追加（24 / 24b / 25 の 3 分岐 / 26 / 回帰）+ 既存 `test_restore_default_*` 4 件を更新。
result_files（**未コミット**）:
  - keyseq/presentation/controllers/config_io/keymap_set_io.py（`restore_default`）
  - tests_ui/test_config_io_characterization_keymap_set_startup.py（+6・既存 4 件更新）
  - instructions/history/05_child_file_save_dialog.md（v0.6 改訂）
  - instructions/phase/06_child_file_save_dialog/tasks/task_17_restore_default_as_new_set.md（新規）
  - instructions/phase/06_child_file_save_dialog/phase.md / instructions/phase/current.md
  - .claude_data/state/decisions.md（4 回目の節）
verified:
  compile: clean
  tests: pass 142
  tests_ui: pass 152（+5・約 10 秒で完走・ハングなし）
  smoke: pass
  review: reviewer（task_17 差分）= **完了可・指摘なし**（処理順序が定義表と一致 /
    `reset_trigger_set_state()` の後に dirty 化＝Q が無効化されない / 既存 API 経由で内部キー直代入なし /
    対象外への波及なし / 追加 6 件は受入条件に過不足なく対応し旧実装なら落ちる /
    既存 4 件の更新はアサーションの削除ではなく Q の新挙動の反映）
  review（暫定仕様 v0.6）: codex-adversarial-reviewer 2 回。1 回目 2 件採用 / 2 回目 1 件除外（上記）

## next_action
- **実機目視をユーザーへ依頼する**（残る唯一の未完了項目。起動は `<repo>\.venv\Scripts\python.exe main.py`。
  **VS Code の ▶ 実行〔小文字ドライブ〕でも 1 周する**）。確認項目:
  (a) 2026-07-29 の①③④⑤ + (b) 2026-07-30 の⑥⑦ + (c) task_13 の新規作成 / 例の設定に戻す +
  (d) task_06 定義「対象範囲 4」の 9 項目の退行なし + (e) 2026-08-01 の①〜④（root 直下に `user/` を作らない /
  個別トリガー一覧保存で sequence 行だけの確認が出る / ダイアログ初期表示の省略 / ホイール）+
  (f) 個別の別名保存後に未保存マークが付き構成セット保存で索引が追随（v0.5-N）+
  (g) **2026-08-02 の v0.6**: 読込 → 例を復元 → 保存で**別名保存ダイアログが出る**（旧 keymap_set が
  上書きされない）/ 未保存の変更があると**復元前に確認が出る** / 例を復元後の保存で
  **子一覧（トリガー一覧 + f1 + f2）が出て、既存の同名 sequence があれば既定が別名保存**。
  結果は `instructions/phase/06_child_file_save_dialog/integration_result.md` §3 へ記録する。
- 目視 OK 後: **task_10（`finalize_records`）を `/task_new` で起票**。正本反映で**必ず明記**する項目は
  `SHARE_NEW` / 非 dirty 子の SKIP 規則（**「保存先に実体があれば SKIP・無ければ SAVE」＝ v0.6 で正本明記対象に追加**）/
  SKIP した子の索引規則 / 依存確認ダイアログと既定ボタン / SKIP 子の dirty 保持 /
  `data_schema.md` §5.4 の「trigger_set は全セット共通」記述の更新 / §5.6 のフォールバック名の経路差
  （一括 = `default` / 個別 = `trigger_set.json`）/ 個別「トリガー一覧を保存」の保存計画化（v0.5-K）と §8 の関係 /
  **v0.3 追加分**（A / A2 / B / C / 変更なし保存でも親は書かれる）/
  **v0.4 追加分**（D/E: 依存確認の提示条件と 4 択・deferred index 例外と上位の dirty 化 / F / G /
  I〔**keymap / sequence 限定・元判定が単独 / 共有中のときだけ**〕/ H / 受入条件 15）/
  **v0.5 追加分**（J / K / L/M / N）/ **v0.6 追加分**（O: 例を復元は中身のある新規作成・同名選択時は
  stem 由来 trigger_set も上書き / P: 未保存確認 / Q: 例の子は dirty 扱い）。
  併せて暫定仕様 05 の凍結・`decisions_archive/06` 作成・`current.md` 完了記載・
  `backlog/INDEX.md`（idea_05 クローズ・idea_06 / idea_07 の条件更新）・`/refactor_check`。

## blockers
- なし。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
- **Phase β の設計の正は暫定仕様 [05](../../instructions/history/05_child_file_save_dialog.md)（**v0.6**・
  ユーザー確定済 2026-08-02）**。フェーズ中は正本 `spec_detail/` を直接改訂せず、**task_10** で昇格＋凍結する。
- **【保存経路の根本原則（再発しやすい）】** runtime の `source_path` 3 種は **config_root 相対**で保持される。
  **書き込みに使う前に必ず解決する**（`repository.save_json` は相対を **cwd 基準**で解決しディレクトリまで作る
  ＝ root 直下 `user/` の正体）。個別保存 API は **stored（記録用・相対）と resolved（書込用・絶対）を分離**（v0.5-J）。
- **【保存計画の要点】** アクションの優先順位は `child_save_plan.build_save_plan` の 1 箇所
  （一覧の選択 > confirmed > **既定 = 保存先に実体があれば SKIP / 無ければ SAVE**）。
  **一覧に行として出るのは dirty な子だけ**。非 dirty の子は既定規則だけで決まり、
  **ダイアログに出ないまま SKIP される**（v0.6 の調査で判明。正本未記載 → task_10 で明記）。
  trigger_set は明示 SKIP エントリが無ければ書かれる（`config_service.py:906-909`）。
- **Phase β の勘所**（実装時に後退しやすい）: ① 未知の参照元・別の上位に属す子は**別名保存が既定**。
  **v0.4-I**（`source_path` なしの子の保存先に既存ファイルがあれば既定は別名保存）は
  **keymap / sequence 限定・元判定が単独 / 共有中のときだけ**（trigger_set を含めると v0.4-D が空振りする）/
  ② 保存計画は **presentation が決定・application が実行**（application に tkinter 依存を持ち込まない）/
  ③ パスが変わる子の上位は**保存必須**・失敗時は**旧索引維持**・**行ごとの粒度**。
  唯一の例外 = **deferred index**（4 択で「保存しない」を明示選択したときのみ）/
  ④ 既定命名の変更は **trigger_set のみ**（keymap_set stem 基準）。
- **不変条件（壊しやすい）**: ③ `dirty_tracker.trigger_set_source_path` と
  `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致**（入口は `dirty_state` の 2 メソッドのみ）/
  ④ 子の `_parent_refs` は**保存先ファイルの集合 + 現在の上位** / ⑥ **canonical identity は比較専用**
  （`normcase` 済み文字列を保存値・戻り値・表示へ混入させない。パス同一性判定は
  `ConfigService.canonical_path` / `is_path_within` の 2 本のみを使う）。
- **`reset_trigger_set_state()` は `trigger_set_dirty = False` にする**。子を dirty 化する処理は**必ずその後**
  （逆順にすると v0.6-Q が無効化される）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  tests_ui の 3 ファイル（`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup`）の `setUp` に **fail-fast ガード**
  （`showerror` / A2 / 依存確認を「呼ばれたら `AssertionError`」に patch）がある。
  **期待するテストは個別 patch で上書きする**。新しいモーダルを増やすときは同じガードを足す。
  ただし `askyesnocancel`（未保存確認）は**ガードへ入れない**（他経路を巻き込むため各テストで個別 patch）。
- **【教訓】ハングしたら `messagebox` / `filedialog` を全遮断して単独実行する**と真因が一発で出る。
- **【tests_ui の罠】`_prepare_loaded_keymap_set` は `save_plan=None` で `save_runtime_data` を呼ぶため
  runtime に source_path が入らない**。source_path 前提のテストは**保存後に
  `load_runtime_data_from_keymap_set_path` で読み直す**こと（さもないと実リポジトリの `config/` に対して
  モーダルを開いてハングする）。
- **申し送り（refactor_check / task_10）**: ⓪ `child_save_dialog.py` が 324 行（目安 300 超）+
  `_add_text_cell` の戻り値が素の dict / ① slugify 後に別々の keymap_set 名が同一 stem へ丸まる衝突
  （受入条件 8 の範囲外）/ ② `dirty_tracker.trigger_set_imported` は読み手不在の残置状態 /
  ③ task_10 で `INTERNAL_TRIGGER_SET_SOURCE_PATH` を runtime 内部キーとして `data_schema.md` に明記 /
  ④ 実機の `config/` に絶対パスで記録済みの `_parent_refs` / 起動設定が残るが**移行処理は不要** /
  ⑤ `config_service.py` は 1600 行超。分割是非は**フェーズ末の `/refactor_check` で判定**。
- **【Codex 運用】**フォワーダが最終出力を返さず完了通知だけ来ることがある（worktree の mtime 停滞を待って
  verifier を回す）。差分 0 件のまま返ることもある（`SendMessage` で再開して回収）。
  **Codex 申告のテスト結果は信用せず必ず verifier で再実行**。**Codex は python をまったく実行できない**
  → 委任にテスト実行を含めない。手順書は `instructions/common/rules_detail/codex_operations.md`。
- **【罠】state ファイル・`instructions/` 配下・code は必ず worktree のパスで編集する**（main 側を編集すると
  commit から漏れる）。**`git grep` は追跡済みファイルのみ**（新規ファイルは直接 `grep`）。
  行数計測は `wc -l`（PowerShell `Measure-Object -Line` は空行を数えない）。
- **保存系リデザインの番号対応**: α=phase05/暫定04〔完了〕 / **β=phase06/暫定05〔進行中〕** /
  γ=phase07/暫定06〔独立・未着手〕 / プリセット=phase08/暫定07〔β とカスケード除外で協調〕。
- **Phase α の成果は正本 `spec_detail/data_schema.md` §5.4 配下が正**（新規/Import/空起動で keymap_set パスが空 →
  保存は別名保存 / 既定はディレクトリ `config/user/keymap_sets/` / 子ファイルは全セット共有〔β の課題〕/
  レガシー `settings/` 経路のみ実装未追従 = idea_09）。
- config_io は `controllers/config_io/` の 6 クラスへ分割済（App が `app.keymap_set_io` 等で直接公開）。
  Phase β の主な触点: `config_service.save_runtime_data` / `_build_split_save_payloads` /
  `config_io/keymap_set_io.py`（`save_keymap_set_to`）/ `controllers/dirty_state.py` /
  `config_io/io_dialogs.py`（`choose_save_path_with_collision`）。
- **レビュアーは 2 本立て**: `reviewer`（sonnet・単一タスクの実装差分）/ `deep-reviewer`（opus・設計文書 /
  複数タスクを跨ぐ差分 / フェーズ完了判定）。使い分けは `.claude/rules/agent_selection.md` が正。
- 未着手 idea: idea_03（hotkey 保存時正規化・優先度低）/ idea_07（参照元の掃除・**β 完了後**。
  孤児 trigger_set・陳腐化した `_parent_refs` はここで扱う）/ idea_08（keymap_set 個別プリセット）/
  idea_09（レガシー settings/ フォールバック）。保留 idea: idea_04 / idea_06（**β で達成見込み**）。
  idea_05 は β が内包（着手中）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 03_startup_font_settings_cleanup / 04_config_io_controller_split / 05_keymap_set_new_and_default_dir。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
