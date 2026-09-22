# task_05c_group_a_escape

## 目的

**群 A の 4 経路へ Escape を結線**し、**Esc に別用途がある状態ではその用途を優先して閉じない**
規範を実装する（暫定仕様 22 **v0.5 §3.6**・受け入れ条件 **§8-12**）。

これにより `grab_modal` を通る **15 経路すべてが Escape で閉じる**状態になり、
正本 `features.md` の Escape 条項を**例外なしで**昇格できる（§4・task_06）。

- **presentation 限定**。domain / application / データスキーマは**不変**。
- スコープ拡大の確定 = ユーザー 2026-09-23（暫定仕様 §2.2-8・§2.2-9・§2.2-10）。

## 規範（暫定仕様 v0.5 §3.6）

**Escape のハンドラはダイアログにつき 1 つにまとめ、状態で分岐する**。別用途を別ハンドラとして
重ねない。

```python
def _on_escape(self, _event):
    if self._recording:          # 別用途が有効な間は
        self._stop_recording()   # そちらを優先し
        return "break"           # 閉じない
    self.destroy()               # 通常時は × と同じ（キャンセル相当）
```

### なぜ「状態分岐」以外は不可か（実測済み・2026-09-23）

| # | 条件 | 結果 |
|---|---|---|
| A | 同一 widget に `<KeyPress>` と `<Escape>` を両方 bind | Escape では **`<Escape>` のみ発火し `<KeyPress>` は発火しない** |
| B | 同一 widget・同一パターンを `add="+"` で 2 つ | 登録順に両方発火 |
| C | B の 1 つ目が `"break"` を返す | 後続は発火しない |

- **実測 A**: 既存の「Esc で停止」は `<KeyPress>` ハンドラ内の `keysym == "esc"` 分岐なので、
  素朴に `bind("<Escape>", self.destroy)` を足すと**停止処理が発火せず閉じてしまう**（退行）。
- **実測 B**: 登録順に依存する形も不可（閉じる側が `__init__` で先に登録されるため先に発火する）。

## 対象範囲（presentation 限定・4 ファイル）

各ファイルで次を行う。**`__init__` 末尾が `grab_modal(...)` である構造は変えない**
（静的検査 `tests_ui/test_nested_modal_grab.py:260` が固定している）。
`bind("<Escape>", ...)` は **`grab_modal` より前**に置く（群 C の 5 経路と同じ形）。

### 1. `keyseq/presentation/dialogs/action_dialog.py`（Esc = 記録停止）

- `__init__` に `self.bind("<Escape>", self._on_escape)` を追加（`grab_modal` の前）。
- `_on_escape(self, _event)` を新設:
  - `self._recording` が真 → `self._stop_recording()` して **`return "break"`**（閉じない）
  - 偽 → `self.destroy()`
- **`_on_key_press` の `key == "esc"` 分岐（`:294-296`）は削除する**
  （実測 A により、`<Escape>` ハンドラがある状態ではこの分岐は到達不能になるため。
  **残すと「動いているように見えて実は死んでいるコード」になる**）。
- `_recording` は `__init__`（`:29`）で `False` に初期化済みなので、生成直後の Escape でも安全。

### 2. `keyseq/presentation/dialogs/trigger_dialog.py`（Esc = 取得停止）

- 同様に `self.bind("<Escape>", self._on_escape)` + `_on_escape` を新設。
- 判定は **`self._capturing`**（`getattr(self, "_capturing", False)` で安全に読む。
  既存 `_stop_capture` と同じ作法）。真なら `self._stop_capture()` + `return "break"`。
- **`_on_capture_keypress` の `k == "esc"` 分岐（`:98-100` 付近）は削除する**（理由は 1 と同じ）。

### 3. `keyseq/presentation/dialogs/keymap_edit_dialog.py`（Esc = 取得停止）

- 2 と同じ（判定は `self._capturing`、停止は `self._stop_capture()`）。
- **`_on_capture_keypress` の `key == "esc"` 分岐（`:100-102` 付近）は削除する**。

### 4. `keyseq/presentation/dialogs/preset_dialog.py`（Esc の別用途なし）

- `self.bind("<Escape>", lambda _event: self.destroy())` を追加（`grab_modal(self, parent,
  focus=self.value_entry)` の前）。群 C の 5 経路と同じ 1 行の形。
- **状態分岐は不要**（このダイアログに Esc の別用途は無い）。

### 5. テスト（`tests_ui/`）

`tests_ui/test_dialog_escape_binding.py` へ**群 A の検査を追加**する（既存の群 C 分は変更しない）。

| 検査 | 期待 |
|---|---|
| 4 経路とも**通常時**に Escape で破棄される | `winfo_exists()` が False・結果が未確定（キャンセル相当） |
| `ActionDialog` の**記録中**に Escape | `_recording` が False へ・**`winfo_exists()` は True**（閉じない） |
| `TriggerDialog` / `KeymapEditDialog` の**取得中**に Escape | `_capturing` が False へ・**窓は残る** |
| 上記の直後にもう一度 Escape | **今度は閉じる** |
| フック解除 | 閉じた場合のみ **ちょうど 1 回**（`get_hook_pause_count()` が 1 → 0）。
  **閉じなかった場合は解除されない**（`1` のまま）ことも固定する |

- **実 Toplevel の 4 クラスなので `tests_ui/escape_delivery.py` の `send_escape` を使う**
  （実配送で検証する）。ただし「**閉じないこと**」の検査には `send_escape` を使えない
  （破棄待ちで fail するため）。その場合は `focus_force` → `update` →
  `event_generate("<Escape>")` → `update` の形を**このテスト内に直書き**し、
  **フォーカスがダイアログ配下に入ったことを確認してから送る**（`send_escape` と同じ順序）。
- 記録中 / 取得中にするには `_start_recording()` / `_start_capture()` を直接呼ぶか、
  「キー入力で記録」「キー入力で取得」ボタンを `invoke()` する。

## 設計メモ / 制約

- **新しい閉じ方を作らない**。4 経路とも「キャンセル」ボタンと同じ結果（`result` を確定せず破棄）。
  `PresetDialog` の「キャンセル」は `self.destroy` なので同一。
- **`_on_key_press` / `_on_capture_keypress` の Esc 以外の処理は一切変えない**
  （記録・取得の本体、修飾キーの扱い、非修飾キーでの自動停止）。
- `destroy()` をオーバーライドしているクラス（`trigger_dialog.py` / `keymap_edit_dialog.py` は
  `destroy` で `_stop_capture()` を呼ぶ）があるため、**`_on_escape` では `destroy()` を呼ぶだけでよい**
  （停止処理を二重に書かない）。
- **`return "break"` を忘れない**（閉じない分岐）。返さないと親へ伝播する可能性がある。
- 関数は 30 行以内を目安にする（`.claude/rules/implementation.md`）。

## 読むファイル

- `instructions/history/22_dialog_keyboard_focus.md` の **§3.5 / §3.6 / §4 / §8-12**
- `keyseq/presentation/dialogs/action_dialog.py`（全体。`_recording` の扱いと `_on_key_press`）
- `keyseq/presentation/dialogs/trigger_dialog.py`（全体）
- `keyseq/presentation/dialogs/keymap_edit_dialog.py`（全体）
- `keyseq/presentation/dialogs/preset_dialog.py`（全体）
- `keyseq/presentation/dialogs/layout_delete_dialog.py:45-55`（群 C の Escape 結線の手本）
- `tests_ui/test_dialog_escape_binding.py`（全体。追加先と既存の作法）
- `tests_ui/escape_delivery.py`（`send_escape` の使い方。**読むだけ・改変しない**）

## 含まない

- **群 B・群 C の再変更**（既に結線済み）。
- `tests_ui/escape_delivery.py` の改修（`deep-reviewer` M2・ユーザー判断待ち）。
- `tests_ui/test_dialog_teardown_flows.py` の `after(0)` 取りこぼし対策（別 family・判断待ち）。
- task_05b の対象（初期フォーカスの widget 同一性検査 / 群 C の実配送化）。
- 正本 `instructions/common/` の更新（task_06）。
- 実機目視（task_05 でまとめて 1 回・§2.2-10）。
- 同型スケルトンの共通化（`bind("<Escape>")` + `protocol` の重複。別タスク化候補のまま）。

## 確認

`.venv` の python を使う（`..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

1. `python -m compileall -q keyseq` が clean。
2. `python -m unittest discover -s tests` 全 pass（556・skipped 7 から不変）。
3. `python -m unittest discover -s tests_ui` が全 pass（**件数は増加**）。
4. 追加した群 A の検査を**単独で 5 回ずつ**実行して全 pass。
5. **静的検査 `tests_ui/test_nested_modal_grab.py` の
   `test_grab_modal_is_last_initialization_statement` が引き続き green**（§8-5）。
6. `python -m tests.smoke_app` が `SMOKE OK`。
7. `git diff --stat keyseq/domain keyseq/application` が**空**（層の逸脱がないこと）。

## 完了条件

- 確認 1〜7 が pass（実測は `verifier`。**Codex に python 実行を依頼しない**）。
- **`reviewer` 採用**（重点観点 = 既存の記録 / 取得ロジックを壊していないか /
  到達不能になった `esc` 分岐を残していないか / `return "break"` の有無 /
  新しい閉じ方を作っていないか / 層の逸脱がないか）。
- **実機目視は task_05 でまとめて実施**（本タスクでは行わない）。
