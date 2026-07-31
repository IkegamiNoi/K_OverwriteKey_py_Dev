# task_12_dependency_confirm_scope

## 目的

依存確認ダイアログ（「トリガー一覧の保存が必要です」）が、上位を単独所有しているときにも出て冗長だった
問題を解消し、あわせて安全側の既定を強化する（暫定仕様 05 **v0.4-D / E / F / I** と **§8 の deferred index 例外**・
受入条件 **15 / 16 / 16b / 17b / 18**）。

- **提示条件を絞る**: 上位（trigger_set）の共有状況が「単独」「新規作成」なら**確認を出さず自動保存**し、
  保存完了メッセージで事後通知する。
- **残るケースは 4 択**（保存 / 別名保存 / 保存しない / キャンセル・**既定ボタン = 別名保存**）。
  「保存しない」= **deferred index**（索引は旧パスのまま・上位を強制 dirty 化して次回保存で追随）。
- **v0.4-I**: `source_path` を持たない子（新規）の保存先に既存ファイルがあるときは、共有状況にかかわらず
  **既定を別名保存**にする。
- **v0.4-F**: v0.3-A2（再計算先の上書き確認）は**維持**する（廃止しない・条件も変えない）。

レイヤ制約: **presentation（判定と UI）+ application（事前検証の例外）**。
**domain 不変・スキーマ不変**。保存計画の実行順序・失敗時の旧索引維持（task_03）の契約は変えない。

## 対象範囲

### 1. `keyseq/application/save_plan.py` — 例外の表明を型で持つ

- `SavePlan` に **`allow_deferred_index: bool = False`** を追加する（frozen dataclass のフィールド追加）。
  既定 `False` なので既存の呼び出しは挙動不変。
- 意味: 「ユーザーが 4 択で『保存しない』を明示選択したため、**パスが変わる子の上位のスキップを許可する**」。
  **presentation がこのフラグを立てる**（自動判定では立てない）。

### 2. `keyseq/application/config_service.py` — deferred index 例外を通す

- `_validate_save_plan`（現行 786-790 行の必須依存チェック）で、
  **`save_plan.allow_deferred_index` が True のときだけ** `SavePlanError` を投げずに通す。
  それ以外の条件（未知の子種別・重複・存在しない key・別名保存先の空/作成不可）は**従来どおり**。
- 書き込み側は変更しない。trigger_set が SKIP なら trigger_set ファイルは書かれず、
  keymap_set の索引（`indexed_trigger_set_path`）も既存パスのままになる（現行実装で成立済み）。
- **`_apply_saved_child_paths` は変更しない**。書いた子の `source_path` が新パスへ更新される現挙動が、
  次回保存での索引追随の前提になる。

### 3. `keyseq/presentation/controllers/config_io/child_save_rows.py` — v0.4-I の既定判定

- 共有状況に **`SHARE_NEW_COLLIDES = "new_collides"`** を追加する。
  - `share_text_for` → **「同名の既存ファイルあり・安全のため別名」**
  - `default_action_for` → **`ACTION_SAVE_AS`**
- `build_row` に **`has_source_path: bool`** を追加する（キーワード引数）。
  **`has_source_path` が False かつ保存先が存在する**なら、`_parent_refs` の内容にかかわらず
  `SHARE_NEW_COLLIDES` を返す（`judge_share_state` の判定より優先）。
  `has_source_path` が True のときは従来どおり `judge_share_state` の結果を使う。
- `collect_child_save_rows` は各子の `source_path` の有無を渡す:
  keymap = `INTERNAL_KEYMAP_SOURCE_PATH` / sequence = `INTERNAL_SEQUENCE_SOURCE_PATH` /
  trigger_set = `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]`（いずれも空文字なら False）。
- `judge_share_state` の**シグネチャと既存判定は変更しない**（新状態は `build_row` 側で被せる）。

### 4. `keyseq/presentation/controllers/config_io/child_save_dialog.py` — 4 択ダイアログ

`confirm_trigger_set_dependency` を **4 択**にする。`messagebox` は 3 択までなので **`tk.Toplevel` で自前に組む**。

- 戻り値は現行と同じ文字列契約: `ACTION_SAVE` / `ACTION_SAVE_AS` / **`ACTION_SKIP`（新規）** /
  `""`（キャンセル = 選び直し）。`ACTION_SAVE_AS` のときに `self.trigger_set_save_as_path` へ
  `asksaveasfilename` の結果を入れる現行の作法は**維持**（別名保存先が空なら `""` を返すのも維持）。
- 表示内容は現行のメッセージを踏襲（保存先が変わるシーケンス一覧 / トリガー一覧の保存先 / 共有状況）＋
  各選択肢の意味を 1 行ずつ。**「保存しない」には「この保存では索引を更新しない（次回保存で反映）」**を添える。
- **既定ボタン = 別名保存**（初期フォーカス）。`Escape` と `WM_DELETE_WINDOW` は**キャンセル**扱い。
- 既存の作法を踏襲: `_app.hook.suspend_hook_for_dialog()` / `resume_hook_after_dialog()` を try/finally で、
  `transient` + `grab_set` + `wait_window`。
- **task_11 のレイアウト実装（一覧ダイアログ）には触らない**。この 4 択ダイアログは固定サイズでよい
  （行数が多いときはメッセージ部だけ縦スクロールにしてもよいが、**必須ではない**）。
- `confirm_recalculated_overwrite`（A2）は **無変更**（v0.4-F）。

### 5. `keyseq/presentation/controllers/config_io/keymap_set_io.py` — 提示条件と deferred index の配線

`_collect_child_save_plan` の依存確認ブロック（現行 194-251 行）を次のようにする。

1. `blocked` が空でなければ `trigger_row = self._trigger_set_row(rows, targets, save_path)` を作る
   （`build_row` の `has_source_path` を渡すこと）。
2. **`trigger_row.share_state` が `SHARE_SOLE` または `SHARE_NEW`** なら:
   - **ダイアログを出さず** `action = ACTION_SAVE` として扱う。
   - **事後通知**を作る（例: 「トリガー一覧も保存して索引を更新しました。」）。既存の
     `recalculation_notice` と**併記**できるようにする（両方出るときは 2 行になる）。
3. それ以外（`SHARE_UNKNOWN` / `SHARE_OTHER_PARENT` / `SHARE_SHARED` / `SHARE_NEW_COLLIDES`）なら
   **4 択ダイアログ**を出し、結果で分岐する:
   - `ACTION_SAVE` / `ACTION_SAVE_AS` — 現行と同じ（確定エントリを `confirmed` に載せて再計算判定へ）
   - **`ACTION_SKIP`（新規）** — trigger_set を SKIP にした計画を作り、**`allow_deferred_index=True`** で返す。
     再計算判定（`_trigger_target_changed` 以降）は**通らない**（保存先が変わらないため）。
   - `""`（キャンセル）— 現行どおり `pending = SavePlan()` にして一覧から選び直し
4. **deferred index を選んだ場合の dirty 化**: `save_keymap_set_to` が**保存成功後**（
   `_clear_saved_child_dirty_flags` の後・`set_dirty(False)` の前後関係に注意）に
   **`dirty_tracker.mark_trigger_set_dirty()`** を呼ぶ。
   `_collect_child_save_plan` の戻り値を `(plan, notice)` から
   **`(plan, notice, deferred_index: bool)`** 等へ広げて伝えること（戻り値の形は実装者判断でよいが、
   **保存前の dirty 状態に依存しない**こと ＝ `_skipped_dirty_children` 頼みにしない）。
   完了メッセージにも 1 行足す（例: 「トリガー一覧は未保存です。次回保存で索引を更新します。」）。

### 6. テスト

**`tests/`（application）**

| # | 内容 |
|---|---|
| 1 | `allow_deferred_index=False`（既定）では、パスが変わる子があり trigger_set が SKIP の計画は従来どおり `SavePlanError` |
| 2 | `allow_deferred_index=True` なら同じ計画が例外にならず、**子は新パスへ書かれ、trigger_set ファイルはバイト列不変**（旧 `sequence_path` を維持）。keymap_set と起動設定は従来どおり書かれる |
| 3 | 2 の後、**trigger_set を保存する計画で再保存 → 再読込**すると `sequence_path` が**新パス**を指し、内容が新パスの子と一致する（受入条件 16b の通し） |

**`tests_ui/`（presentation）**

| # | 内容 |
|---|---|
| 4 | 上位が「単独」「新規作成」のとき**依存確認ダイアログが呼ばれず**、trigger_set が `ACTION_SAVE` の計画になり、完了メッセージに事後通知が入る（受入条件 15） |
| 5 | 上位が「所有元不明 / 別の構成 / 共有中 / 同名の既存ファイルあり」のとき **4 択ダイアログが呼ばれる**（受入条件 16） |
| 6 | 4 択で「保存しない」を選ぶと `allow_deferred_index=True` の計画になり、**保存後に `trigger_set_dirty` が True**（保存前が False でも）（受入条件 16b の presentation 側） |
| 7 | 4 択の既定フォーカスが「別名保存」・`Escape` / ウィンドウを閉じるでキャンセル（`""` 相当）になる |
| 8 | **v0.4-I**: `source_path` を持たない子の保存先に既存ファイルがあると、その `_parent_refs` が現在の上位のみでも既定が**別名保存**になり、表示が「同名の既存ファイルあり・安全のため別名」（受入条件 17b） |
| 9 | **受入条件 18（再現テスト・先に書く）**: 出力シーケンスのみ dirty の状態で keymap_set 保存 → 一覧で**別名保存**を選ぶ → **指定した保存先にファイルが作られ**、保存された trigger_set の `sequence_path` が**新パス**を指す（旧パスへ書かれない）。**別名保存先が新規ファイル名の場合と既存ファイル名の場合の両方**、かつ**単独所有（確認なし自動保存）と 4 択で「保存」を選んだ場合の両方**で成立すること |

- 既存テストで `messagebox.askyesnocancel` を patch して依存確認を駆動しているものは、
  **新しい 4 択ダイアログの呼び出しに合わせて更新**する（**アサーションは緩めない**）。
- ダイアログは monkeypatch で選択を駆動する既存手法（`tests_ui` の作法）を踏襲する。

### 設計メモ / 制約

- **判定は presentation・実行は application**（暫定仕様 §2 指摘②）。`allow_deferred_index` は
  presentation が立てるフラグで、application はそれを**検証の緩和にのみ**使う
  （application が自分で「スキップしてよい」と判断しない）。
- **A2（`confirm_recalculated_overwrite`）と `_recalculated_overwrite_rows` の条件を変えない**。
  ただし `build_row` に `has_source_path` が増えるため、`_recalculated_overwrite_rows` からの呼び出しにも
  正しい値を渡すこと（新規の子が再計算先の既存ファイルに当たるケースは `SHARE_NEW_COLLIDES` になり、
  `!= SHARE_SOLE` なので A2 の対象に入る＝ v0.3-A2 の critical 指摘と同じ守り方になる）。
- **canonical identity（v0.3-B）でパスを比較する**。`canonical_path` / `is_path_within` 以外の
  素の文字列比較を復活させない。
- 4 択ダイアログの実装で `_app` 以外のグローバル状態を持たない。`trigger_set_save_as_path` の
  受け渡し方式（インスタンス属性）は現行踏襲でよい。
- `keymap_set_io.py` の `_collect_child_save_plan` は既に長い。**本タスクでの分割は最小限**にとどめ、
  大きな構造変更はフェーズ末の `/refactor_check` へ回す。

## 含まない

- **`data` を新規化・置換する入口の trigger_set 状態リセット（v0.4-H）— task_13**。
- **正本 `spec_detail/` への反映 — task_10**。
- 一覧ダイアログのレイアウト（task_11 で完了。**触らない**）。
- A2 の廃止・条件変更（v0.4-F で**維持**と決定済み）。
- 既定保存先の命名変更（v0.4-G で**不採用**。`_allocate_unique_*` は現挙動のまま）。
- keymap_set 側の依存（keymap のパスが変わる場合）の 4 択化 — 本タスクは **trigger_set の依存確認のみ**。
- 個別保存ボタンの統合（暫定仕様 §11）。

## 確認

`.venv` の python で実行する（worktree ルートから `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests_ui` が clean
2. `-m unittest discover -s tests` が全 pass（現行 136 件 + 追加分）
3. `-m unittest discover -s tests_ui` が全 pass（現行 124 件 + 追加分）
4. `-m tests.smoke_app` が pass
5. **受入条件 15 / 16 / 16b / 17b / 18**: 上記テスト 1〜9 が pass
6. 既存の特性テスト（保存 JSON のバイト列比較）を**緩めずに** pass すること
7. **受入条件 6 の回帰**: 上位が単独 / 新規のときは従来どおり**スキップできない**
   （自動保存されることをもって満たす）。`allow_deferred_index` を立てない経路で
   `SavePlanError` が出ることをテスト 1 で固定

## 完了条件

- 上記確認 1〜7 が pass・**reviewer 採用**。
- 実機目視（単独所有なら確認が出ない / 共有時は 4 択が出る）は **task_10 の前にユーザーがまとめて実施**する。
