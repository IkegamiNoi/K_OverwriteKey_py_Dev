# task_13_data_replace_state_reset

## 目的

`data` を新規化・置換する入口が **trigger_set の状態（`dirty_tracker.trigger_set_source_path` /
`trigger_set_dirty` / `trigger_set_imported`）をリセットしていない**実バグを直す
（暫定仕様 05 **v0.4-H** / §7・受入条件 **17**）。

`data` は新規化されるのに tracker が前の構成の値を保持するため、**直後に個別「トリガー一覧を保存」を押すと
前の構成の trigger_set へ無確認で書く**（一括保存経路は `data` 側を見るため正しい）。
Phase β の不変条件「`dirty_tracker.trigger_set_source_path` と
`data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は常に一致」に反している。

レイヤ制約: **presentation 限定**（`controllers/dirty_state.py` と `config_io/keymap_set_io.py`）。
**application / domain 不変・スキーマ不変**。仕様変更ではなく**バグ修正**。

## 対象範囲（presentation 限定）

### 1. `keyseq/presentation/controllers/dirty_state.py` — リセットの入口を 1 本用意する

`DirtyStateTracker` に **trigger_set の状態を初期化するメソッドを 1 つ追加**する
（名前は `reset_trigger_set_state` を想定。実装者判断で変えてよいが、**リセットの入口はこの 1 本に集約**すること）。

- `set_trigger_set_source_path("")` を通して **tracker と `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` の両方**を空にする
  （**直接代入を復活させない** = 既存の不変条件④）
- `trigger_set_dirty = False` / `trigger_set_imported = False` にする
- `_on_change()` の呼び出し有無は既存メソッドの作法に合わせる（`set_dirty` を経由する呼び出し元があるため、
  このメソッド自体は表示更新を強制しなくてよい）

### 2. `keyseq/presentation/controllers/config_io/keymap_set_io.py` — 2 つの入口から呼ぶ

`data` を新規化・置換している次の 2 箇所で、**`data` を差し替えた直後**に 1 のメソッドを呼ぶ。

| 入口 | 現状 | 変更 |
|---|---|---|
| `new_config`（48-64 行） | `data` を新規化するが trigger_set 状態を触らない | 1 のリセットを呼ぶ |
| `restore_default`（520-529 行） | 同上（`new_default_data()` で置換のみ） | 1 のリセットを呼ぶ |

- **呼ぶ位置**: `self._app.data = ...` の後、`_sync_control_vars_from_data()` の前後どちらでもよいが、
  **`set_dirty(True)` より前**にすること（dirty 表示の上書きを避ける）。
- **`apply_loaded_data_to_ui`（読込 / Import / 起動設定変更）は変更しない**。
  既に `sync_trigger_set_source_path_from_data()` + `trigger_set_imported = False` +
  `trigger_set_dirty = False` を行っており、同期されている（**回帰しないことをテストで固定**する）。
- `new_config` / `restore_default` の**それ以外の挙動は変えない**
  （`set_dirty(True)` のまま・個別 dirty フラグの付与や `clear_individual_dirty_flags()` の追加はしない）。

### 3. テスト（`tests_ui/`）

既存の `tests_ui` テストファイル（`test_child_save_dialog.py` か、`new_config` / `restore_default` を
扱っている既存ファイルのうち適切な方）へ追加する。**新規ファイルは作らない**。

| # | 内容 |
|---|---|
| 1 | keymap_set を保存して `trigger_set_source_path` が入った状態から **`new_config`** を実行すると、`dirty_tracker.trigger_set_source_path` が空になり、`data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` も空（**両者が一致**）。`trigger_set_dirty` / `trigger_set_imported` も False |
| 2 | 同じ状態から **`restore_default`** を実行しても 1 と同じになる（確認ダイアログ `askyesno` は patch して「はい」を返す） |
| 3 | **受入条件 17**: `new_config` 直後に個別「トリガー一覧を保存」（`trigger_set_io.save_trigger_set_file`）を実行しても、**前の構成の trigger_set ファイルが書き換わらない**。`source_path` が空なので保存先の選択（`choose_save_path_with_collision`）へ入ることを確認する（選択をキャンセルすれば何も書かれない） |
| 4 | 同じことを **`restore_default` 直後**でも確認する |
| 5 | **回帰**: 読込（`load_keymap_set_from`）/ Import（`import_config`）経路では、`apply_loaded_data_to_ui` を通じて従来どおり tracker と `data` が同期されている（リセットで壊していない） |

- テストは `tests_ui` の既存手法（tkinter の widget / ダイアログを patch して駆動）を踏襲する。
- **task_12 で入れた fail-fast ガード**（`showerror` / A2 / 依存確認が呼ばれたら `AssertionError`）がある
  クラスへ追加する場合は、そのガードを壊さないこと。保存経路を通すテストで想定外のモーダルが出たら
  即 fail するのが正しい状態。

### 設計メモ / 制約

- **変更の入口は `dirty_state` のメソッドだけ**にする（`trigger_set_source_path` への直接代入や、
  `keymap_set_io` から `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` を直接触る実装にしない）。
- `new_config` は `data["triggers"] = []` にするため trigger_set は「新規」状態になる。
  **個別 dirty フラグを新たに立てない**こと（未作成の子は保存時に既定計画で書かれる。§3 末尾）。
- `trigger_set_imported` は現状読み手がいない残置状態だが、**リセット対象には含める**
  （tracker の状態を一箇所で初期化する意図を明確にするため）。

## 含まない

- **正本 `spec_detail/` への反映 — task_10**（`INTERNAL_TRIGGER_SET_SOURCE_PATH` の明記を含む）。
- 依存確認 / 一覧ダイアログ / 保存計画まわりの変更（task_11・task_12 で完了。**触らない**）。
- `apply_loaded_data_to_ui` の整理・共通化（読込 / Import 経路は現状維持）。
- 個別保存ボタンの統合（暫定仕様 §11）/ `dirty_tracker.trigger_set_imported` の廃止
  （読み手不在の残置状態。`/refactor_check` の申し送り事項のまま）。
- keymap / sequence 側の source_path リセット（本タスクは **trigger_set の状態のみ**）。

## 確認

`.venv` の python で実行する（worktree ルートから `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests_ui` が clean
2. `-m unittest discover -s tests` が全 pass（現行 138 件）
3. `-m unittest discover -s tests_ui` が全 pass（現行 131 件 + 追加分）・**完走する**
4. `-m tests.smoke_app` が pass
5. **受入条件 17**: 上記テスト 1〜5 が pass
6. 既存の特性テスト（保存 JSON のバイト列比較）を**緩めずに** pass すること

## 完了条件

- 上記確認 1〜6 が pass・**reviewer 採用**。
- 実機目視（新規作成直後に個別「トリガー一覧を保存」で前の構成が書き換わらないこと）は
  **task_10 の前にユーザーがまとめて実施**する。本タスクでは実施しない。
