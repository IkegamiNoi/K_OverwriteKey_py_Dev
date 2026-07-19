# task_04_font_apply_and_uivars

## 目的

負債①（責務混在: `set_ui_font_delta`）・④（`ui_vars` の App private 直読み）の解消。
`set_ui_font_delta` を**案A（最小抽出）**で分割し、`UiVars` を引数化する（暫定仕様
[§6 案A](../../../history/02_startup_font_settings_cleanup.md)・受け入れ条件 §8-5/§8-6/§8-7）。

- **挙動不変**（coerce・差分なし早期 return・適用順序・永続化・**メニュー再構築は build_menu_bar のみ / bind_menu_shortcuts 非呼出**・フラッシュ文言を保つ）。
- **presentation 限定**・application/domain/infrastructure 不変・スキーマ不変・初期化順序不変。
- **案B（FontSettingsController 新設）は実装しない**（暫定仕様 §6・スコープ外）。`_ui_font_delta_pt` の所有は App のまま。

## 対象範囲（presentation 限定・案A分割 + UiVars 引数化）

### 1. `keyseq/presentation/app.py` — `set_ui_font_delta` の案A分割

現行 `set_ui_font_delta`（現 app.py 内・~227-243相当）を 2 メソッドに分割する（**App 内に留める**）:

```python
    def _apply_font_delta(self, delta: int) -> bool:
        new_delta = coerce_font_delta(delta)
        if new_delta == int(getattr(self, "_ui_font_delta_pt", 0)):
            return False
        self._ui_font_delta_pt = new_delta
        self.ui_vars.ui_font_delta_var.set(int(new_delta))
        apply_global_theme(self, font_delta_pt=new_delta)
        self.config_io.write_startup({"ui_font_delta_pt": new_delta})
        return True

    def set_ui_font_delta(self, delta: int):
        if not self._apply_font_delta(delta):
            return
        if hasattr(self, "menubar"):
            build_menu_bar(self)
        new_delta = self._ui_font_delta_pt
        if new_delta == 0:
            self._set_flash_message("フォントサイズを標準にしました。")
        else:
            self._set_flash_message(f"フォントサイズを {new_delta:+d} にしました。")
```

- **等価性の要**: 「coerce → 差分なし早期 return → 状態更新 → var.set → apply_global_theme → write_startup」を
  `_apply_font_delta` に、「build_menu_bar（`hasattr(self, "menubar")` ガード保持）+ フラッシュ通知」を `set_ui_font_delta` に。
  適用順序・早期 return の位置・フラッシュ文言（標準 / `{:+d}`）を変えない。**`bind_menu_shortcuts` を呼ばない**。

### 2. `keyseq/presentation/ui_vars.py` — 引数化（App private 直読みの解消）

- `UiVars.__init__` を `ui_font_delta_pt` を**引数で受け取る**形に変更する:
  - シグネチャ: `def __init__(self, master, ui_font_delta_pt: int) -> None:`
  - `ui_vars.py:17` の `value=int(master._ui_font_delta_pt)` → `value=int(ui_font_delta_pt)`。
  - **`master._ui_font_delta_pt` の直読みを廃止**（受け入れ条件 §8-5: `grep "_ui_font_delta_pt" ui_vars.py` が 0 件）。
  - 他の `master.data.get(...)` 等の既存参照は**変更しない**（今回対象は font delta の直読みのみ）。

### 3. `keyseq/presentation/app.py` — `UiVars` 生成の引数渡し

- `app.py`（`UiVars(self)` の生成行・現 L69 相当）を `UiVars(self, ui_font_delta_pt=self._ui_font_delta_pt)` に変更する。
- 生成位置は変えない（`_ui_font_delta_pt` は直前で算出済み。初期化順序不変）。

### 4. 呼び出し側の追随確認（UiVars を直接生成する箇所）

- `UiVars(` を直接生成する箇所が app.py 以外にあれば（テスト含む）引数追加に追随させる。
  無ければ変更不要（`grep -rn "UiVars(" keyseq/ tests/ tests_ui/` で確認）。

## 設計メモ / 制約

- **実行環境**: python は必ず `..\..\..\.venv\Scripts\python.exe`（worktree 相対）。
- **安全網の担保**: 既存 `tests_ui/test_startup_font_characterization.py::test_set_ui_font_delta_applies_only_real_changes` は
  観測挙動（差分なし早期 return / build_menu_bar のみ・bind_menu_shortcuts 非呼出 / apply_global_theme・write_startup 呼出 / フラッシュ文言）を
  固定している。**この特性テストを無改変で pass させる**ことが案A分割の挙動不変の証明。原則このテストは変更しない。
- **依存方向**: すべて presentation 内。`ui_vars.py` は master の公開情報を引数で受け取る（private 直読みを避ける）。
- **やってはいけない**: 案B（FontSettingsController）新設、`_ui_font_delta_pt` の所有移動、フォント範囲/既定/文言の変更、
  メニュー再構築の頻度差（build_menu_bar のみ）の変更、application/domain の変更、正本反映（task_05）。

## 含まない

- 正本反映・記録（task_05: 昇格判断・凍結・codebase_map・decisions_archive/03・idea_02 の INDEX_done 移動・refactor_check）。
- 案B（FontSettingsController）の新設・`_ui_font_delta_pt` の所有移動（暫定仕様 §6・将来 idea）。
- フォント範囲・既定値・startup.json スキーマ・メニュー構成/文言の変更。

## 確認

`.venv` python で以下を実行し、いずれも pass すること:

- 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py`（clean）
- テスト: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`（86 維持）/
  `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui`（20 維持・**特性テスト無改変で pass**）
- smoke: `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app`（pass）
- 受け入れ条件（暫定仕様 §8-5/§8-6/§8-7）:
  - `grep -n "_ui_font_delta_pt" keyseq/presentation/ui_vars.py` が **0 件**（App private 直読み解消・§8-5）
  - `set_ui_font_delta` と `_apply_font_delta` が分離され、後者が「状態・適用・永続化」・前者が「メニュー再構築 + フラッシュ」を担う（§8-6・目視 + 特性テスト）
  - フォント変更時に `build_menu_bar` のみ・`bind_menu_shortcuts` 非呼出（§8-7・特性テストが担保）
- 統合退行: `codex-reviewer`（標準レビュー）を `reviewer` と**併用**する（複数タスクを跨ぐ動作確認・agent_selection.md）。

## 完了条件

- 上記「確認」全 pass・**reviewer 採用**（CLAUDE.md レビュー必須）+ **codex-reviewer 併用**（統合退行の二次レビュー）。
- **実機目視（ユーザー実施・必須ゲート）**: 本タスク完了後に以下をユーザーが確認する（暫定仕様 §8-11,12）。
  この目視完了までフェーズ最終確認は保留（task_05 へ進む前提条件）:
  1. 起動時（startup.json **正常 / 欠損 / 破損 / 非dict**）のフォント適用と警告挙動（正常・欠損・非dict=警告なし / 破損のみ警告）。
  2. メニューからのフォント変更 → 即時反映・永続化・再起動後の保持。
  3. `keymap_set_path` を持つ構成の起動復元（構成が読める）。
