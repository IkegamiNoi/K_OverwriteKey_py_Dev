# task_04_split_keymap_set_and_startup

## 目的

`config_io_controller.py` に残る **A（構成セット）+ A'（split base dir ヘルパ）/ B（起動設定）/ C（共有ダイアログ）**を
`controllers/config_io/` 配下の3モジュールへ分割する。暫定仕様
[03](../../../history/03_config_io_controller_split.md) §3。task_03（D/E/F 分割）に続く分割の第2段。

- **挙動不変が絶対前提**。メソッド本体は**ロジック不変で移設**する。
- レイヤ制約: **presentation 限定**。domain / application（`config_service` 等）不変・スキーマ不変。
- 完了後、ConfigIoController は**全公開メソッドが委譲の薄いファサード**になる（呼び出し元 30 箇所は
  task_05 まで `app.config_io.<method>` を使うため。委譲層は task_05 で削除予定）。
- 安全網: task_01（`test_config_io_characterization.py`・19件）+ task_02
  （`test_config_io_characterization_keymap_set_startup.py`・35件）。

## 対象範囲（presentation 限定・新規3モジュール + ConfigIoController のファサード化）

### 新規 `config_io/keymap_set_io.py` — `class KeymapSetIo`

`__init__(self, app) -> None: self._app = app`。以下の **A + A'** を本体そのまま移設:
`confirm_save_if_dirty` / `new_config` / `save_keymap_set` / `save_as` / `save_keymap_set_to` /
`load_keymap_set_from` / `import_config` / `export_config` / `restore_default` / `set_startup_keymap_set` /
`apply_loaded_data_to_ui` / `choose_split_base_dir_for_keymap_set`（A'）。

- import: `os` / `from tkinter import filedialog, messagebox`。
- **同一モジュール内のメソッド呼び出しは `self.<method>`**（confirm_save_if_dirty / save_keymap_set /
  save_as / save_keymap_set_to / choose_split_base_dir_for_keymap_set / apply_loaded_data_to_ui は全て A/A'）。
- **クロスモジュール呼び出しは `self._app.config_io.<method>` 経由**（移行期の委譲）:
  `set_startup_keymap_set` 内の **`write_startup`（B）→ `self._app.config_io.write_startup(...)`**。

### 新規 `config_io/startup_io.py` — `class StartupIo`

**B** を移設: `load_startup_and_config` / `write_startup`。

- import: `os` / `from tkinter import messagebox` / `from keyseq.presentation.theme import coerce_font_delta`。
- **クロスモジュール**: `load_startup_and_config` 内の **`apply_loaded_data_to_ui`（A）→
  `self._app.config_io.apply_loaded_data_to_ui()`**。
- `write_startup` は同一モジュール内で完結（クロスなし）。**`os.path.exists` は patch しない前提の実装のまま**
  （テストは実ファイルで分岐を作る）。

### 新規 `config_io/io_dialogs.py` — `class IoDialogs`

**C** を移設: `choose_save_path_with_collision` / `ask_link_label_to_filename`。

- import: `os` / `import tkinter as tk` / `from tkinter import filedialog, messagebox, ttk`。
- クロスモジュール呼び出しなし（filedialog / messagebox / tk / ttk / `self._app.hook` のみ）。

### `config_io_controller.py`（ファサード化）

- `__init__` で **6 クラス**を生成・保持する（既存の D/E/F 3 つ + 新 A/B/C 3 つ）:
  ```python
  self._keymap_set_io = KeymapSetIo(app)
  self._startup_io = StartupIo(app)
  self._io_dialogs = IoDialogs(app)
  self._keymap_io = KeymapFileIo(app)         # task_03 で追加済
  self._trigger_set_io = TriggerSetFileIo(app)
  self._sequence_io = SequenceFileIo(app)
  ```
- A/A'/B/C の**メソッド本体を削除し、対応する新クラスへ委譲する薄いメソッドに置き換える**
  （task_03 の D/E/F 委譲と同じ形。移行期の一時ラッパー・削除予定コメントを付す）。
- **D/E/F の委譲メソッド（task_03 で作成）はそのまま**。D/E/F は `self._app.config_io.<C/A helper>` を
  呼ぶが、ConfigIoController がそれらを IoDialogs / KeymapSetIo へ委譲するため**D/E/F は無変更で動く**
  （facade 経由で解決）。
- import: 新3クラスを追加 import。A/B/C 移設で ConfigIoController が直接使わなくなった import
  （`os` / `tk` / `filedialog` / `messagebox` / `coerce_font_delta` / `normalize_key_name` 等）は削除する
  （未使用 import を残さない）。

### 設計メモ / 制約

- **本体はロジック不変で移設**する。条件式・呼び出し順・例外処理・ダイアログ文言・flash メッセージを一切変えない。
- **クロスモジュール呼び出しは 2 箇所のみ**（`set_startup_keymap_set`→`write_startup` /
  `load_startup_and_config`→`apply_loaded_data_to_ui`）。いずれも `self._app.config_io.<method>` 経由にする。
  それ以外はすべて同一モジュール内（`self.`）か App 参照（`self._app.<...>`）。
- **共通化しない**。A/B/C を無理にまとめず、責務ごとに3モジュールへ分ける。
- **E の不整合は task_03 で移設済み。本タスクでは trigger_set_file_io.py を触らない**。
- **reach-through（`self._app.<...>`）は現状維持**（スコープ外）。
- 各新モジュールの目安行数: KeymapSetIo ≈ 220 行 / StartupIo ≈ 50 行 / IoDialogs ≈ 60 行（300 行以内目安）。

## 特性テストの調整（メインが対応・reviewer 通過必須）

task_03 と同じく、**task_02 の特性テストが内部 A/B メソッドを accessor 経由で mock している箇所**は
分割で mock が外れる（`confirm_save_if_dirty` / `save_keymap_set` / `save_as` /
`choose_split_base_dir_for_keymap_set` / `write_startup` / `apply_loaded_data_to_ui` を
`_config_set_io`/`_startup_io` 経由で patch している箇所）。これらは **Option A（境界 mock へ調整）**
（decisions 04・ユーザー確定）に従い、内部メソッド mock → 境界 mock へ書き換える。**assert する挙動は保持**し、
テストを緩めない。この調整はメインセッションが行う（production は codex-implementer）。

## 含まない

- **呼び出し元 30 箇所の差し替え**（`app.config_io` → `app.keymap_set_io` 等）と**委譲層の削除** → task_05。
- **D/E/F の再変更**（無変更で動くはず。壊れたら移設ミス）。
- **E の source_path 不整合の修正** → [idea_05](../../../backlog/idea_05_trigger_set_source_path_inconsistency.md)。
- **正本反映（codebase_map.md）・暫定仕様の凍結** → task_06。
- `self._app.` reach-through の解消 / `config_service`（application）の変更。

## 確認

python は**必ず** `..\..\..\.venv\Scripts\python.exe`（worktree 相対）。各テストは `timeout 150` を付す。

1. `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests_ui`
2. `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_config_io_characterization`（**19件 pass**）
3. `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_config_io_characterization_keymap_set_startup`
   （**35件 pass**・境界 mock 調整後）
4. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` → **pass 86**
5. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` → **pass 74**（増減なし）
6. `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` → pass
7. `git diff` で A/B/C の移設がロジック不変であること / `config_service`（application）に変更がないこと /
   `config_io_controller.py` の A/B/C 本体が委譲メソッドになっていること。
8. `git grep -n "def confirm_save_if_dirty\|def write_startup\|def choose_save_path_with_collision" keyseq`
   で定義が新モジュール側にあること。

## 完了条件

- 上記「確認」1〜8 がすべて pass（特にテスト pass = 挙動不変の担保）。
- **reviewer 採用**（5 観点 + 本タスク固有: 挙動不変〔ロジック移設か〕/ クロスモジュール呼び出しが
  facade 経由か / 共通化していないか / 委譲層に削除予定コメントがあるか / テスト調整が assert を緩めていないか）。
- 統合退行のため **codex-reviewer 併用**（`.claude/rules/agent_selection.md`）。
- 実機目視: 本タスクでは実施しない（フェーズ末 task_06 の前にまとめて実施）。
