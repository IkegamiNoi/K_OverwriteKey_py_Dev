# task_05_version_and_license

## 目的

バージョン情報のダイアログ（暫定 53 §7.1）とライセンスの窓（§7.2）を作り、メニュー「ヘルプ」の残り 2 項目を足す（§3）。
同梱物のライセンス全文のデータ（`third_party/`。**メインが入手元から取り込み済み**）を読み込み、版の一致を検査テストで確かめる。
**presentation 限定（`help/` に窓と読込・`menu_bar.py`・`app.py` の数行）。domain / application 不変・スキーマ不変。`LICENSE` の写しを作らない。**

## 取り込み済みのデータ（メインが作成・変更しない）

`keyseq/presentation/help/content/third_party/`:
- `third_party.json` = `[{"name", "version", "license", "file"}]` 14 件（外部ライブラリ 11 → Python → Tcl → Tk の順）
- `<name>.txt` 14 個。入手元:
  - dist-info の同梱ファイル: keyboard・pyautogui・pynput（`COPYING.LGPL`）・pyscreeze・pymsgbox・pytweening・pyrect・pyperclip・six
  - 配布物に同梱が無いもの: mouseinfo・pygetwindow = 上流リポジトリの `LICENSE.txt`（いずれも履歴が初回コミット 1 回だけ・記録した版のリリースより前。取得コミット mouseinfo `74af3ed`・PyGetWindow `6bd22c7`）/ Tcl = 上流 `tcltk/tcl` のタグ `core-8-6-15` の `license.terms`
  - Python = 実行環境の `LICENSE.txt`（3.14.6）/ Tk = 実行環境の `tcl/tk8.6/license.terms`（8.6.15）
- ライセンス名は**同梱の本文を正**とした（§2 の pymsgbox と同じ原則）: pyscreeze・pytweening も METADATA は MIT だが本文は BSD 3 条項。

## 対象範囲（presentation 限定）

### `keyseq/presentation/help/third_party.py`（新規・Tk 非依存）

- `ThirdPartyEntry`（frozen dataclass: `name`・`version`・`license`・`file`）・`ThirdPartyNotice`（`entry`・`text: str | None`・`error: str = ""`）。
- `load_third_party(directory: Path | None = None) -> tuple[list[ThirdPartyNotice], str]`: 既定は `third_party_dir()`。`third_party.json` を読み、形式（配列・各要素の 4 キーが空でない文字列・`file` が `/` `\` `..` を含まない）を検査。誤り・読めないときは `([], 理由)`。各全文は UTF-8 で読み、読めないものは `text=None`・`error` に理由（他は続ける）。**例外を外へ出さない**。
- `load_license_text() -> str | None`: `license_path()`（task_01）の全文。読めなければ `None`。

### `keyseq/presentation/help/version_dialog.py`（新規）

- `open_version_dialog(app) -> tk.Toplevel`（§7.1）: 小さなモーダル（`grab_modal(dialog, app)`・題「バージョン情報」）。
  `app.hook.suspend_hook_for_dialog(dialog)` で開いている間フックを止める（既存のモーダルと同じ順序・作法にならう）。
  表示（選択・コピーできる読み取り専用の `tk.Text`。名前付きフォント）:
  `Key Replacer Sequencer` / `バージョン {keyseq.__version__}` / `Copyright (C) 2026 池上ノイ (Ikegami Noi)` / `ライセンス: GNU General Public License v3` / `実行環境: Python {platform.python_version()}・Tk {tk の patchlevel}`。
  ボタン「閉じる」・Escape で閉じる（既存のダイアログの Escape の束縛の作法にならう）。初期フォーカスは「閉じる」。

### `keyseq/presentation/help/license_window.py`（新規）

- `LicenseWindow(tk.Toplevel)`（§7.2）: モーダルにしない・transient にしない・grab を取らない。題「ライセンス」。読み取り専用で縦スクロールする `tk.Text`（選択・コピー可・Ctrl+C）。大きさは 720×560（画面に収める）・`minsize(420, 300)`・位置と大きさは記録しない。Escape で閉じる。名前付きフォントだけを使う（フォント変更の通知は受けない）。
- 本文の順: ①`Key Replacer Sequencer` / 著作権表記 / `GNU General Public License v3` / `LICENSE` の全文（読めなければ「LICENSE を読み込めませんでした。」）②同梱物の一覧（1 行 1 件「名前 版 — ライセンス名」）③同梱物ごとの全文（見出し = 「名前 版」。全文が読めなければ「全文を読み込めませんでした。（理由）」）。`third_party.json` 自体が読めなければ②③の代わりに「同梱物の一覧を読み込めませんでした。（理由）」。
- `LicenseWindowController(app)`: `open()`（無ければ作る・あれば `deiconify` + `lift` + `focus_set`）・`window`・`close()`・`apply_topmost()`（`app.ui_vars.always_on_top_var` を当てる。開く・前面化のときにも当てる）。破棄で参照を捨てる（`HelpWindowController` と同じ作り）。

### `keyseq/presentation/views/menu_bar.py`

- 「ヘルプ」の区切りの後に「バージョン情報」→ `open_version_dialog(app)`（または `app` の小メソッド経由）・「ライセンス」→ `app.license.open()`。「…」なし（D3）。

### `keyseq/presentation/app.py`

- `self.license = LicenseWindowController(self)`（`self.help` の隣）。
- `_apply_always_on_top`: `self.help.apply_topmost()` の隣で `self.license.apply_topmost()`（例外はログ・既存の書き方にならう。`resync_keyboard_topmost` はその後のまま）。
- `on_close`: `self.help.close()` の隣で `self.license.close()`。

### tests（新規 `tests/test_third_party.py`）

- 同梱の `third_party.json` が `load_third_party()` で成功・14 件・各全文が読めて空でない・`file` の重複なし・並び（外部 11 → Python → Tcl → Tk）。
- **版の一致（§7.2）**: Python・Tcl・Tk 以外の各件について `importlib.metadata.version(name)` と `version` が一致（入っていなければ `subTest` 内で skip）。
- Python の件の `version` が `platform.python_version()` と一致・Tcl / Tk の `version` が `tkinter.Tcl().eval("info patchlevel")` と一致（Tk が使えなければ skip）。
- 失敗系: 無いフォルダ・壊れた JSON・キー欠落・`file` に `..` → `([], 理由)`・例外なし / 全文の 1 つが無い → その件だけ `text=None`。
- `load_license_text()` が GPL v3 の全文（`"GNU GENERAL PUBLIC LICENSE"` を含む）を返す。
- `bundled_paths.license_path()` 以外に `LICENSE` の写しがリポジトリに無い（`keyseq/` 配下に `LICENSE` という名のファイルが無い）。

### tests_ui（`tests_ui/test_help_window.py` に追加、または新規 `tests_ui/test_version_license.py`）

- メニュー「ヘルプ」= 「使い方」「よくある質問」区切り「バージョン情報」「ライセンス」。`set_ui_font_delta` の後も同じ（§10-1 はここで完了）。
- バージョン情報: 題・`__version__` の値・著作権表記・ライセンス名・実行環境の行が出る・grab がダイアログ・`get_hook_pause_count()` が開いている間 1・閉じる / Escape で 0 に戻る。
- ライセンス: 1 つだけ（2 回目の `open` で同じ窓）・本文に `LICENSE` の先頭行・一覧の 14 行・各見出しが出る・grab を取らない・`always_on_top_var` ON で `-topmost` 1・切替に追従・`on_close` で閉じる。

### 設計メモ / 制約

- 全文データ（`third_party/` 配下）は変更しない（入手元の本文そのまま）。読込の都合で文字コード・改行の問題があれば止めて報告する。
- `help/` から domain / application を import しない。`keyseq.__version__` の import は可。
- ファイルはおおむね 300 行以内・関数 30 行以内。

## 読むファイル

- `instructions/history/53_help_window.md` §3（58-70 行）・§7（221-241 行）
- `keyseq/presentation/help/bundled_paths.py`・`help_window_controller.py`（作りの手本）・`help_window.py`（Text の扱いの手本・必要部分のみ）
- `keyseq/presentation/views/menu_bar.py`・`keyseq/presentation/app.py` の `_apply_always_on_top`・`on_close`
- モーダルの手本: `keyseq/presentation/dialogs/orphan_sweep_dialog.py`（小さなモーダル・閉じるボタン・Escape・フック停止の順序）
- `keyseq/presentation/help/content/third_party/third_party.json`

## 含まない

- ダイアログの「?」（task_04）・本文の執筆（task_06）
- exe 化の対応（`bundled_root` の変更等。§11）・正本反映（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` clean
- `tests.test_third_party`・追加した tests_ui pass
- tests 全体 pass / tests_ui 全体（既知の負債 `test_compact_window` の 1 件を除き pass）/ smoke pass

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_08
