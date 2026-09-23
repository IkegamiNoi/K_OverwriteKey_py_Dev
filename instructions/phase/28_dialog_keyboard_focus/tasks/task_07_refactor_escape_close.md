# task_07_refactor_escape_close

## 目的

phase 28 の `/refactor_check`（判定 = 推奨・M3）で承認された
[提案書 11](../../../modified_proposal/11_refactor_dialog_escape_secondary_use.md) の項目 1（R11-1）を実施する。
「Esc に別用途がある間はそちらを優先し、押しっぱなしでは閉じない」処理（正本 `features.md` §4.6「モーダルダイアログの作法」）が
3 ダイアログに複製されているのを、**クロージャに状態を持つ関数 1 つ**へ寄せる。

レイヤ制約: **presentation 限定・挙動不変**。domain / application・スキーマ・`modal.py` は変更しない。
テスト（`tests_ui/`）は**変更しない**見込み（テストは `_on_escape` / `_escape_held` を直接参照していない）。

## 対象範囲（presentation 限定・挙動不変）

### 1. keyseq/presentation/dialogs/escape_close.py（新規）

- `bind_escape_close(window, *, is_busy, stop) -> None` を置く（形は提案書 11 の「変更後」スケッチのとおり）:
  - `is_busy()` が真 → `stop()` を呼び、印を立てて `"break"`（**印より先に判定**）
  - 印が立っている → `"break"`（閉じない）
  - それ以外 → `window.destroy()`
  - `<KeyRelease-Escape>` で印を消す（`"break"` は返さない）
  - 印は**クロージャに持つ**（ウィジェット属性を増やさない。`grab_modal` と同じ方針）
- 型注釈を付ける（`window: tk.Toplevel` / `is_busy: Callable[[], bool]` / `stop: Callable[[], None]`）。docstring は 1 行。

### 2. action_dialog.py / trigger_dialog.py / keymap_edit_dialog.py（keyseq/presentation/dialogs/）

- `self._escape_held = False` の初期化・`self.bind("<Escape>", ...)`・`self.bind("<KeyRelease-Escape>", ...)`・
  `_on_escape`・`_on_escape_release` を削除し、`grab_modal(...)` の**直前**で `bind_escape_close(...)` を呼ぶ:
  - `ActionDialog`: `is_busy=lambda: getattr(self, "_recording", False)`, `stop=self._stop_recording`
  - `TriggerDialog` / `KeymapEditDialog`: `is_busy=lambda: getattr(self, "_capturing", False)`, `stop=self._stop_capture`
- `__init__` の**最後の文は `grab_modal(...)` のまま**（静的検査 `tests_ui/test_nested_modal_grab.py`）。
- `_stop_recording` / `_stop_capture` / 記録・取得の開始処理は変更しない。

### 3. instructions/common/codebase_map.md（文書・メイン担当）

- `modal.py` 節の Escape の結線の記述で `_on_escape` / `_escape_held` / `_on_escape_release` を
  `dialogs/escape_close.py` の `bind_escape_close` へ置き換え、presentation のフォルダ構成へ 1 行追加する。
  **この文書更新は実装後にメインセッションが行う**（Codex には依頼しない）。

### 設計メモ / 制約

- **挙動不変**。判定順（記録・取得中 → 印 → 閉じる）・印を立てるのは Escape による停止のみ・`<KeyRelease-Escape>` で消す、
  をすべて保つ（暫定仕様 22 §3.6.1〔凍結〕→ 正本 `features.md` §4.6）。
- `preset_dialog.py` や群 B・C の単純な `bind("<Escape>", ... destroy)` は**対象外**（`current.md`「同型スケルトンの共通化」で別扱い）。
- `lambda` で `getattr(..., False)` を使うのは既存の `_capturing` の読み方に揃えるため。

## 読むファイル

1. `instructions/modified_proposal/11_refactor_dialog_escape_secondary_use.md`（全体）
2. `keyseq/presentation/dialogs/action_dialog.py:25-35` / `:125-146`
3. `keyseq/presentation/dialogs/trigger_dialog.py:18-70`
4. `keyseq/presentation/dialogs/keymap_edit_dialog.py:18-70`
5. `keyseq/presentation/modal.py:65-105`（クロージャで状態を持つ手本）

## 含まない

- 群 B・C・`PresetDialog` の Escape 結線の共通化（`current.md` 別タスク化候補）。
- 挙動・文言の変更 / テストの変更（必要になったら実装を止めて報告）。
- idea_33 / idea_34。
- python の実行（Codex は実行できない。実測は `verifier`）。

## 確認

`.venv` の python（`..\..\..\.venv\Scripts\python.exe`）で `verifier` が実施する。

1. `python -m compileall -q keyseq` clean。
2. `python -m unittest tests_ui.test_dialog_escape_binding -v` 全 pass（8 件）。
3. **変異検査**: `escape_close.py` の「印が立っていたら閉じない」分岐を外す → 押しっぱなしのテストが赤 /
   判定順を逆にする → 再開のテストが赤（確認後は元へ戻し `git diff` で確認）。
4. `python -m unittest tests_ui.test_nested_modal_grab` pass。
5. `python -m unittest discover -s tests` 556 ran OK（skipped 7）。
6. `python -m unittest discover -s tests_ui` 509 ran OK。
7. `python -m tests.smoke_app` が `SMOKE OK`。
8. `git diff --stat` が 3 ダイアログ + 新規 `escape_close.py` + `codebase_map.md` のみ。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。
- phase 28 の完了処理: `current.md` の「アクティブなフェーズ」を「なし」へ戻す / 提案書 11 を「実施完了」へ /
  `decisions_archive/28` の refactor_check 節へ実施結果を 1〜2 行。
- 実機目視は**不要**（挙動不変・自動テストと変異検査で担保。A3 の経路は task_05e で確認済）。
