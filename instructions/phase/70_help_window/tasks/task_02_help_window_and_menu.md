# task_02_help_window_and_menu

## 目的

ヘルプの窓（タブ「主要機能」「QA」・2 段の Expander・フィルターの UI・ハイライト・件数・一致なし・Escape・初期フォーカス・
単一性・前面化）と、メニュー「ヘルプ」の骨格（「使い方」「よくある質問」と区切り）を作る（暫定 53 §3・§4.1・§4.2・§4.3）。
**presentation 限定（`keyseq/presentation/help/` に窓と管理役を足す・`menu_bar.py`・`app.py` に管理役の生成 1 行）。
task_01 の純関数（`help_filter`・`help_content`）を使い、照合・正規化をここで書き直さない。domain / application 不変・スキーマ不変。**

## 対象範囲（presentation 限定）

### `keyseq/presentation/help/help_window_controller.py`（新規）

- `HelpWindowController(app, *, load_content: Callable[[], HelpLoadResult] = load_help_content)`
  - `open(tab: str) -> None`（`tab` は `"guide"` / `"faq"`）: 窓が無ければ作って指定のタブを選ぶ。あれば最小化を `deiconify` で戻し、`lift` + `focus_set`、指定のタブへ切り替える（**フィルターはそのまま**）。
  - `window` プロパティ（開いていなければ `None`）・`close() -> None`（開いていれば破棄。無ければ何もしない）。
  - 窓が破棄されたら（× / Escape / `close`）参照を捨てる（`<Destroy>` は窓自身の破棄だけを見る）。次に開くときは作り直す（状態を持ち越さない）。
  - 本文は窓を作るたびに `load_content()` で読む。

### `keyseq/presentation/help/help_window.py`（新規）

- `HelpWindow(tk.Toplevel)`: 題「ヘルプ」。**モーダルにしない・`transient` にしない・grab を取らない**。
  - 初期の大きさ = 幅 720・高さ 560（画面〔`winfo_screenwidth/height`〕に収まらなければ収まる大きさへ）・`minsize(420, 300)`・位置は指定しない。
  - 上から: 「絞り込み:」ラベル + `ttk.Entry`（フィルター）+ 消去ボタン「×」→ `ttk.Notebook`（「主要機能」「QA」）。
  - 読込の失敗（`HelpLoadResult.content is None`）: Notebook の代わりに「ヘルプを読み込めませんでした。（理由）」を出す（フィルター欄は出してよいが何もしない）。例外を外へ出さない。
  - `select_tab(tab: str)`・`filter_text`（現在の入力）を持つ。
  - フィルター: 入力の変更ごと（`StringVar` の trace または `<KeyRelease>` ではなく変更の通知）に `parse_query` → 各タブへ適用。
    タブ見出し = 入力が空でないとき「主要機能 (N)」「QA (N)」（N = 一致項目数・0 も出す）、空なら件数なし。
    消去ボタン・全削除で空にすると、全項目を表示し**すべて閉じた状態**へ戻す。
  - 初期フォーカス = Notebook（入力欄にしない）。
  - Escape（窓全体）: 入力欄にフォーカスがあり入力が空でなければ入力を消す（`"break"`）。それ以外は窓を閉じる（× と同じ）。
  - フォントは `apply_global_theme` の名前付きフォント（`TkDefaultFont` 等）を使う。見出しの太字など派生フォントを作るなら、作り直し用のメソッド `on_font_changed()` を用意だけしておく（呼び出しの配線は task_03）。

### `keyseq/presentation/help/help_tab_view.py`（新規・1 タブ分の表示）

- 推奨方式（§4.2 の例）: タブごとに 1 つの読み取り専用 `tk.Text`（`wrap="word"` 相当で窓の幅に合わせて折り返す・縦スクロールバー付き）に、大分類の見出し・項目の見出し・本文を流し込み、
  開閉・隠すはタグの `elide`、ハイライトはタグの背景色で行う。ほかの方式でも下の見た目と操作を満たせばよい（方式を変えたら完了報告に理由を書く）。
- 見た目: 大分類の見出し = 「▶ 大分類名」/「▼ 大分類名」。その下に項目の見出し（字下げ 1 段・同じ記号）。項目を開くと本文（さらに字下げ。`list` は「・」付きの箇条）。**既定はすべて閉じる**。
- 開閉の操作:
  - 見出しのクリックで開閉。
  - キー: 本文の Text にフォーカスがあるとき、上下キーで「選択中の見出し」（見えている見出しだけを順にたどる・印を付けて `see` する）を移し、Enter / Space / KP_Enter で開閉。見出しをクリックしたらその見出しを「選択中」にする。
- 本文の文字は選択・コピーできる: 本文をクリックしたら Text へ `focus_set`（Ctrl+C が入力欄へ流れない）・Ctrl+C でコピー・右クリックで「コピー」のメニュー。
- マウスホイールは、カーソルのある Text をスクロールする（Text の既定の動作で足りるなら追加しない）。
- フィルター（`apply_filter(terms: tuple[str, ...]) -> int`・戻り値 = 一致項目数）:
  - `item_matches((大分類名, 項目の見出し, item_plain_text(item)), terms)` で判定（task_01）。一致した項目は開き、その大分類も開く。一致しない項目・一致項目の無い大分類は隠す。
  - 項目の見出しと本文の一致箇所を `highlight_ranges` で求め、語ごと・出現ごとにハイライト（大分類名の中はしない）。ハイライトの色はモジュール定数 1 つ。
  - 一致 0 件なら「一致する項目はありません。」をそのタブに出す。
  - `terms` が空 → 全表示・ハイライトなし・すべて閉じる。
- 状態（開閉）はこのビューが持つ。テストから見られるよう、少なくとも `is_category_open(id)`・`is_item_open(id)`・`is_item_visible(id)`・`highlight_spans(item_id) -> list[(start, end)]`（項目の見出し・本文それぞれの元の文字列上の位置。どちらの文字列か区別できる形）・`toggle(id)` を公開する（名前は実装で決めてよい。テストと合わせる）。

### `keyseq/presentation/views/menu_bar.py`

- 「設定」の右に「ヘルプ」のカスケードを足す: 「使い方」→ `app.help.open("guide")`・「よくある質問」→ `app.help.open("faq")`・区切り。「…」は付けない（`ui_terms.md` D3）。ショートカットなし。
  （「バージョン情報」「ライセンス」は task_05 で区切りの後へ足す）

### `keyseq/presentation/app.py`

- コントローラ群の生成箇所（`self.hook = HookController(self)` 付近）で `self.help = HelpWindowController(self)` を作る（`build_menu_bar` より前）。それ以外は変えない。

### `tests_ui/test_help_window.py`（新規）

- App を立てる既存の作法（`tests_ui/test_compact_header_view.py` の setUpClass の patch 群）にならう。本文は `load_content` へテスト用の内容（2〜3 大分類・項目に `ß`・`ガ` を含む本文・p と list）を渡して差し替える（`app.help` を差し替え用の内容で作り直すか、`load_content` 属性を差し替える）。
- 項目:
  - メニューバーに「ヘルプ」があり、「使い方」「よくある質問」と区切りが並ぶ。`set_ui_font_delta` でメニューを作り直した後も同じ
  - `open("guide")` で窓が 1 つ開き題「ヘルプ」・選択タブ = 主要機能。続けて `open("faq")` で同じ窓のまま QA タブへ。入力したフィルターは保たれる
  - 窓は grab を取らず（`grab_current()` が窓でない）・`transient` でない・初期フォーカスが入力欄でない
  - 既定ですべて閉じる。見出しのクリック（`event_generate` か公開メソッド）とキー（上下 + Enter / Space）で開閉できる
  - フィルター: 件数がタブ見出しに出る（0 を含む）・一致項目と大分類が開く・一致しない項目が隠れる・ハイライトの位置（`ß` の後ろの語でずれない）・AND・一致なしの表示・空にすると全表示かつすべて閉じる・件数が消える
  - Escape: 入力欄にフォーカスがあり入力ありなら入力だけ消える / それ以外は窓が閉じ、次の `open` で作り直される（フィルター空・すべて閉じる）
  - 読込の失敗（`HelpLoadResult(None, "理由")`）で窓に「ヘルプを読み込めませんでした。（理由）」が出て例外にならない
  - × で閉じた後 `app.help.window is None`

### 設計メモ / 制約

- **開いただけでフックを止めない**（入力欄の FocusIn でのフック停止は task_03。本タスクでは入力欄にフォーカスがあってもフックに触らない）。
- 照合・正規化・ハイライト位置の計算は task_01 の関数だけを使う（Text の検索機能で置き換えない）。Text 上の位置への変換（元の文字列上の位置 → Text の index）はこのビューで行う。
- ファイルの大きさはおおむね 300 行以内・関数 30 行以内を目安に、窓 / 1 タブの表示 / 管理役で分ける。
- `help/` から domain / application を import しない。

## 読むファイル

- `instructions/history/53_help_window.md` §2（38-57 行）・§3〜§4.3（58-110 行）
- task_01 の成果: `keyseq/presentation/help/help_content.py`・`help_filter.py`（関数の署名）
- `keyseq/presentation/views/menu_bar.py`（編集対象・全体）
- `keyseq/presentation/app.py` 268-300 行（コントローラ生成）・410-420 行（メニュー構築）・468-494 行（フォント変更とメニュー作り直し）
- 開閉の操作感の手本: `keyseq/presentation/controllers/compact_header_controller.py` 30-60 行
- tests_ui の手本: `tests_ui/test_compact_header_view.py` 1-60 行・`tests_ui/escape_delivery.py`（フォーカスの取り方）

## 含まない

- 入力欄のフォーカスでのフック停止・フォント変更の通知の配線・「常に手前」の追従とキーボードUIの再同期・アプリ終了時に閉じる（task_03）
- ダイアログの「?」（task_04）
- 「バージョン情報」「ライセンス」（task_05）
- 本文の執筆（task_06）・正本反映（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_help_window` pass
- tests 全体 pass / tests_ui 全体（既知の負債 `test_compact_window` の 1 件を除き pass）/ smoke pass

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_08 でまとめて実施
