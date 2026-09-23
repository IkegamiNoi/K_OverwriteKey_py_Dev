# task_01_executor_invalid_type

## 目的

`ActionExecutor.execute` で**種類が不正なアクション**（暫定仕様 24 §3.1）を判定し、**何も送らず**
`on_action_error` で通知して、呼び出し元へ「送らなかった」を返す（§3.2 / §3.5）。
既存の 3 種（`hotkey` / `text` / `mouse_click`）は従来どおり送り、「送った」を返す。

**application 限定（`keyseq/application/action_executor.py`）+ テスト新設。runner / presentation / domain は不変。スキーマ不変**。
戻り値を runner が使うのは task_02（本タスク時点では戻り値は捨てられ、挙動差は「不正な種類で送らず通知する」のみ）。

## 対象範囲（application 限定・executor 1 ファイル + テスト新設）

### `keyseq/application/action_executor.py`

1. `execute(self, action: dict) -> bool` に変更する。
   - 種類の取り出し: `raw = action.get("type")` を **`isinstance(raw, str)` のときだけ** `raw.strip()`、それ以外は `""`（§3.1。
     正規化を経ない dict でも例外にしない）。判定は `.lower()` した値で行う。
   - `hotkey` / `text` / `mouse_click`: **既存の処理をそのまま**呼び、`True` を返す。内部のエラー（hotkey 検証 / `x`・`y` 不正 /
     送信例外）の扱い・通知は変えない（検証エラー・`x` / `y` 不正・mouse_click の送信失敗は `True`。hotkey / text の送信例外は従来どおり `execute` の外へ抜ける）。
   - **それ以外（無い / 空 / 空白のみ / 未知 / 非文字列）**: `input_gateway` を呼ばず・send guard に入らず、
     `self._on_action_error(notified_action, err)` を 1 回呼んで **`False`** を返す。
     **末尾の `self._write_text(str(value))` フォールバックは削除する**。
2. `notified_action` = `action` の**浅いコピー**に `type` を 1 の文字列（strip 済み・小文字化しない。非文字列なら `""`）で入れたもの。
   **元の `action` は書き換えない**（§3.2）。
3. `err` の文（§3.5）: 小さな private 関数（例 `_invalid_type_message(type_text: str, action: dict) -> str`）で組み立てる。
   - 形: `種類が不正です（hotkey / text / mouse_click のいずれか）。種類: <type_text または「(なし)」>` +
     ラベルがあれば ` / ラベル: <label>`。
   - ラベル: `action.get("label")` が `str` で strip 後に空でなければ含める（非文字列・空なら省く）。
   - 値の切り詰めはしない（値は `show_action_error` 側の「値:」欄が表示する）。

### `tests/test_action_executor_type.py`（新規）

`tests/test_action_executor_drag.py:9-22` と同じ組み立て（`input_gateway` / 各コールバックは `Mock`）で、下記「確認」の 1〜6 を実装する。

### 設計メモ / 制約

- **`value` の扱いは変えない**（既存 3 種へ渡す `value = action.get("value") or ""` と `str(value)` はそのまま）。
- `_execute_hotkey` / `_execute_mouse_click` / `_write_text` の中身は触らない。戻り値の `True` は `execute` 側で返す。
- 通知は `on_action_error` のみ（`on_runtime_error` は呼ばない）。application から presentation を import しない。
- 文言の日本語・全角括弧・区切り（` / `）は上記のとおり固定（テストで完全一致を見る）。

## 読むファイル

1. 主入力 `instructions/history/24_unknown_action_type_handling.md` §3.1 / §3.2 / §3.5 / §6
2. `keyseq/application/action_executor.py`（編集対象・全体 165 行）
3. `tests/test_action_executor_drag.py:1-35`（テストの組み立ての手本）
4. `keyseq/presentation/controllers/hook_controller.py:17-24`（`HookController.__init__`）/ `:235-253`（`show_action_error`。読むだけ）
5. `keyseq/domain/config.py:144-158`（`normalize_actions`。確認 1 の正規化経由ケース用）

## 含まない

- `sequence_runner.py` で戻り値を使う（run_to_end の停止 / 単発の index を進めない）・`perform_action` の型・
  `presentation/app.py` の `_perform_action` の委譲・executor × runner の組み合わせテスト（**task_02**）
- 正本 `data_schema.md` / `codebase_map.md` の改訂・暫定 24 の凍結（**task_03**）
- `hook_controller.py` の変更（文言・型防御とも。暫定 24 §7 / phase.md「含まない」）
- `x` / `y` 不正・hotkey 検証エラーの通知や進み方の変更（暫定 24 §7）

## 確認

- 追加する単体テスト（`tests/test_action_executor_type.py`）:
  1. 不正な種類 = `type` 無し / `""` / `"   "` / `"hotky"` / 直接渡す非文字列（`["hotkey"]` / `1` / `None`）/
     `normalize_actions([{"type": ["hotkey"], "value": "alt+f4"}])[0]` のそれぞれで:
     `execute` が **`False`**・`input_gateway` の呼び出し 0 件（`gateway.method_calls == []`）・`send_guard_count == 0`・
     `on_action_error` 1 回・`on_runtime_error` 0 回。
  2. `err` の完全一致: 種類 `"hotky"`・ラベル `" 保存 "` → `種類が不正です（hotkey / text / mouse_click のいずれか）。種類: hotky / ラベル: 保存` /
     種類なし・ラベル無し → `…。種類: (なし)` / ラベルが非文字列 → ラベル部を省く。
  3. `on_action_error` に渡る `action` の `type` が `str`（非文字列を直接渡したケースで `""`）で、**元の `action` は変わっていない**（`type` が元のまま）。
  4. **実際の `HookController(Mock()).show_action_error`**（`patch.object(hook_controller.messagebox, "showerror")`）を
     `on_action_error` に結線し、`type` が `["hotkey"]` のアクションを `execute` しても例外にならず、`showerror` が 1 回呼ばれる。
  5. 既存 3 種（`"hotkey"` / `" TEXT "` / `"Mouse_Click"`）は従来どおり送られ `True`（hotkey は `validate_hotkey` の Mock が `("", "ctrl+c")` を返す設定で
     `send_hotkey` 1 回 / text は `write_text` 1 回 / mouse_click は `click_mouse` 1 回）。
  6. 既存経路の内部エラーでも `True`: hotkey 検証エラー（`validate_hotkey` が `("エラー", "")`）→ `on_action_error` 1 回・送信なし・`True` /
     `mouse_click` の `x` 不正 → `on_runtime_error` 1 回・`True`。
- 実測（`verifier`・`.venv` python）:
  - `compileall -q keyseq main.py tests tests_ui` clean
  - `-m unittest discover -s tests` 全 pass（件数は追加分だけ増える）
  - `-m unittest discover -s tests_ui` 全 pass
  - `-m tests.smoke_app` pass
- `git diff -- keyseq` が `keyseq/application/action_executor.py` のみ

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は**不要**（UI から不正な種類を作れず手編集 JSON のみの経路。単体テストで固定する。シーケンス停止は task_02 のテストで固定）。
