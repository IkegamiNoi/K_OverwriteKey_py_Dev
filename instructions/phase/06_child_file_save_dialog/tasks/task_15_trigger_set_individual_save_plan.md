# task_15_trigger_set_individual_save_plan

## 目的

個別「トリガー一覧を保存 / 別名で保存」を**保存計画駆動**にし、dirty な出力シーケンスがあるときは
一括保存と同じ子ファイル保存ダイアログを出す（暫定仕様 05 **v0.5-K**・§3 末尾・§8・受入条件 **20**・**21**・**21b**）。

現状の `config_service.save_trigger_set_file` は保存計画を受け取らず、**全 sequence を無確認で上書き**する。
§8 の「粒度の厳守（trigger_set 保存が全 sequence を巻き込まない）」に反し、§5 の安全網
（未知の参照元・別の上位に属す子は別名保存が既定）も迂回する。

レイヤ制約: **application（`save_trigger_set_file` に保存計画を通す）+ presentation（`trigger_set_file_io`）**。
**domain 不変・スキーマ不変**。一括保存経路（`save_runtime_data`）と一覧ダイアログ UI は変更しない。

## 対象範囲（個別 trigger_set 保存経路 限定）

### 1. `keyseq/application/config_service.py` — `save_trigger_set_file` が保存計画を受け取る

- キーワード引数 `save_plan: SavePlan | None = None` を追加する（**既定 None = 従来どおり全 sequence を書く**。
  既存の呼び出し元・テストを壊さないため）。
- `_build_trigger_set_payloads(..., save_plan=save_plan or SavePlan())` へ渡す
  （現在は固定で `SavePlan()`。`config_service.py:250`）。
- 書き込みを**スキップ対象で分岐**させる（現在は `sequence_items` を全件書く。`:252-253`）。
  `save_runtime_data` の該当箇所（`:376-382`）と**同じ規則**にする:
  - `item["skip"]` が True の sequence は**書かない**
  - 索引（trigger_payload の `sequence_path`）は `_build_trigger_set_payloads` が既に
    「書く子＝新パス / skip＝旧 `source_path`（実在時のみ・無ければ空）」を作るので**そのまま使う**
- 戻り値の triggers 更新（`:256-275`）も**書いた子だけ**にする:
  skip した sequence の `INTERNAL_SEQUENCE_SOURCE_PATH` / `INTERNAL_SEQUENCE_PARENT_REFS` /
  `INTERNAL_SEQUENCE_DIRTY` を**書き換えない**（dirty のまま残す）。書いた子は従来どおり
  source_path 更新・`_parent_refs` 反映・`dirty=False`。
- trigger_set 本体は**常に書く**（この操作の主目的。行にもしない）。

### 2. `keyseq/presentation/controllers/config_io/trigger_set_file_io.py` — 計画の組み立て

`save_trigger_set_to_path`（36-57）の前段に、**保存計画を組み立てる非公開メソッド**を足す
（`keymap_set_io._collect_child_save_plan` と同じ役割だが、**再解決ループは不要**）。

手順:

1. `config_service.resolve_child_save_targets(...)` を、
   **`SavePlan(entries=(ChildSaveEntry(CHILD_TRIGGER_SET, "", ACTION_SAVE_AS, <保存先パス>),))`** を渡して呼ぶ。
   これで sequence の既定保存先が**この保存先の trigger_set を基準に**解決される
   （`keymap_set_path` は `self._app.keymap_set_path` をそのまま渡す。空でも動くことを確認する）。
2. 同じ `save_plan` を渡して `collect_child_save_rows(...)` を呼び、**`kind == CHILD_SEQUENCE` の行だけ**を残す
   （keymap 行・trigger_set 行はこの操作の対象外なので捨てる）。
3. 行が 0 件なら**ダイアログを出さず** `choices = {}` で次へ進む。
   1 件以上なら `child_save_dialog.ask_child_save_actions(rows)` を出す。
   **キャンセル（`None`）ならこの保存操作全体を中止**する（trigger_set も書かない・フラッシュのみ）。
4. `child_save_plan.build_save_plan(data=..., rows=..., choices=..., targets=..., confirmed=<1 の SavePlan>)`
   で計画を作る。**未実体化の子（保存先に実体が無い）は既定で `ACTION_SAVE`・実体があり dirty でない子は
   `ACTION_SKIP`** になる（`child_save_plan.py:72` の既定規則。v0.5-K の「未実体化の子は書く」はこれで満たす）。
5. 得た計画を `config_service.save_trigger_set_file(..., save_plan=plan)` へ渡す。

- **`save_trigger_set_file`（個別保存ボタン）と `save_trigger_set_file_as`（別名保存）の両方**がこの経路を通る
  （どちらも最終的に `save_trigger_set_to_path` を呼ぶため、計画の組み立ては `save_trigger_set_to_path` 側へ置く）。
- 保存後の dirty 反映: **書いた sequence の `INTERNAL_SEQUENCE_DIRTY` は 1 の戻り値で False になる**。
  **skip した sequence は dirty のまま**にする（次回の保存で再提示される）。
  `dirty_tracker.sync_dirty_state()` は従来どおり最後に呼ぶ。
- **依存確認ダイアログ（v0.4-D/E）・deferred index はこの経路では発生させない**
  （trigger_set 自身を必ず書くため索引は同じ保存で更新される）。`confirm_trigger_set_dependency` を呼ばない。

### 3. テスト

| 追加先 | # | 内容 |
|---|---|---|
| `tests/` | 1 | `save_trigger_set_file` に skip を含む `SavePlan` を渡すと、**skip した sequence のファイルが書かれず**（バイト列不変）、trigger_set の `sequence_path` が**旧パス**を指す。`save_plan=None` では従来どおり全件書かれる（回帰なし） |
| 〃 | 2 | `ACTION_SAVE_AS` を含む計画で、指定先に書かれ索引が新パスを指す |
| `tests_ui/` | 3 | **受入条件 20**: dirty な sequence がある状態で個別「トリガー一覧を保存」→ 一覧ダイアログが出る。行は **sequence のみ**（trigger_set 行・keymap 行が無い）。dirty な sequence が無ければ**ダイアログが出ない** |
| 〃 | 4 | **受入条件 20**: ダイアログをキャンセルすると **trigger_set ファイルもバイト列不変**（何も書かれない） |
| 〃 | 5 | **受入条件 21**: 「保存しない」を選んだ sequence はファイルが書かれず索引が旧パス・**dirty のまま**。「別名保存」を選んだ sequence は指定先に書かれ索引が新パス。**dirty でない既存 sequence のファイルは一切書かれない**（mtime / バイト列で確認） |
| 〃 | 6 | **受入条件 21b**: 旧形式（`sequence_path` なし・`actions` インライン）の trigger_set を読み込んだ直後に個別保存すると、各シーケンスがファイル化され索引がそれを指し、**再読込した内容が一致**する |
| 〃 | 7 | **回帰**: 一括保存（`save_keymap_set_to`）の挙動が変わっていない（既存の特性テストが緩めずに pass） |

- `tests_ui` の **fail-fast ガード**を壊さないこと。この経路で `confirm_trigger_set_dependency` が
  呼ばれたら **AssertionError で落ちるのが正しい**（依存確認を出さない設計の固定になる）。

### 設計メモ / 制約

- **`_collect_child_save_plan`（`keymap_set_io`）を共通化しない**。あちらは再解決ループ・依存確認・A2 確認を
  含み、こちらは不要。**同じ部品（`resolve_child_save_targets` / `collect_child_save_rows` /
  `ask_child_save_actions` / `build_save_plan`）を呼ぶだけ**にとどめる（過剰共通化の回避＝
  `anti_patterns.md` 3。共通化の要否は `/refactor_check` で判定する）。
- `collect_child_save_rows` のシグネチャ・判定規則は**変更しない**（一括経路と共有しているため）。
  sequence だけに絞るのは**呼び出し側のフィルタ**で行う。
- `save_trigger_set_file` の既定引数 `save_plan=None` を「全件書く」にするのは**移行のためではなく**、
  読込直後の別経路（`load_trigger_set_file` 系のテスト等）から使われる素の API を保つため。
  **恒久互換レイヤーではない**（`file_organization_rules.md`）。個別保存経路は必ず計画を渡す。
- **task_14 の J（相対パス解決）が先に入っている前提**で書く。順序が前後する場合は
  `save_trigger_set_file` の解決規約（resolved で書く / stored を返す）を壊さないこと。

## 含まない

- **個別保存のパス解決・上位の dirty 化（v0.5-J / N）— task_14**。
- **一覧ダイアログの初期省略計算・マウスホイール（v0.5-L/M）— task_16**。
- **正本 `spec_detail/` への反映 — task_10**。
- keymap の個別保存にダイアログを出すこと（子を持たないため対象外）。
- 一括保存経路（`keymap_set_io._collect_child_save_plan` / `save_runtime_data`）の変更。
- 個別保存ボタンの UI 統合（暫定仕様 §11）/ idea_06 の共通ドライバ化（`/refactor_check` の判断対象）。

## 確認

`.venv` の python で実行する（worktree ルートから `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean
2. `-m unittest discover -s tests` が全 pass（既存 + 追加分）
3. `-m unittest discover -s tests_ui` が全 pass（既存 + 追加分）・**完走する**
4. `-m tests.smoke_app` が pass
5. **受入条件 20・21・21b**: 上記テスト 1〜7 が pass
6. 既存の特性テスト（保存 JSON のバイト列比較）を**緩めずに** pass すること

## 完了条件

- 上記確認 1〜6 が pass・**reviewer 採用**。
- 実機目視（シーケンス変更後にトリガー一覧から保存してダイアログが出ること）は
  **task_10 の前にユーザーがまとめて実施**する。本タスクでは実施しない。
