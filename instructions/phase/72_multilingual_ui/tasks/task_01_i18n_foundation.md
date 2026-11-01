# task_01_i18n_foundation

## 目的

多言語対応の基盤を作る（暫定 55 §3・§4・§5・§3.4）。文言カタログ `keyseq/shared/i18n/`・言語の決定・
テストの言語固定・メニュー「設定」の言語の項目と保存・再起動の知らせ・ヘルプ本文の読む順。
**新規 `keyseq/shared/`（標準ライブラリのみ・他の層を import しない）+ presentation の結線。application / domain / infrastructure は不変。
既存の文言のキー化はしない**（task_03〜06）。config.json の任意キー `ui_language` を足す（読み書きの既存経路は変更しない）。

## 対象範囲（新規 shared/i18n + presentation の結線 + テスト）

### `keyseq/shared/__init__.py`・`keyseq/shared/i18n/`（新規）

- `__init__.py` は公開面の再輸出のみ（下記の関数）。実体は `catalog.py`（読込・引き方）等に分けてよい。各ファイル 300 行以内。
- `locales/ja.json`・`locales/en.json`（UTF-8・暫定 55 §3.1 の形式）。本 task で入れるキーは `_meta` と本 task の新規文言だけ:
  | キー | ja | en |
  |---|---|---|
  | `_meta.name` | 日本語 | English |
  | `menu.settings.language` | 言語 / Language | Language / 言語 |
  | `dialog.language_restart.title` | 言語 | Language |
  | `dialog.language_restart.body` | 言語の変更はアプリを再起動すると反映されます。 | The language change will take effect after you restart the app. |
- 関数（シグネチャはこのとおり。`key` / `lang` は**位置専用**）:
  - `tr(key, /, **params) -> str` — 今の言語で引く。探す順 = 今の言語 → `en` → `ja` → キー文字列（重複は飛ばす）。
    全部に無いときはキー文字列を返し、キーごとに 1 回だけ `logging.warning`。差し込み（`str.format_map`）に失敗したら
    差し込み前の文字列を返して warning（例外にしない）。`params` が空なら差し込みをしない（`{` を含む文言をそのまま返す）。
  - `tr_in(lang, key, /, **params) -> str` — 指定した言語で 1 回だけ引く（同じ探す順・同じ失敗時の扱い）。今の言語は変えない。
  - `available_languages() -> list[tuple[str, str]]` — `(code, _meta.name)` の一覧。並び = `ja`・`en`・残りはコード順。
    ファイル名 `<code>.json` の `<code>` が `^[a-z0-9]+(-[a-z0-9]+)*$` に合わないもの・読めない / JSON オブジェクトでない /
    `_meta.name` が文字列でないものは除く（warning）。
  - `resolve_language(value) -> str` — `ui_language` の保存値から使う言語を決める純関数。文字列で一覧にあるコードならそれ、
    それ以外（無い〔None〕/ 非文字列 / 一覧に無い）は `"en"`。
  - `set_language(code) -> None` — 今の言語を決める（App が起動時に 1 回呼ぶ）。`fix_language` 済みなら何もしない。
  - `current_language() -> str`
  - `fix_language(code) -> None` — **テスト用**。今の言語を固定し、以後の `set_language` を無視する。
  - `reset_for_tests(locales_dir: Path | None = None) -> None` — **テスト用**。読込済みのカタログ・固定・警告済みキーを捨て、
    必要なら locales の場所を差し替える（暫定 55 §3.1 の「場所を差し替える口」を兼ねる）。
- 言語を決める前（`set_language` 前）に `tr` が呼ばれたら `ja` を今の言語として使う（暫定 55 §3.2）。
- カタログは使うときに読み、読んだものを保持する（言語ごと）。値が文字列でないキーはそのキーだけ無いものとする。
  別スレッドから `tr` が呼ばれても壊れないよう、読込は `threading.Lock` で守る。
- locales の場所の既定は `Path(__file__)` からの相対。

### `keyseq/presentation/app.py`

- `__init__` で、`load_startup_settings` の直後・**画面を作る前**（`apply_global_theme` より前）に
  `set_language(resolve_language(self._startup_settings.get("ui_language")))` を呼ぶ。
- `load_startup_settings` の `on_read_error` は、その場で messagebox を出さず例外を保持し、言語を決めた後に今と同じ文言で
  警告を出す（文言のキー化は task_03）。
- `set_ui_language(code: str) -> None` を足す: 保存済みの `ui_language`（`self._startup_settings` の値を `resolve_language` した言語）
  と同じなら何もしない。違えば `self.startup_io.write_startup({"ui_language": code})` を呼び、成功したら
  `messagebox.showinfo(tr_in(code, "dialog.language_restart.title"), tr_in(code, "dialog.language_restart.body"), parent=self)`。
  今の言語（`current_language()`）は変えない。

### `keyseq/presentation/ui_vars.py`

- 保存済みの言語を持つ `ui_language_var`（`tk.StringVar`・初期値 = `resolve_language(保存値)`）を足す（メニューのラジオ項目の変数）。

### `keyseq/presentation/views/menu_bar.py`

- 「設定」の「フォントサイズ」の cascade の直後に、`tr("menu.settings.language")` の cascade を足す。中は
  `available_languages()` のラジオ項目（label = 表示名・value = コード・variable = `ui_language_var`・
  command = `app.set_ui_language(code)`）。チェックは保存済みの言語に付く（今表示している言語ではない）。

### `keyseq/presentation/help/help_content.py`

- `load_help_content(path=None)`: `path` が None のとき、`help_content_path(lang)` を `current_language()` → `en` → `ja`
  （重複は飛ばす）の順に試し、最初に読めて今の検証を通ったものを返す。全部だめなら最初の言語の失敗結果を返す
  （窓内の表示は今のまま）。`path` を渡したときは今のまま（その 1 ファイルだけ）。検証エラー文のキー化はしない（task_05）。

### テスト（追加・修正）

- 新規 `tests/test_i18n.py`: §確認の i18n 項目。locales は `reset_for_tests(tmp_dir)` で一時フォルダへ差し替えて検証し、
  最後に `reset_for_tests()` で戻す。
- **テストの言語固定**: tests / tests_ui のうち `App()` を作る、または画面の文言を assert するテストモジュールすべての import 直後に
  `fix_language("ja")` を 1 行足す（tests_ui は `-s tests_ui` で起動するため共通の初期化を置けない）。
  加えて、`App(` を含むテストモジュールが `fix_language(` を含むことを調べる静的テストを `tests/test_i18n_test_language_fixed.py` に置く。
- tests_ui: メニューに言語の cascade とラジオ項目（日本語・English）があること / 違う言語を選ぶと `write_startup` に
  `ui_language` が渡り、選んだ言語の文言で `showinfo` が出る（messagebox を patch）/ 同じ言語なら書かない・出さない /
  今の言語は変わらない。
- `ui_language` が書き込みの 2 経路で残ること: `startup_io.write_startup` で他のキーを書いても残る /
  `build_startup_payload(startup_data=...)` が `ui_language` を残す（tests/ の単体で可）。
- `tests/test_help_content.py`: 読む順（今の言語のファイルが無い → `en` → `ja`）のテストを足す（`help_content_path` を patch）。

## 設計メモ / 制約

- shared は他の層（`keyseq.presentation` 等）を import しない。tkinter も使わない。
- `tr` をモジュールの import 時に評価しない（本 task の新規コードでも。定数にはキーを持つ）。
- `fix_language` / `reset_for_tests` 以外にテストのための分岐を本体へ入れない（`unittest` の有無を見る等はしない）。
- `startup_settings.py` / `startup_io.py` / `split_payloads.py` は変更しない（未知キーを保持するため。暫定 55 §1）。
- 既存の日本語の文言は 1 文字も変えない。

## 読むファイル

1. `instructions/history/55_multilingual_ui.md` §3〜§5（§3.4 を含む）
2. `keyseq/presentation/app.py:105-150`（初期化）・`:470-500`（`_apply_font_delta` / `set_ui_font_delta` の作法）
3. `keyseq/presentation/startup_settings.py`・`keyseq/presentation/controllers/config_io/startup_io.py:42-65`
4. `keyseq/presentation/views/menu_bar.py`・`keyseq/presentation/ui_vars.py`
5. `keyseq/presentation/help/help_content.py:130-170`・`keyseq/presentation/bundled_paths.py`・`tests/test_help_content.py`
6. `keyseq/application/config_service/split_payloads.py:483-505`
7. テストの手本: `tests_ui/test_app_ui_flows.py:1-60`（App を作るテストの形）

## 含まない

- 既存の文言のキー化（task_03〜06）・ヘルプ本文の検証エラー文（task_05）・表示文字列の内部値の分離（task_02）
- `en.json` の全キー（task_08）・`help_en.json`（task_09）・日本語リテラルの静的検査（task_10）
- 正本の改訂（task_12）

## 確認

- `tests/test_i18n.py`: 探す順（選んだ言語 → en → ja → キー）/ ja を選んだとき ja → en → キー / 全部に無いときキー文字列と warning は 1 回 /
  差し込み成功・引数不足で差し込み前の文字列 / `tr("k", key="x")`・`tr_in("en", "k", lang="x")` が差し込みとして働く /
  `params` なしで `{` を含む文言がそのまま / 値が非文字列のキーは無い扱い / 言語を決める前の `tr` は ja /
  `fix_language` 後の `set_language` は無視 / `tr_in` は今の言語を変えない /
  `available_languages` の並び・規則に合わない名前・壊れた JSON・`_meta.name` 非文字列の除外 /
  `resolve_language`（None・非文字列・未知コード → en / ja・en はそのまま）/ 同梱の ja.json・en.json が読め `_meta.name` を持ち、
  en が ja の全キーを持つ（本 task の時点のキー）/ shared/i18n のソースが `keyseq.` 配下を import していない
- tests_ui の言語メニュー・保存・知らせ・今の言語不変 / `ui_language` が 2 経路で残る / ヘルプの読む順
- 静的テスト: `App(` を含むテストモジュールが全部 `fix_language(` を含む
- 既存テスト全 pass（`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui`）・`-m compileall keyseq` clean・
  `-m tests.smoke_app` OK

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_12 でまとめて実施（本 task では行わない）。
