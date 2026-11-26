# task_02_presentation_menu_and_save

## 目的

task_01 の `ScrollInvert` を config.json の `scroll_invert` と結び、設定メニューのサブメニュー「スクロールの向き」から縦・横の反転を切り替えて保存・反映できるようにする（暫定 62 §2・§3・§5）。ヘルプ本文に 1 文を足す。
**presentation 限定（+ 言語ファイル・ヘルプ本文）・domain / application は task_01 の公開関数を使うだけで変えない・infrastructure 不変**。

## 対象範囲（presentation 限定）

### `keyseq/presentation/ui_vars.py`

- `UiVars.__init__` に任意のキーワード引数 `scroll_invert: ScrollInvert = NO_SCROLL_INVERT`（`keyseq.domain.mouse_scroll` から import）を足し、
  `self.scroll_invert_vertical_var` / `self.scroll_invert_horizontal_var`（`tk.BooleanVar`・初期値 = `scroll_invert.vertical` / `.horizontal`）を作る。

### `keyseq/presentation/app.py`

- 起動時: `_startup_settings` を読んだ後（`UiVars(` の組み立てより前）に `self._scroll_invert = coerce_scroll_invert(self._startup_settings.get("scroll_invert"))` を置き、`UiVars(..., scroll_invert=self._scroll_invert)` へ渡す（§3・§7-1。config.json が読めないときは `load_startup_settings` が空の dict を返すので両方 False になる・既存の読込失敗の警告はそのまま）。
- `ActionExecutor(` の組み立てに `get_scroll_invert=lambda: self._scroll_invert` を足す（§4・不変の値を返す）。
- 新しいメソッド `set_scroll_invert(self) -> None`（`set_ui_language` の直後に置く・§5）:
  1. `chosen = ScrollInvert(vertical=bool(vertical_var.get()), horizontal=bool(horizontal_var.get()))`（**実行した時点のチェック 2 つの値**）
  2. `saved = coerce_scroll_invert(self._startup_settings.get("scroll_invert"))`
  3. `chosen == saved` なら何もしない（書かない）
  4. `self.startup_io.write_startup({"scroll_invert": scroll_invert_to_json(chosen)})` が False なら 2 つの変数を `saved` の値へ戻して終わる（`self._scroll_invert` は変えない）
  5. 成功したら `self._scroll_invert = chosen`（**属性への 1 回の代入**）
  - 構成セットの未保存の印（dirty）には触れない。フラッシュメッセージは出さない。
- `_scroll_invert` は構成セットの新規作成・読込・Import・サンプルに戻す の経路で書き換えない（既存の経路は触らない）。

### `keyseq/presentation/views/menu_bar.py`

- 設定メニューの「物理キー名を表示」の後の `add_separator()` の直後、「フォントサイズ」の cascade より前に、サブメニュー（`tk.Menu(settings_menu, tearoff=False)`）を作り、
  `add_checkbutton(label=tr("menu.settings.scroll_direction.invert_vertical"), variable=app.ui_vars.scroll_invert_vertical_var, command=app.menu_commands.defer(app.set_scroll_invert))`
  と横（`invert_horizontal`・`scroll_invert_horizontal_var`）の 2 つを足して `settings_menu.add_cascade(label=tr("menu.settings.scroll_direction"), menu=...)` で置く（§2・§5。区切りは足さない＝ Language が「フォントサイズ」の直後のままになる）。

### 言語ファイル

- `keyseq/shared/i18n/locales/ja.json` / `en.json` に、既存の `menu.settings.*` のキーの並び（アルファベット順）に合わせて 3 キーを足す:
  - `menu.settings.scroll_direction`: 「スクロールの向き」/ `Scroll direction`
  - `menu.settings.scroll_direction.invert_vertical`: 「縦を反転」/ `Invert vertical`
  - `menu.settings.scroll_direction.invert_horizontal`: 「横を反転」/ `Invert horizontal`

### ヘルプ本文

- `keyseq/presentation/help/content/help_ja.json:312` の文字列を「mouse_scroll: マウスのホイールを回します。向きは設定メニューの「スクロールの向き」で反転できます（Mac のナチュラルなスクロールを使っている場合など）。」にする。
- `keyseq/presentation/help/content/help_en.json:179` の文字列を「mouse_scroll: Scrolls the mouse wheel. You can invert the direction in Settings > Scroll direction (for example, when you use natural scrolling on a Mac).」にする。

### テスト

- **既存の期待値の変更**: `tests/test_menu_bar_deferral.py`
  - :32 の `ui_vars=SimpleNamespace(...)` に `scroll_invert_vertical_var=Mock(), scroll_invert_horizontal_var=Mock()` を足し、:33 の app に `set_scroll_invert=Mock()` を足す。
  - :46 の `physical_checks` を `variable is app.ui_vars.keyboard_show_physical_key_labels_var` で絞る（:50 の `len == 1` はそのまま）。新しく `scroll_checks`（2 つの変数のどちらかを持つ checkbutton）を取り、`len == 2` を確かめる。
  - :47 の `len(deferred) == len(commands) + len(language_radios)` を `+ len(scroll_checks)` に、:51 の `22 + len(available_languages())` を `24 + len(available_languages())` に変える。
  - 既存のテストの途中に新しいテストを差し込まない。
- **新規** `tests/test_scroll_invert_setting.py`（`App.set_scroll_invert` を SimpleNamespace の fake self で呼ぶ単体テスト。変数は `get` / `set` を持つ小さな fake）:
  - 保存済みと同じ → `write_startup` を呼ばない・`_scroll_invert` 不変。
  - 縦だけ ON → `write_startup({"scroll_invert": {"vertical": True, "horizontal": False}})`・`_scroll_invert == ScrollInvert(vertical=True)`（§7-4）。
  - 保存済みが不正（`"scroll_invert": "x"`）でチェックが両方 False → 書かない（正規化した保存済みと比べる）。
  - `write_startup` が False → 2 つの変数が保存済みの値に戻り、`_scroll_invert` は前の値のまま（§7-5）。
  - dirty の印に触れない（fake self に `mark_dirty` 等を持たせず、属性エラーにならないこと＝触れていないことで担保。または `self.state` を Mock にして呼ばれないことを確かめる）（§7-5a）。
- **新規** `tests_ui/test_scroll_invert_menu.py`（`tests_ui/test_ui_language.py` の `setUpClass` / `_settings_menu` / `_make_app_with_startup_settings` の組み立てを手本にする・`fix_language("ja")`）:
  - サブメニュー「スクロールの向き」が「物理キー名を表示」の後・「フォントサイズ」の前にあり、中は checkbutton 2 つ（ラベル「縦を反転」「横を反転」・変数が `ui_vars` の 2 つ）。「Language」は「フォントサイズ」の直後のまま。
  - 起動時: `{"scroll_invert": {"vertical": True}}` → 縦の変数 True・横 False・`app.action_executor._get_scroll_invert()` が `ScrollInvert(vertical=True)`。`{}` と `{"scroll_invert": 5}` → 両方 False（§7-1）。
  - チェックの command を呼ぶと（Windows では即時・macOS では `menu_commands` の待ち行列。テストでは `app.set_scroll_invert` を直接呼んでよい）`write_startup` が両方のキーで呼ばれ、`action_executor._get_scroll_invert()` が新しい値を返す（§7-4・6）。

### 設計メモ / 制約

- 保存の失敗時の戻しと「保存済みと同じなら書かない」は `set_ui_language`（`app.py:592-599`）と同じ形にする。
- 保存は必ず `menu_commands.defer` を通す（`write_startup` の失敗の messagebox がモーダル・`features.md` §4.8）。checkbutton の変数自体はメニューが即時に切り替えるので、待ちの間もチェックは選んだ値を示す（§5）。
- executor へは Tk の変数を渡さない（`lambda: self._scroll_invert`）。
- 一覧・ダイアログ・JSON の `direction` は変えない（§2・§7-7）。

## 読むファイル

- `keyseq/presentation/ui_vars.py`（全体）
- `keyseq/presentation/app.py:140-170`（起動設定の読込・`UiVars(`）・`:200-226`（`ActionExecutor(`）・`:578-600`（`set_ui_font_delta`・`set_ui_language`）
- `keyseq/presentation/views/menu_bar.py:27-63`（設定メニュー）
- `keyseq/domain/mouse_scroll.py`（task_01 で足した `ScrollInvert`・`NO_SCROLL_INVERT`・`coerce_scroll_invert`・`scroll_invert_to_json`）
- `keyseq/shared/i18n/locales/ja.json:245-260`・`en.json:245-260`・`keyseq/presentation/help/content/help_ja.json:305-318`・`help_en.json:175-182`
- `tests/test_menu_bar_deferral.py`（全体）・`tests_ui/test_ui_language.py:1-135`・`:214-230`（手本）
- `instructions/history/62_scroll_direction_setting.md` §2・§3・§5・§7

## 含まない

- domain / application の変更（task_01 で完了）・infrastructure の変更
- 統合確認（tests / tests_ui / smoke の全体）・Windows / macOS の実機目視（task_03）
- 正本 `spec_detail/`・`codebase_map.md` の反映（task_04）
- 多重起動での config.json の上書き（idea_70）

## 確認

- `../../../.venv/bin/python -m compileall -q keyseq tests tests_ui` が clean
- `../../../.venv/bin/python -m unittest tests.test_menu_bar_deferral tests.test_scroll_invert_setting -v` が pass
- `../../../.venv/bin/python -m unittest tests_ui.test_scroll_invert_menu tests_ui.test_ui_language -v` が pass（Mac は tests_ui をモジュール指定で流す）
- `../../../.venv/bin/python -m unittest discover -s tests` が全 pass（i18n の静的テスト〔ソースに日本語を書かない・ja / en のキーの一致〕を含む）
- 差分が「対象範囲」のファイルに限られる（`git diff --stat`）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視（メニューの見た目・Mac での遅延・実際の向き）は task_03 でまとめて実施。
