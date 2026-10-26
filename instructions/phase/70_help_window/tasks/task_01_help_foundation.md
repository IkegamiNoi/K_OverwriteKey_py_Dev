# task_01_help_foundation

## 目的

ヘルプの土台を作る: `__version__`（暫定 53 §7.1）・同梱データの位置の解決を 1 か所に集める関数（§7.2 末尾）・
本文データファイルの読込と検査（§5.1・§5.2・§4.3 の NFC / 結合文字なし）・フィルターの純関数（§4.3）・
大分類だけの `help_ja.json` の骨組み（§5.3）。
**presentation 限定（`keyseq/presentation/help/` を新設）+ `keyseq/__init__.py`。Tk に依存しない純関数とデータのみ。
domain / application 不変・config の JSON スキーマ不変。窓・メニューは作らない。**

## 対象範囲（新規ファイル + `keyseq/__init__.py` の 1 行）

### `keyseq/__init__.py`

- `__version__ = "0.1.0"` を足す（docstring は残す）。

### `keyseq/presentation/help/__init__.py`（新規）

- パッケージ docstring のみ（再輸出はしない）。

### `keyseq/presentation/help/bundled_paths.py`（新規）

- `bundled_root() -> Path`: 同梱データの基準位置 = リポジトリ直下（`keyseq/` の親）。`__file__` 基準で求める。
  **位置の解決はこの関数 1 つだけ**（exe 化のフェーズではここだけ直す）。docstring にその旨を書く。
- 派生（すべて `bundled_root()` から求める。ほかの場所で `__file__` から組み立てない）:
  - `license_path() -> Path` = `bundled_root() / "LICENSE"`
  - `help_content_dir() -> Path` = `bundled_root() / "keyseq" / "presentation" / "help" / "content"`
  - `help_content_path(lang: str = "ja") -> Path` = `help_content_dir() / f"help_{lang}.json"`
  - `third_party_dir() -> Path` = `help_content_dir() / "third_party"`（フォルダ自体は task_05 で作る。本タスクでは関数だけ）

### `keyseq/presentation/help/help_content.py`（新規）

- frozen dataclass:
  - `HelpBlock(kind: str, text: str = "", items: tuple[str, ...] = ())` — `kind` は `"p"` / `"list"`
  - `HelpItem(id: str, title: str, body: tuple[HelpBlock, ...])`
  - `HelpCategory(id: str, title: str, items: tuple[HelpItem, ...])`
  - `HelpContent(guide: tuple[HelpCategory, ...], faq: tuple[HelpCategory, ...])`
  - `HelpLoadResult(content: HelpContent | None, error: str = "")` — 成功なら `content` あり・`error` 空、失敗なら `content=None`・`error` に理由
- `parse_help_content(data: object) -> HelpContent`: §5.2 の形式を検査して組み立てる。誤りは `ValueError`（理由の文言は日本語・どこの誤りか分かる形。例 `tabs.guide[0].items[1].id が重複しています: keymap.switch`）。検査:
  - 最上位が object・`format == 1`（int。bool は不可）・`tabs` が object で `guide` と `faq` がともに配列
  - 大分類: object・`id` / `title` が空でない文字列・`items` が配列（空配列は可＝骨組み用）
  - 項目: object・`id` / `title` が空でない文字列・`id` が「大分類 id + `.` + 空でない名前」・`body` が配列
  - `body` の要素: `{"type": "p", "text": 文字列}` または `{"type": "list", "items": [文字列, ...]}`（`items` は空でない配列・要素はすべて文字列）。それ以外の `type` は誤り
  - `id` は大分類・項目を通してファイル全体（guide と faq の両方）で一意
  - 未知のキーは無視する（拒否しない）
- `load_help_content(path: Path | None = None) -> HelpLoadResult`: 既定は `help_content_path("ja")`。UTF-8 で読み `json.loads` → `parse_help_content`。
  **ファイルが無い・読めない（`OSError`）・`UnicodeDecodeError`・JSON の誤り・`ValueError` は例外を外へ出さず** `HelpLoadResult(None, 理由)` を返す（§5.2。部分表示はしない＝一部の誤りでも全体を失敗にする）。
- `item_plain_text(item: HelpItem) -> str`: 本文を検索・表示用の 1 つの文字列にする（ブロックを `"\n"` でつなぐ。`list` は各箇条を `"\n"` でつなぐ。箇条の記号は付けない）。
- `find_text_issues(content: HelpContent) -> list[str]`: §4.3 の条件を検査し、違反の説明を返す（無ければ空）。対象 = 大分類名・項目の見出し・本文のすべての文字列。条件:
  - `unicodedata.is_normalized("NFC", s)` であること
  - 各文字 `c` について `unicodedata.normalize("NFKC", c)` に一般カテゴリ `M*`（`unicodedata.category(x).startswith("M")`）の文字が含まれないこと
  - 読込（`load_help_content`）では呼ばない（検査テスト専用。同梱データなので出荷前にテストで止める）

### `keyseq/presentation/help/help_filter.py`（新規・Tk 非依存の純関数）

- `normalize_text(s: str) -> str` = `unicodedata.normalize("NFKC", s).casefold()`
- `parse_query(query: str) -> tuple[str, ...]`: 全体を `normalize_text` → 前後の空白を除く → 空白（全角空白を含む。NFKC で半角になる。`str.split()` で可）で区切った語の tuple。空なら `()`。
- `NormalizedText`（frozen dataclass）: `text: str`（正規化後）・`positions: tuple[int, ...]`（正規化後の各文字 → 元の文字の位置。`len(positions) == len(text)`）
- `normalize_with_positions(s: str) -> NormalizedText`: **1 文字ずつ** `normalize_text` し、広がった全部の文字を元の 1 文字の位置へ対応させる（`ß`→`ss`・`㍿`→`株式会社`）。
- `item_matches(fields: Sequence[str], terms: Sequence[str]) -> bool`: 各 field を 1 文字ずつ正規化したものを `"\n"` でつないだ文字列に、すべての語が部分文字列として含まれるか（AND・境界をまたぐ一致を作らない）。`terms` が空なら `True`。
  呼び出し側は `fields = (大分類名, 項目の見出し, item_plain_text(item))` を渡す想定（本タスクでは関数のみ）。
- `highlight_ranges(s: str, terms: Sequence[str]) -> list[tuple[int, int]]`: `s`（項目の見出しまたは本文）の中の一致箇所を、**語ごと・出現ごとにすべて**、元の文字列上の `[start, end)` で返す（正規化後の一致 `[a, b)` → `(positions[a], positions[b-1] + 1)`）。出現の探索は 1 文字ずつずらして重なる出現も拾う。結果は `(start, end)` の昇順・重複する同一範囲は 1 つにまとめる（隣接・重なりの併合はしない）。`terms` が空なら `[]`。
- 1 文字が広がった文字の途中だけに一致した場合（例: 語 `s` が `ß` の片方）も元の 1 文字全体を範囲にする（上の変換で自然にそうなる）。

### `keyseq/presentation/help/content/help_ja.json`（新規・骨組み）

- `{"format": 1, "tabs": {"guide": [...], "faq": [...]}}`。大分類だけを並べ、`items` はすべて空配列（本文は task_06）。
- guide（この順・`id` / `title`）: `intro` はじめに / `config_set` 構成セットとファイル / `keymap` キーマップ / `trigger` トリガー / `sequence` 出力シーケンス / `hook` フック / `view_mode` 表示の切替 / `keyboard_ui` キーボードUI / `screen_grid` 画面の枠 / `preset` プリセット / `file_cleanup` ファイルの整理
- faq（この順）: `trouble` 動かないとき / `limits` できないこと / `save_files` 保存とファイル / `key_input` キーの入力
- UTF-8・2 スペース字下げ・末尾改行。

### tests（新規）

- `tests/test_help_content.py`
  - 同梱の `help_ja.json` が `load_help_content()` で成功し（`error == ""`）、`find_text_issues` が空・`format`/大分類の id と並びが上の一覧どおり
  - `bundled_paths`: `license_path()` が存在するファイル・`help_content_path()` が存在・すべての派生が `bundled_root()` の下
  - 形式の誤りごとに `parse_help_content` が `ValueError`（format 違い・bool の format・tabs 欠落・guide が配列でない・id 空・項目 id の接頭辞違い・id 重複〔guide と faq を跨ぐ場合を含む〕・未知の body type・list の items が空 / 文字列以外）
  - 正常系: p と list を含む項目が dataclass へ正しく入る・未知のキーは無視
  - `load_help_content` の失敗: 無いファイル・壊れた JSON・UTF-8 でないバイト・形式の誤り → いずれも例外を出さず `content is None` かつ `error` が空でない（一時フォルダを使う）
  - `item_plain_text` のつなぎ方
  - `find_text_issues`: NFD の文字（`"が"`）・半角カナの濁点（`"ｶﾞ"`）・結合文字単独を検出し、通常の日本語・`ß`・`㍿` は検出しない
- `tests/test_help_filter.py`
  - `parse_query`: 前後の空白・全角空白区切り・全角英数と大小（`"ＡＢＣ　def"` → `("abc", "def")`）・空 / 空白のみ → `()`
  - `normalize_with_positions`: `ß` / `㍿` の広がりと位置・`len(positions) == len(text)`
  - 検索語 `ｶﾞ` と `ガ` のどちらでも本文の「ガ」に一致し、`highlight_ranges` が元の「ガ」の位置を返す（§10-4）
  - `ß` / `㍿` を含む本文で、後ろの一致の位置がずれない（例: `"㍿テスト"` で `テスト` → `(1, 4)`）・`"ss"` で `"ßx"` → `(0, 1)`
  - `item_matches`: AND・ひらがなとカタカナは区別・大分類名だけ / 見出しだけ / 本文だけの一致・**field 境界をまたぐ語は一致しない**・語なしは `True`
  - `highlight_ranges`: 複数語・同じ語の複数出現・重なる出現（`"aaa"` で `"aa"` → `(0,2),(1,3)`）・昇順
- `tests/test_version.py`（または `test_help_content.py` 内）: `keyseq.__version__ == "0.1.0"`

### 設計メモ / 制約

- §4.3 の「1 文字ずつの正規化と全体の正規化の一致」は、`find_text_issues` が空であることを前提に成り立つ。フィルター側で全体の正規化に切り替えたり、結合文字を特別扱いする分岐を作らない。
- 検索語側は全体を正規化する（`parse_query`）。本文側は 1 文字ずつ（`normalize_with_positions`）。
- `help/` から domain / application / infrastructure を import しない。tkinter も import しない（本タスクの全ファイル）。
- 関数はおおむね 30 行以内（検査は小関数に分ける）。

## 読むファイル

- `instructions/history/53_help_window.md` §2（38-57 行）・§4.3（97-110 行）・§5（127-172 行）・§7.1〜§7.2（221-241 行）
- `keyseq/__init__.py`（編集対象）
- `instructions/common/spec_detail/ui_terms.md`（大分類名の表記確認のみ。必要時）
- 既存テストの書き方の手本: `tests/test_keyboard_layout_files.py` の冒頭 40 行程度（unittest 形式）

## 含まない

- ヘルプの窓・メニュー「ヘルプ」（task_02）
- フック停止・フォント追従・常に手前（task_03）
- ダイアログの「?」と飛び先 id の検査（task_04）
- バージョン情報・ライセンスの窓・`third_party/` のデータと版の検査（task_05。本タスクは `third_party_dir()` の関数のみ）
- 本文の執筆（task_06）
- `app.base_dir`（config の位置）の変更・正本 / codebase_map の更新（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_help_content tests.test_help_filter`（+ `tests.test_version` を作った場合）pass
- tests 全体 pass（件数 ≥ 直近 1834 + 追加分）/ tests_ui 全体（既知の負債 `test_compact_window` の 1 件を除き pass）/ smoke pass
- `keyseq/presentation/help/` 配下に tkinter・domain・application の import が無いこと（grep）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視なし（画面を作らないため）。まとめての目視は task_08
