# task_03_import_and_empty_start_path

## 目的

`keymap_set_path` が固定 `default.json` を差したまま残る経路を塞ぐ。対象は 2 つ。

- **Import**: 保存済みセットを開いた状態で Import すると `keymap_set_path` が**元セットのまま残り**、
  次の保存で元セットを上書きしうる（敵対的レビュー指摘①）。→ 成功時は**無条件で空**にする。
- **空起動**: stored keymap_set が見つからない/読めないとき、無言で空データ起動するが
  `keymap_set_path` は `default.json` を差したまま残る。→ **空**にする。

- 根拠: 暫定仕様 [04](../../../history/04_keymap_set_new_and_default_dir.md) §5 / **受入条件 3・4**。
- **レイヤ制約**: presentation のみ（`controllers/config_io/keymap_set_io.py` /
  `controllers/config_io/startup_io.py`）。application / domain / infrastructure 不変・**スキーマ不変**。
- **挙動変更タスク**。新挙動は特性テストで固定する（暫定仕様 §8）。

## 対象範囲（presentation 限定 + テスト）

### `keyseq/presentation/controllers/config_io/keymap_set_io.py`

**`import_config`（:134-158）**: 成功経路（`load_legacy_runtime_data` 直後・`:147-148`）の
```python
if not self._app.keymap_set_path:
    self._app.keymap_set_path = self._app.paths.preferred_keymap_set_path()
```
を **`self._app.keymap_set_path = ""`**（無条件）に置き換える。位置は現行の分岐と同じ
（`apply_loaded_data_to_ui()` の前）。**例外経路（`except`）は変更しない**（失敗時はパスを触らない）。
`confirm_save_if_dirty` / ダイアログ / `set_dirty(True)` / フラッシュ・showinfo 文言は**変更しない**。

### `keyseq/presentation/controllers/config_io/startup_io.py`

**`load_startup_and_config`（:11-35）**: `:18` の
`self._app.keymap_set_path = self._app.paths.preferred_keymap_set_path()` を
**`self._app.keymap_set_path = ""`** にする。

- stored path が実在し読み込みに成功した場合は `:28` で `resolved_keymap_set_path` を代入する
  （**現状維持**）。
- stored path が空 / 不在 / 読込例外の場合は `""` のまま `new_empty_data()` 起動へ進む（受入 4）。
- `except Exception: pass` の握りつぶし・`apply_loaded_data_to_ui()` の呼び出し・
  `write_startup` は**変更しない**（`write_startup` の base は task_04）。

### 既存テストの更新（`tests_ui/test_config_io_characterization_keymap_set_startup.py`）

1. **`test_load_startup_and_config_empty_when_stored_path_missing`（:532-543）**: 旧挙動
   （`keymap_set_path == "default.json"`）を固定している → **`""` を期待**へ更新する。
   他の検証（`data == {"empty": True}` / `apply_loaded_data_to_ui` 1 回）は変更しない。
2. **`test_import_config_success`（:349-364）**: `preferred_keymap_set_path` の patch が不要になる
   → patch を外し、**`keymap_set_path == ""` の検証を追加**する。他の検証
   （`data` / `set_dirty(True)` / `showinfo`）は変更しない。
3. `test_load_startup_and_config_loads_when_stored_path_exists`（:512-530）と
   `..._swallows_load_exception_and_falls_back`（:545-561）は**変更しない**
   （`preferred_keymap_set_path` の patch は呼ばれなくなるだけで無害）。

### 新規テスト（新挙動の固定・同ファイル）

1. **Import の無条件クリア**: 開始時 `keymap_set_path` が**非空**（例: `"current.json"`）でも、
   Import 成功後は `""` になる（＝次の保存が別名保存になる。指摘①の核心）。
2. **Import 失敗時は据え置き**: `load_legacy_runtime_data` が例外を投げた場合、
   `keymap_set_path` が**開始時の値のまま**であること（回帰）。

## 含まない

- **`config_paths.py` の変更**（`preferred_keymap_set_path` / `normalize_keymap_set_save_path` /
  suggest 系）。§5 のとおり「保存ターゲットとして到達しない」ことの**監査のみ**行い、関数は据え置く。
  `tests/test_config_paths.py` も変更しない。
- **`app.py`（`:64` の `keymap_set_path = resolve_keymap_set_path()` 初期化）**。`:172` の
  `load_startup_and_config()` が必ず上書きするため本タスクでは触らない。
  **もし上書きされない経路を発見したら実装を止めて報告すること**（仕様判断が必要なため）。
- `prompt_if_missing` の撤去 / `write_startup` の base 既定（**task_04**）
- `save_keymap_set` / `save_as` / `new_config`（**task_02 で完了済**・再変更しない）
- `config_service` の分割保存ロジック（**フェーズ外** = Phase β）
- 「見つからなければ選択ダイアログ」等の起動 UX（暫定仕様 §9 スコープ外）

## 確認

python は**リポジトリルートの `.venv`** を使う（worktree 相対 `..\..\..\.venv\Scripts\python.exe`。
グローバル `py` は使わない）。※テストの実行は verifier が行うため、実装側は実行しなくてよい。

1. `-m compileall -q keyseq main.py tests_ui` — clean
2. `-m unittest discover -s tests` — 全 pass（**87 件から減らないこと**）
3. `-m unittest discover -s tests_ui` — 全 pass（既存 80 件 + 新規 2 件。**減らないこと**）
4. `-m tests.smoke_app` — pass
5. `grep -n "preferred_keymap_set_path" keyseq/presentation/controllers/config_io/*.py` — **0 件**
   （`keymap_set_io.py` / `startup_io.py` の双方から消えていること）
6. **保存ターゲット監査（コード確認・変更不要）**: `save_keymap_set_to` の呼び出し元が
   `save_keymap_set`（空パスは task_02 で `save_as` へ分岐）と `save_as`（空文字なら `return False`）
   のみであり、**空パスが `normalize_keymap_set_save_path` へ到達しない**ことを確認して報告する。

## 完了条件

- 上記確認 1〜6 がすべて pass・**reviewer 採用**。
- 実機目視は本タスクでは行わず、**task_05（統合退行）でまとめて**ユーザーに依頼する。
