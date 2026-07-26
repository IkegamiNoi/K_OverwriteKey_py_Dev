# task_05_replace_call_sites

## 目的

暫定仕様 [03](../../../history/03_config_io_controller_split.md) **§4=案B** に従い、ConfigIoController の
**委譲ファサードを削除**し、呼び出し元を分割後の 6 オブジェクトへ直接差し替える。分割の最終段。

- **挙動不変が絶対前提**。参照の付け替えのみで、ロジック・呼び出し順・文言を変えない。
- レイヤ制約: **presentation 限定**。domain / application 不変・スキーマ不変。
- 完了条件: `grep -rn "config_io\." keyseq main.py tests tests_ui` の**残存 0 件**（`config_io` という名が消える）。

## メソッド → 所有オブジェクトの対応表（差し替えの正）

| 所有オブジェクト（App 上の新属性） | クラス | 公開メソッド |
|---|---|---|
| `app.keymap_set_io` | KeymapSetIo | confirm_save_if_dirty / new_config / save_keymap_set / save_as / save_keymap_set_to / load_keymap_set_from / import_config / export_config / restore_default / set_startup_keymap_set / apply_loaded_data_to_ui / choose_split_base_dir_for_keymap_set |
| `app.startup_io` | StartupIo | load_startup_and_config / write_startup |
| `app.io_dialogs` | IoDialogs | choose_save_path_with_collision / ask_link_label_to_filename |
| `app.keymap_io` | KeymapFileIo | selected_keymap_for_io / save_selected_keymap / save_selected_keymap_as / save_keymap_to_path / load_keymap_file |
| `app.trigger_set_io` | TriggerSetFileIo | save_trigger_set_file / save_trigger_set_file_as / save_trigger_set_to_path / load_trigger_set_file |
| `app.sequence_io` | SequenceFileIo | save_selected_sequence / save_selected_sequence_as / save_sequence_to_path / load_sequence_file |

`app.config_io.<method>` / `self._app.config_io.<method>` を、上表で `<method>` を所有するオブジェクトへ
差し替える（例: `app.config_io.save_keymap_set()` → `app.keymap_set_io.save_keymap_set()`）。

## 対象範囲（production = Codex 担当）

### `keyseq/presentation/app.py`

- **`from ...config_io_controller import ConfigIoController` を削除**し、6 クラスを import する
  （`from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo` 等）。
- **`:135 self.config_io = ConfigIoController(self)` を削除**し、代わりに 6 オブジェクトを生成する:
  ```python
  self.keymap_set_io = KeymapSetIo(self)
  self.startup_io = StartupIo(self)
  self.io_dialogs = IoDialogs(self)
  self.keymap_io = KeymapFileIo(self)
  self.trigger_set_io = TriggerSetFileIo(self)
  self.sequence_io = SequenceFileIo(self)
  ```
  **生成位置は現 `:135` と同じ**（`load_startup_and_config` を呼ぶ `:160` より前であること。
  分割オブジェクトは互いを実行時に `self._app.<owner>` で参照するため、6 つとも `:160` 前に存在すればよい）。
- 内部 7 箇所を差し替え: `:160` load_startup_and_config → `self.startup_io` / `:243` write_startup → `self.startup_io` /
  `:270` save_keymap_set → `self.keymap_set_io` / `:276` new_config → `self.keymap_set_io` /
  `:282` save_as → `self.keymap_set_io` / `:288` load_keymap_set_from → `self.keymap_set_io` /
  `:430` confirm_save_if_dirty → `self.keymap_set_io`。

### `keyseq/presentation/controllers/config_io_controller.py` を**削除**

ファサードは不要になる（案B）。ファイルごと削除する。

### 分割モジュール内部のクロスモジュール呼び出し（9 箇所）— `self._app.config_io` → `self._app.<owner>`

- `config_io/keymap_file_io.py:30` choose_save_path_with_collision → `self._app.io_dialogs`
- `config_io/keymap_file_io.py:56` ask_link_label_to_filename → `self._app.io_dialogs`
- `config_io/keymap_set_io.py:202` write_startup → `self._app.startup_io`
- `config_io/sequence_file_io.py:21` choose_save_path_with_collision → `self._app.io_dialogs`
- `config_io/sequence_file_io.py:48` ask_link_label_to_filename → `self._app.io_dialogs`
- `config_io/startup_io.py:29` apply_loaded_data_to_ui → `self._app.keymap_set_io`
- `config_io/startup_io.py:35` apply_loaded_data_to_ui → `self._app.keymap_set_io`
- `config_io/trigger_set_file_io.py:16` choose_save_path_with_collision → `self._app.io_dialogs`
- `config_io/trigger_set_file_io.py:58` confirm_save_if_dirty → `self._app.keymap_set_io`

### 外部呼び出し元（非テスト・上表どおり差し替え）

- `controllers/layout_controller.py:138` save_keymap_set → `self._app.keymap_set_io`
- `views/full_view/file_frame.py:15-19` save_keymap_set / save_as / load_keymap_set_from / new_config → `app.keymap_set_io`
- `views/full_view/keymap_box.py:38-40` save_selected_keymap / _as / load_keymap_file → `app.keymap_io`
- `views/full_view/sequence_box.py:34-36` save_selected_sequence / _as / load_sequence_file → `app.sequence_io`
- `views/full_view/trigger_box.py:35-37` save_trigger_set_file / _as / load_trigger_set_file → `app.trigger_set_io`
- `views/menu_bar.py:8-18` new_config / save_keymap_set / save_as / load_keymap_set_from / import_config /
  export_config / set_startup_keymap_set / restore_default → `app.keymap_set_io`

### 設計メモ / 制約

- **参照の付け替えのみ**。ロジック・引数・呼び出し順・ダイアログ文言を一切変えない。
- **`config_io` という名を残さない**（互換エイリアス禁止・案B）。
- 分割オブジェクトの生成順序は問わない（相互参照は実行時 `self._app.<owner>`）が、**6 つとも
  `load_startup_and_config` 呼び出し前に生成**すること。
- `codebase_map.md` 等の正本ドキュメント更新は **task_06**（本タスクでは触らない）。

## 含まない

- **テスト 3 ファイルのアクセサ / patch 調整** → **メインセッションが担当**（下記）。Codex は触らないこと。
- 正本反映（codebase_map.md 更新・暫定仕様凍結・/refactor_check）→ task_06。
- E の source_path 不整合の修正 → idea_05。D/E/F・A/B/C の**ロジック**変更（付け替えのみ）。

## テスト調整（メインが対応・reviewer 通過必須）

Codex の production 差し替え後、メインが以下のテスト参照を新 app 属性へ最終調整する:

- `tests_ui/test_config_io_characterization.py`（task_01）: アクセサを
  `_dialog_io`→`app.io_dialogs` / `_keymap_io`→`app.keymap_io` / `_trigger_set_io`→`app.trigger_set_io` /
  `_sequence_io`→`app.sequence_io` へ。
- `tests_ui/test_config_io_characterization_keymap_set_startup.py`（task_02）: `_config_set_io`→`app.keymap_set_io` /
  `_startup_io`→`app.startup_io` へ。**facade patch（`self.app.config_io.write_startup` /
  `self.app.config_io.apply_loaded_data_to_ui`）は所有オブジェクトへ**（write_startup→`app.startup_io` /
  apply→`app.keymap_set_io`。差し替え後は分割モジュールが `self._app.startup_io` 等を呼ぶため）。
- `tests_ui/test_startup_font_characterization.py:62`: `self.app.config_io.write_startup` → `self.app.startup_io.write_startup`。

**assert する挙動は保持**（アクセサの向き先を変えるだけ）。

## 確認

python は**必ず** `..\..\..\.venv\Scripts\python.exe`。各テストに `timeout 150`。

1. `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests_ui`
2. `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_config_io_characterization`（19件 pass）
3. `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_config_io_characterization_keymap_set_startup`（35件 pass）
4. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`（86）
5. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui`（74）
6. `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app`（pass）
7. **`grep -rn "config_io\." keyseq main.py tests tests_ui` の残存 0 件**（`config_io` 名の消滅）。
   `config_io_controller.py` が削除されていること。
8. `git diff` で参照の付け替えのみ（ロジック不変）であること。application/domain 無変更。

## 完了条件

- 上記「確認」1〜8 がすべて pass（特に 7 の残存 0 件 = 案B の完了・テスト全緑 = 挙動不変）。
- **reviewer 採用** + **codex-reviewer 併用**（統合退行・phase.md が Codex 統合レビューを本命とする箇所）。
- 実機目視: 本タスクでは実施しない。**task_06 正本反映の前にユーザー必須ゲートとして実施**する。
