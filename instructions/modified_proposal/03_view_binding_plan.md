# リファクタリング計画書 03（バインド先のコントローラ直接参照化・挙動不変）

- 作成日: 2026-07-05
- **前提: 計画書 02（`instruction/modified_proposal/02_app_split_plan.md`）の全項目が完了していること**（main の `keyseq/presentation/` にコントローラ 7 ファイル + `config_paths.py` / `listbox_utils.py` が存在する状態）。本計画も行番号は記載しない。対象は必ずクラス名・メソッド名で特定すること。
- 実行環境の前提: Windows 11 / PowerShell / Python は `py` ランチャで起動する（素の `python` は使わない）。
- 本計画の性質: **機能追加・仕様変更・バグ修正は一切行わない。ロジックの移動・統合も行わない。** 目的は、計画 02 が安全装置として残した「App ファサード（1〜3 行の委譲メソッド・プロパティ約 130 個）」を、参照元（views / dialogs / keyboard_window / `App.__init__` の配線 / コントローラ間参照 / tests_ui）の**参照先付け替え**によって不要化し、削除することである。
- 併読必須: `AGENTS.md`、`instruction/common/architecture_rules.md`、`instruction/common/dev_rules.md`、`instruction/common/file_organization_rules.md`。

---

## 1. 現状理解（実行者への文脈共有）

### 1.1 計画 02 完了後の app.py の内訳

`keyseq/presentation/app.py` は約 990 行・App のメソッド 162 個。うち **134 個が 3 行以下の委譲メソッドまたはプロパティ**であり、実ロジックは約 350 行しかない（`__init__` 約 127 行、`_build_ui` / `_build_menu` / `_build_status_area` 約 126 行、`validate_hotkey` 31 行、View 切替・フォント・ショートカット・フラッシュ表示など）。

つまり app.py 縮小の残り手段は「ロジックの抽出」ではなく「**委譲ボイラープレートの削除**」であり、それには参照元の付け替えが必要。これは計画 02 の §5 が「次期計画候補」と明記した作業である。

### 1.2 コントローラの保持名（`App.__init__` で生成）

| 現在の属性名（私有） | クラス | 本計画後の公開名 |
|---|---|---|
| `self.paths` | `ConfigPaths` | `self.paths`（変更なし・既に公開） |
| `self._dirty_tracker` | `DirtyStateTracker` | `self.dirty_tracker` |
| `self._stop_key_capture` | `SingleKeyCaptureController` | `self.stop_key_capture` |
| `self._toggle_key_capture` | `SingleKeyCaptureController` | `self.toggle_key_capture` |
| `self._config_io` | `ConfigIoController` | `self.config_io` |
| `self._layout` | `LayoutController` | `self.layout` |
| `self._keymap_panel` | `KeymapPanelController` | `self.keymap_panel` |
| `self._trigger_panel` | `TriggerPanelController` | `self.trigger_panel` |
| `self._hook` | `HookController` | `self.hook` |

### 1.3 外部参照の全体像（付け替え対象）

1. **views.py**: `command=app.save_keymap_set` / `bind(..., app._on_keymap_list_select)` 等、約 45 箇所のメソッド参照（Tk 変数・ウィジェット生やしは本計画では触らない → 計画 04）。
2. **dialogs.py**: `parent.suspend_hook_for_dialog()`（5 箇所）/ `parent.resume_hook_after_dialog()`（5 箇所）/ `parent.validate_hotkey()`（2 箇所）/ `parent.data`（3 箇所）/ `parent._dialog_result`（2 箇所）。
3. **keyboard_window.py**: `master.suspend_hook_for_dialog` / `master.resume_hook_after_dialog`（`hasattr` ガード付き・各 1 箇所）。
4. **`App.__init__` の配線**: `KeyStateManager(resolve_scan_code=self._resolve_key_name_from_scan_code)`、`InputRouter(... on_stop_hook=self.stop_hook, on_toggle_mode=self.toggle_custom_input_enabled, get_hook_pause_count=self._get_hook_pause_count, ...)`、`SequenceRunner(... select_trigger=self._select_trigger_by_key, refresh_actions=self._refresh_actions, update_status=self._update_status, ...)` などのコールバック配線。
5. **コントローラ内部**: `self._app._set_dirty(...)` / `self._app._refresh_keyboard_window()` / `self._app.hook_active` 等、ファサード経由の相互参照。
6. **tests_ui/test_app_ui_flows.py**: `app._refresh_triggers()` / `app._set_dirty(...)` / `app._start_stop_key_capture()` 等、旧ファサード契約を呼ぶテスト。

### 1.4 分割方針（本計画の設計判断）

- **参照の付け替えのみ**。メソッド本体は 1 行も書き換えない（呼び出し式の参照先だけ変える）。移動・統合・分解は行わない。
- 付け替え後の参照形は `app.<コントローラ公開名>.<公開メソッド>`（例: `app.config_io.save_keymap_set`）。**コントローラのインスタンスを変数・フィールドに取り出して保持することは禁止**（`io = app.config_io` のようなキャッシュ不可。常に App 経由で解決する。データ読込などで将来コントローラを差し替え可能に保つため）。
- コントローラ間の相互参照も同じ形に付け替える: `self._app._set_dirty(True)` → `self._app.dirty_tracker.set_dirty(True)`。**コントローラが他コントローラをフィールドに保持することは引き続き禁止。**
- **App に残すメソッド**（削除してはならない。実ロジックまたは複数コントローラの調整役）:
  - Tk ルート・組み立て: `_build_ui` / `_build_menu` / `_build_status_area` / `_bind_menu_shortcuts` / `on_close` / `show_full_view` / `show_compact_view` / `_apply_compact_geometry` / `_restore_full_geometry` / `_apply_always_on_top`
  - 実ロジック: `validate_hotkey`（dialogs の外部契約。31 行の実体）/ `_set_flash_message` / `_update_file_status` / `_load_startup_settings` / `_sync_control_vars_from_data` / `set_ui_font_delta` / `_coerce_font_delta` / `open_preset_manager` / `_is_menu_shortcut_enabled` / ショートカットハンドラ群（`_on_shortcut_*`）
  - 調整役（複数コントローラをまたぐ既存ロジック。本計画で**公開名化する**が削除しない）:
    - `_toggle_stop_key_capture` / `_toggle_toggle_key_capture`（相互排他: 片方を止めてから他方を開始）→ `toggle_stop_key_capture` / `toggle_toggle_key_capture`
    - `_start_stop_key_capture` / `_start_toggle_key_capture`（同上の相互排他入り）→ `start_stop_key_capture` / `start_toggle_key_capture`
    - `_mark_sequence_dirty` / `_mark_keymap_dirty`（「引数 None ならアクティブ対象を解決する」デフォルト解決）→ `mark_sequence_dirty` / `mark_keymap_dirty`
  - 配線用薄ヘルパ: `_get_send_guard_count` / `_perform_action` / `_find_trigger_by_key` / `_find_keymap_target` / `_find_keymap_switch_target_id`
  - 外部契約の状態: `data` / `state` / `keymap_set_path` / `startup_path` / `_startup_settings` / `_dialog_result` / Tk 変数群（`stop_key_var` 等）/ View が生やすウィジェット参照（`keymap_listbox` 等）— **すべて現状のまま**
- **削除対象**: 上記「残すもの」以外の委譲メソッド・プロパティ全部。ただし削除は必ず「参照 0 件を grep で確認してから」行う（§1.5）。

### 1.5 共通付け替え手順（全項目で必ずこの手順に従う）

各項目は「対象グループの委譲メソッド」ごとに次を行う。

1. `git grep -n "<委譲名>" -- keyseq tests tests_ui` で参照元をすべて列挙する。
2. 参照元それぞれを `app.<コントローラ公開名>.<公開メソッド>` 形式（コントローラ内からは `self._app.<コントローラ公開名>.<公開メソッド>`）へ書き換える。委譲メソッドが引数の詰め替えをしている場合（例: 計画 02 S3 の状態依存 3 メソッド、S4 のデフォルト解決）は**付け替えず、App に公開名で残す**（§1.4 の調整役）。
3. 再度 `git grep -n "<委譲名>" -- keyseq tests tests_ui` を実行し、**残る参照が App 内の定義 1 件のみ**になったことを確認してから、App の委譲メソッド／プロパティを削除する。参照が残っている場合は削除しない（付け替え漏れ）。
4. 標準検証（§2 で定義）と項目ごとの手動確認を行う。

### 1.6 tests_ui の扱い（計画 02 の禁止事項の明示的解除）

計画 02 は「tests_ui は変更禁止（ファサード契約そのものであるため）」と定めた。**本計画はその契約自体を『コントローラ公開メソッド』へ移すため、tests_ui の参照経路の書き換えを許可する（項目 V1 でのみ行う）。** ただし**アサーション（検証している挙動・期待値）は 1 つも変えてはならない**。変えるのは呼び出し経路のみ。

---

## 2. 項目 V0: 前提確認とブランチ作成（最初に必ず実行）

```powershell
git status                          # クリーンであること
git rev-parse HEAD                  # ベースラインとして記録（報告書に残す）

# 計画02の完了確認
git grep -n "class HookController" -- keyseq/presentation/hook_controller.py         # 1 件
git grep -n "class TriggerPanelController" -- keyseq/presentation/trigger_panel_controller.py  # 1 件
git grep -n "self._hook = HookController" -- keyseq/presentation/app.py              # 1 件

py -m compileall -q keyseq main.py
py -m unittest discover -s tests -v      # 全緑
py -m unittest discover -s tests_ui -v   # 全緑（ウィンドウが一瞬開く）
py -m tests.smoke_app                    # SMOKE OK
```

1 つでも満たさなければ中断して報告する。満たしたら:

```powershell
git switch -c refactor/03-view-binding
```

> **標準検証** =
> `py -m compileall -q keyseq main.py`
> → `py -m unittest discover -s tests -v`（全緑）
> → `py -m unittest discover -s tests_ui -v`（全緑）
> → `py -m tests.smoke_app`（**SMOKE OK** の表示）

---

## 3. 作業項目リスト（この順に実行。1 項目 = 1 コミット）

> 完了条件を満たせなければ `git checkout -- .` / `git revert HEAD` で戻し、中断して報告する。

---

### V1: コントローラ属性の公開名化と tests_ui の新契約化

- **どう変えるか**:
  1. `App.__init__` の §1.2 の表のとおり、コントローラ保持属性を公開名へリネームする（`self._hook` → `self.hook` 等 8 個）。`git grep -nE "_hook\b|_trigger_panel|_keymap_panel|_config_io|_layout\b|_dirty_tracker|_stop_key_capture|_toggle_key_capture" -- keyseq` で app.py 内の全参照（委譲メソッドの本体）を追従させる。
  2. App の調整役メソッドを公開名化する（§1.4: `toggle_stop_key_capture` / `toggle_toggle_key_capture` / `start_stop_key_capture` / `start_toggle_key_capture` / `mark_sequence_dirty` / `mark_keymap_dirty`）。旧 `_` 付き名の参照元（views / コントローラ / tests_ui）をすべて追従させ、旧名は残さない。
  3. `tests_ui/test_app_ui_flows.py` の呼び出し経路を新契約へ書き換える。**アサーションは変更禁止**。対応表:
     - `app._refresh_triggers()` → `app.trigger_panel.refresh_triggers()`
     - `app._refresh_actions()` → `app.trigger_panel.refresh_actions()`
     - `app._set_selected_trigger_index(n)` → `app.trigger_panel.set_selected_trigger_index(n)`
     - `app._update_status()` → `app.trigger_panel.update_status()`
     - `app._set_dirty(b)` → `app.dirty_tracker.set_dirty(b)`
     - `app._get_hook_pause_count()` → `app.hook.get_hook_pause_count()`
     - `app._start_stop_key_capture()` → `app.start_stop_key_capture()`（App の調整役・公開名）
     - `app._stop_stop_key_capture(cancel=True)` → `app.stop_key_capture.stop(cancel=True)`
     - `app._capturing_stop_key` → `app.stop_key_capture.capturing`
     - `app._refresh_keymap_list_ui()` → `app.keymap_panel.refresh_keymap_list_ui()`
     - `app._compact_mode` / `app.suspend_hook_for_dialog()` / `app.resume_hook_after_dialog()` / `app.show_compact_view()` / `app.show_full_view()` / `app.open_keyboard_window()` / `app.keyboard_window` → この項目では変更しない（後続項目で付け替えるものは、その項目で書き換える）。
  4. **この項目では委譲メソッドの削除は行わない**（公開名化とテスト経路変更のみ。全部残っていても二重経路で動く）。
- **完了条件**: `git grep -nE "self\._hook\b|self\._trigger_panel|self\._keymap_panel|self\._config_io|self\._layout\b|self\._dirty_tracker|self\._stop_key_capture|self\._toggle_key_capture" -- keyseq` が 0 件 → 標準検証。
- **リスク / 戻し方**: 低（機械的リネーム。スモークで即検出）。`git revert HEAD`。
- **依存**: V0

---

### V2: フック制御系の付け替えと委譲削除

- **対象委譲**: `toggle_hook` / `toggle_triggers_enabled` / `toggle_custom_input_enabled` / `start_hook` / `stop_hook` / `suspend_hook_for_dialog` / `resume_hook_after_dialog` / `_get_hook_pause_count` / `_show_action_error` / `_sync_hook_toggle_buttons` / `_sync_trigger_toggle_buttons` / `_validate_hook_configuration`（残存していれば）、プロパティ `hook_active` / `custom_input_enabled`
- **どう変えるか**（§1.5 の手順で 1 委譲ずつ）:
  - views.py: `command=app.toggle_hook` → `command=app.hook.toggle_hook`（FullView / CompactView 各 1）、`command=app.toggle_triggers_enabled` → `app.hook.toggle_triggers_enabled`（同）。
  - dialogs.py: `parent.suspend_hook_for_dialog()` → `parent.hook.suspend_hook_for_dialog()`（5 箇所）、`parent.resume_hook_after_dialog()` → `parent.hook.resume_hook_after_dialog()`（5 箇所）。
  - keyboard_window.py: `hasattr(master, "suspend_hook_for_dialog")` ガードごと `master.hook.suspend_hook_for_dialog` 系に書き換える（`hasattr(master, "hook")` ガードに変更。ガードの有無という挙動は維持する）。
  - `App.__init__` 配線: `on_stop_hook=self.stop_hook` → `self.hook.stop_hook`、`on_toggle_mode=self.toggle_custom_input_enabled` → `self.hook.toggle_custom_input_enabled`、`get_hook_pause_count=self._get_hook_pause_count` → `self.hook.get_hook_pause_count`、`get_custom_input_enabled=lambda: bool(self.custom_input_enabled)` → `lambda: bool(self.hook.custom_input_enabled)`、`on_action_error=lambda ...: self._show_action_error(...)` → `self.hook.show_action_error(...)`。
    **注意**: コントローラ生成（§計画 02 1.4 の生成ブロック）は `KeyStateManager` / `InputRouter` の生成より後にある。配線がラムダ・メソッド参照であるため呼び出し時解決になり順序問題は起きないが、**メソッド参照渡し（`self.hook.stop_hook` を直接渡す形）は生成順に依存する**。`InputRouter` 生成時点で `self.hook` が未生成なら、コントローラ生成ブロックを `InputRouter` 生成より前へ移すのではなく、**ラムダで包む**（`on_stop_hook=lambda: self.hook.stop_hook()`）こと。生成ブロックの位置は動かさない。
  - コントローラ内・App 残留コード内の `self._app.hook_active` / `self._app.custom_input_enabled` / `self._app.suspend_hook_for_dialog()` 等 → `self._app.hook.hook_active` / `self._app.hook.custom_input_enabled` / `self._app.hook.suspend_hook_for_dialog()`。
  - tests_ui の `app.suspend_hook_for_dialog()` / `app.resume_hook_after_dialog()` → `app.hook.suspend_hook_for_dialog()` / `app.hook.resume_hook_after_dialog()`（アサーション不変）。
  - 付け替え完了後、§1.5-3 の grep 確認を経て App から当該委譲・プロパティを削除する。
- **完了条件**: 各委譲名の grep が定義 0 件 → 標準検証 → **手動確認（必須・計画 02 S10 と同じ 6 項目）**: フック ON/OFF、ダイアログ中の自動停止と復帰（ネスト含む）、停止キー、トグルキー、suppress、send guard（text アクションの再トリガー無し）。**確認前に停止キーを必ず設定すること。**
- **リスク / 戻し方**: **最大**（安全機構の参照経路変更）。異常があれば即 `git revert HEAD`。
- **依存**: V1

---

### V3: キーキャプチャ系の付け替えと委譲削除

- **対象委譲**: `clear_stop_key` / `clear_toggle_key` / `_stop_stop_key_capture` / `_stop_toggle_key_capture` / `_on_stop_key_capture_keypress` / `_on_toggle_key_capture_keypress`（残存していれば）、プロパティ `_capturing_stop_key` / `_capturing_toggle_key`
- **どう変えるか**:
  - views.py: `command=app._toggle_stop_key_capture` → `command=app.toggle_stop_key_capture`（V1 で公開名化済みの App 調整役。コントローラ直ではない点に注意）、`command=app.clear_stop_key` → `command=app.stop_key_capture.clear`。トグルキー側も同様。
  - App 残留コード（`_is_menu_shortcut_enabled` / `show_compact_view` 等）の `self._capturing_stop_key` → `self.stop_key_capture.capturing`（トグル側も同様）。
  - 付け替え後、grep 確認を経て委譲・プロパティを削除。**`toggle_stop_key_capture` / `start_stop_key_capture` 等の相互排他調整役 4 メソッドは削除しない。**
- **完了条件**: grep 0 件 → 標準検証 → 手動確認: 計画 02 S5 の 5 項目（取得 → F9 確定、Esc キャンセル、トグル側取得、重複エラーダイアログ、クリア）。
- **リスク / 戻し方**: 中。`git revert HEAD`。
- **依存**: V2

---

### V4: 保存・読込系の付け替えと委譲削除

- **対象委譲**: `new_config` / `save_keymap_set` / `save_as` / `load_keymap_set_from` / `import_config` / `export_config` / `restore_default` / `set_startup_keymap_set` / `save_selected_keymap` / `save_selected_keymap_as` / `load_keymap_file` / `save_trigger_set_file` / `save_trigger_set_file_as` / `load_trigger_set_file` / `save_selected_sequence` / `save_selected_sequence_as` / `load_sequence_file` / `_confirm_save_if_dirty` / `_write_startup` / `_apply_loaded_data_to_ui`、ダーティ系委譲 `_set_dirty` / `_has_unsaved_changes` / `_sync_dirty_state` / `_clear_individual_dirty_flags` / `_has_individual_dirty`、プロパティ `_is_dirty` / `_config_dirty` / `_trigger_set_source_path` / `_trigger_set_imported` / `_trigger_set_dirty`（残存していれば）、パス系委譲（`_preferred_keymap_set_path` ほか計画 02 S3 の全ファサード。**状態依存 3 メソッド `_suggest_keymap_set_dialog_path` / `_suggest_keymap_set_dialog_dir` / `_keymap_set_file_stem` は引数詰め替えを含むため App に公開名で残す**: `suggest_keymap_set_dialog_path` 等）
- **どう変えるか**:
  - views.py: ファイル系ボタン 17 箇所を `app.config_io.<公開名>` へ（例: `command=app.save_keymap_set` → `command=app.config_io.save_keymap_set`）。
  - `App._build_menu`: メニュー項目の `command=self.new_config` 等を `self.config_io.new_config` 等へ。ショートカットハンドラ（`_on_shortcut_save` 等）内の呼び出しも同様。
  - `App.on_close` の `self._confirm_save_if_dirty()` → `self.config_io.confirm_save_if_dirty()`。`set_ui_font_delta` 内の `_write_startup` → `self.config_io.write_startup()`。
  - コントローラ内の `self._app._set_dirty(...)` → `self._app.dirty_tracker.set_dirty(...)`、`self._app._preferred_keymap_set_path()` → `self._app.paths.preferred_keymap_set_path()` 等、ダーティ系・パス系の相互参照を一括付け替え。
  - 付け替え後、grep 確認を経て委譲・プロパティを削除。
- **完了条件**: grep 0 件 → 標準検証 → **手動確認（必須・計画 02 S6 と同じ一巡）**: 新規作成 → トリガー追加 → 保存 → 読込 → Export → Import → 別名で保存。各操作後のステータスバー表示が従来どおり。
- **リスク / 戻し方**: 中〜大（最重要データ経路）。`git revert HEAD`。
- **依存**: V1（V2/V3 とは独立だが、順番どおりの実施を推奨）

---

### V5: レイアウト系の付け替えと委譲削除

- **対象委譲**: `open_keyboard_window` / `on_keyboard_layout_selected` / `add_external_keyboard_layout` / `delete_keyboard_layout` / `toggle_keyboard_show_physical_key_labels` / `_refresh_keyboard_window` / `_reload_keyboard_layouts` / `_sync_keyboard_layout_controls` / `_resolve_key_name_from_scan_code` ほかレイアウト系委譲・プロパティ（`keyboard_window` プロパティ含む）
- **どう変えるか**:
  - views.py: `command=app.open_keyboard_window` → `app.layout.open_keyboard_window`（2 箇所）、`bind("<<ComboboxSelected>>", app.on_keyboard_layout_selected)` → `app.layout.on_keyboard_layout_selected`（2 箇所）。
  - `App._build_menu`: レイアウト系メニュー項目を `self.layout.<公開名>` へ。
  - `App.__init__` 配線: `KeyStateManager(resolve_scan_code=self._resolve_key_name_from_scan_code)` / `InputRouter(... resolve_scan_code=...)` → **ラムダで包んで** `lambda sc: self.layout.resolve_key_name_from_scan_code(sc)`（`KeyStateManager` 生成時点で `self.layout` が未生成のため。V2 の注意と同じ理由）。
  - コントローラ内の `self._app._refresh_keyboard_window()` → `self._app.layout.refresh_keyboard_window()` 等。
  - tests_ui: `app.open_keyboard_window()` → `app.layout.open_keyboard_window()`。`app.keyboard_window` は LayoutController のフィールドへ → `app.layout.keyboard_window`（アサーション不変）。
  - 付け替え後、grep 確認を経て委譲・プロパティを削除。
- **完了条件**: grep 0 件 → 標準検証 → 手動確認: レイアウトコンボ切替、キーボード UI 開閉、外部レイアウト追加→削除（確認後、構成セットへ変更を残さない）。
- **リスク / 戻し方**: 中。`git revert HEAD`。
- **依存**: V1

---

### V6: キーマップパネル系の付け替えと委譲削除

- **対象委譲**: `_on_keymap_list_select` / `_on_keymap_list_focus_index_change` / `_on_keymap_list_double_click` / `_add_keymap` / `_edit_selected_keymap` / `_delete_keymap` / `_select_keymap` / `_refresh_keymap_list_ui` / `activate_keymap_by_id` / `assign_keymap_from_keyboard_ui` / `clear_keymap_from_keyboard_ui` / `_get_active_keymap_text` ほかキーマップ系委譲
- **どう変えるか**:
  - views.py: キーマップ Listbox の bind 3 箇所とボタン 4 箇所を `app.keymap_panel.<公開名>` へ。
  - `App.__init__` 配線: `on_select_keymap=lambda keymap_id: self.activate_keymap_by_id(...)` → `self.keymap_panel.activate_keymap_by_id(...)`。
  - LayoutController 内の KeyboardWindow 配線（`assign_keymap_from_keyboard_ui` / `clear_keymap_from_keyboard_ui`）→ `self._app.keymap_panel.<公開名>`。
  - コントローラ内・App 残留コードの `self._app._refresh_keymap_list_ui()` / `self._app._get_active_keymap_text()` 等 → `self._app.keymap_panel.<公開名>`。
  - tests_ui: V1 で付け替え済み（`app.keymap_panel.refresh_keymap_list_ui()`）。
  - 付け替え後、grep 確認を経て委譲を削除。
- **完了条件**: grep 0 件 → 標準検証 → 手動確認: キーマップ追加 → 変更 → 選択 → 削除、キーボード UI 上の左クリック割当・右クリッククリア。
- **リスク / 戻し方**: 中。`git revert HEAD`。
- **依存**: V1、V5（KeyboardWindow 配線）

---

### V7: トリガー/シーケンスパネル系の付け替えと委譲削除

- **対象委譲**: `add_trigger` / `rename_trigger` / `delete_trigger` / `update_suppress` / `update_run_to_end` / `update_run_to_end_delay` / `add_action` / `edit_action` / `delete_action` / `move_action` / `_on_trigger_list_focus_index_change` / `_on_trigger_double_click` / `_on_action_list_select` / `_on_action_list_focus_index_change` / `_on_action_double_click` / `_refresh_triggers` / `_refresh_actions` / `_update_status` / `_set_selected_trigger_index` / `_select_trigger_by_key` / `_selected_trigger` / `_sync_trigger_selection_to_views` ほかトリガー系委譲
- **どう変えるか**:
  - views.py: トリガー/アクション Listbox の bind 計 6 箇所とボタン群を `app.trigger_panel.<公開名>` へ。`move_action` は `lambda: app.trigger_panel.move_action(-1)` の形（元のラムダ構造を維持）。
  - `App.__init__` 配線（SequenceRunner）: `select_trigger=self._select_trigger_by_key` → `lambda key: self.trigger_panel.select_trigger_by_key(key)`、`refresh_actions=self._refresh_actions` → `lambda: self.trigger_panel.refresh_actions()`、`update_status=self._update_status` → `lambda: self.trigger_panel.update_status()`（生成順の理由で必ずラムダ。V2 の注意と同じ）。
  - コントローラ内の `self._app._selected_trigger()` / `self._app._refresh_triggers()` / `self._app._update_status()` 等 → `self._app.trigger_panel.<公開名>`。App の `mark_sequence_dirty`（調整役）内の `self._selected_trigger()` も `self.trigger_panel.selected_trigger()` へ。
  - 付け替え後、grep 確認を経て委譲を削除。
- **完了条件**: grep 0 件 → 標準検証 → 手動確認: トリガー追加/変更/削除、アクション追加/編集/削除/上下移動、suppress・連続実行・間隔(ms)、フル⇔省略の選択共有。
- **リスク / 戻し方**: 中〜大（触る面積が最大）。`git revert HEAD`。
- **依存**: V1、V6

---

### V8: 残存委譲の総ざらいと Listbox ヘルパの直接使用化

- **どう変えるか**:
  1. `_focused_listbox_index` / `_sync_listbox_selection_to_focus`（計画 02 S2 の委譲）: 参照元コントローラを `listbox_utils` のモジュール関数直接呼び出し（`focused_listbox_index(self._app, ...)`）へ付け替え、App の委譲を削除する。
  2. app.py に対して機械的な総ざらいを行う:
     ```powershell
     # 3行以下の def を列挙し、本体が「self.<controller>.<name>(...)」1 行だけのものを目視で抽出
     git grep -nA2 "def " -- keyseq/presentation/app.py
     ```
     残っている委譲それぞれについて §1.5 の手順（参照列挙 → 付け替え → grep 0 件 → 削除）を適用する。**§1.4 の「App に残すメソッド」リストに該当するものは削除しない。**
  3. 判断に迷う委譲（引数詰め替えあり・複数コントローラ参照あり）は削除せず、報告書に「残した理由」を列挙する。
- **完了条件**: 標準検証 → 残存委譲の一覧と残した理由が報告に含まれること。
- **リスク / 戻し方**: 低〜中。`git revert HEAD`。
- **依存**: V2〜V7

---

### V9: 最終検証・実測とドキュメント更新

- **やること**:
  1. 標準検証をフルで実行。
  2. `(Get-Content keyseq/presentation/app.py | Measure-Object -Line).Lines` を実測し報告する。**目安は 500 行未満**（超えても完了条件違反ではないが、削除漏れの委譲が無いか V8-2 の総ざらいを再確認すること）。
  3. **手動確認の総仕上げ**: 計画 02 S10 の 6 項目（フック関連）をもう一度フルで実施。
  4. `instruction/common/codebase_map.md` を更新する: App の項を「Tk ルート・View 切替・メニュー・コントローラ生成と配線・調整役メソッド（キャプチャ相互排他、ダーティ既定解決）・dialogs 向け契約（`validate_hotkey` / `_dialog_result`）」に書き換え、「views/dialogs/keyboard_window はコントローラを `app.<名前>` 経由で直接参照する」ことを追記。
  5. 最終報告: コミット一覧、app.py の行数推移、削除した委譲の個数、残した委譲とその理由、スキップ・失敗項目の有無。
- **完了条件**: 上記すべて完了し `git status` クリーン。
- **依存**: V1〜V8

---

## 4. やらないことリスト（実行者は以下を行ってはならない）

1. **ロジックの移動・統合・分解**。本計画は参照先の付け替えと、参照が消えた委譲の削除のみ。メソッド本体の書き換えは行わない（呼び出し式の参照先変更を除く）。
2. **Widget クラス化・フォルダ再編・ファイル移動**（計画 04 の領分）。
3. **挙動変更・バグ修正・機能追加**。エラーメッセージ・フラッシュ文言・ダイアログ文言は 1 文字も変えない。
4. **コントローラ参照のキャッシュ**（`io = app.config_io` のような変数・フィールドへの取り出し。ラムダ内で都度 `self.<名前>` を解決する形は可）。
5. **コントローラが他コントローラをフィールドに保持すること**（参照は常に `self._app.<コントローラ名>` 経由）。
6. **§1.4「App に残すメソッド」の削除**。
7. **tests/ の既存テストの期待値変更、tests_ui のアサーション変更**（呼び出し経路の書き換えは V1 および各項目の指定範囲でのみ可）。
8. **JSON 仕様・保存フォーマットの変更**、依存ライブラリの追加・更新、application / domain / infrastructure 層の変更。
9. **フックを張ったままの放置**。手動確認でフック ON にしたら必ず停止してから終了する。
10. **git push**（ローカルコミットまで。push はユーザーが行う）。

## 5. 補足: 本計画完了後の姿と、その先（参考情報。作業対象ではない）

- 完了後の app.py: `__init__`（生成と配線）+ UI 組み立て（`_build_ui` / `_build_menu` / `_build_status_area`）+ View 切替 + 調整役メソッド数個 + dialogs 向け契約、で約 400〜500 行。
- 次期計画（04）: LabelFrame 単位の Widget クラス化（View ごとに専用 Widget、共通化しない）、`controllers/` / `views/` の種類別フォルダ再編、共有 Tk 変数ホルダー導入、App の組み立て専念化。`instruction/modified_proposal/04_widget_split_plan.md` を参照。

## 6. 実行者への指示文（この計画書を渡すときにそのままコピペする)

```
あなたはこのリポジトリのリファクタリング実行者です。
instruction/modified_proposal/03_view_binding_plan.md を最初から最後まで読み、記載どおりに作業してください。

厳守事項:
- まず「項目 V0」の前提条件チェックを行う。計画02が未完了なら作業せず、その旨を報告して終了する。
- V0 → V1 → … → V9 の順に 1 項目ずつ実施する。1 項目 = 1 コミット。
- 各項目は §1.5「共通付け替え手順」に厳密に従う。委譲の削除は必ず「参照が定義のみ」を git grep で確認してから行う。
- 各項目の「完了条件」（grep + 標準検証 + 手動確認）をすべて満たしてからコミットする。
  満たせない場合は変更を破棄（git checkout -- . / git revert）して中断し、何がどう失敗したかを報告する。
- 「やらないことリスト」に該当する変更は、改善に見えても行わない。
- tests_ui はアサーション変更禁止（呼び出し経路の書き換えのみ可）。
- Python は py コマンドで実行する。挙動を変えないことが最優先。
- V2 と V9 のフック手動確認 6 項目は省略禁止。確認前に必ず停止キーを設定すること。

最終成果物:
- refactor/03-view-binding ブランチ上の一連のコミット
- 実施項目 / スキップ項目 / app.py の行数推移 / 削除した委譲数 / 残した委譲と理由 / 各項目の検証結果を列挙した報告
```
