# リファクタリング計画書 02（app.py の分割・挙動不変）

- 作成日: 2026-07-04
- **前提: 計画書 01（`instruction/modified_proposal/01_refactoring_plan.md`）の全項目が完了していること。** 本計画は 01 実施後のコードを基準にするため、**行番号は記載しない**。対象は必ずクラス名・メソッド名で特定すること。
- 実行環境の前提: Windows 11 / PowerShell / Python は `py` ランチャで起動する（素の `python` はストアのスタブの可能性があるため使わない）。
- 本計画の性質: **機能追加・仕様変更・バグ修正は一切行わない。** 目的は `keyseq/presentation/app.py`（01 完了後で約 3,000 行）を責務単位のモジュールへ分割し、1,000 行未満（目安）の「組み立て役 + ファサード」に縮小すること。
- 併読必須: `AGENTS.md`、`instruction/common/architecture_rules.md`、`instruction/common/dev_rules.md`。

---

## 1. 現状理解（実行者への文脈共有）

### 1.1 App クラスの構造と、分割が難しい理由

`App(tk.Tk)` は次の 3 役を兼ねている。

1. **Tk ルートウィンドウ**（geometry、メニュー、View 切替、mainloop）
2. **全コントローラ**（保存/読込、フック制御、トリガー/キーマップ編集、レイアウト管理、キーキャプチャ）
3. **サービスロケータ**: `views.py` / `dialogs.py` / `keyboard_window.py` が App の属性へ直接手を伸ばす

3 が分割の難所である。外部から掴まれている「取っ手」は大きく 3 種類:

- **メソッド参照**: View のボタンが `command=app.save_keymap_set` のように App のメソッドを直接バインドする（`toggle_hook` / `add_trigger` / `_on_keymap_list_select` など約 45 個。`_` 付き私有メソッドもバインドされている点に注意）
- **属性参照**: View が `app.stop_key_var` などの Tk 変数を参照し、逆に View が `app.hook_toggle_btn` / `app.keymap_listbox` などのウィジェット参照を App に**生やす**
- **プロトコル的参照**: ダイアログ類が `parent.suspend_hook_for_dialog()` / `parent.resume_hook_after_dialog()` / `parent._dialog_result` / `parent.validate_hotkey()` / `parent.data` を使う。`keyboard_window.py` は `master.suspend_hook_for_dialog` を `hasattr` 越しに使う

### 1.2 分割方針（本計画の設計判断）

**「App をファサードとして残す委譲方式」** を採る。

- 責務ごとのクラスを新モジュールに切り出し、`App.__init__` で生成して保持する
- 外部（views / dialogs / keyboard_window / メニュー / `__init__` の配線）から参照されるメソッドは、App に**同名の 1 行委譲メソッド**として残す。したがって **views.py / dialogs.py / keyboard_window.py は本計画では 1 文字も変更しない**
- mixin 方式（多重継承で機械分割）は採らない。ファイルは減るが暗黙の `self` 共有が残り、テスト可能性が改善しないため

### 1.3 共通移設手順（全項目で必ずこの手順に従う）

各抽出項目は次のレシピで行う。

1. 新モジュールを `keyseq/presentation/` 直下に作成し、クラスを定義する。コンストラクタは原則 `def __init__(self, app) -> None: self._app = app` のみ（例外は各項目に明記）。
2. 指定されたメソッドを App から新クラスへ**移動**する。このとき:
   - **命名規則**: 移動先では先頭のアンダースコアを 1 つ除去した公開名にする（`_refresh_triggers` → `refresh_triggers`）。元々 `_` の無い名前はそのまま。
   - メソッド本文中の `self.xxx` を分類する: 参照先が**同じ項目で一緒に移動するもの** → `self.xxx`（新公開名に追従）／**App に残るもの・別グループのもの** → `self._app.xxx`（**既存名のまま**。ファサード経由で呼ぶ）。
   - **禁止**: `self._app.data` や `self._app.keymap_set_path` をコントローラのフィールドに複製・キャッシュすること。これらは読込のたびに**差し替わる**ため、必ず毎回 `self._app.` 経由で読む。
   - **禁止**: コントローラ同士の直接参照。他グループの機能は必ず `self._app.<既存名>(...)`（ファサード）経由で呼ぶ。
3. 移動した各メソッドについて `git grep -n "<既存名>" -- keyseq tests tests_ui` を実行し、参照元を分類する:
   - 新クラス内のみ → App 側に何も残さない
   - それ以外（views / dialogs / keyboard_window / app.py の残留コード / `App.__init__` の配線 / テスト）から参照される → App に同名の委譲を残す:
     ```python
     def _refresh_triggers(self):
         return self._trigger_panel.refresh_triggers()
     ```
4. 状態フィールド（`hook_active` など）を移す場合は、外部参照があるものだけ App に読み取り用 `@property` を残す（各項目に明記）。**このとき `App.__init__` にある当該フィールドの初期化行（例: `self._capturing_stop_key = False`）は必ず削除する**（初期値はコントローラの `__init__` で設定する）。setter の無いプロパティへ `__init__` が代入すると `AttributeError` で起動しなくなるため、消し忘れはスモークで即検出される。
5. 検証:
   ```powershell
   git grep -nE "def <既存名1>|def <既存名2>|…" -- keyseq/presentation/app.py
   # → 委譲 1 行のメソッドだけが残っていること（本体ロジックが app.py に残っていないこと）
   git grep -n "def _" -- keyseq/presentation/<新モジュール>.py   # 0 件（公開名規則の確認）
   ```
   の後、**標準検証**（§2 で定義）と項目ごとの手動確認を行う。

### 1.4 `App.__init__` でのコントローラ生成位置

- **`ConfigPaths`（S3）のみ例外**: `self.user_root` の `os.makedirs(...)` 直後・`self.startup_path = self._resolve_startup_path()` より**前**に生成する（パス解決ファサードが `__init__` の早い段階で使われるため）。
- それ以外のコントローラは `self.state = AppState()` の直後・`self.data = ...` の前にまとめて生成する。生成は参照の保持のみで副作用を持たないこと（Tk ウィジェットや data には触らない）。項目を進めるたびに、この生成ブロックへ 1 行ずつ追加していく:

```python
self.state = AppState()
# --- controllers (計画02で順次追加) ---
self._dirty_tracker = DirtyStateTracker(...)
self._stop_key_capture = SingleKeyCaptureController(self, ...)
...
```

---

## 2. 項目 0: 安全網の構築（最初に必ず実行）

### 0-a. 前提条件の確認（1 つでも満たさなければ中断して報告）

```powershell
git status                          # クリーンであること
git rev-parse HEAD                  # ベースラインとして記録（報告書に残す）

# 計画01の完了確認（すべて期待どおりであること）
git grep -n "class ActionDialog" -- keyseq/presentation/views.py      # 0 件（R1）
git grep -in "chain" -- keyseq                                        # 0 件（R5）
git grep -n "def _save_keymap_set_to" -- keyseq/presentation/app.py   # 1 件（R11）
git grep -n "def _sync_control_vars_from_data" -- keyseq/presentation/app.py  # 1 件（R12）
git grep -n "def slugify_file_stem" -- keyseq/application/config_service.py   # 1 件（R14）
git grep -n "def normalize_tk_keysym" -- keyseq/presentation/tk_keys.py       # 1 件（R7）

py -m unittest discover -s tests -v   # 計画01のテストが全緑
py tests/smoke_app.py                 # SMOKE OK
```

```powershell
git switch -c refactor/02-app-split
```

### 0-b. UI レベル特性テスト（ファサード契約の固定）を追加

`tests_ui/` ディレクトリを新規作成し、以下を**この内容のまま**作成する。ヘッドレスの `tests/` とは分離する（GUI が必要なため。`discover -s tests` には混ぜない）。

このテストは 2 つの役割を持つ:
- 分割前後で UI の観測可能な挙動が変わらないことの固定
- **App ファサードとして残さなければならないメソッド群の契約**（このテストが呼ぶ `app._refresh_triggers` / `app._set_dirty` / `app._start_stop_key_capture` 等は、全項目完了後も App 上で同名で呼べなければならない）

#### `tests_ui/test_app_ui_flows.py`

```python
"""App を実際に生成して、ダイアログを出さない範囲の UI 挙動を固定する。

- グローバルフックは一切開始しない（start_hook を呼ばない）
- ファイル保存を伴う操作は行わない（config/ を汚さない）
- GUI が開ける環境（通常のデスクトップセッション）で実行すること
"""
import unittest

from keyseq.presentation.app import App


class AppUiFlowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = App()
        cls.app.update_idletasks()
        # 実環境の構成に依存しないよう、テスト用データへ差し替える
        cls.app.data = cls.app.config_service.normalize_runtime_data(
            {
                "triggers": [
                    {"key": "f1", "label": "one", "actions": [{"type": "text", "value": "a"}]},
                    {"key": "f2", "label": "two", "actions": []},
                ],
                "keymaps": [{"id": "km1", "label": "Main", "mappings": {"a": "b"}}],
                "active_keymap_id": "km1",
            }
        )
        cls.app.state.reset_indices()
        cls.app._refresh_triggers()
        cls.app._refresh_actions()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.app._set_dirty(False)
        finally:
            cls.app.destroy()

    def test_trigger_lists_populated(self):
        self.assertEqual(self.app.full_view.trigger_list.size(), 2)
        self.assertEqual(self.app.compact_view.trigger_list.size(), 2)

    def test_selection_updates_status(self):
        self.app._set_selected_trigger_index(1)
        self.assertIn("選択中: f2", self.app.status_var.get())
        self.app._set_selected_trigger_index(0)
        self.assertIn("選択中: f1", self.app.status_var.get())

    def test_status_shows_hook_off(self):
        self.app._update_status()
        self.assertIn("フック: OFF", self.app.status_var.get())

    def test_dirty_flag_reflected_in_file_status(self):
        self.app._set_dirty(True)
        self.assertIn("未保存", self.app.file_status_var.get())
        self.app._set_dirty(False)
        self.assertIn("保存済み", self.app.file_status_var.get())

    def test_compact_and_full_view_switch(self):
        self.app.show_compact_view()
        self.assertTrue(self.app._compact_mode)
        self.assertIn("選択:", self.app.status_var.get())
        self.app.show_full_view()
        self.assertFalse(self.app._compact_mode)

    def test_hook_suspend_counter_nesting(self):
        self.assertEqual(self.app._get_hook_pause_count(), 0)
        self.app.suspend_hook_for_dialog()
        self.app.suspend_hook_for_dialog()
        self.assertEqual(self.app._get_hook_pause_count(), 2)
        self.app.resume_hook_after_dialog()
        self.app.resume_hook_after_dialog()
        self.assertEqual(self.app._get_hook_pause_count(), 0)

    def test_stop_key_capture_start_and_cancel(self):
        self.app._start_stop_key_capture()
        self.assertTrue(self.app._capturing_stop_key)
        self.assertEqual(self.app._get_hook_pause_count(), 1)
        self.app._stop_stop_key_capture(cancel=True)
        self.assertFalse(self.app._capturing_stop_key)
        self.assertEqual(self.app._get_hook_pause_count(), 0)

    def test_keymap_list_shows_active_marker(self):
        self.app._refresh_keymap_list_ui()
        first = self.app.keymap_listbox.get(0)
        self.assertTrue(first.startswith("> "))
        self.assertIn("Main", first)

    def test_keyboard_window_opens_and_closes(self):
        self.app.open_keyboard_window()
        self.assertIsNotNone(self.app.keyboard_window)
        self.app.keyboard_window._handle_close()
        self.assertIsNone(self.app.keyboard_window)


if __name__ == "__main__":
    unittest.main()
```

> 注意: `_capturing_stop_key` / `hook_active` / `_compact_mode` のような**状態フィールドも外部契約**である（このテストと views 等が読む）。項目 S6 / S11 で状態がコントローラへ移った後は、App に読み取り用 `@property` を残して同名で読めるようにする（各項目に明記）。

### 0-c. 完了条件

```powershell
py -m unittest discover -s tests -v      # 全緑
py -m unittest discover -s tests_ui -v   # 全緑（ウィンドウが一瞬開く）
py tests/smoke_app.py                    # SMOKE OK
git add tests_ui/
git commit -m "test: app.py 分割前の UI 特性テストを追加した。"
```

以降の**標準検証**を次のとおり定義する:

> **標準検証** =
> `py -m compileall -q keyseq main.py`
> → `py -m unittest discover -s tests -v`（全緑）
> → `py -m unittest discover -s tests_ui -v`（全緑）
> → `py tests/smoke_app.py`（**SMOKE OK** の表示）

---

## 3. 作業項目リスト（この順に実行。1 項目 = 1 コミット）

> 共通ルールは §1.3 の移設手順。完了条件を満たせなければ `git checkout -- .` / `git revert HEAD` で戻し、中断して報告する。

---

### S1: 計画01で拾い漏れたデッドコード 2 件を削除

- **対象**: `App._preferred_config_path`、`App._sync_startup_config_path`
- **問題**: どちらも定義のみで呼び出し元ゼロ（計画01の網から漏れていた）。分割で死物を新居に運ばないよう先に消す。
- **どう変えるか**: 削除前に `git grep -n "_preferred_config_path\|_sync_startup_config_path" -- keyseq` 相当（`git grep -nE`）で定義以外の参照が無いことを確認してから 2 メソッドを削除する。参照が見つかった場合は削除せず中断して報告。
- **完了条件**:
  ```powershell
  git grep -nE "_preferred_config_path|_sync_startup_config_path" -- keyseq  # 0 件
  ```
  → 標準検証。
- **リスク / 戻し方**: ほぼゼロ。`git revert HEAD`。
- **依存**: 項目 0

---

### S2: Listbox 選択ヘルパを関数として抽出（ウォームアップ）

- **対象**: `App._focused_listbox_index`、`App._sync_listbox_selection_to_focus`
- **問題**: トリガー一覧・キーマップ一覧・アクション一覧の 3 つの Listbox で共用されるロジックが App のメソッドになっており、後続のパネル分割（S8/S9）で双方から必要になる。
- **どう変えるか**: 新規 `keyseq/presentation/listbox_utils.py` にモジュール関数として移す。`self.focus_get()` は Tk ルートに依存するため、ルートを引数に取る:
  ```python
  from __future__ import annotations

  import tkinter as tk


  def focused_listbox_index(root: tk.Misc, listbox: tk.Listbox, item_count: int) -> int | None:
      """Listbox にフォーカスがある場合は active 行を、なければ選択行を返す。"""
      # （元の App._focused_listbox_index の本体をそのまま移す。
      #   self.focus_get() → root.focus_get() に置換）


  def sync_listbox_selection_to_focus(root: tk.Misc, listbox: tk.Listbox, item_count: int) -> int | None:
      # （元の App._sync_listbox_selection_to_focus の本体をそのまま移す。
      #   self._focused_listbox_index(...) → focused_listbox_index(root, ...) に置換）
  ```
  App 側は委譲を残す（呼び出し箇所が多いため）:
  ```python
  def _focused_listbox_index(self, listbox, item_count):
      return focused_listbox_index(self, listbox, item_count)

  def _sync_listbox_selection_to_focus(self, listbox, item_count):
      return sync_listbox_selection_to_focus(self, listbox, item_count)
  ```
- **完了条件**: §1.3-5 の grep（app.py に本体が残っていないこと）→ 標準検証（tests_ui の `test_selection_updates_status` が選択同期の不変を担保）。
- **リスク / 戻し方**: 低。`git revert HEAD`。
- **依存**: 項目 0

---

### S3: パス解決を `ConfigPaths` として抽出

- **対象**: 以下の App メソッド（移動先では先頭 `_` を除去した公開名にする）:
  `_preferred_startup_path` / `_preferred_keymap_set_path` / `_preferred_keymap_sets_dir` / `_preferred_keymaps_dir` / `_preferred_trigger_sets_dir` / `_preferred_sequences_dir` / `_legacy_settings_dir` / `_resolve_startup_path` / `_resolve_keymap_set_path` / `_resolve_keylayout_dir` / `_is_within_legacy_settings` / `_is_within_config_root` / `_normalize_keymap_set_save_path` / `_suggest_keymap_set_dialog_path` / `_suggest_keymap_set_dialog_dir` / `_json_dialog_initial_dir` / `_filename_stem` / `_suggest_json_path` / `_keymap_set_file_stem` / `_to_rel_if_possible` / `_to_config_relative_or_absolute`
- **問題**: パス規約（デフォルト位置・レガシー位置・config 相対/絶対の使い分け）が App に埋まっており、単体テストできない。実際にはほぼ純関数群。
- **どう変えるか**: 新規 `keyseq/presentation/config_paths.py`:
  ```python
  from __future__ import annotations

  import os
  import re


  class ConfigPaths:
      """設定ファイル群の配置規約とパス解決。App の実行時状態には依存しない。"""

      def __init__(self, *, base_dir: str, config_root: str, user_root: str, config_service) -> None:
          self.base_dir = base_dir
          self.config_root = config_root
          self.user_root = user_root
          self._config_service = config_service
      ...
  ```
  - `self.base_dir` / `self.config_root` / `self.user_root` への参照はコンストラクタ引数由来のフィールドに置換。
  - `self.config_service.slugify_file_stem` / `resolve_startup_relative_path` / `to_config_relative_or_absolute` への参照は `self._config_service.` に置換。
  - **実行時状態に依存する 3 メソッドはシグネチャを変える**（App の状態を読まない設計にするため）:
    - `suggest_keymap_set_dialog_path(current_keymap_set_path: str) -> str`
    - `suggest_keymap_set_dialog_dir(current_keymap_set_path: str) -> str`
    - `keymap_set_file_stem(current_keymap_set_path: str) -> str`
  - App 側のファサード（全メソッド分残す。状態依存の 3 つは現在値を渡す）:
    ```python
    def _suggest_keymap_set_dialog_dir(self) -> str:
        return self.paths.suggest_keymap_set_dialog_dir(str(getattr(self, "keymap_set_path", "") or ""))
    ```
  - `App.__init__` の生成ブロック（§1.4）に `self.paths = ConfigPaths(...)` を追加。生成は `self.config_service` 定義後・`self.startup_path = self._resolve_startup_path()` より**前**に行うこと（`_resolve_startup_path` がファサード経由で paths を使うため）。
- **新規テスト**: `tests/test_config_paths.py` を追加する（ヘッドレス可）:
  ```python
  import os
  import tempfile
  import unittest

  from keyseq.application.config_service import ConfigService
  from keyseq.infrastructure.json_repository import JsonRepository
  from keyseq.presentation.config_paths import ConfigPaths


  class ConfigPathsTest(unittest.TestCase):
      def setUp(self):
          self.tmp = tempfile.TemporaryDirectory()
          base = self.tmp.name
          self.base_dir = base
          self.config_root = os.path.join(base, "config")
          self.user_root = os.path.join(self.config_root, "user")
          os.makedirs(self.user_root, exist_ok=True)
          self.paths = ConfigPaths(
              base_dir=self.base_dir,
              config_root=self.config_root,
              user_root=self.user_root,
              config_service=ConfigService(JsonRepository()),
          )

      def tearDown(self):
          self.tmp.cleanup()

      def test_preferred_paths(self):
          self.assertEqual(
              self.paths.preferred_keymap_set_path(),
              os.path.join(self.config_root, "user", "keymap_sets", "default.json"),
          )
          self.assertEqual(
              self.paths.preferred_startup_path(),
              os.path.join(self.config_root, "config.json"),
          )

      def test_normalize_keymap_set_save_path(self):
          # 空 → デフォルト
          self.assertEqual(
              self.paths.normalize_keymap_set_save_path(""),
              self.paths.preferred_keymap_set_path(),
          )
          # "config/" 始まりの相対 → base_dir 基準
          self.assertEqual(
              self.paths.normalize_keymap_set_save_path("config/user/keymap_sets/a.json"),
              os.path.normpath(os.path.join(self.base_dir, "config", "user", "keymap_sets", "a.json")),
          )
          # その他の相対 → config_root 基準
          self.assertEqual(
              self.paths.normalize_keymap_set_save_path("user/keymap_sets/a.json"),
              os.path.normpath(os.path.join(self.config_root, "user", "keymap_sets", "a.json")),
          )
          # レガシー settings/ 配下 → デフォルトへ矯正
          legacy = os.path.join(self.base_dir, "settings", "config.json")
          self.assertEqual(
              self.paths.normalize_keymap_set_save_path(legacy),
              self.paths.preferred_keymap_set_path(),
          )

      def test_resolve_startup_path_prefers_new_location(self):
          new_path = os.path.join(self.config_root, "config.json")
          # 新ファイルが無い → レガシー位置を返す
          self.assertEqual(
              self.paths.resolve_startup_path(),
              os.path.join(self.base_dir, "settings", "startup.json"),
          )
          with open(new_path, "w", encoding="utf-8") as f:
              f.write("{}")
          self.assertEqual(self.paths.resolve_startup_path(), new_path)

      def test_suggest_dialog_dir_falls_back(self):
          # keymap_sets ディレクトリが無い場合は config_root
          self.assertEqual(
              self.paths.suggest_keymap_set_dialog_dir(""),
              self.config_root,
          )


  if __name__ == "__main__":
      unittest.main()
  ```
- **完了条件**: §1.3-5 の grep → `py -m unittest tests.test_config_paths -v` 全緑 → 標準検証。
- **リスク / 戻し方**: 低〜中（`__init__` 内の生成順序ミスで起動時 AttributeError → スモークで即検出）。`git revert HEAD`。
- **依存**: S1

---

### S4: ダーティ状態管理を `DirtyStateTracker` として抽出

- **対象**: メソッド `_set_dirty` / `_mark_keymap_dirty` / `_mark_trigger_set_dirty` / `_mark_sequence_dirty` / `_has_unsaved_changes` / `_sync_dirty_state` / `_has_individual_dirty` / `_clear_individual_dirty_flags`、状態 `_is_dirty` / `_config_dirty` / `_trigger_set_source_path` / `_trigger_set_imported` / `_trigger_set_dirty`
- **問題**: 「何が未保存か」という 1 つの関心事が、フラグ 5 個 + メソッド 8 個として App 中に散っている。
- **どう変えるか**: 新規 `keyseq/presentation/dirty_state.py`:
  ```python
  class DirtyStateTracker:
      """構成セット全体・trigger_set・個別 keymap/sequence の未保存状態を一元管理する。"""

      def __init__(self, *, get_data, keymap_service, config_service, on_change) -> None:
          self._get_data = get_data          # lambda: app.data（dict は差し替わるため毎回取得）
          self._keymap_service = keymap_service
          self._config_service = config_service
          self._on_change = on_change        # 表示更新コールバック（app._update_file_status）
          self.is_dirty = False
          self.config_dirty = False
          self.trigger_set_source_path = ""
          self.trigger_set_imported = False
          self.trigger_set_dirty = False
  ```
  - 各メソッドを移動（公開名化）。`self._update_file_status()` の呼び出しは `self._on_change()` に置換。
  - `mark_keymap_dirty` / `mark_sequence_dirty` の「引数 None ならアクティブ keymap / 選択中トリガーを対象にする」というデフォルト解決は **App のファサード側に残す**（tracker は明示的な対象 dict または None を受け取り、None なら全体ダーティのみ立てる、では挙動が変わるため不可。以下の形にする）:
    ```python
    # App 側（ファサード）
    def _mark_sequence_dirty(self, trigger: dict | None = None) -> None:
        target = trigger if isinstance(trigger, dict) else self._selected_trigger()
        self._dirty_tracker.mark_sequence_dirty(target)

    def _mark_keymap_dirty(self, keymap: dict | None = None) -> None:
        target = keymap if keymap is not None else self.keymap_service.get_active_keymap(self.data)
        self._dirty_tracker.mark_keymap_dirty(target)
    ```
    tracker 側の `mark_sequence_dirty(target)` は「target が dict なら内部キーを立てる + `set_dirty(True, config_dirty=False)`」という元ロジックをそのまま持つ。
  - `_trigger_set_source_path` 等 3 状態は S6 完了まで app.py の残留コードからも読み書きされるため、App に**プロパティ（getter/setter）**を残す:
    ```python
    @property
    def _trigger_set_source_path(self) -> str:
        return self._dirty_tracker.trigger_set_source_path

    @_trigger_set_source_path.setter
    def _trigger_set_source_path(self, value: str) -> None:
        self._dirty_tracker.trigger_set_source_path = str(value or "")
    ```
    （`_trigger_set_imported` / `_trigger_set_dirty` も同様。bool 化して格納。）
  - `__init__` の生成ブロックに追加。`on_change=self._update_file_status` を渡すが、`_update_file_status` は `_build_ui` 後でないと `file_status_var` が無い。現行コードも同様の順序依存を `hasattr` ではなく呼び出し順で回避しているため、**生成時にコールバックを呼ばないこと**（生成は参照保持のみ）を守れば問題ない。
- **新規テスト**: `tests/test_dirty_state.py`（フェイク data とコールバック記録で、mark→has_unsaved→clear の遷移を 5 ケース程度固定。`config_dirty=False` 指定時に `_config_dirty` が立たないこと、`clear_individual_dirty_flags` が trigger/keymap の内部キーを落とすことを含める）。
- **完了条件**: §1.3-5 の grep → 標準検証（tests_ui の `test_dirty_flag_reflected_in_file_status` が表示連動の不変を担保）→ 手動確認: アプリでトリガーを追加するとステータスバーが「未保存」になり、保存すると「保存済み」に戻る。
- **リスク / 戻し方**: 中（ダーティ判定の漏れは「保存確認が出ない」事故につながる）。`git revert HEAD`。
- **依存**: S1

---

### S5: 停止キー/トグルキーのキャプチャを統合して `SingleKeyCaptureController` に抽出

- **対象**: `_toggle_stop_key_capture` / `_start_stop_key_capture` / `_stop_stop_key_capture` / `_on_stop_key_capture_keypress` / `clear_stop_key` と、トグルキー側の同型 5 メソッド、状態 `_capturing_stop_key` / `_capturing_toggle_key`
- **問題**: 2 系統がほぼ完全な同型コード（差分は data キー・ボタン・文言・競合チェックの組合せのみ）。計画01では挙動リスクを理由に共通化を見送ったが、分割でどのみち触るこのタイミングが統合の適期。
- **どう変えるか**: 新規 `keyseq/presentation/key_capture.py`:
  ```python
  from __future__ import annotations

  from tkinter import messagebox

  from keyseq.presentation.tk_keys import normalize_tk_keysym


  class SingleKeyCaptureController:
      """「単キーを 1 つキャプチャして data に書く」処理の共通実装。

      キャプチャ中はフックを一時停止する（App.suspend_hook_for_dialog / resume_hook_after_dialog）。
      """

      def __init__(
          self,
          app,
          *,
          data_key: str,            # "hook_stop_key" / "hook_toggle_key"
          var_attr: str,            # "stop_key_var" / "toggle_key_var"
          capture_btn_attr: str,    # "stop_key_capture_btn" / "toggle_key_capture_btn"
          clear_btn_attr: str,      # "stop_key_clear_btn" / "toggle_key_clear_btn"
          focus_entry_attr: str,    # "stop_key_entry" / "toggle_key_entry"
          label: str,               # "停止トリガー" / "トグルキー"
          single_key_example: str,  # "f12" / "f11"
          conflict_checks,          # list[tuple[Callable[[App, str], bool], str]]
      ) -> None:
          self._app = app
          self.capturing = False
          ...
  ```
  - `conflict_checks` は「(判定関数, 相手の名称)」のリスト。判定が True ならエラーダイアログ
    `f"{label}が{相手の名称}と重複しています:\n{key}"` を出して確定しない。App 側の生成時に渡す:
    ```python
    self._stop_key_capture = SingleKeyCaptureController(
        self,
        data_key="hook_stop_key",
        var_attr="stop_key_var",
        capture_btn_attr="stop_key_capture_btn",
        clear_btn_attr="stop_key_clear_btn",
        focus_entry_attr="stop_key_entry",
        label="停止トリガー",
        single_key_example="f12",
        conflict_checks=[
            (lambda app, key: app.trigger_service.key_exists(app.data, key), "トリガー一覧"),
            (lambda app, key: app.trigger_service.is_toggle_key_conflict(app.data, key), "トグルキー"),
            (lambda app, key: bool(app.keymap_service.get_keymap_by_switch_key(app.data, key)), "キーマップ直接切替キー"),
            (lambda app, key: app.keymap_service.source_key_exists(app.data, key), "キーマップ元キー"),
        ],
    )
    self._toggle_key_capture = SingleKeyCaptureController(
        self,
        data_key="hook_toggle_key",
        ...,
        label="トグルキー",
        single_key_example="f11",
        conflict_checks=[
            (lambda app, key: app.trigger_service.key_exists(app.data, key), "トリガー一覧"),
            (lambda app, key: app.trigger_service.is_stop_key_conflict(app.data, key), "停止キー"),
            (lambda app, key: bool(app.keymap_service.get_keymap_by_switch_key(app.data, key)), "キーマップ直接切替キー"),
            (lambda app, key: app.keymap_service.source_key_exists(app.data, key), "キーマップ元キー"),
        ],
    )
    ```
  - コントローラの `start()` / `stop(cancel)` / `toggle()` / `clear()` / `_on_keypress(event)` は元の停止キー版の本文を移し、固有値をパラメータ参照に置換する。元コードとの対応を厳密に保つこと:
    - ボタン文言: 取得中 `"取得中…（Escで停止）"` ↔ 通常 `"キー入力で取得"`（両系統共通）
    - 修飾キー単体（ctrl/shift/alt/windows）は無視、`"+"` 入りは
      `f"{label}は単キーのみ対応です（例: {single_key_example}）。"` でエラー
    - 確定時: `app.data[data_key] = key` → Tk 変数更新 → `app._set_dirty(True)` → `stop(cancel=False)`
    - `input_gateway.validate_key_name` による妥当性チェックと `"不明なキー名です:..."` エラーも移す
    - キーの正規化は `normalize_tk_keysym(event.keysym)`（R7 の共通関数）を使う
  - **相互排他**: 元コードでは stop 開始時に toggle キャプチャを止め、逆も同様。App のファサードで実現する:
    ```python
    def _start_stop_key_capture(self):
        self._toggle_key_capture.stop(cancel=True)
        self._stop_key_capture.start()
    ```
  - **状態の外部参照**: `_capturing_stop_key` / `_capturing_toggle_key` は `_is_menu_shortcut_enabled` と `show_compact_view` と tests_ui が読むため、App に読み取りプロパティを残す:
    ```python
    @property
    def _capturing_stop_key(self) -> bool:
        return self._stop_key_capture.capturing
    ```
  - views.py がバインドする `_toggle_stop_key_capture` / `clear_stop_key` / `_toggle_toggle_key_capture` / `clear_toggle_key` は委譲として残す。
  - 統合後、`App._normalize_tk_key_for_trigger` の参照元が無くなる場合は削除する（`git grep` で確認。キーマップ切替キャプチャは計画01 R2 で削除済みのため、残る参照は無いはず）。
- **完了条件**: §1.3-5 の grep → 標準検証（tests_ui の `test_stop_key_capture_start_and_cancel` を含む）→ **手動確認（必須）**: `py main.py` で起動し、
  1. 「キー入力で取得」→ F9 押下 → 停止トリガー欄に `f9` が入り「未保存」になる
  2. もう一度取得 → Esc → キャンセルされ値が変わらない
  3. トグルキー側でも同様に取得できる
  4. 停止キーに設定済みのキーをトグルキーへ取得しようとするとエラーダイアログが出る
  5. 「クリア」で空に戻る
- **リスク / 戻し方**: **中〜大**（本計画で唯一「同型 2 実装 → 1 実装」の書き換えを含む）。エラーメッセージ文言の完全一致まで含めて元コードと突き合わせること。手動確認 4 項目で異常があれば `git revert HEAD`。
- **依存**: S4（`_set_dirty` ファサード確定後）、計画01 R7（`tk_keys.py`）

---

### S6: 保存・読込フローを `ConfigIoController` として抽出

- **対象メソッド**（すべて `keyseq/presentation/config_io_controller.py` の `ConfigIoController` へ。公開名化）:
  - 構成セット系: `_confirm_save_if_dirty` / `new_config` / `save_keymap_set` / `save_as` / `_save_keymap_set_to` / `load_keymap_set_from` / `import_config` / `export_config` / `restore_default` / `set_startup_keymap_set` / `_apply_loaded_data_to_ui` / `_choose_split_base_dir_for_keymap_set` / `_load_startup_and_config` / `_write_startup`
  - 個別 JSON IO 系: `_choose_save_path_with_collision` / `_ask_link_label_to_filename` / `_selected_keymap_for_io` / `save_selected_keymap` / `save_selected_keymap_as` / `_save_keymap_to_path` / `load_keymap_file` / `save_trigger_set_file` / `save_trigger_set_file_as` / `_save_trigger_set_to_path` / `load_trigger_set_file` / `save_selected_sequence` / `save_selected_sequence_as` / `_save_sequence_to_path` / `load_sequence_file`
  - **App に残すもの**: `_load_startup_settings`（`__init__` の極めて早い段階で呼ばれるため）、`_sync_control_vars_from_data`（Tk 変数を直接触る UI 同期）、`open_preset_manager`、`set_ui_font_delta` / `_coerce_font_delta`（フォント設定。`_write_startup` はファサード経由で呼ぶ）
- **問題**: App の約 650 行を占める最大の塊。ダイアログ表示と ConfigService 呼び出しの組合せで、パス解決（S3）・ダーティ管理（S4）と強く結合している。
- **どう変えるか**: §1.3 のレシピどおり機械的に移す。注意点:
  - `self.keymap_set_path` / `self.startup_path` / `self._startup_settings` / `self.data` への読み書きはすべて `self._app.` 経由（**App の属性のまま残す**。コントローラに持たせない）。
  - パス系ヘルパ呼び出し（`_preferred_keymap_set_path` 等）は `self._app._preferred_keymap_set_path()`（S3 ファサード）経由。
  - ダーティ系（`_set_dirty` / `_clear_individual_dirty_flags` / `_has_unsaved_changes` / `_trigger_set_*`）も `self._app.` 経由。
  - `_ask_link_label_to_filename` は `tk.Toplevel(self._app)` を親にする（元は `tk.Toplevel(self)`）。
  - `_load_startup_and_config` は `__init__` から `self._config_io.load_startup_and_config()` として呼ぶ（コントローラ生成が §1.4 の位置なら順序問題なし）。
  - メニューと views がバインドする `new_config` / `save_keymap_set` / `save_as` / `load_keymap_set_from` / `import_config` / `export_config` / `set_startup_keymap_set` / `restore_default` と、views の個別保存/読込ボタン群（`save_selected_keymap` ほか 9 個）、他コントローラ・残留コードが呼ぶ `_confirm_save_if_dirty`（`on_close` が使用）/ `_write_startup` / `_apply_loaded_data_to_ui` は委譲を残す。
- **完了条件**: §1.3-5 の grep → 標準検証 → **手動確認（必須）**: 新規作成 → トリガー追加 → 保存 → 読込（構成セット）→ Export → Import → 別名で保存、を一巡し、各操作後のステータスバー表示（未保存/保存済み・フラッシュ文言）が従来どおりであること。`config/user/` 配下に保存した場合の生成ファイル構成が計画01のテスト（`tests/test_config_service.py`）の期待と同じであること。
- **リスク / 戻し方**: 中〜大（最重要データ経路）。ConfigService 層の挙動は `tests/test_config_service.py` が固定済みなので、事故が起きるとすれば「App 状態（keymap_set_path 等）の更新漏れ」— 手動一巡で検出できる。`git revert HEAD`。
- **依存**: S3、S4

---

### S7: キーボードレイアウト管理と KeyboardWindow 開閉を `LayoutController` として抽出

- **対象メソッド**（→ `keyseq/presentation/layout_controller.py` の `LayoutController`）:
  `open_keyboard_window` / `_on_keyboard_window_closed` / `_refresh_keyboard_window` / `_get_current_keyboard_layout` / `_get_fallback_keyboard_layout_id` / `_reload_keyboard_layouts` / `_sync_keyboard_layout_controls` / `_rebuild_keyboard_layout_display_maps` / `_persist_keyboard_layout_selection` / `toggle_keyboard_show_physical_key_labels` / `_set_keyboard_layout_selection` / `on_keyboard_layout_selected` / `add_external_keyboard_layout` / `delete_keyboard_layout` / `_resolve_key_name_from_scan_code` / `_should_debug_special_key_event` / `_debug_special_key_event`
  移動する状態: `keyboard_layout_id` / `_keyboard_layout_entries` / `_keyboard_layout_display_to_id` / `_keyboard_layout_id_to_display` / `keyboard_window` / `keyboard_layouts_dir`
- **問題**: レイアウト辞書・表示名マップ・KeyboardWindow のライフサイクルという独立した関心事が App に同居。
- **どう変えるか**: §1.3 のレシピどおり。注意点:
  - `keyboard_window` は tests_ui が `app.keyboard_window` を読むため、App に読み書きプロパティを残す（内部実体はコントローラのフィールド）。
  - `_resolve_key_name_from_scan_code` は `App.__init__` で `KeyStateManager` / `InputRouter` に配線されている。**配線はファサード（App の同名メソッド）のまま**にすれば生成順序の問題は起きない（呼び出し時に解決されるため）。
  - `_persist_keyboard_layout_selection` は `save_keymap_set(show_success_dialog=False)`（S6 ファサード）経由。
  - `keyboard_layout_var` / `keyboard_layout_combo` / `compact_keyboard_layout_combo` / `keyboard_show_physical_key_labels_var` は App の属性のまま（View が生やす）。コントローラから `self._app.` で参照。
  - メニュー/views がバインドする `open_keyboard_window` / `on_keyboard_layout_selected` / `add_external_keyboard_layout` / `delete_keyboard_layout` / `toggle_keyboard_show_physical_key_labels` は委譲を残す。
- **完了条件**: §1.3-5 の grep → 標準検証（tests_ui の `test_keyboard_window_opens_and_closes` を含む）→ 手動確認: レイアウトコンボで切替、キーボードUIを開く、`config/user/keylayout/jis.json` を「外部レイアウトを追加」で登録→コンボに現れる→「レイアウトを削除」で外す（**確認後、構成セットに変更を残さないよう元の状態に戻して保存し直すか、保存せず終了する**）。
- **リスク / 戻し方**: 中。`git revert HEAD`。
- **依存**: S6（`_persist_keyboard_layout_selection` が保存ファサードを呼ぶため）

---

### S8: キーマップ管理パネルを `KeymapPanelController` として抽出

- **対象メソッド**（→ `keyseq/presentation/keymap_panel_controller.py` の `KeymapPanelController`）:
  `_format_keymap_display_name` / `_format_keymap_list_entry` / `_selected_keymap_list_index` / `_sync_keymap_manage_buttons` / `_refresh_keymap_list_ui` / `_on_keymap_list_select` / `_on_keymap_list_focus_index_change` / `_on_keymap_list_double_click` / `_add_keymap` / `_rename_keymap_label` / `_delete_keymap` / `_select_keymap` / `_edit_selected_keymap` / `_apply_keymap_edit` / `_validate_keymap_switch_assignment` / `activate_keymap_by_id` / `assign_keymap_from_keyboard_ui` / `clear_keymap_from_keyboard_ui` / `_get_active_keymap_text`
- **問題**: キーマップ一覧 UI と data 操作の塊（約 450 行）。
- **どう変えるか**: §1.3 のレシピどおり。注意点:
  - Listbox 選択は S2 の `listbox_utils` 関数を直接使う（`focused_listbox_index(self._app, self._app.keymap_listbox, ...)`）。
  - `_refresh_keyboard_window`（S7）・`_update_status`（S9 まで App 残留）・`_set_dirty` / `_mark_keymap_dirty`（S4）・`_set_flash_message`（App 残留）は `self._app.` 経由。
  - 委譲を残すもの: views がバインドする 7 個（`_on_keymap_list_select` / `_on_keymap_list_focus_index_change` / `_on_keymap_list_double_click` / `_add_keymap` / `_edit_selected_keymap` / `_delete_keymap` / `_select_keymap`）、`__init__` 配線が使う `activate_keymap_by_id`、KeyboardWindow 配線が使う `assign_keymap_from_keyboard_ui` / `clear_keymap_from_keyboard_ui`、残留コード（S6 の `_selected_keymap_for_io`、S9 の `_update_status`）が使う `_selected_keymap_list_index` / `_refresh_keymap_list_ui` / `_get_active_keymap_text`、tests_ui が使う `_refresh_keymap_list_ui`。
- **完了条件**: §1.3-5 の grep → 標準検証（tests_ui の `test_keymap_list_shows_active_marker` を含む）→ 手動確認: キーマップの追加 → キーマップ変更（切替キー設定）→ 選択 → 削除、キーボードUI上での左クリック割当・右クリッククリア。
- **リスク / 戻し方**: 中〜大。`git revert HEAD`。
- **依存**: S2、S4、S7

---

### S9: トリガー/シーケンスパネルとステータス表示を `TriggerPanelController` として抽出

- **対象メソッド**（→ `keyseq/presentation/trigger_panel_controller.py` の `TriggerPanelController`）:
  選択系: `_sync_trigger_selection_to_views` / `_set_selected_trigger_index` / `_select_trigger_by_key` / `_selected_trigger_index` / `_selected_trigger` / `_selected_trigger_key` / `_on_trigger_list_focus_index_change` / `_on_trigger_double_click`
  表示系: `_refresh_triggers` / `_refresh_actions` / `_select_next_action_row` / `_sync_suppress_checkbox` / `_sync_run_to_end_ui` / `_update_status` / `_get_next_action_summary`
  編集系: `add_trigger` / `rename_trigger` / `delete_trigger` / `_selected_action_index` / `add_action` / `edit_action` / `delete_action` / `move_action` / `_on_action_list_select` / `_on_action_list_focus_index_change` / `_on_action_double_click` / `update_suppress` / `update_run_to_end` / `update_run_to_end_delay`
- **問題**: App 最大の UI ロジック群（約 500 行）。
- **どう変えるか**: §1.3 のレシピどおり。注意点:
  - `self._selected_trigger_idx` / `self._indices` は `AppState` 由来の App プロパティであり、**App に残す**。コントローラからは `self._app._selected_trigger_idx` で読み書きする。
  - `_update_status` は `hook_active` / `custom_input_enabled`（S11 まで App の属性）と `_get_active_keymap_text`（S8 ファサード）を `self._app.` 経由で読む。
  - `_dialog_result` は ActionDialog が `parent._dialog_result` に書く外部契約なので **App の属性のまま**。コントローラは `self._app._dialog_result` で読む。
  - `_refresh_triggers` 内の `_refresh_keymap_list_ui` / `_refresh_keyboard_window` 呼び出しは `self._app.` 経由。
  - 委譲を残すもの: views がバインドする多数（`add_trigger` / `rename_trigger` / `delete_trigger` / `update_suppress` / `update_run_to_end` / `update_run_to_end_delay` / `add_action` / `edit_action` / `delete_action` / `move_action` / `_on_trigger_list_focus_index_change` / `_on_trigger_double_click` / `_on_action_list_select` / `_on_action_list_focus_index_change` / `_on_action_double_click`）、`__init__` 配線（SequenceRunner）が使う `_select_trigger_by_key` / `_refresh_actions` / `_update_status`、残留・他コントローラが使う `_refresh_triggers` / `_selected_trigger` / `_set_selected_trigger_index` / `_selected_trigger_key`、tests_ui が使うもの一式。
- **完了条件**: §1.3-5 の grep → 標準検証（tests_ui のトリガー系テスト全部）→ 手動確認: トリガー追加/変更/削除、アクション追加/編集/削除/上下移動、suppress・連続実行・間隔(ms) の切替、省略表示との選択共有。
- **リスク / 戻し方**: 中〜大（触る面積が最大）。`git revert HEAD`。
- **依存**: S2、S4、S8

---

### S10: フック制御を `HookController` として抽出（最後に実施）

- **対象メソッド**（→ `keyseq/presentation/hook_controller.py` の `HookController`）:
  `suspend_hook_for_dialog` / `resume_hook_after_dialog` / `_get_hook_pause_count` / `start_hook` / `stop_hook` / `toggle_hook` / `toggle_custom_input_enabled` / `toggle_triggers_enabled` / `_validate_hook_configuration` / `_on_input_event` / `_sync_hook_toggle_buttons` / `_sync_trigger_toggle_buttons` / `_show_action_error`
  移動する状態: `hook_active` / `custom_input_enabled` / `_hook_suspend_count` / `_hook_was_active_before_dialog` / `_error_dialog_open`
  **App に残すもの**: `_get_send_guard_count`（ActionExecutor への配線グルー）、`_perform_action`、`validate_hotkey`（dialogs が `parent.validate_hotkey` で使う外部契約）、`_find_trigger_by_key` / `_find_keymap_target` / `_find_keymap_switch_target_id`（配線用の薄いヘルパ）
- **問題**: フック開始/停止・サスペンドカウンタ・イベント入口という安全機構の中枢。**suppress と send guard の仕組みを壊すと無限ループや「キーが全部死ぬ」事故になるため、他の全項目が安定してから最後に行う。**
- **どう変えるか**: §1.3 のレシピどおり。特別な注意:
  - `hook_active` / `custom_input_enabled` は多数の残留コード・コントローラ・tests_ui から読まれるため、App に**プロパティ**を残す。書き込みは元コードで `App` 自身しか行っていないため getter のみで良いか必ず `git grep -nE "hook_active\s*=|custom_input_enabled\s*=" -- keyseq` で確認し、コントローラ外からの代入が残っていれば setter も用意する。`App.__init__` にある初期化代入（`self.hook_active = False` / `self.custom_input_enabled = True`）は削除し、コントローラの `__init__` で初期化する。
  - `suspend_hook_for_dialog` / `resume_hook_after_dialog` は dialogs / keyboard_window / 各コントローラが使う最重要ファサード。**必ず委譲を残す**（tests_ui の `test_hook_suspend_counter_nesting` が契約を固定している）。
  - `_on_input_event` は `HookCoordinator.start()` に渡されるコールバック。配線（`start_hook` 内）ごと移動するので参照は自然に閉じるが、`git grep -n "_on_input_event" -- keyseq` で他参照が無いことを確認する。
  - `_show_action_error` は `__init__` の ActionExecutor 配線ラムダから参照される → 委譲を残す。
- **完了条件**: §1.3-5 の grep → 標準検証 → **手動確認（必須・入念に）**: `py main.py` で、
  1. トリガー（hotkey: `ctrl+c` など）を登録して開始（フックON）→ トリガーキーで実行される → 停止（フックOFF）
  2. フックON中にアクション編集ダイアログを開く → トリガーキーを押しても発火しない → ダイアログを閉じるとフックが自動復帰して発火する（ネスト対応の確認: ダイアログ from ダイアログでも復帰は最後の 1 回）
  3. 停止キーを設定してフックON → 停止キーでフックが止まる
  4. トグルキーで通常トリガーの有効/無効が切り替わる
  5. suppress チェックの ON/OFF でキーが飲まれる/通る
  6. text アクションを実行しても**送信された文字で再トリガーしない**（send guard の確認: トリガーキーと同じ文字を text で送る設定にして確認）
- **リスク / 戻し方**: **最大**。手動確認 6 項目のうち 1 つでも異常があれば即 `git revert HEAD` し、原因を特定してから再試行。**フックが暴走した場合（キー入力が効かなくなった場合）に備え、確認前に停止キーを必ず設定しておくこと。**
- **依存**: S1〜S9 すべて

---

### S11: 最終検証・実測とドキュメント更新

- **やること**:
  1. 標準検証をフルで実行。
  2. `(Get-Content keyseq/presentation/app.py | Measure-Object -Line).Lines` を実測し報告する。**目安は 1,000 行未満**（委譲メソッドが多いため 700〜900 行程度になる見込み。超えていても完了条件違反ではないが、本体ロジックが残っていないか §1.3-5 の grep を再確認すること）。
  3. `instruction/common/codebase_map.md` を更新する（AGENTS.md の「クラス構成が変わったらドキュメント更新」ルールに従う）。「主な責務」節の App の項を以下の趣旨で書き換え、新モジュール一覧を追記する:
     - App: Tk ルート・View 切替・メニュー・各コントローラの生成と配線・外部（views/dialogs）向けファサード
     - ConfigPaths: 設定ファイルの配置規約とパス解決
     - DirtyStateTracker: 未保存状態の一元管理
     - SingleKeyCaptureController: 停止キー/トグルキーのキャプチャ
     - ConfigIoController: 構成セット・個別JSONの保存/読込フロー
     - LayoutController: キーボードレイアウトと KeyboardWindow 管理
     - KeymapPanelController: キーマップ管理パネル
     - TriggerPanelController: トリガー/シーケンスパネルとステータス表示
     - HookController: フック開始/停止・サスペンド・入力イベント入口
  4. 最終報告: コミット一覧（`git log --oneline <ベースライン>..HEAD`）、app.py の行数推移、スキップ・失敗項目の有無。
- **完了条件**: 上記すべて完了し `git status` クリーン。
- **依存**: S1〜S10 のうち実施したすべて

---

## 4. やらないことリスト（実行者は以下を行ってはならない）

1. **views.py / dialogs.py / keyboard_window.py の変更**。バインド先をコントローラへ付け替えたくなっても行わない（ファサード維持が本計画の安全装置。付け替えは次期計画）。
2. **コントローラ同士の直接参照**。相互作用は必ず App ファサード経由。
3. **挙動変更・バグ修正・機能追加**。計画01 付録の潜在バグも直さない。エラーメッセージ・フラッシュ文言・ダイアログ文言は 1 文字も変えない。
4. **メソッドの統合・分解**（S5 の 2 系統統合を除く）。移動は 1 メソッド = 1 メソッドの機械移設。
5. **`self._app.data` 等のフィールドへのキャッシュ**（§1.3-2 の禁止事項）。
6. **JSON 仕様・保存フォーマットの変更**、依存ライブラリの追加・更新（pytest 等の導入禁止）。
7. **application / domain / infrastructure 層の変更**（本計画は presentation 層内の再配置のみ。ただし S1 のデッドコード削除と S11 のドキュメント更新は除く）。
8. **tests/ の既存テストの期待値変更**。tests_ui のテストも変更禁止（ファサード契約そのものであるため。落ちたら実装側が間違っている）。
9. **一括整形・リネーム**（§1.3 の「先頭 `_` 除去」以外の改名禁止）。
10. **フックを張ったままの放置**。手動確認でフックONにしたら必ず停止してから終了する。

## 5. 補足: 本計画完了後の姿と、その先（参考情報。作業対象ではない）

- 完了後の `keyseq/presentation/`: `app.py`（組み立て + ファサード）+ コントローラ 7 ファイル + `listbox_utils.py` / `config_paths.py` / `tk_keys.py` / 既存 View 群。各ファイル 500 行未満。
- 次期計画の候補（今回はやらない）: views のバインド先をコントローラへ直接付け替えてファサード委譲を段階的に削減する／コントローラの `app` 依存を明示的なインターフェイスに絞る／`_` 付きファサード名の公開化。

## 6. 実行者への指示文（この計画書を渡すときにそのままコピペする)

```
あなたはこのリポジトリのリファクタリング実行者です。
instruction/modified_proposal/02_app_split_plan.md を最初から最後まで読み、記載どおりに作業してください。

厳守事項:
- まず「項目 0」の前提条件チェックを行う。計画01が未完了なら作業せず、その旨を報告して終了する。
- 項目 0 → S1 → S2 → … → S11 の順に 1 項目ずつ実施する。1 項目 = 1 コミット。
- 各項目は §1.3「共通移設手順」のレシピに厳密に従う。移動対象メソッドごとに git grep で参照元を確認し、
  外部参照があるものは App に同名の委譲を残す。
- 各項目の「完了条件」（grep + 標準検証 + 手動確認）をすべて満たしてからコミットする。
  満たせない場合は変更を破棄（git checkout -- . / git revert）して中断し、何がどう失敗したかを報告する。
- 「やらないことリスト」に該当する変更は、改善に見えても行わない。
  特に views.py / dialogs.py / keyboard_window.py は 1 文字も変更しない。
- tests/ と tests_ui/ のテスト期待値は変更禁止（テストが落ちたら実装側の誤り）。
- Python は py コマンドで実行する。挙動を変えないことが最優先。
- S10（フック制御）の手動確認 6 項目は省略禁止。確認前に必ず停止キーを設定すること。

最終成果物:
- refactor/02-app-split ブランチ上の一連のコミット
- 実施項目 / スキップ項目 / app.py の行数推移 / 各項目の検証結果を列挙した報告
```
