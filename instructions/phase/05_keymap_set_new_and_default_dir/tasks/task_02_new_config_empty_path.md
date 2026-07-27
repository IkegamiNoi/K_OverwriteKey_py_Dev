# task_02_new_config_empty_path

## 目的

新規作成を「ファイルなし」にし、保存の空パスを別名保存へ分岐させる（点1 の無言上書きの解消）。
現状の `new_config` は末尾で `keymap_set_path` に `preferred_keymap_set_path()`（固定
`config/user/keymap_sets/default.json`）を設定するため、「保存」を押すと別名保存を経ずに
`default.json` へ書き込まれる。

- 根拠: 暫定仕様 [04](../../../history/04_keymap_set_new_and_default_dir.md) §3 / §4 / §7-1 /
  **受入条件 1**。
- **レイヤ制約**: presentation のみ（`controllers/config_io/keymap_set_io.py`）。
  application / domain / infrastructure 不変・**スキーマ不変**・`config_paths.py` は触らない（task_03）。
- **挙動変更タスク**。新挙動は特性テストで固定する（暫定仕様 §8）。

## 対象範囲（presentation 限定 + テスト）

### `keyseq/presentation/controllers/config_io/keymap_set_io.py`

1. **`new_config`（:26-42）**: `:33` の
   `self._app.keymap_set_path = self._app.paths.preferred_keymap_set_path()` を
   **`self._app.keymap_set_path = ""`** にする。**他の行（`new_default_data` → `triggers=[]` →
   `normalize_runtime_data` → UI 同期 → インデックス初期化 → `set_dirty(True)` →
   フラッシュ「新規作成しました（未保存）。」）は変更しない**。

2. **`save_keymap_set`（:44-49）**: 先頭で空パスなら `save_as` へ委譲する。
   ```python
   def save_keymap_set(self, *, show_success_dialog: bool = True) -> bool:
       if not self._app.keymap_set_path:
           return self.save_as(show_success_dialog=show_success_dialog)
       return self.save_keymap_set_to(
           self._app.keymap_set_path,
           flash_message="保存しました。",
           show_success_dialog=show_success_dialog,
       )
   ```

3. **`save_as`（:51-66）**: `initialfile` が固定 `default.json` にならないようにする。
   - `keymap_set_path` が**空**のとき → **`keymap_set.json`**（一般名・§7-1 でユーザー確定）
   - `keymap_set_path` が**非空**のとき → **従来どおり**現在パスの basename
     （`suggest_keymap_set_dialog_path()` 由来。変更しない）
   - 既定ファイル名はモジュール定数（例: `DEFAULT_KEYMAP_SET_FILENAME = "keymap_set.json"`）として置く。
   - `title` / `initialdir` / `defaultextension` / `filetypes` は**変更しない**。

4. **`confirm_save_if_dirty`（:9-24）と `save_keymap_set_to`（:68-92）は変更しない**。
   `confirm_save_if_dirty` は既に `keymap_set_path` の有無で分岐しており、空なら `save_as` を
   直接呼ぶため、2 の変更と二重に save_as へ回ることはない。

### 既存テストの更新

- `tests_ui/test_config_io_characterization_keymap_set_startup.py` の
  **`test_new_config_success`（:283-297）は旧挙動を固定している**
  （`preferred_keymap_set_path` を `"k.json"` に patch し、`keymap_set_path == "k.json"` を期待）。
  → **新挙動**（`keymap_set_path == ""`・`preferred_keymap_set_path` の patch は不要）へ更新する。
  同テスト内の他の検証（`triggers == []` / `set_dirty(True)` / フラッシュ文言）は**変更しない**。

### 新規テスト（新挙動の固定・`tests_ui/`）

既存の characterization テストの手法（`patch.object` によるダイアログ・保存の差し替え）を踏襲する。

1. `save_keymap_set`: `keymap_set_path` が空 → **`save_as` が 1 回呼ばれ、`save_keymap_set_to` は
   呼ばれない**（`show_success_dialog` が引き継がれることも確認）。
2. `save_keymap_set`: `keymap_set_path` が非空 → **従来どおり `save_keymap_set_to` が
   そのパスで呼ばれる**（回帰確認・`save_as` は呼ばれない）。
3. `save_as`: `keymap_set_path` が空 → `asksaveasfilename` に渡る
   **`initialfile == "keymap_set.json"`**。
4. `save_as`: `keymap_set_path` が非空 → `initialfile` が**現在ファイルの basename**（従来どおり）。

※ `new_config` の空パス化は上記「既存テストの更新」で固定されるため、重複するテストは追加しない。

## 含まない

- `import_config` の無条件クリア / 空起動時の `keymap_set_path` 空化 /
  `config_paths.py` の `default.json` 用途整理（**task_03**）
- `prompt_if_missing` の撤去（**task_04**）
- `save_keymap_set_to` の正規化・分割保存・ダイアログのロジック（**変更しない**）
- `confirm_save_if_dirty` の分岐変更（**変更しない**）
- `config_service.save_runtime_data` の子ファイル書き出し（**フェーズ外** = Phase β）
- 「保存」ボタンの表示名変更（暫定仕様 §2 で「保存」のまま据え置きと確定済）

## 確認

python は**作業ツリー直下の `.venv`** を使う（`.\.venv\Scripts\python.exe`。グローバル `py` は使わない）。

1. `-m compileall -q keyseq main.py tests_ui` — clean
2. `-m unittest discover -s tests` — 全 pass（**87 件から減らないこと**）
3. `-m unittest discover -s tests_ui` — 全 pass（既存 76 件 + 新規 4 件相当。**減らないこと**）
4. `-m tests.smoke_app` — pass
5. `grep -n "preferred_keymap_set_path" keyseq/presentation/controllers/config_io/keymap_set_io.py` —
   **`new_config` 内に残っていないこと**（`import_config` 内の参照は task_03 で扱うため残ってよい）

## 完了条件

- 上記確認 1〜5 がすべて pass・**reviewer 採用**。
- 実機目視は本タスクでは行わず、**task_05（統合退行）でまとめて**ユーザーに依頼する。
