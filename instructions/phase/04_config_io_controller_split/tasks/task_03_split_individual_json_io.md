# task_03_split_individual_json_io

## 目的

`config_io_controller.py` の **D（keymap）/ E（trigger_set）/ F（sequence）** の個別 JSON IO を、
`controllers/config_io/` パッケージ配下の 3 モジュールへ分割する。暫定仕様
[03](../../../history/03_config_io_controller_split.md) §3（親フォルダ方式）・§5=**案1（共通化しない）**。

- **挙動不変が絶対前提**。メソッド本体は**ロジックを変えずそのまま移設**する。
- レイヤ制約: **presentation 限定**。domain / application（`config_service` 等）不変・スキーマ不変。
- 安全網: task_01 の `tests_ui/test_config_io_characterization.py`（D/E/F を覆う）が
  **本体を書き換えずに pass** し続けること。task_02 の A/B テストも pass のまま。

## 対象範囲（presentation 限定・新規3モジュール + config_io_controller.py の委譲化）

### 新規パッケージ `keyseq/presentation/controllers/config_io/`

`__init__.py` を作成する（公開面の定義。空でも可だが、下記3クラスを re-export してよい）。

### 新規 `config_io/keymap_file_io.py` — `class KeymapFileIo`

`__init__(self, app) -> None: self._app = app`。以下のメソッドを
`config_io_controller.py` の D（現 `:344-437`）から**本体そのまま**移設する:
`selected_keymap_for_io` / `save_selected_keymap` / `save_selected_keymap_as` /
`save_keymap_to_path` / `load_keymap_file`。

- import: `os` / `from tkinter import filedialog, messagebox` / `from keyseq.domain.config import normalize_key_name`。
- **C/A ヘルパへの依存は `self._app.config_io` 経由で呼ぶ**（移行期の委譲。task_04 まで
  ConfigIoController に残るため）: `self._app.config_io.choose_save_path_with_collision(...)`（現 `:363`）/
  `self._app.config_io.ask_link_label_to_filename(...)`（現 `:389`）。
  それ以外の `self._app.<...>` 参照は現状のまま（reach-through は本フェーズ対象外）。

### 新規 `config_io/trigger_set_file_io.py` — `class TriggerSetFileIo`

E（現 `:438-515`）から移設: `save_trigger_set_file` / `save_trigger_set_file_as` /
`save_trigger_set_to_path` / `load_trigger_set_file`。

- import: `os` / `from tkinter import filedialog, messagebox`。
- C/A ヘルパ依存を `self._app.config_io` 経由に: `choose_save_path_with_collision`（現 `:445`）/
  `confirm_save_if_dirty`（`load_trigger_set_file` 冒頭・現 `:487`）。
- **【厳守】E の既存不整合をそのまま移設する**（暫定仕様 §1「既存の不整合」）:
  `save_trigger_set_file` の source_path 読みは `getattr(self._app, "_trigger_set_source_path", "")`
  （未定義・常に ""）のまま。`:440` の到達不能な askyesno も**そのまま残す**。
  `save_trigger_set_file_as` は `ask_link_label_to_filename` を**呼ばない**まま（D/F との差異を維持）。
  **「明らかなバグだから」と直さないこと**（修正は idea_05・phase 04 完了後）。

### 新規 `config_io/sequence_file_io.py` — `class SequenceFileIo`

F（現 `:516-598`）から移設: `save_selected_sequence` / `save_selected_sequence_as` /
`save_sequence_to_path` / `load_sequence_file`。

- import: `from tkinter import filedialog, messagebox`。
- C ヘルパ依存を `self._app.config_io` 経由に: `choose_save_path_with_collision`（現 `:528`）/
  `ask_link_label_to_filename`（現 `:555`）。

### `config_io_controller.py`（委譲化）

- `__init__` で 3 クラスを生成して保持する:
  ```python
  self._keymap_io = KeymapFileIo(app)
  self._trigger_set_io = TriggerSetFileIo(app)
  self._sequence_io = SequenceFileIo(app)
  ```
- D/E/F の**メソッド本体を削除し、対応する新クラスへ委譲する薄いメソッドに置き換える**
  （呼び出し元 30 箇所は task_05 まで `app.config_io.<method>` を使うため、公開面は維持する）:
  ```python
  def save_selected_keymap(self) -> bool:
      return self._keymap_io.save_selected_keymap()
  # 以下 D/E/F の全公開メソッドを同様に委譲
  ```
  この委譲層は**移行期の一時ラッパー**（task_05 で呼び出し元を差し替えたら削除予定。
  `file_organization_rules.md`「一時的なラッパーは移行期間のみ可」）。削除予定である旨のコメントを付す。
- **C ヘルパ（`choose_save_path_with_collision` / `ask_link_label_to_filename`）と A メソッドは
  ConfigIoController に残す**（task_04 で移動）。
- import: 新3クラスを import する。D/E/F 専用だった import（`normalize_key_name` 等）が
  ConfigIoController で未使用になれば削除してよい（未使用 import を残さない）。

### 設計メモ / 制約

- **本体はロジック不変で移設する**。条件式・呼び出し順・例外処理・ダイアログ文言・flash メッセージを一切変えない。
- **共通化しない**（§5=案1）。D/E/F を共通基底や共有ヘルパへまとめないこと。3 モジュールに素直に分ける。
- `config_io/` 配下にオニオン層名（domain 等）を使わない。ファイル名は内容を表す（file_organization_rules）。
- 各新モジュールは 300 行以内目安に収まる見込み（最大 F ≈ 94 行）。
- **reach-through（`self._app.<...>`）は現状維持**。本タスクで App private 参照を整理しない（スコープ外）。

## 含まない

- **A（構成セット）/ B（起動設定）/ C（共有ダイアログ）の分割** → task_04。C・A は本タスクでは
  ConfigIoController に残し、D/E/F から `self._app.config_io` 経由で呼ぶ。
- **呼び出し元 30 箇所の差し替え**（`app.config_io` → `app.keymap_io` 等）→ task_05。
  本タスクでは公開面（`app.config_io.<method>`）を委譲で維持する。
- **E の source_path 不整合の修正** → [idea_05](../../../backlog/idea_05_trigger_set_source_path_inconsistency.md)。
- **D/E/F の共通化** → [idea_06](../../../backlog/idea_06_individual_json_io_unification.md)（保留）。
- 特性テストの変更（**本体を書き換えず pass** させる。アクセサ `_keymap_io` 等はまだ `app.config_io` を返す）。

## 確認

python は**必ず** `..\..\..\.venv\Scripts\python.exe`（worktree 相対）を使う。

1. `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests_ui`（構文・import 解決）
2. **特性テストが本体無変更で pass**:
   - `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_config_io_characterization`（D/E/F・**19件 pass**）
   - `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_config_io_characterization_keymap_set_startup`（A/B・**35件 pass**）
3. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` → **pass 86**
4. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` → **pass 74**（増減なし）
5. `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` → pass
6. `git diff` で **D/E/F の移設がロジック不変**であること（本体の差分が「移動」であって書き換えでないこと）。
   `config_service`（application）に変更がないこと。
7. `config_io_controller.py` に D/E/F のメソッド本体が残っておらず、委譲メソッドになっていること。
   `git grep -n "def save_selected_keymap" keyseq` で定義が新モジュール側にあること。

## 完了条件

- 上記「確認」1〜7 がすべて pass（特にテスト無変更 pass = 挙動不変の担保）。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点 + 本タスク固有: 挙動不変〔ロジック移設か〕/
  E の不整合を直していないか / 共通化していないか / 委譲層に削除予定コメントがあるか）。
  統合退行のため **codex-reviewer 併用**（`.claude/rules/agent_selection.md`）。
- 実機目視: 本タスクでは実施しない（フェーズ末 task_06 の前にまとめて実施）。
