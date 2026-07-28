# task_06b_review_fixes

## 目的

task_06 の 2 本立てレビュー（`deep-reviewer` = 修正して採用 / `codex-reviewer` = P1 2 件）で出た指摘のうち、
**task_07（正本反映）へ進む前に直すべき 6 件（A〜F）** を修正する（ユーザー確定 2026-07-29）。
中心は **受入条件 9（trigger_set の source_path が keymap / sequence と一貫）の未達解消**。

- レイヤ制約: presentation（`config_io` / `dirty_state`）+ application（参照元マージのみ）。
  **domain 不変・スキーマ不変**（`_parent_refs` のキー自体は task_01 のまま。書き込み内容の算出だけ直す）。
- **仕様の追加はしない**。暫定仕様 05 §4・§7・§8 の**未達を埋める**修正に限る。

## 対象範囲

### A. 依存確認で選んだ trigger_set の別名保存先が最終 plan に載らない（codex P1 ①）

**現象**: `_collect_child_save_plan` の `pending` は**保存先の解決にしか使われず**、最終 plan にマージされない。
trigger_set が非 dirty だと一覧に行が無いため、再ループ後の `build_save_plan` が非 dirty 既定
（`child_save_plan.py:67`）で `ACTION_SAVE` / `ACTION_SKIP` を作り直し、**ユーザーが選んだパスが消える**。
その結果 `_resolve_trigger_set_save_path` が runtime の旧 `source_path` へフォールバックし、
**旧ファイルを上書き**する（さらに `_trigger_target_changed` が再び真になり一覧が余計に再表示される）。

**修正**: `build_save_plan` に**確定済みエントリ**を渡せるようにする。

```python
def build_save_plan(*, data, rows, choices, targets, confirmed: SavePlan | None = None) -> SavePlan
```

- 各子のアクションの**優先順位**を 1 箇所で決める:
  **① 一覧の選択（`choices`）> ② `confirmed` のエントリ > ③ 非 dirty 既定（存在すれば SKIP / 無ければ SAVE）**
- `keymap_set_io._collect_child_save_plan` は `confirmed=pending` を渡す。
- 結果として、確定済み trigger_set がある周回では `_trigger_target_changed` が偽になり**再ループしない**こと。

### B. trigger_set の source_path が二重管理（deep 高1 + codex P1 ②）＝ **受入条件 9 の未達**

**現象**: application は runtime の `INTERNAL_TRIGGER_SET_SOURCE_PATH` を、presentation は
`dirty_tracker.trigger_set_source_path` を正としており、**一度も同期していない**。実害 3 つ:

- (a) keymap_set 読込直後は tracker が空（`keymap_set_io.py:395` が毎回クリア）→ 個別「トリガー一覧を保存」で
  **毎回保存先を聞かれる**（keymap / sequence は聞かれない ＝ 一貫性が無い）
- (b) 個別保存で tracker だけ新パスへ進み runtime キーは旧パス → 直後の一括保存が**旧パスへ書き**、
  直前に作ったファイルが孤児化する
- (c) `sequence_file_io.py:59` の `parent_ref=dirty_tracker.trigger_set_source_path` が空 →
  **個別シーケンス保存で §4 の参照元記録ができない**

**修正**（§7 の確定軸 = 案1「`dirty_tracker` へ寄せる」に合わせ、**両者を常に一致させる**）:

- `dirty_state.DirtyStateTracker` に**状態変更の入口を 1 本化**する（`__init__` で `get_data` と
  `config_service` を既に受けているので、runtime キーも書ける）:

  ```python
  def set_trigger_set_source_path(self, path: str) -> None:
      """tracker と runtime の内部キーを同時に更新する（両者の不一致を作らない）"""
  def sync_trigger_set_source_path_from_data(self) -> None:
      """runtime の内部キーを tracker へ取り込む（読込直後・一括保存直後に呼ぶ）"""
  ```

- 呼び出し側を置き換える（**直接代入を残さない**）:
  - `keymap_set_io.apply_loaded_data_to_ui`（`:395`）: `= ""` を **`sync_trigger_set_source_path_from_data()`** へ
  - `keymap_set_io.save_keymap_set_to`: `save_runtime_data` 成功後に
    **`sync_trigger_set_source_path_from_data()`**（別名保存・既定命名変更で変わった先を取り込む）
  - `trigger_set_file_io`（`:45` / `:75`）: `= path` を **`set_trigger_set_source_path(path)`** へ
- **不変条件**: `dirty_tracker.trigger_set_source_path` と `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は
  常に同じ値を指す（片方だけ更新する経路を作らない）。

### C. dirty 行 0 件のとき依存確認の「選び直す」が無限ループ（deep 中4）

**現象**: `rows` が空だと一覧ダイアログを出さない（`keymap_set_io.py:145`）ため、依存確認で「選び直す」を
選ぶと**戻る先が無く confirm が延々と再表示される**（到達例: 子が dirty でない + trigger_set ファイルは存在
〔既定 SKIP〕+ 保存先が未作成の sequence がある）。

**修正**: 「選び直す」時に **`rows` が空なら `None`（保存中止）を返す**（1 バイトも書かない）。
`rows` があるときの挙動は現状どおり（`pending` をリセットして一覧へ戻る）。

### D. 受入条件 9 のテストが主張を固定していない（deep 中2）

現行 `tests_ui/test_config_io_characterization.py::test_trigger_set_save_uses_dirty_tracker_source_path` は
tracker に**手で代入**してから「個別保存が tracker を読む」ことだけを見ており、(a) の非対称を検出できない。

**追加するテスト**（既存ファイルへ追加。新規ファイルは作らない）:

1. **読込直後**に `dirty_tracker.trigger_set_source_path` が `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` と一致する
2. **一括保存で trigger_set のパスが変わった後**、tracker が**新パス**を指す
3. **個別保存で新パスにした後**、一括保存が**新パスへ書く**（旧ファイルは更新されない = バイト列不変）
4. 上記 3 の後、個別シーケンス保存の `parent_ref` が**空でない**（(c) の回帰）

### E. ダイアログ本体が全テストで迂回され 1 行も実行されていない（deep 中3）

`tests_ui/test_child_save_dialog.py` は全ケースで `ask_child_save_actions` を patch しており、
`ChildSaveDialog` の内部（行の生成・既定ラジオ・OK の返り値・別名保存先の解決）が未実行。

**追加するテスト**（既存 `tests_ui/test_child_save_dialog.py` へ追加。実 App を起こす既存の流儀に合わせ、
`wait_window` をモックする等で**実表示せずに**内部を叩く）:

1. 行ごとのラジオの初期値が `row.default_action` になっている
2. OK で `{(kind, key): (action, target_path)}` が返る（選択したとおり）
3. `ACTION_SAVE_AS` の行で `asksaveasfilename` が**キャンセル**されたら **`None`**（＝ 一覧へ戻る）
4. キャンセルボタン / `WM_DELETE_WINDOW` で **`None`**

### F. 別名保存で既存ファイルの `_parent_refs` が失われる（deep 中5）

**現象**: 子ファイルの payload の `_parent_refs` は **in-memory の集合 + 現在の上位**で、
**保存先ファイルが持つ既存の参照元を読まずに丸ごと置換**する（`config_service.py:1112-1120` / `1256-1264` 付近）。
共有ファイルへ別名保存すると**他構成の所有記録が消え**、次回の §5 判定が UNKNOWN 側へ劣化する。

**修正**: 子を書く直前に、**保存先ファイルの既存 `_parent_refs` を読み、それに現在の上位をマージ**する
（§4「現在の上位パスを集合へ追加」= 保存先ファイルの集合に対する追加、と読む）。

- 既存の `read_parent_refs`（task_04）と `_merge_parent_ref`（task_01・重複排除・順序保持）を再利用する。
- **best-effort**（読めない・壊れている・キー無しは無視して現状どおり書く。例外を投げない）。
- 対象は keymap / trigger_set / sequence の 3 種。**`ACTION_SKIP` の子は書かないので対象外**。
- 既存の後方互換テスト（親未指定なら出力 JSON 不変）を壊さないこと。

### 設計メモ / 制約

- **A の優先順位は `child_save_plan.py` に 1 箇所だけ置く**（`keymap_set_io` 側で後付けマージしない。
  計画の組み立て規則がオーケストレーションへ散るのを避ける）。
- **B は「入口を 1 本化」が本質**。同期呼び出しを増やすのではなく、直接代入を残さないこと。
- **F は application 側**（保存先ファイルを読むのは I/O 責務）。presentation から渡さない。
- 指摘の一部は**本タスクで直さず task_07（正本反映）で明文化**する（下記「含まない」）。

## 含まない

- **正本 `spec_detail/` への明記** → **task_07**。対象（レビューで洗い出し済み）:
  `SHARE_NEW`（deep 8）/ 非 dirty 子の SKIP 規則（deep 7）/ SKIP した子の索引規則（deep 6）/
  依存確認ダイアログの存在と既定ボタン / SKIP 子の dirty 保持 /
  `data_schema.md` §5.4 の「trigger_set は全セット共通ファイルを共有」記述の更新（deep 11）/
  §5.6 のフォールバック名が経路ごとに異なる点（一括 = `default` / 個別 = `trigger_set.json`）/
  個別「トリガー一覧を保存」が全 sequence を書く点と §8 の関係（deep 13）
- **sequence の共有判定の「現在の上位」が計画後の trigger_set 保存先である点**（deep 9・表示文言の食い違い）→ **保留**
- **`os.makedirs` が事前検証で走る点**（deep 10・docstring との文言差）→ **保留**
- **一覧再表示で選択が全リセットされる点**（deep 16）→ **保留**（task_05 で意図した簡素化）
- **`_ask_save_as_path` が `choose_save_path_with_collision` を使っていない点**（deep 14）→ **保留**
- **`keymap_set_io.py` / `config_service.py` の行数超過の分割**（deep 12）→ **task_07 の `/refactor_check`**
- **個別保存ボタンの統合 / 参照元の掃除機能 / hotkey_presets** → スコープ外（暫定仕様 §11）

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `../../../.venv/Scripts/python.exe`）を使う。

1. `-m compileall -q keyseq main.py tests_ui` → clean
2. `-m unittest discover -s tests` → fail 0（現在 129 件 + 追加分）
3. `-m unittest discover -s tests_ui` → fail 0（現在 97 件 + 追加分）
4. `-m tests.smoke_app` → pass
5. **A**: 非 dirty の trigger_set を依存確認で「別名保存」したとき、
   **選んだパスへ書かれる**（旧 source_path のファイルはバイト列不変）。一覧の再表示が**1 回で収束**する
6. **B**: D の 4 テストが pass。加えて `dirty_tracker.trigger_set_source_path` と
   `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` が**読込後・一括保存後・個別保存後のいずれでも一致**する
7. **C**: dirty 行 0 件 + 依存あり の状態で「選び直す」を返すと、**確認が再表示されず保存が中止**され、
   **1 ファイルも書かれない**
8. **E**: ダイアログ内部の 4 テストが pass
9. **F**: 既存 `_parent_refs` を持つファイルへ別名保存すると、**既存の参照元が残ったまま**現在の上位が追加される。
   親未指定時の出力 JSON は従来どおり（後方互換テストが無修正で pass）
10. 既存の後方互換テスト（`tests/test_config_service.py` の保存 JSON 完全一致）が**無修正で pass**
11. `integration_result.md` の受入条件 **9 の行を「pass」へ更新**し、固定テストを D のものへ差し替える

## 完了条件

- 上記確認 1〜11 がすべて pass（実測は `verifier` が `.venv` で行う）。
- **`reviewer` 採用**（観点: 指摘 A〜F が実際に塞がれたか / 状態変更の入口が 1 本化されたか〔B〕/
  計画の組み立て規則が 1 箇所か〔A〕/ 保留とした指摘を勝手に直していないか / 過剰実装が無いか）。
- **実機目視は本タスク完了後にユーザーが実施**（task_06 の 9 項目 + deep-reviewer 推奨の 6 項目）。
  結果は `integration_result.md` §3 へ記録する。
