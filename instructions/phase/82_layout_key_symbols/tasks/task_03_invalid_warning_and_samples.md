# task_03_invalid_warning_and_samples

## 目的

選んでいるレイアウトの `key_symbols` が不正で使えないとき、ステータスバー中央の一時メッセージ欄の「下敷き」として警告を出す（ほかの一時メッセージが消えたら戻す）。レイアウトの追加で読んだレイアウトの `key_symbols` が使えないときは、追加できたことと警告の両方を出す。見本の jis.json / us_tkl.json に `key_symbols` を書く（暫定 62 §3 の警告・§7）。
**presentation と見本の JSON 限定**。domain・application・infrastructure・`keyboard_layouts.py` の読込（task_01 で済み）は変えない。新しい部品は作らず、ダイアログも使わない。

## 対象範囲（presentation + 見本 JSON）

### `keyseq/presentation/app.py`（一時メッセージ欄の下敷き）

- 下敷きの文言 `self._flash_underlay: str = ""` を持つ（`_flash_message` の初期化 `:368-369` の隣）。
- `set_flash_underlay(text: str) -> None` を足す: 文言を持ち直し、今の一時メッセージ（`_flash_message`）が空なら欄にすぐ出す（空の文言なら欄を空にする）。一時メッセージがあれば欄は変えない。
- 欄に出す文言 = 一時メッセージがあればそれ、無ければ下敷き。次の 3 か所をこの規則にする:
  - `_clear_flash_message`（`:539`）: 空にする代わりに下敷きを出す。
  - `_set_flash_message`（`:544`）: `msg` が空なら下敷きを出す（`_flash_message` は空のまま）。`msg` があれば今と同じ。
  - `_refresh_status_bar`（`:524`）: 同じ規則で書き直す。
- `_flash_message`（今の一時メッセージ）の意味は変えない（`hook_controller.py:290` が読む）。4 秒で消える・消えないの動きも変えない。

### `keyseq/presentation/controllers/layout_controller.py`

- `_refresh_active_layout`（`:223`）の末尾で、選んでいるレイアウト（`self._active_layout`）の `key_symbols_invalid_reason` が空でなければ警告の文言（表示名 `display_name` と理由）を、空なら `""` を `self._app.set_flash_underlay(...)` に渡す（`app` が持たなければ何もしない）。これで起動・構成の読込・選択・追加・削除・フックキーの個別設定の切替の読み直しのたびに下敷きが決め直される（§3）。
- `add_external_keyboard_layout`（`:349`）: 読んだ `layout` の `key_symbols_invalid_reason` が空でなければ、`keyboard.layout.added` の代わりに、追加できたことと警告の両方が分かる文言で `_set_flash_message` する（自動で消える・今と同じ）。空なら今のまま。

### `keyseq/shared/i18n/locales/ja.json`・`en.json`

- 警告の文言（例 `keyboard.layout.key_symbols.ignored`: 「レイアウト「{name}」の key_symbols を使っていません: {reason}」）と、追加のときの文言（例 `keyboard.layout.added_key_symbols_ignored`: 追加した旨 + 警告）を両方に足す。表記は `instructions/common/spec_detail/ui_terms.md`（日本語の表記規則・英語 E1〜E7）。

### 見本 `config/user/keylayout/`（§7）

- `jis.json`: 最上位に `"key_symbols": {"backslash": "＼", "\\": "＼", "ro": "＼"}`（`＼` は全角 U+FF3C・`yen` は書かない）。`key_display_names` の行の直後に置く。
- `us_tkl.json`: 最上位に `"key_symbols": {}`（`key_display_names` の直後）。
- `jis_mac.json`・`us_mac.json`・`de.json`・`jis_test.json` は変えない。
- ファイルの他の部分（並び・書式）は変えない。

### テスト（追加。期待値を変える既存のテストがあれば `ファイル:行` を報告）

- app の下敷き（`tests/test_app_control_sync.py` の手本に倣う単体、または `tests_ui` で `App` を使う場合は import 直後に `fix_language("ja")`）: 下敷きだけ → 欄に出る / 一時メッセージ → そちらが出る / 自動で消える・空で置き換える → 下敷きに戻る / 下敷きを空にする → 一時メッセージが無ければ欄が空 / 一時メッセージ中に下敷きを変えても欄は変わらない。
- `tests/test_layout_controller_registration.py`（または `test_layout_controller_scan_code.py`）: 不正な `key_symbols` のレイアウトを選ぶ → `set_flash_underlay` に表示名と理由を含む文言 / 正常なレイアウト → `""` / 追加したレイアウトが不正 → 追加の警告の文言・正常 → 今の `keyboard.layout.added`。
- `tests/test_keyboard_layout_files.py`: jis.json の `key_symbol_map` が 3 件（`backslash`・`\`・`ro` → `＼`）で理由が空 / us_tkl.json は空で理由が空 / jis_mac.json は空。
- ja / en のキーの一致（既存の静的テストで通ること）。

## 読むファイル

- 暫定 62: `instructions/history/62_layout_key_symbols.md` §3（警告）・§7
- `keyseq/presentation/app.py:360-372`・`:510-560`
- `keyseq/presentation/controllers/layout_controller.py:215-245`・`:345-375`
- `keyseq/presentation/controllers/hook_controller.py:283-300`（`_flash_message` の読み方を変えないための確認）
- `keyseq/presentation/keyboard_layouts.py:22-40`（`key_symbols_invalid_reason`・`display_name`）
- `keyseq/shared/i18n/locales/ja.json:185-225`・`en.json` の同じキー
- `config/user/keylayout/jis.json:1-6`・`us_tkl.json:1-6`
- テストの手本: `tests/test_app_control_sync.py:30-70`・`tests/test_layout_controller_registration.py`（既存のテストの書き方だけ）・`tests/test_keyboard_layout_files.py:280-300`

## 含まない

- 統合確認と実機目視（task_04）・正本の更新（task_05）
- 選んでいないレイアウトの警告（追加のとき以外）・警告専用の欄・ダイアログ
- `keyboard_layouts.py` の読込・domain の変更（task_01）・表の配線と描き直し（task_02）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass
- 変更に関係する tests_ui のモジュール（下敷きのテストを tests_ui に置いた場合はそのモジュール・`tests_ui.test_app_ui_flows`）が pass
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass
- tests_ui 全体は task_04 で流す

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_04 でまとめて実施（jis.json での `＼` の表示・不正な `key_symbols` の警告）。
