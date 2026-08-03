# task_06b_hook_keys_display_switch

## 目的

個別指定チェックの ON⇄OFF で**表示と runtime の切替**を行い、**個別値をセッション内に保持**する。
ON→OFF では個別値を退避して表示・runtime を全体デフォルトへ、OFF→ON では退避値を復元する。
**復活するのは保存前の同一セッション内のみ**とし、OFF のまま保存したら退避値を破棄する。

- 根拠: [暫定仕様 06](../../../history/06_hook_keys_global_default.md) §2（ON→OFF の内部保持と再 ON での復活・
  保存後は再 ON しても空）/ §4 末尾（表示切替）/ §7 受入条件 **5**。
- **レイヤ制約**: **presentation 限定**（`app.py` + `controllers/config_io/keymap_set_io.py`）。
  application・domain・View・`key_capture.py`（task_06 完了済み）は**変更しない**。
- task_05 で新設した `App.toggle_hook_keys_individual` を**拡張する**タスク。

## 対象範囲（presentation 限定・2 ファイル）

### 1. `keyseq/presentation/app.py`

**(a) 退避先のフィールドを `__init__` へ追加**（`ui_vars` 生成の近く）:

```python
        self._retained_hook_keys: dict[str, str] | None = None
```

**(b) `toggle_hook_keys_individual`（task_05 で新設）を拡張する**:

```python
    def toggle_hook_keys_individual(self):
        individual = bool(self.ui_vars.hook_keys_individual_var.get())
        if individual:
            retained = self._retained_hook_keys or {}
            self.data["hook_stop_key"] = str(retained.get("hook_stop_key", ""))
            self.data["hook_toggle_key"] = str(retained.get("hook_toggle_key", ""))
            self._retained_hook_keys = None
        else:
            self._retained_hook_keys = {
                "hook_stop_key": str(self.data.get("hook_stop_key", "")),
                "hook_toggle_key": str(self.data.get("hook_toggle_key", "")),
            }
        self.data["hook_keys_individual"] = individual
        if not individual:
            self.config_service.apply_global_hook_key_defaults(self.data, config_root=self.config_root)
        self._sync_control_vars_from_data()
        self.dirty_tracker.set_dirty(True)
```

- **順序が重要**: `hook_keys_individual` を書いた**後**に `apply_global_hook_key_defaults` を呼ぶ
  （この API はフラグが真なら何もしないため。task_02）。
- **退避は復元時に消費する**（`None` に戻す）。ON→OFF→ON→OFF と往復しても、2 回目の OFF で
  そのときの値を改めて退避する。
- **退避が無い状態の OFF→ON は両キーを `""` にする**。理由: OFF の keymap_set は保存時に個別値が
  空文字化されており（task_03）、読込時も個別値を runtime へ持ち込まない（task_02）。
  ＝「保存後は再 ON しても空」（§2）と一致する。**全体デフォルト値を個別値として引き継がない**
  （引き継ぐと、意図せず全体デフォルトが keymap_set へ焼き付く）。
- 表示反映は既存の `_sync_control_vars_from_data`（data → Var の唯一の入口・task_05）を使う。

**(c) 退避を破棄する公開メソッドを追加**（`toggle_hook_keys_individual` の直後）:

```python
    def discard_retained_hook_keys(self) -> None:
        """保持していた個別値を捨てる（保存後・別データ読込後は復活させない）。"""
        self._retained_hook_keys = None
```

### 2. `keyseq/presentation/controllers/config_io/keymap_set_io.py`

`discard_retained_hook_keys()` を**次の 4 箇所**で呼ぶ（いずれも 1 行）:

| メソッド | 位置 | 理由 |
|---|---|---|
| `save_keymap_set_to` | 保存成功後・`dirty_tracker.set_dirty(False)`（現 `:128`）の**直前** | §2「復活は保存前のみ」 |
| `apply_loaded_data_to_ui` | 先頭（現 `:646` 付近） | 別の keymap_set を読み込んだら前のセットの個別値は無効 |
| `new_config` | `_sync_control_vars_from_data()`（現 `:60`）の**直前** | 新規作成で前のセットの値を持ち越さない |
| `restore_default` | `_sync_control_vars_from_data()`（現 `:605`）の**直前** | 既定復元で前のセットの値を持ち越さない |

- **`_sync_control_vars_from_data` の中に破棄を入れてはいけない**
  （`toggle_hook_keys_individual` 自身がこれを呼ぶため、退避が即座に消える）。

### 設計メモ / 制約

- 退避は **runtime（`app.data`）とは別に App が持つ**。`app.data` の内部キーとして持たない
  （保存経路・スキーマへ影響させないため）。
- **フック層は無変更**。runtime の `hook_stop_key` / `hook_toggle_key` を切り替えるだけで、
  フックは常に解決済みの値を直読みする（暫定仕様 §3）。
- チェック操作で dirty にする既存判断（task_05）は維持する。
- OFF 時の**キー編集**（capture / clear）は task_06 で実装済み。本タスクは**チェックの切替**のみを扱う。

## 含まない

- capture / clear の所有者切替・dirty 非汚染（task_06 完了済み。`key_capture.py` は**変更しない**）。
- チェックボックス UI の追加（task_05 完了済み。View は**変更しない**）。
- 全体デフォルトの読み書き API（task_02 / task_04 完了済み。`config_service` / `startup_io` は**変更しない**）。
- Entry / ボタンの活性制御（本フェーズでは行わない）。
- 統合確認・受入条件 1〜8 の通し確認（task_07）/ 正本反映（task_08）。

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. **ON→OFF の切替**（`tests_ui/test_app_ui_flows.py`。config.json に全体デフォルトを用意して実 IO で検証）:
   - 個別値（例 `f5` / `f6`）を持つ ON 状態から OFF にすると、
     `app.data` と `stop_key_var` / `toggle_key_var` が**全体デフォルト値**になる
   - **dirty が立つ**（チェック操作は keymap_set の保存値を変えるため）
3. **OFF→ON の復元**:
   - 直前に ON→OFF した場合、再 ON で `app.data` / Var が**退避していた個別値**へ戻る
   - **退避が無い状態**（読込直後の OFF など）で ON にすると、両キーが **`""`** になる
     （全体デフォルト値を引き継がない）
   - ON→OFF→ON→OFF と往復しても、2 回目の OFF で**そのときの値**が退避される（消費の確認）
4. **保存後は復活しない**（受入条件 5）:
   - ON→OFF の後に keymap_set を保存し、その後 ON にすると両キーが `""` になる
     （`save_keymap_set_to` 成功時に破棄されている）
5. **別データを読み込んだら復活しない**:
   - ON→OFF の後に `apply_loaded_data_to_ui` / `new_config` / `restore_default` を通すと、
     その後の ON で両キーが `""` になる
6. `-m unittest discover -s tests` が全 pass（現在 168 件。**増減しない想定**）。
7. `-m unittest discover -s tests_ui` が全 pass（現在 173 件 + 追加分。**件数を報告**）。
8. `-m tests.smoke_app` が pass。

## 完了条件

- 「確認」1〜8 がすべて pass（テスト実測は `verifier` が行う。Codex は python を実行できない）。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点 + phase.md レビュー方針の
  **5「セッション内復活の境界」**〔保存後・別データ読込後に復活しないか〕と
  **2「キー解決点が 1 箇所か」**〔全体デフォルトの取得が `apply_global_hook_key_defaults` 経由か〕）。
- **実機目視は task_07 でまとめて実施**（本タスク完了で Phase γ の UI 挙動が一通り揃う）。
