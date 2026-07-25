# task_02_characterization_tests_keymap_set_startup

## 目的

分割の**安全網②**として、A（構成セット = keymap_set）と B（起動設定 = startup.json）の
**現行挙動を固定する特性テスト**を追加する。task_01（C+D/E/F）と対になり、
後続 task_04（A+A'/B/C の分割）を守る。根拠は暫定仕様
[03](../../../history/03_config_io_controller_split.md) §7-2 表の A・B 行。

- **本タスクはテストのみを追加する。production コードを 1 行も変更しない**（`keyseq/` は読むだけ）。
- レイヤ制約: 追加先は `tests_ui/` のみ。domain / application / presentation いずれも不変。スキーマ不変。
- **分割前のコード（現在の `config_io_controller.py`）で pass すること**が完了条件。
  分割後（task_04）も**テスト本体を書き換えずに** pass する状態を目指す（設計メモ参照）。

## 対象範囲（tests_ui 限定・新規ファイル 1 本）

### `tests_ui/test_config_io_characterization_keymap_set_startup.py`（新規）

task_01（`tests_ui/test_config_io_characterization.py`）と**同じ設計制約**を踏襲する（設計メモ参照）。
期待値は**現行実装の実挙動**であり、あるべき姿ではない。

#### A: 構成セット（keymap_set）

| 対象 | 固定する分岐 |
|---|---|
| `confirm_save_if_dirty` | ①dirty なし → 即 `True`（ダイアログ出さない）②askyesnocancel が cancel(None) → `False` ③no(False) → `True`（保存しない）④yes(True) + `keymap_set_path` あり → `save_keymap_set` 経由 ⑤yes + path なし → `save_as` 経由。ダイアログ文言「未保存の変更 / 未保存の変更があります。\n{action}の前に保存しますか？」を固定 |
| `save_keymap_set_to` | ①成功: `config_service.save_runtime_data` 呼び出し・`keymap_set_path`/`startup_path`/`_startup_settings` 更新・`clear_individual_dirty_flags`・`set_dirty(False)`・flash・(show_success_dialog 時) showinfo。②例外: flash「保存失敗: {e}」(auto_clear=False)・showerror・`False`・dirty 維持 |
| `choose_split_base_dir_for_keymap_set` | ①config_root 内 → 即 `""`（ダイアログ出さない）②外 + yes → `dirname(abspath(save_path))` ③外 + no → `""` |
| `load_keymap_set_from` | ①confirm_save_if_dirty が False → 早期 return ②askopenfilename 空 → return ③成功: `load_runtime_data_from_keymap_set_path`・`apply_loaded_data_to_ui`・refresh・`set_dirty(False)`・flash・showinfo ④例外: flash「読込失敗: {e}」・showerror |
| `new_config` | ①confirm False → return ②成功: `new_default_data`→`triggers=[]`→`normalize_runtime_data`・`keymap_set_path` 設定・refresh・`set_dirty(True)`・flash |
| `import_config` | ①confirm False → return ②askopenfilename 空 → return ③成功: `load_legacy_runtime_data`・`set_dirty(True)`・showinfo ④例外: showerror |
| `export_config` | ①asksaveasfilename 空 → return ②成功: `export_runtime_data`・showinfo ③例外: showerror |
| `restore_default` | ①askyesno no → 何もしない ②yes: `new_default_data`・`set_dirty(True)`・flash |
| `set_startup_keymap_set` | ①confirm False → return ②askopenfilename 空 → return ③読込例外 → showerror・**早期 return**（後続を実行しない）④成功: `load_runtime_data_from_keymap_set_path`→`write_startup({keymap_set_path, prompt_if_missing})`→`apply_loaded_data_to_ui`→refresh→`set_dirty(False)`→flash→showinfo |

**`set_startup_keymap_set` の注意**（暫定仕様 §7-2）: `write_startup` 内で `save_startup` が例外を投げても
`write_startup` は showerror で握りつぶす（`:285-286`）ため、`set_startup_keymap_set` は
**保存失敗後もデータ適用・dirty 解除・成功 showinfo を続行する**。この現挙動を固定する。

#### B: 起動設定（startup.json）

| 対象 | 固定する分岐 |
|---|---|
| `write_startup` | ①既定値（`prompt_if_missing`/`ui_font_delta_pt`/`last_used_directory`）に現 `_startup_settings` と引数 dict を順にマージ ②`config_path` キーを除去 ③`ui_font_delta_pt` を `coerce_font_delta` で正規化 ④`save_startup` 成功時は `startup_path`・`_startup_settings` 更新 ⑤`save_startup` 例外時は showerror「startup.json 保存失敗」（例外を吸収し raise しない） |
| `load_startup_and_config` | ①`_startup_settings` に有効な `keymap_set_path` があり実在 → `load_runtime_data_from_keymap_set_path`・`apply_loaded_data_to_ui`・**return**（`keymap_set_path` 更新）②stored path 空 or 不在 → 空データ（`new_empty_data`）で起動 ③**読込例外 → `except Exception: pass`（`:261-262`）で握りつぶし、空データ fallback**。この握りつぶしを明示的に固定する |

### 設計メモ / 制約（task_01 と同一・必ず踏襲）

1. **patch は `tkinter` モジュール属性に対して行う**（`tkinter.messagebox.*` / `tkinter.filedialog.*`）。
   実装モジュール（`config_io_controller`）の変数を patch しないこと（task_04 の分割で壊れる）。
2. **呼び出し口はテスト内のアクセサ関数 1 箇所に集約**する（例: `def _config_set_io(app): return app.config_io` /
   `def _startup_io(app): return app.config_io`）。task_05 の差し替えに備える。
3. **保存はコントローラの変換ロジックを assert する**（A/B の特性化の要点）。
   A（`save_keymap_set_to`）も B（`write_startup`）も**単一 JSON を直接書かず `config_service` へ委譲**する
   （keymap_set は split 構成で複数ファイル / startup は `config_service.save_startup` が書く）。
   したがって task_01 のようなファイルのバイト列比較は A/B には直接適用できない。代わりに、
   **`config_service` の該当メソッドを patch し、コントローラが渡す引数（`write_startup` なら
   マージ後 dict = 既定値マージ・`config_path` 除去・`ui_font_delta_pt` の coerce の結果 /
   `save_keymap_set_to` なら `save_runtime_data` の呼び出しと戻り値の反映）を assert** する。
   これが「保存内容を固定する」task_01 の原則の A/B 版。dict 比較で緩めるのではなく、
   **コントローラの変換ロジックそのものを対象に据える**（config_service の内部は本タスクの対象外）。
4. **ダイアログは文言を完全一致で assert**する（タイトルと本文）。呼び出し順が意味を持つ経路は順序も見る。
5. `set_startup_keymap_set` の「保存失敗後も続行」・`load_startup_and_config` の「例外握りつぶし」は
   **現状を正として固定**する（is-a-bug として書かない）。
6. App の状態（`data` / `keymap_set_path` / `_startup_settings` / `dirty_tracker` の各フラグ）は
   `setUp` で明示的に初期化し、テスト間で汚染しない。App 生成は task_01 と同じ
   （`ConfigService.load_startup` と `os.makedirs` を patch して `App()` を 1 個生成）。

## 含まない

- **C / D / E / F の特性テスト** → task_01 で追加済（`tests_ui/test_config_io_characterization.py`）。重複して書かない。
- **分割の実施そのもの** → task_03（D/E/F）/ task_04（A/B/C）。
- **呼び出し元 30 箇所の差し替え** → task_05。
- **E の source_path 不整合の修正** → [idea_05](../../../backlog/idea_05_trigger_set_source_path_inconsistency.md)。
- production コードの変更全般（`self._app.` reach-through・ダイアログ文言・`config_service` 等）。

## 確認

python は**必ず** `..\..\..\.venv\Scripts\python.exe`（worktree 相対）を使う。

1. 新規テストが分割前のコードで pass:
   `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_config_io_characterization_keymap_set_startup -v`
   → 全 pass。skip / expectedFailure を含めないこと。
2. `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests_ui`
3. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` → pass 86（増減なし）
4. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` → **pass 39 + 本タスク追加分**
5. `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` → pass
6. `git diff --stat` で **`keyseq/` 配下の変更が 0 件**であること。
7. テストが `config_io_controller` のモジュール変数を patch していないこと（`grep` で確認）。

## 完了条件

- 上記「確認」1〜7 がすべて pass。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点 + 本タスク固有: production 無変更 /
  `set_startup_keymap_set` の保存失敗後続行と `load_startup_and_config` の握りつぶしを固定できているか /
  分割後も壊れない patch 方式か）。
- 実機目視: **本タスクでは実施しない**（テスト追加のみ）。フェーズの実機目視は task_06 の前にまとめて実施。
