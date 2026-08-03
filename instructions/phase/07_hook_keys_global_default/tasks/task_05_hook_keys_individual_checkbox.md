# task_05_hook_keys_individual_checkbox

## 目的

フックラベルフレームに**「このキーマップセットで個別指定する」チェックボックス**を追加し、
keymap_set の `hook_keys_individual` と双方向に同期させる。
チェックの ON/OFF が runtime（`app.data`）へ反映され、keymap_set 読込時にはチェック状態が復元される
状態を作る。

- 根拠: [暫定仕様 06](../../../history/06_hook_keys_global_default.md) §4 前半（チェックボックスの追加）/
  §7 受入条件 **3**（チェック ON で個別指定できる）。
- **レイヤ制約**: **presentation 限定**（`ui_vars.py` / `app.py` / `views/*/hook_frame.py`）。
  application・domain・フック層は**変更しない**。
- **本タスクはチェックの追加と `hook_keys_individual` の同期まで**。
  キー表示の切替・個別値の保持・capture / clear の所有者切替は **task_06**。

## 対象範囲（presentation 限定・4 ファイル）

### 1. `keyseq/presentation/ui_vars.py`

`keyboard_show_physical_key_labels_var` と同じ書式で Var を 1 個追加する
（`toggle_key_var` の近く = hook 関連の並びに置く）:

```python
        self.hook_keys_individual_var = tk.BooleanVar(
            master=master,
            value=bool(master.data.get("hook_keys_individual", False)),
        )
```

### 2. `keyseq/presentation/app.py`

**(a) `_sync_control_vars_from_data`（`:394-401`）へ 1 行追加**（`toggle_key_var` の直後）:

```python
        self.ui_vars.hook_keys_individual_var.set(bool(self.data.get("hook_keys_individual", False)))
```

**(b) チェック操作のハンドラを新設**（`toggle_stop_key_capture`〔`:422`〕の近く = hook 関連メソッドの並び）:

```python
    def toggle_hook_keys_individual(self):
        self.data["hook_keys_individual"] = bool(self.ui_vars.hook_keys_individual_var.get())
        self.dirty_tracker.set_dirty(True)
```

- `hook_keys_individual` は keymap_set に保存される値なので、**変更したら dirty にする**のが正しい
  （暫定仕様 §4 の「dirty 非汚染」は **OFF 時のキー編集**に対する要件であり、チェック操作自体は対象外）。
- **キー表示（`stop_key_var` / `toggle_key_var`）は書き換えない**。ON⇄OFF の表示切替と個別値の
  内部保持は task_06 の責務（ここで先取りすると二重実装になる）。
- 既存の `toggle_keyboard_show_physical_key_labels`（`layout_controller.py:144`）と同じ
  「Var → data + 後処理」の形を踏襲する。

### 3. `keyseq/presentation/views/full_view/hook_frame.py`

`full_hook_line2` の **row=2** にチェックボタンを追加する（既存の grid 構造を崩さない）:

```python
        self.hook_keys_individual_check = ttk.Checkbutton(
            self.full_hook_line2,
            text="このキーマップセットで個別指定する",
            variable=app.ui_vars.hook_keys_individual_var,
            command=app.toggle_hook_keys_individual,
        )
        self.hook_keys_individual_check.grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 0))
```

### 4. `keyseq/presentation/views/compact_view/hook_frame.py`

`compact_hook_line2` の **row=2** に**同じ Var を共有する表示専用のチェック**を追加する
（`columnspan=2`）:

```python
        self.hook_keys_individual_check = ttk.Checkbutton(
            self.compact_hook_line2,
            text="このキーマップセットで個別指定する",
            variable=app.ui_vars.hook_keys_individual_var,
            state="disabled",
        )
```

- **compact は表示専用（`state="disabled"`・`command` 無し）**とする。
  理由: compact のフックキーは既に readonly Entry のみで capture / clear ボタンを持たない
  ＝「compact は表示のみ」という既存方針に合わせる。
  （この点は task_07 の実機目視でユーザー確認の対象にする）
- **未使用の `import tkinter as tk` を増やさない**（現行の import 構成を変えない）。

### 設計メモ / 制約

- **同期の入口は 2 本だけ**: data → Var は `_sync_control_vars_from_data`、
  Var → data は `toggle_hook_keys_individual`。**他の場所で `hook_keys_individual` を
  読み書きしない**（`.claude/rules/python_rules.md`「状態変更の入口を散らさない」）。
- `apply_loaded_data_to_ui` / `new_config` / `restore_default` は既に
  `_sync_control_vars_from_data` を呼ぶため、**これらの経路は変更不要**
  （keymap_set 読込・新規作成・既定復元でチェック状態が自動的に追従する）。
- full / compact は**同一の `BooleanVar` インスタンスを共有**する（`ui_vars` が持つ 1 個）。
  ビューごとに別の Var を作らない（表示が食い違う）。

## 含まない

- **capture / clear の所有者切替（ON=個別値 / OFF=全体デフォルト）・OFF 時の dirty 非汚染・
  ON⇄OFF での表示切替・個別値のセッション内保持・OFF 保存後の保持値破棄** → すべて **task_06**。
  本タスクでは `key_capture.py` を**変更しない**。
- **task_04 で新設した `StartupIo.write_global_hook_keys` を呼ぶこと** → task_06。
  本タスクは config.json を一切書かない。
- 読込時の解決（task_02）/ 保存時の空文字化（task_03）/ 全体デフォルト更新 API（task_04）。
- フック層（`input_router` / `hook_controller` / `keyboard_window`）の変更。
- チェック状態に応じた Entry / ボタンの活性制御（task_06 の表示切替に含める）。
- 正本 `spec_detail/` への反映（task_08）。

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. **新規 UI テスト**（`tests_ui/test_app_ui_flows.py` へ追加。ビューは
   `app.full_view.hook_frame` / `app.compact_view.hook_frame` で参照できる）:
   - full / compact の**両方**にチェックが存在し、**同一の `BooleanVar` を共有**している
     （`str(widget.cget("variable"))` が一致すること）
   - compact 側は `state` が `disabled`（表示専用）
   - `app.data["hook_keys_individual"] = True` → `_sync_control_vars_from_data()` で
     Var が `True` になる（`False` でも同様に追従する）
   - Var を `True` にして `toggle_hook_keys_individual()` を呼ぶと
     `app.data["hook_keys_individual"]` が `True` になり、**dirty が立つ**
     （`False` へ戻す操作でも data が追従すること）
   - `toggle_hook_keys_individual()` が **`stop_key_var` / `toggle_key_var` を変更しない**
     （表示切替は task_06 の責務・先取り防止）
3. **既存の keymap_set 読込経路でチェック状態が復元される**ことの確認
   （`tests_ui/test_config_io_characterization_keymap_set_startup.py` または上記ファイル）:
   - 移行で個別指定 ON になる keymap_set を読み込むと、チェックが ON になる
4. `-m unittest discover -s tests` が全 pass（現在 168 件。**presentation 限定のため増減しない想定**）。
5. `-m unittest discover -s tests_ui` が全 pass（現在 165 件 + 追加分。**件数を報告**）。
6. `-m tests.smoke_app` が pass。

## 完了条件

- 「確認」1〜6 がすべて pass（テスト実測は `verifier` が行う。Codex は python を実行できない）。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点 + phase.md レビュー方針の
  **6「層の分離」**〔presentation に閉じているか / application・domain を触っていないか〕と、
  **task_06 の先取りが無いこと**〔`key_capture.py` 無変更 / キー表示を書き換えていない〕）。
- **実機目視は本タスクでは実施しない**（チェックは付くが挙動の切替は task_06 で入るため、
  単体では確認しきれない）。Phase γ の実機目視は **task_07** でまとめて実施する。
  その際 **compact のチェックを表示専用にした判断**をユーザー確認の対象に含める。
