# task_01_key_display_names_and_samples

## 目的

レイアウトの JSON の最上位の任意キー `key_display_names`（キー名 → 表示名）を読み込めるようにし（暫定 52 §4.1）、
見本 `config/user/keylayout/us_tkl.json`（内蔵の US TKL と同じ行）を新規に置き、jis.json に表の例と `label` の改行を足す（§2-9・§6）。
**presentation のレイアウト読込（`keyboard_layouts.py`）と見本 JSON・tests に限定。描画（キーボードUI）は変えない。既存キーの意味は不変（表が無い JSON は今と同じ）。**

## 対象範囲（keyboard_layouts.py・見本 JSON・tests 限定）

### `keyseq/presentation/keyboard_layouts.py`

- `KeyboardLayout` に `key_display_names: tuple[tuple[str, str], ...] = ()` を足す（正規化済みのキー名と表示名の組・frozen のまま。既定は空）
- `KeyboardLayout` にメソッド `key_display_name(self, key_name: str) -> str | None` を足す: `normalize_key_name(key_name)` が表にあり値が空でなければその値、無ければ `None`（同じキーが複数あるときは後の組）
- `validate_layout_json` に `key_display_names` の検証を足し、戻り値の dict に `"key_display_names"`（組の tuple）を入れる（§4.1）:
  - 無い・`null` → 空
  - object（dict）でなければ `ValueError`（文言は既存にならう: `key_display_namesはobjectである必要があります。`）
  - 値が文字列でなければ `ValueError`（`key_display_names.<元のキー>は文字列である必要があります。`）
  - キーは `normalize_key_name` で正規化（正規化して空になるキーは `ValueError`: `key_display_namesのキーが空です。`）
  - 正規化後に重なるキーは後に書いた方を採る（拒否しない）。組の tuple には重なりを除いた結果を JSON の出現順で入れる
  - 値は空文字も可（`key_display_name` で `None` 扱い）・値の `\n` はそのまま保持（strip しない）
- `keyboard_layout_from_dict` で `key_display_names` を `KeyboardLayout` へ渡す
- 内蔵の `BUILTIN_LAYOUTS` は変えない（表は空 = 既定値）

### `config/user/keylayout/us_tkl.json`（新規）

- `layout_id` = `us_tkl_sample`・`display_name` = `US TKL（見本）`・`key_display_names` = `{}`
- `keys` = `_DEFAULT_US_TKL_KEYS`（`keyboard_layouts.py:38-126`）と同じ行・同じ順。各行に `id`・`label`・`x`・`y`・`w`・`h` を明記（省略していた `w` / `h` は 1.0）。`scan_code` は書かない
- 書式は jis.json にならう（1 行 1 キー・UTF-8・2 スペース字下げ）
- `.gitignore` の `config/` に当たるため、コミット時に `git add -f` が必要（実装者はコミットしない。メインが行う）

### `config/user/keylayout/jis.json`

- 最上位の `display_name` の後に `"key_display_names": {"zenkaku_hankaku": "半角\n全角"}` を足す
- `zenkaku_hankaku` の行の `label` を `"半角\n全角"` にする（他の行は変えない）

### `tests/test_keyboard_layout_files.py`

- `LAYOUT_PATHS` に `"us_tkl": LAYOUT_DIR / "us_tkl.json"` を足す（既存の全見本の検査に us_tkl も入る）
- 追加テスト:
  - `key_display_names` が無い / `null` → 空・`key_display_name` は `None`
  - object でない（配列・文字列）→ `ValueError` / 値が文字列でない（数値・`null`）→ `ValueError` / 正規化して空になるキー（`"  "`）→ `ValueError`
  - キーの正規化（例: `"Page Up"` と `page up` の照会が一致）・重なりは後勝ち・空文字の値は `None`・`\n` を保持
  - us_tkl.json の行（`id`・`label`・`x`・`y`・`w`・`h`・`scan_code`〔None〕・`extra_scan_codes`〔空〕）が内蔵の US TKL と同じ順で完全に一致し、`layout_id` = `us_tkl_sample`・表は空
  - jis.json の `key_display_name("zenkaku_hankaku")` = `"半角\n全角"`・その行の `label` = `"半角\n全角"`

### 設計メモ / 制約

- 既存の `extra_scan_codes` の検証（`keyboard_layouts.py:211-220`）と同じ書き方・同じ文言の調子にそろえる
- `KeyboardLayout` は比較・写し（phase 65 の `LayoutController` の写し）に使われるため、可変の dict を持たせない（tuple の組）
- 表示名をキーボードUIで使うのは task_02。本タスクでは参照用のメソッドまで

## 読むファイル

- `keyseq/presentation/keyboard_layouts.py`（編集対象・全体）
- `config/user/keylayout/jis.json`（編集対象・全体）
- `tests/test_keyboard_layout_files.py`（編集対象・全体）
- `instructions/history/52_keyboard_ui_key_labels.md` §2・§4.1・§6

## 含まない

- キーボードUIでの表示名の使用・文字合わせ・`\n` の描画（task_02）
- 最小サイズ（task_03）・幅の記録（task_04）
- 正本（`features.md` §4.6・`codebase_map.md`）の更新（task_06）
- de.json の変更

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_keyboard_layout_files` pass（追加テスト含む）
- tests 全体 pass（件数 ≥ 直近 1819 + 追加分・skip 7 は環境依存）/ tests_ui 全体 pass（1149）/ smoke pass
- `us_tkl.json` が JSON として読め、`load_layout_from_json` で読み込める

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_06 でまとめて実施
