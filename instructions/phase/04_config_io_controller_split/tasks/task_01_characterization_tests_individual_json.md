# task_01_characterization_tests_individual_json

## 目的

分割の**安全網**として、個別 JSON IO（D: keymap / E: trigger_set / F: sequence）と
共有ダイアログヘルパ（C）の**現行挙動を固定する特性テスト**を追加する。
根拠は暫定仕様 [03](../../../history/03_config_io_controller_split.md) §7-2 の経路表（C / D / E / F の行）と
§1「安全網の現状」（対象クラスの直接テストが存在しない）。

- **本タスクはテストのみを追加する。production コードを 1 行も変更しない**
  （`keyseq/` 配下は読むだけ）。
- レイヤ制約: 追加先は `tests_ui/` のみ。domain / application / presentation いずれも不変。スキーマ不変。
- **分割前のコード（現在の `config_io_controller.py`）で pass すること**が完了条件。
  分割後（task_03 / task_04）も**テスト本体を書き換えずに** pass する状態を目指す（設計メモ参照）。

## 対象範囲（tests_ui 限定・新規ファイル 1 本）

### `tests_ui/test_config_io_characterization.py`（新規）

`tests_ui/test_startup_font_characterization.py` の構成（`setUpClass` で App を 1 個生成し、
`ConfigService.load_startup` と `os.makedirs` を patch）を踏襲する。

固定する経路は以下。**期待値は現行実装の実挙動**であり、あるべき姿ではない。

#### C: 共有ダイアログヘルパ

| 対象 | 固定する分岐 |
|---|---|
| `choose_save_path_with_collision` | ①衝突なし → suggested_path をそのまま返す ②衝突 + yes → 同じパスを返す（上書き）③衝突 + no → `asksaveasfilename` の戻り値を返す ④衝突 + cancel(None) → `""` を返す |
| `ask_link_label_to_filename` | ①OK + チェック on → `True` ②OK + チェック off → `False` ③キャンセル → `RuntimeError` ④WM_DELETE_WINDOW → `RuntimeError` ⑤**いずれの経路でも `hook.suspend_hook_for_dialog` と `hook.resume_hook_after_dialog` の呼び出し回数が一致する**こと |

#### D: keymap（`save_selected_keymap` / `_as` / `save_keymap_to_path` / `load_keymap_file`）

| 固定する分岐 |
|---|
| 未選択（`selected_keymap_for_io` が `None, None`）→ showinfo「対象のキーマップを選択してください。」・`False` を返す |
| source_path あり + imported + dirty → askyesno「読込で持ってきたキーマップです。\n別名で保存しますか？」→ yes で `save_selected_keymap_as` へ / no でそのまま保存 |
| source_path なし → `choose_save_path_with_collision` を通る（title="キーマップを保存"）|
| `_as` でラベル連動 on → `keymap["label"]` がファイル名 stem に変わる / キャンセル（RuntimeError）→ `False` を返し保存しない |
| `save_keymap_to_path` 成功 → 保存 JSON の**バイト列**・`keymap_panel.refresh_keymap_list_ui(preferred_index=index)`・`layout.refresh_keyboard_window()`・flash「キーマップを保存しました。」・showinfo |
| `save_keymap_to_path` 例外 → flash「キーマップ保存失敗: {e}」(auto_clear=False)・showerror・`False` |
| `load_keymap_file` 成功 / パス空（何もしない）/ 例外 |

#### E: trigger_set（`save_trigger_set_file` / `_as` / `save_trigger_set_to_path` / `load_trigger_set_file`）

D と同じ観点に加えて、**以下の現行挙動を明示的に固定する**（暫定仕様 §1「既存の不整合」）:

| 固定する分岐 |
|---|
| **`:440` の askyesno（「読込で持ってきたトリガー一覧です。」）が到達不能であること**。`dirty_tracker.trigger_set_source_path` に値を入れ imported/dirty を立てても、`save_trigger_set_file` は askyesno を**呼ばず** `choose_save_path_with_collision` へ進む |
| **`_as` が `ask_link_label_to_filename` を呼ばない**こと（D / F との差異）|
| `load_trigger_set_file` の冒頭で `confirm_save_if_dirty` が呼ばれること（D / F との差異）|
| `save_trigger_set_to_path` 成功時に `dirty_tracker` の 3 属性（source_path / imported=False / dirty=False）が更新されること |

> **重要**: これらは既知の不整合だが、本フェーズでは**現状を正**として固定する。
> 修正は [idea_05](../../../backlog/idea_05_trigger_set_source_path_inconsistency.md)（phase 04 完了後）。
> テストコードに「idea_05 で変更予定」のコメントを 1 行入れること。

#### F: sequence（`save_selected_sequence` / `_as` / `save_sequence_to_path` / `load_sequence_file`）

D と同じ観点に加えて:

| 固定する分岐 |
|---|
| 未選択 → showinfo「対象のトリガーを選択してください。」（load 時は「読込先のトリガーを選択してください。」）|
| `save_sequence_to_path` が**引数の `trigger` dict を破壊的に更新**すること（`trigger.update(sequence)`）|
| `dirty_tracker.mark_trigger_set_dirty()` が呼ばれること（D / E との差異）|

### 設計メモ / 制約

**① patch は `tkinter` モジュールの属性に対して行う（最重要）**

`config_io_controller.py` は `from tkinter import filedialog, messagebox, ttk` で束縛している。
`patch.object(config_io_controller, "messagebox", ...)` のように**モジュール変数を差し替えると、
task_03 / task_04 でモジュールが分かれた瞬間にテストが壊れる**（安全網が守るべき対象と同時に壊れる）。

```python
# NG: 分割で壊れる
patch.object(config_io_controller, "messagebox")
# OK: from-import は同じモジュールオブジェクトを束縛するため、どの実装モジュールからでも効く
patch.object(tkinter.messagebox, "showinfo")
patch.object(tkinter.filedialog, "asksaveasfilename")
patch.object(tkinter, "Toplevel")   # ask_link_label_to_filename 用
```

**② 呼び出し口はテスト内のヘルパ 1 箇所に集約する**

task_04（案 B）で呼び出し元が `app.config_io.X()` → `app.<新名>.X()` に変わる。
テスト側の呼び出しを直接書くと task_04 で全面修正になるため、**クラスタごとに 1 つの
アクセサ関数**を用意し、そこだけ直せば済む形にする。

```python
def _keymap_io(app):        # task_04 でここ 1 行だけ変える
    return app.config_io
```

**③ 保存 JSON はバイト列で比較する**

`tmp_path` 相当（`tempfile.TemporaryDirectory`）に実ファイルを書き、`read_bytes()` で比較する。
`json.load` して dict 比較にすると、キー順・インデント・改行コードの変化を検出できない
（暫定仕様 §2「保存 JSON のバイト列」を守れない）。

**④ ダイアログは「文言と呼び出し順」を assert する**

`showinfo` / `showerror` / `askyesno` の fake は呼び出し引数を記録し、**タイトルと本文を完全一致で
assert** する。呼び出し順が意味を持つ経路（保存 → flash → showinfo）は記録リストの順序も見る。

**⑤ やってはいけないこと**

- production コードの変更（テストを通すためのリファクタを含む）
- E の不整合の「修正」（§対象範囲の警告参照）
- D / E / F を共通化したテストヘルパへまとめること（**テスト側でも 3 種を個別に書く**。
  暫定仕様 §5 = 案 1 の趣旨。共通化すると 9 点の差異が見えなくなる）
- 既存 `tests_ui/test_startup_font_characterization.py` の変更

## 含まない

- **A（構成セット）と B（起動設定）の特性テスト** → **task_02**
  （`confirm_save_if_dirty` / `save_keymap_set_to` / `choose_split_base_dir_for_keymap_set` /
  `load_keymap_set_from` / `new_config` / `import_config` / `export_config` / `restore_default` /
  `set_startup_keymap_set` / `write_startup` / `load_startup_and_config`）
- **分割の実施そのもの** → task_03（D/E/F）/ task_04（A/B/C）
- **呼び出し元 30 箇所の差し替え** → task_05
- **E の source_path 不整合の修正** → [idea_05](../../../backlog/idea_05_trigger_set_source_path_inconsistency.md)（本フェーズ範囲外）
- **D/E/F の共通化** → [idea_06](../../../backlog/idea_06_individual_json_io_unification.md)（保留）
- production コードの変更全般（`self._app.` reach-through・ダイアログ文言・`config_service` 等）

## 確認

python は**必ずリポジトリルートの `.venv`** を使う（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

1. **新規テストが分割前のコードで pass すること**（本タスクの主目的）
   ```
   ..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_config_io_characterization -v
   ```
   → 全ケース pass。**skip / expectedFailure を含めないこと**。
2. 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests_ui`
3. 既存テストの退行なし:
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` → **pass 86**（増減なし）
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` → **pass 20 + 新規追加分**
   - `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` → pass
4. `git diff --stat` で **`keyseq/` 配下の変更が 0 件**であること（production 無変更の機械的確認）。
5. テストが `tkinter.messagebox` / `tkinter.filedialog` / `tkinter.Toplevel` を patch しており、
   `config_io_controller` のモジュール変数を patch していないこと（設計メモ①・`grep` で確認）。

## 完了条件

- 上記「確認」1〜5 がすべて pass。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点 + 本タスク固有の観点:
  production 無変更 / E の不整合を固定できているか / 分割後も壊れない patch 方式か)。
- 実機目視: **本タスクでは実施しない**（テスト追加のみで挙動が変わらないため）。
  フェーズの実機目視は task_06（正本反映）の前にまとめて実施する。
