# task_06_hook_key_capture_ownership

## 目的

hook キーの capture / clear を**所有者切替可能**にする。個別指定 ON なら従来どおり keymap_set の
個別値を編集して dirty にし、**OFF なら `config/config.json` の全体デフォルトを編集**（task_04 の
成否付き API 経由）して runtime へ即反映し、**keymap_set を dirty にしない**。

- 根拠: [暫定仕様 06](../../../history/06_hook_keys_global_default.md) §4 後半（capture/clear の所有者切替・
  dirty 保全は「OFF 前の dirty 状態を記録し操作後に復元する」方式）/ §3 末尾（OFF 編集時は config.json と
  `app.data` の両方を更新して即反映）/ §5（保存成功時のみ確定）/ §7 受入条件 **4・7**。
- **レイヤ制約**: **presentation 限定**（`controllers/key_capture.py` + `controllers/dirty_state.py`）。
  application・domain・フック層・View は**変更しない**。
- **本タスクは capture / clear の書き込み先切替と dirty 非汚染まで**。
  ON⇄OFF の表示切替・個別値のセッション内保持・OFF 保存後の破棄は **task_06b**。

## 対象範囲（presentation 限定・2 ファイル）

### 1. `keyseq/presentation/controllers/dirty_state.py`

dirty 状態の記録・復元を **`DirtyStateTracker` の責務**として追加する
（`set_dirty` の近く。状態変更の入口を散らさないため呼び出し側でフィールドを直接読み書きしない）:

```python
    def capture_dirty_snapshot(self) -> tuple[bool, bool]:
        """dirty 状態を記録する（OFF 操作の前後で復元するため）。"""
        return (bool(self.is_dirty), bool(self.config_dirty))

    def restore_dirty_snapshot(self, snapshot: tuple[bool, bool]) -> None:
        self.is_dirty, self.config_dirty = bool(snapshot[0]), bool(snapshot[1])
        self._on_change()
```

- 個別 dirty フラグ（keymap / sequence / trigger_set）は capture が触らないため**対象外**
  （記録・復元の対象は `is_dirty` / `config_dirty` の 2 つだけ）。

### 2. `keyseq/presentation/controllers/key_capture.py`

**書き込み点を 1 本にまとめる**。現在 `clear()`（`:90-94`）と `on_keypress()`（`:131-133`）に
散っている「data へ書く → Var へ反映 → dirty」を、次の private メソッドへ集約する:

```python
    def _apply_key(self, key: str, *, mark_dirty: bool = True) -> bool:
        """所有者に応じて hook キーを確定する（確定できたら True）。

        ON : keymap_set の個別値を更新し dirty にする（従来どおり）
        OFF: config.json の全体デフォルトを更新し、成功時のみ runtime / 表示を確定する。
             keymap_set は dirty にしない（前後の dirty 状態を記録・復元する）
        """
```

**ON（`self._app.data.get("hook_keys_individual")` が真）**:

- `self._app.data[self._data_key] = key` / `self._var.set(key)` /
  `mark_dirty` が真なら `self._app.dirty_tracker.set_dirty(True)` → `True` を返す。
- **既存挙動の維持**: `clear()` は「旧値が空なら dirty にしない」ため、
  `clear()` からは `mark_dirty=bool(old)` を渡す（`on_keypress` は既定の `True`）。

**OFF**:

1. `snapshot = self._app.dirty_tracker.capture_dirty_snapshot()`
2. `try:` の中で
   - 相手側のキーは runtime から読む（更新対象でない方は現状維持）:
     `stop_key` / `toggle_key` の 2 値を組み立てる（`self._data_key` が
     `"hook_stop_key"` なら stop 側が `key`、そうでなければ toggle 側が `key`）
   - `self._app.startup_io.write_global_hook_keys(stop_key=..., toggle_key=...)` を呼ぶ
   - **戻り値が偽なら何も確定せず `False` を返す**（runtime も Var も書き換えない = 旧値維持・受入条件 7）
   - 真なら `self._app.data[self._data_key] = key` と `self._var.set(key)`（§3 の即反映）→ `True`
3. `finally:` で `self._app.dirty_tracker.restore_dirty_snapshot(snapshot)`
   （**例外経路でも dirty が汚れない**こと = phase.md レビュー方針 3）

**呼び出し側の差し替え**:

- `clear()`: 旧値を読んだあと `self._apply_key("", mark_dirty=bool(old))` を呼ぶ。
- `on_keypress()`: 既存の確定 3 行を `if not self._apply_key(key): self.stop(cancel=True); return "break"` +
  成功時は従来どおり `self.stop(cancel=False)` へ置き換える
  （**失敗時は確定せずキャプチャを終了する**。エラー表示は `write_startup` の `showerror` が既に行う）。

### 設計メモ / 制約

- **OFF で書くのは 2 キーとも**（`write_global_hook_keys` は 2 キー同時指定の API）。
  更新しない側は `app.data` の現在値をそのまま渡す＝ runtime は OFF のとき全体デフォルトを
  保持している（task_02）ため、**現在の全体デフォルトがそのまま再書き込みされる**のが正しい。
- **`hook_keys_individual` の判定は `self._app.data` を見る**（Var ではなく runtime。
  task_05 で両者は同期済みだが、data 側が状態の正）。
- **conflict_checks / validate_key_name の検証は所有者に関係なく従来どおり先に行う**
  （`_apply_key` は検証を通過した値だけを受け取る。検証ロジックを OFF 用に分岐させない）。
- **`_apply_key` 以外に hook キーへの書き込み点を作らない**（散らすと「OFF なのに keymap_set が
  dirty になる」不具合の温床）。

## 含まない

- **ON⇄OFF の表示切替（OFF で全体デフォルト表示 / 再 ON で個別値を復元）・個別値のセッション内保持・
  OFF 保存後の保持値破棄** → **task_06b**。本タスクでは
  `App.toggle_hook_keys_individual`（task_05 で新設）を**変更しない**。
- チェックボックス UI（task_05 完了済み）/ 全体デフォルトの書き込み API 本体（task_04 完了済み。
  `startup_io.py` は**変更しない**）/ 読込時の解決（task_02）/ 保存時の空文字化（task_03）。
- フック層（`input_router` / `hook_controller` / `keyboard_window` / `app.py`）の変更。
- Entry / ボタンの活性制御（本フェーズでは行わない）。
- 正本 `spec_detail/` への反映（task_08）。

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. **`DirtyStateTracker` の記録・復元テスト**（`tests_ui/test_app_ui_flows.py` か既存の dirty 系テスト）:
   - `capture_dirty_snapshot` → `set_dirty(True)` → `restore_dirty_snapshot` で
     `is_dirty` / `config_dirty` が元へ戻る（dirty → clean / clean → dirty の両方向）
3. **ON の capture / clear が従来どおり**（`tests_ui/test_app_ui_flows.py`）:
   - `hook_keys_individual = True` で `on_keypress`（または `_apply_key`）→ `app.data` と Var が
     更新され **dirty が立つ**。**`write_global_hook_keys` は呼ばれない**
   - `clear()` は旧値が非空なら dirty、**空なら dirty にしない**（既存挙動の維持）
4. **OFF の capture / clear が全体デフォルトを更新する**:
   - `hook_keys_individual = False` で確定 → `write_global_hook_keys` が
     **2 キーとも**（更新しない側は現在値）で呼ばれ、`app.data` と Var が更新される
   - **dirty が変化しない**（前が clean なら clean のまま / 前が dirty なら dirty のまま）
   - `clear()` は全体デフォルトを `""` で更新する
5. **保存失敗時に確定しない**（受入条件 7）:
   - `write_global_hook_keys` が `False` を返すと `app.data` / Var が**変化せず**、dirty も変化しない
   - `write_global_hook_keys` が**例外を投げても** dirty が復元される（`finally` の検証）
6. `-m unittest discover -s tests` が全 pass（現在 168 件。**増減しない想定**）。
7. `-m unittest discover -s tests_ui` が全 pass（現在 169 件 + 追加分。**件数を報告**）。
8. `-m tests.smoke_app` が pass。

## 完了条件

- 「確認」1〜8 がすべて pass（テスト実測は `verifier` が行う。Codex は python を実行できない）。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点 + phase.md レビュー方針の
  **3「dirty 非汚染」**〔例外経路でも記録・復元が成立するか / `dirty_tracker` の不変条件を壊さないか〕と
  **4「保存失敗時の扱い」**〔失敗時に UI / ランタイムを確定させていないか〕）。
- **実機目視は本タスクでは実施しない**（表示切替が task_06b で入るまで通しの操作にならないため）。
  Phase γ の実機目視は **task_07** でまとめて実施する。
