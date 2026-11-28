# task_01_key_symbols_load_and_domain

## 目的

レイアウトの JSON の任意キー `key_symbols` を読み込み（不正なら表だけを使わず理由を持つ）、domain の記号の表示と一覧の整形の関数が上書きの表を引数で受け取れるようにする（暫定 64 §3 の読込・§4・§5）。
**domain と presentation の `keyboard_layouts.py` 限定**。domain はレイアウトを参照しない（表は引数だけ）。表を実際に渡す配線（一覧・キーボードUI）は task_02、警告の表示は task_03。保存するキー名・送信・逆引き（`tk_keys.py:73`）は変えない。既存の呼び出し（引数なし）の表示は変えない。

## 対象範囲（domain + presentation/keyboard_layouts.py・新規の引数は既定 None）

### `keyseq/domain/key_symbols.py`

- `display_key_name(key_name: str, key_symbols: Mapping[str, str] | None = None) -> str` にする。
  - `key_symbols` があれば、`normalize_key_name(key_name)`（`keyseq/domain/config.py:122`）で引いて、見つかった値を返す。
  - 見つからない・`None` なら今と同じ（`KEY_SYMBOLS` を `strip().lower()` で引き、無ければ入力をそのまま返す）。
  - `normalize_key_name` の import で循環が起きる場合（`config.py:9` が `key_symbols` を import している）は、関数内で import するか、同じ正規化（`strip().lower()` + 別名 `{"minus": "-"}`）を `config.py` から参照できる形にする。正規化の規則を 2 か所に書き写さない。

### `keyseq/domain/config.py`

- `format_trigger_list_item(index, trigger, *, key_symbols: Mapping[str, str] | None = None)`: `display_key_name(..., key_symbols)` に渡す。
- `format_action_list_item(..., key_symbols: Mapping[str, str] | None = None)`（既存のキーワード引数の並びに足す）: key_hold の行のとき `key_hold.format_key_hold_value(action, key_symbols=key_symbols)` に渡す。他の種類の行は変えない。

### `keyseq/domain/key_hold.py`

- `format_key_hold_value(action, *, key_symbols: Mapping[str, str] | None = None)`: 解析に成功したキーの行（`parsed.button is None` の 2 か所・`:134`・`:136`）だけ `display_key_name(parsed.key, key_symbols)` にする。不正な行・マウスの行は今のまま（§4）。

### `keyseq/presentation/keyboard_layouts.py`

- `KeyboardLayout` に 2 つの欄を足す（既定値付き・既存の生成を壊さない）:
  - `key_symbols: tuple[tuple[str, str], ...] = ()`（`key_display_names` と同じ形）
  - `key_symbols_invalid_reason: str = ""`（空 = 不正でない。不正なら理由の文言〔翻訳済み〕）
  - 上書きの表を dict で返すプロパティ（例 `key_symbol_map`）。task_02 が domain へ渡すのに使う。
- `validate_layout_json` で `key_symbols` を読む（§3）:
  - 無い・`null` → 空・理由なし。
  - 次のどれかなら**例外を投げず**、表を空・理由を 1 つ（最初に見つかったもの）にする: object でない / 値が文字列でない / キーを `normalize_key_name` すると空 / 値に `\n` か `\r` を含む。
  - 正規化後に重なるキーは後に書いた方。値が空文字・空白だけ（`strip()` が空）のキーは表に入れない（不正ではない）。それ以外の値は書いたまま（前後の空白も除かない）。
  - 戻り値の dict に `key_symbols` と `key_symbols_invalid_reason` を足し、`keyboard_layout_from_dict` で `KeyboardLayout` へ渡す。
  - `key_display_names` 等ほかの項目の読込エラーは今のまま（例外）。
- 内蔵の US TKL（`BUILTIN_LAYOUTS`）は空・理由なし（既定値のまま）。

### `keyseq/shared/i18n/locales/ja.json`・`en.json`

- 理由の文言 4 つ（object でない / 値が文字列でない〔キー名を含める〕/ キーが空 / 値に改行〔キー名を含める〕）を両方に足す。キー名は既存の `keyboard.layout.error.key_display_name*`（`ja.json:205-207`）に倣い `keyboard.layout.key_symbols.invalid.<種類>` 等。表記は `instructions/common/spec_detail/ui_terms.md`（日本語の表記規則・英語 E1〜E7）。

### テスト（追加・既存の期待値は変えない）

- `tests/test_key_symbols.py`: 上書きの表あり（当たる・当たらないで `KEY_SYMBOLS` へ落ちる・表に無い名前はそのまま）/ `minus` を `-` の上書きで引く / `None` と空の表で今と同じ。
- `tests/test_domain_config.py`: `format_trigger_list_item` に表を渡すと上書き・渡さないと今のまま / `format_action_list_item` の key_hold の行に表が届く。
- `tests/test_key_hold.py`: キーの行（押す・離す・リピート）は上書き / 不正な行（`[key_hold] <値>`）・マウスの行は表を渡しても変わらない / `value: "minus"` の行が `-` の上書きに当たる。
- `tests/test_keyboard_layout_files.py`（または同じ読込のテストがあるファイル）: `key_symbols` の正常 / 無い・`null` / 4 つの不正（例外にならず表が空・理由が入り、`keys` など他の項目は読める）/ 重なるキーは後勝ち / 空文字・空白だけは表に入らない / 前後の空白を保つ / `key_symbol_map` の dict / 内蔵の US TKL は空。

## 読むファイル

- 暫定 64: `instructions/history/64_layout_key_symbols.md` §3〜§5
- `keyseq/domain/key_symbols.py`（全体）・`keyseq/domain/config.py:1-20`・`:117-125`・`:487-555`・`keyseq/domain/key_hold.py:80-145`
- `keyseq/presentation/keyboard_layouts.py:1-45`・`:140-300`（`key_display_names` の読込が手本）
- `keyseq/shared/i18n/locales/ja.json:200-210`・`en.json` の同じキー
- テストの手本: `tests/test_key_symbols.py`・`tests/test_domain_config.py:595-630`・`tests/test_keyboard_layout_files.py` の `key_display_names` のテスト

## 含まない

- 表を一覧・キーボードUI・呼び出し先の表示枠へ渡す配線と、レイアウトの切替での描き直し（task_02）
- ステータスバーの警告の下敷き・追加のときの文言・見本 jis.json / us_tkl.json の変更（task_03）
- 正本 `spec_detail/`・`codebase_map.md` の更新（task_05）
- `KEY_SYMBOLS` の値の変更・`tk_keys.py:73` の逆引きの変更

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_key_symbols tests.test_domain_config tests.test_key_hold tests.test_keyboard_layout_files` が pass（追加分を含む）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass（既存の期待値は不変・暫定 64 §8-2・§8-9）
- i18n の静的テスト（ja / en のキーの一致・ソースに日本語を書かない）が tests に含まれて pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は無し（task_04 でまとめて実施）。
