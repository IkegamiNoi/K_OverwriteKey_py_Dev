# task_01_vk_to_scan_code

## 目的

キーボードUI の編集中に押したキーの名前（`KeyboardWindow._normalize_tk_key`）で、Tk の `keycode`（VK）を走査コードへ変換してから、**外部レイアウトの `scan_code` だけ**で引く（phase 61 phase.md「確定」「含む」・idea_47 の調査結果）。F1 / F10 / F12 が `kana` / `henkan` / `muhenkan` になる不具合を直し、jis.json の JIS の特殊キーを解決できるようにする。
**presentation 限定（`keyboard_window.py`・`keyboard_layouts.py`）。application・domain・フック・送信・JSON スキーマ不変。`resolve_key_id_from_scan_code` の挙動（レイアウト → 既知の特殊キーの表）は変えない。**

## 対象範囲（presentation 限定・既存 2 ファイル + テスト）

### `keyseq/presentation/keyboard_layouts.py`

* 新しい関数 `resolve_layout_key_id_from_scan_code(layout: KeyboardLayout | None, scan_code: object) -> str` — 今の `resolve_key_id_from_scan_code` のレイアウトを引く部分だけ（`int` にできない・レイアウトなし・当たらないは `""`。既知の特殊キーの表へは落とさない）
* `resolve_key_id_from_scan_code` はこの関数で引き、当たらなければ今どおり `resolve_known_key_name_from_scan_code` へ落とす（挙動不変・重複を避けるための置き換えのみ）

### `keyseq/presentation/keyboard_window.py`

* `_normalize_tk_key`: レイアウトを引く部分を次に置き換える。順序（テンキー → `TK_KEYSYM_TO_KEYBOARD_NAME` → 走査コードでレイアウト → keysym の小文字）は変えない
  * `scan_code = win32_window.vk_to_scan_code(keycode)`（`keycode` が無い・`int` にできないときは呼ばずに飛ばす）。`None` ならレイアウトを引かない
  * `resolve_layout_key_id_from_scan_code(self._layout, scan_code)` で引き、当たれば `normalize_key_name` して返す
* import: `from keyseq.infrastructure import win32_window`（presentation → infrastructure の直接参照は前例 `keymap_panel_controller.py:13` と同じ）・`resolve_layout_key_id_from_scan_code`。使わなくなった `resolve_key_id_from_scan_code` の import は外す

### テスト

* `tests/test_keyboard_layout_files.py` か新規 `tests/test_keyboard_layout_scan_code.py`（どちらでもよい）: `resolve_layout_key_id_from_scan_code` がレイアウトに当たれば id・当たらなければ `""`（既知の表の 41 / 112 / 121 / 123 でも `""`）/ `resolve_key_id_from_scan_code` は今どおり既知の表へ落ちる（41 → `zenkaku_hankaku`）
* 新規 `tests_ui/test_keyboard_window_scan_code.py`: `KeyboardWindow._normalize_tk_key` を `SimpleNamespace(_layout=...)` を self にして呼ぶ（窓は作らない）。`keyboard_window.win32_window.vk_to_scan_code` を `patch` して実機に依存しない:
  1. F1 / F10 / F12（keysym `F1` 等・keycode 112 / 121 / 123・変換後 59 / 68 / 88）→ 既定の US TKL・jis.json の両方で `f1` / `f10` / `f12`
  2. jis.json で 無変換 / 変換 / 半角/全角（keycode 0x1D / 0x1C / 0xF3・変換後 123 / 121 / 41）→ `muhenkan` / `henkan` / `zenkaku_hankaku`
  3. 既定の US TKL で US の「`」（keysym `grave`・keycode 0xC0・変換後 41）→ `grave`（`zenkaku_hankaku` にならない）
  4. 変換できない（`None`）→ keysym の小文字（例: keysym `Kana`・keycode 0x15 → `kana` ではなく keysym 由来の名前）
  5. テンキー（既存の `numpad_name_from_tk_event`）と keysym の表（`Return` → `enter`）が先に効く（`vk_to_scan_code` を呼ばない）
  * jis.json は `config/user/keylayout/jis.json` を `load_layout_from_json` で読む（`tests/test_keyboard_layout_files.py` の読み方を手本）

### 設計メモ / 制約

* フックの実行時・画面の枠の編集の窓・`LayoutController.resolve_key_name_from_scan_code` は `resolve_key_id_from_scan_code` を使い続ける（既知の表へ落ちる挙動のまま・idea_49）
* `keyboard_window.py` の他の箇所・他の取得の入口は変えない

## 読むファイル

1. `instructions/phase/61_keyboard_ui_vk_to_scan_code/phase.md`（確定・含む）
2. `keyseq/presentation/keyboard_window.py:1-35`（import）・`_normalize_tk_key`（`def _normalize_tk_key` から 16 行）
3. `keyseq/presentation/keyboard_layouts.py:1-35,250-256,327-340`
4. `keyseq/infrastructure/win32_window.py:138-148`（`vk_to_scan_code`）
5. 手本: `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:452-467` / `tests/test_keyboard_layout_files.py:1-40`

## 含まない

* 正本・`codebase_map.md` の更新・decisions（task_02）
* フックの実行時・送信の既知の特殊キーの表の扱い（idea_49）/ 記号キーの名前（idea_45）/ かな（VK 0x15）の解決の作り込み

## 確認

* `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
* `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_keyboard_window_scan_code -v` と追加した `tests` のテストが全 pass（上記 1〜5）
* 既存の `tests`・`tests_ui`（同時に 1 本だけ）・`-m tests.smoke_app` が全 pass
* **ユーザーの実機目視**（JIS 配列・レイアウト = jis.json）: キーボードUI で元キーの枠をクリックし、F1 / F10 / F12・無変換・変換・半角/全角・かな を押して、送信先に入る名前（F キーは `f1` 等・無変換 / 変換 / 半角全角は `muhenkan` / `henkan` / `zenkaku_hankaku`・かなは何が入るかを記録）

## 完了条件

- 上記確認 pass・**reviewer 採用**・**ユーザーの実機目視 OK**。
