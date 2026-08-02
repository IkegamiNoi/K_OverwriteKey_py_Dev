# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-02T12:00:00
phase: `instructions/phase/06_child_file_save_dialog`（保存系リデザイン **Phase β**）
last_commit_location: claude/device-testing-procedures-16467e ※現在地はセッション開始時の git 実測値が正

## current
focus: **task_18 完了（v0.7 の実装も完了）。残るは実機目視（R1〜R11）と task_10（正本反映）**。
mode: pending_review

## last_action
ts: 2026-08-02T12:00:00
who: main
summary: |
  【実機目視手順の統合 → 5 回目のフィードバック → 暫定仕様 05 を **v0.7** へ改訂 → task_18 実装・完了】
  - **目視手順の統合**: task_01〜17 に散在していた目視項目を操作順に統合した
    `instructions/phase/06_child_file_save_dialog/manual_check_plan.md`（**R1〜R11**・起動 A/B の 2 周）を新規作成。
    **task_06 のチェックリスト #5 / #6 は v0.3-A・v0.4-D/E で仕様が変わっており旧文言のままだと誤 NG**
    になる点を R6 に明記して読み替えた。
  - **5 回目の目視指摘**: 「例を復元」→ **既存名**の keymap_set を選んで保存したとき、同名の trigger_set が
    実在するのに既定ラジオが「保存」（表示は「単独」）。
  - **切り分け**: **仕様どおり**（実バグではない）。v0.4-I は trigger_set 対象外で、既存 trigger_set の
    `_parent_refs` が選択した keymap_set のみ＝「単独」判定。§2【v0.6-O】/ 受入条件 24b に明記済み。
  - **ただし表示の欠陥**: 共有状況 5 値のうち保存先にファイルが無いのは「新規作成」だけで、「単独」は
    既存ファイルの上書きを意味するのに語からそれが読めない → **v0.7-R**。**表示文言のみ**
    「単独」→「**この構成のみが所有・既存を上書き**」（ユーザー確定。案 B〔trigger_set 行への注記追加〕/
    案 C〔v0.4-I 拡張＝2026-07-30 に却下済〕は不採用）。受入条件 27 を追加。
  - **敵対的レビュー 3 件**（needs-attention）: high〔実装タスク未接続〕= 採用（task_18 起票）/
    medium1〔条項・手順が「単独」を画面表示として記述〕= **修正して採用・範囲限定**（仕様書は v0.7 節の
    「判定名を指す」定義で解決済とし、`manual_check_plan.md` の R6 更新 + R11 追加のみ）/
    medium2〔受入条件 27 が検出不能〕= 採用（3 点検証へ書き換え）。
  - **task_18 実装**（`codex-implementer` へ委任）: `share_text_for(SHARE_SOLE)` の戻り値 1 行のみ変更。
    **presentation 限定・挙動不変**（判定名 `SHARE_SOLE`・`default_action_for`・`keymap_set_io.py` の
    `(SHARE_SOLE, SHARE_NEW)` 分岐はすべて無変更）。テスト 3 件追加 +
    既存 fixture は**レイアウト境界の 4 箇所のみ**新文言へ差替（残り 12 箇所は温存）。
result_files（**未コミット**）:
  - keyseq/presentation/controllers/config_io/child_save_rows.py（`share_text_for` の SHARE_SOLE・1 行）
  - tests/test_child_save_rows.py（+2）/ tests_ui/test_child_save_dialog.py（+1・fixture 4 箇所更新）
  - instructions/history/05_child_file_save_dialog.md（v0.7 改訂・§5・受入条件 27・§12）
  - instructions/phase/06_child_file_save_dialog/manual_check_plan.md（新規・R1〜R11）
  - instructions/phase/06_child_file_save_dialog/tasks/task_18_share_state_sole_wording.md（新規）
  - instructions/phase/06_child_file_save_dialog/phase.md / instructions/phase/current.md
  - .claude_data/state/decisions.md（5 回目の節）
verified:
  compile: clean
  tests: pass 144（+2）
  tests_ui: pass 153（+1・16.3 秒で完走・ハングなし）
  smoke: pass
  regression_check: 追加 3 件は**旧文言へ戻すと全て fail**することを verifier が実測し、確認後に復元済み
  review: reviewer（task_18 差分）= **完了可・指摘なし**（挙動不変を確認 / 追加 3 件が受入条件 27 の
    3 点に 1:1 対応 / fixture 差替はレイアウト境界 4 箇所に限定され不要変更なし / 「含まない」項目への波及なし）
  review（暫定仕様 v0.7）: codex-adversarial-reviewer 1 回（3 件。上記のとおり採用・範囲限定採用）

## next_action
- **実機目視をユーザーが実施中**（残る未完了項目）。手順は
  **[manual_check_plan.md](../../instructions/phase/06_child_file_save_dialog/manual_check_plan.md) の R1〜R11 が正**
  （R1 個別保存のパス解決 / R2 個別トリガー一覧保存の子一覧 / R3 ダイアログの見た目 4 点 /
  R4 一括保存の基本 / R5 所有元不明・共有中〔JSON 手編集の準備が要る〕/ R6 依存確認・別名保存後 /
  R7 個別別名保存の索引追随 / R8 新規作成直後の個別保存 / R9 例を復元 / R10 VS Code ▶ 起動の小文字ドライブ /
  **R11 共有状況の新文言**）。起動は `<repo>\.venv\Scripts\python.exe main.py`（R10 のみ VS Code の ▶）。
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
  stem 由来 trigger_set も上書き / P: 未保存確認 / Q: 例の子は dirty 扱い）/
  **v0.7 追加分**（R: 共有状況表示は上書きの有無が読み取れる文言にする。判定名 `SHARE_SOLE` は不変）。
  併せて暫定仕様 05 の凍結・`decisions_archive/06` 作成・`current.md` 完了記載・
  `backlog/INDEX.md`（idea_05 クローズ・idea_06 / idea_07 の条件更新）・`/refactor_check`。

## blockers
- なし。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
- **Phase β の設計の正は暫定仕様 [05](../../instructions/history/05_child_file_save_dialog.md)（**v0.7**・
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
- **【共有状況の判定名と表示文言は別物】**（v0.7 以降）。仕様書・タスク定義が「共有状況が単独 / 新規作成なら〜」
  と書くのは**判定名**（`SHARE_SOLE` / `SHARE_NEW`）を指す。画面表示は `share_text_for` が持ち、
  `SHARE_SOLE` の表示は**「この構成のみが所有・既存を上書き」**（旧「単独」）。
  分岐は必ず判定名で書き、文言で分岐しない。
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
