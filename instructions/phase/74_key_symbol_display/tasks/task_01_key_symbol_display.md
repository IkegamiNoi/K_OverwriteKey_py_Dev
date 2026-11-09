# task_01_key_symbol_display

## 目的

正本 `features.md` §4.6「記号キーのキー名の表示」を実装する。記号キーの単語のキー名を、キーボードUIのキー置換の枠・トリガー一覧・出力シーケンス一覧の key_hold で記号として表示する。
**domain + presentation の表示のみ。保存値・送信・記録・JSON スキーマは不変。**

## 対象範囲（表示の 3 箇所と変換の表のみ）

### 新規 `keyseq/domain/key_symbols.py`

- 正本の表 35 個を定数の dict で持つ。
- `display_key_name(key_name: str) -> str`: `key_name` を trim + 小文字にして表を引き、あれば記号、無ければ**渡された `key_name` をそのまま**返す。

### `keyseq/domain/config.py`

- `format_trigger_list_item` で、正規化後の `key` を `display_key_name` に通して表示する。

### `keyseq/domain/key_hold.py`

- `format_key_hold_value` のキーの行（リピートあり / なしの 2 つ）で `parsed.key` を `display_key_name` に通して表示する。不正な行とマウスボタンの表示は変えない。

### `keyseq/presentation/keyboard_window.py`

- `redraw` の `kind == "keymap"` の分岐を、`key_display_names` の値 → `display_key_name(display)` の順にする。`kind` が keymap 以外の枠は変えない。

### テスト

- 新規 `tests/test_key_symbols.py`: 表の全 35 個の対応 / 大文字・前後の空白 / 表に無い名前はそのまま / 空文字。
- `tests/test_domain_config.py`: トリガー一覧で `bar` → `01. |: label` 相当、記号でないキーは不変。
- `tests/test_key_hold.py`: `[press] |`・リピートありの行（`bar` → `|（リピート）`）・`[release]` の行。
- `tests_ui/test_keyboard_key_text.py` に、キーボードUIの枠で`bar` が `|` になること・`key_display_names` が優先されることを足す。

### 設計メモ / 制約

- `key_symbols.py` は `config.py` を import しない（`config.py` から import するため循環を避ける）。
- 表の値は言語ファイルに入れない（`tr` を通さない）。
- `normalize_key_name` と `_KEY_NAME_ALIASES` は変更しない。

## 読むファイル

- `instructions/common/spec_detail/features.md` の見出し「記号キーのキー名の表示」の項
- `keyseq/domain/config.py:115-117,460-465`
- `keyseq/domain/key_hold.py`（import 部と 119-139 行）
- `keyseq/presentation/keyboard_window.py`（import 部と 461-464 行）
- `tests/test_domain_config.py:590-597`
- `tests/test_key_hold.py:155-170`
- `tests_ui/test_keyboard_key_text.py`（手本の既存テスト）

## 含まない

- hotkey の一覧・入力欄・キーマップ編集のキー置換一覧・切替 / 停止 / トグルキーの欄の表示
- 保存するキー名と記録の経路の変更（idea_45）
- `codebase_map.md` の更新・統合確認・実機目視（task_02）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui`
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_key_symbols tests.test_domain_config tests.test_key_hold tests.test_keyboard_layout_files` が pass
- `../../../.venv/Scripts/python.exe -m unittest tests_ui.test_keyboard_key_text` が pass
- 静的確認: `display_key_name` の呼び出しが上記 3 ファイルとテストだけであること

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_02 でまとめて実施。
