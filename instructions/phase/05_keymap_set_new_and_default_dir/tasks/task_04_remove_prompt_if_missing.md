# task_04_remove_prompt_if_missing

## 目的

死にフラグ `prompt_if_missing`（保存・正規化されるが**どこからも参照されない**）の
読み・正規化・書き込みをコードから撤去し、**新規に作成される `config/config.json` に
当該キーが出力されない**状態にする。

- 根拠: 暫定仕様 [04](../../../history/04_keymap_set_new_and_default_dir.md) §6 / **受入条件 5・6**。
- **既存 config.json に残る値は能動削除しない**（`pop` しない）。未知キー保持契約により
  既存値は次回保存でも再出力されうるが、実害のない死にキーとして**残置を許容**する（暫定仕様 §6・指摘③）。
- **レイヤ制約**: presentation（`startup_settings.py` / `controllers/config_io/startup_io.py` /
  `controllers/config_io/keymap_set_io.py`）+ application（`config_service.py` の **startup 正規化 1 行のみ**）。
  domain / infrastructure 不変。**スキーマは後方互換**（他キーに触れない・既存キー削除禁止）。
- **挙動変更タスク**。新挙動は特性テストで固定する（暫定仕様 §8）。

## 対象範囲（4 箇所の撤去 + テスト）

### 1. `keyseq/application/config_service.py`

`_build_startup_payload`（`:545`）の
```python
payload["prompt_if_missing"] = bool(payload.get("prompt_if_missing", True))
```
を**削除**する。前後の行（`ui_font_delta_pt` / `last_used_directory` / `legacy_path` 分岐）は変更しない。
冒頭の `payload.update(safe_deepcopy(startup_data))` は変更しない（＝既存値が入っていれば**そのまま残る**。
これが残置許容の実体であり、`pop` を足してはいけない）。

### 2. `keyseq/presentation/startup_settings.py`

`load_startup_settings`（`:17`）の
```python
startup["prompt_if_missing"] = bool(startup.get("prompt_if_missing", True))
```
を**削除**する。あわせて docstring（`:5`）の「型ガードと正規化（font_delta / prompt_if_missing）」を
`font_delta` のみの記述へ直す。`ui_font_delta_pt` の正規化・未知キー全保持・`on_read_error` 経路は不変。

### 3. `keyseq/presentation/controllers/config_io/startup_io.py`

`write_startup`（`:38-42`）の base 既定から `"prompt_if_missing": True,` の行を**削除**する。
残る既定は `ui_font_delta_pt` / `last_used_directory`。`current` / `data` のマージ順・
`config_path` の `pop`・`coerce_font_delta`・保存失敗時の showerror は**変更しない**。

### 4. `keyseq/presentation/controllers/config_io/keymap_set_io.py`

`set_startup_keymap_set`（`:211`）の `write_startup` 引数辞書から `"prompt_if_missing": True` を**削除**し、
`{"keymap_set_path": self._app.paths.to_config_relative_or_absolute(path)}` のみにする。
同メソッドの他の処理（確認・ダイアログ・読込例外時の早期 return・flash・showinfo）は**変更しない**。

### 既存テストの更新

1. **`tests/test_startup_settings.py`**（4 箇所）
   - `:31` / `:46` / `:61`: 期待値 `{"ui_font_delta_pt": 0, "prompt_if_missing": True}` →
     **`{"ui_font_delta_pt": 0}`**（既定注入が止まることの固定）。
   - `:65-94` `test_normal_dict_preserves_unknown_keys_and_normalizes_values`: 入力の
     `"prompt_if_missing": 0` は**未知キーとしてそのまま保持**されるため、期待値を
     `"prompt_if_missing": False`（bool 正規化後）→ **`"prompt_if_missing": 0`（入力のまま）** へ更新する。
     他キーの期待値・`assertIs(result, startup)` は変更しない。
2. **`tests_ui/test_config_io_characterization_keymap_set_startup.py`**
   - `:503-519` `test_write_startup_merges_defaults_current_and_arg`: 期待 base から
     `"prompt_if_missing": True,` を**除去**する（残り 3 キー）。他の検証は変更しない。
3. **`tests_ui/test_startup_font_characterization.py`（`:56-78`）は変更しない**。
   `_startup_settings` 側に `prompt_if_missing: True` が入っている入力なので、
   撤去後も `base.update(current)` で保存 dict に残る＝**期待値は現行のまま pass する**。
   これが**残置許容（受入 6）の回帰テスト**になるため、期待値から消してはならない。

### 新規テスト（新挙動の固定）

1. **`tests/test_config_service.py`**（`SaveLoadRoundTripTest` と同ファイル・既存の
   `save_runtime_data(..., startup_data=...)` の呼び方を流用。`tempfile.TemporaryDirectory` 使用）
   - **受入 5**: `startup_data={}` で `save_runtime_data` した戻り値 `startup` に
     `"prompt_if_missing"` が**含まれない**（`assertNotIn`）。
   - **受入 6**: `startup_data={"prompt_if_missing": True}` で保存すると、戻り値 `startup` に
     `prompt_if_missing == True` が**そのまま残る**（能動削除していないこと）。同時に
     `startup["keymap_set_path"]` が従来どおり設定されること（他キー不変）も確認する。
2. **`tests_ui/test_config_io_characterization_keymap_set_startup.py`**（`# ===== B: write_startup =====` 節）
   - `_startup_settings = {}` の状態で `write_startup({"ui_font_delta_pt": 0})` を呼び、
     保存された base のキー集合に `"prompt_if_missing"` が**含まれない**こと（既定からの消滅）。
   - `set_startup_keymap_set` の成功経路で `startup_io.write_startup` を patch し、
     **渡された引数 dict が `keymap_set_path` のみ**で `prompt_if_missing` を含まないこと
     （`:471-500` の既存成功系テストの patch 構成を流用。`_silence_refresh` 等の既存ヘルパを使う）。

## 含まない

- **既存 config.json からの `prompt_if_missing` の能動削除**（`pop` の追加。残置許容が確定事項）。
- `keymap_set_path` / `ui_font_delta_pt` / `last_used_directory` / `config_path` など**他キーの挙動変更**。
- `load_startup_and_config` の空起動 path（**task_03 で完了済**・再変更しない）。
- `new_config` / `save_keymap_set` / `save_as` / `import_config`（**task_01〜03 で完了済**）。
- `config_paths.py`（`preferred_keymap_set_path` 等）の整理。
- 統合退行の通し確認・非変更経路の回帰確認・実機目視（**task_05**）。
- 正本 `data_schema.md` / `codebase_map.md` への反映（**task_06**）。
- `config_service.save_runtime_data` の子ファイル書き出しロジック（**フェーズ外** = Phase β）。

## 確認

python は**リポジトリルートの `.venv`** を使う（worktree 相対 `..\..\..\.venv\Scripts\python.exe`。
グローバル `py` は使わない）。※テストの実行は verifier が行うため、実装側は実行しなくてよい。

1. `-m compileall -q keyseq main.py tests_ui` — clean
2. `-m unittest discover -s tests` — 全 pass（既存 87 件 + 新規 2 件 = **89 件。減らないこと**）
3. `-m unittest discover -s tests_ui` — 全 pass（既存 82 件 + 新規 2 件 = **84 件。減らないこと**）
4. `-m tests.smoke_app` — pass
5. `grep -rn "prompt_if_missing" keyseq/` — **0 件**（`keyseq/` 配下から完全消滅。
   `tests_ui/test_startup_font_characterization.py` 等テスト側の残置は正しいので削らない）
6. `tests_ui/test_startup_font_characterization.py:56` の
   `test_load_startup_settings_preserves_unknown_keys_through_save` が**無修正で pass**すること
   （＝残置許容・受入 6 の担保）

## 完了条件

- 上記確認 1〜6 がすべて pass・**reviewer 採用**。
- 実機目視は本タスクでは行わず、**task_05（統合退行）でまとめて**ユーザーに依頼する
  （「既存 `prompt_if_missing` 付き config.json での起動・保存」を目視項目に含める）。
