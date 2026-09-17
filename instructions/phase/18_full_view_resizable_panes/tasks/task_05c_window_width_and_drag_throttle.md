# task_05c_window_width_and_drag_throttle

## 目的

task_05 の実機目視を受けた暫定仕様 16 **v0.4**（ユーザー確定 2026-09-17）の追加分を実装する。
①**フル表示時のウィンドウ幅の保存・復元**（§2-13・§3-8・§5-15/16/18）②**既定幅を既定ウィンドウ幅 780 基準で算出**（§3-6・§3-8）
③**終了時の保存順序**（フック停止後に保存・`destroy` を保証）④**ドラッグ中の移動イベントの間引き**（案 L・§2-14・§3-2・§5-17）。
**presentation 限定**。domain / application / infrastructure は変更しない。JSON はキー `full_view_window_width` の追加のみ（後方互換）。

## 対象範囲（presentation 3 ファイル + tests 1 + tests_ui 1 新規）

### `keyseq/presentation/pane_width_rules.py`

- 定数 `WINDOW_WIDTH_KEY = "full_view_window_width"` / `DEFAULT_WINDOW_WIDTH = 780` を追加。
- `parse_saved_window_width(raw: object, screen_width: int) -> int | None`: `bool` / 非 int / 1 未満 → `None`。
  正の int は `min(raw, screen_width)`（§3-8 値の検証）。
- `default_basis_main_width(main_width: int, window_width: int) -> int`: `main_width - (window_width - DEFAULT_WINDOW_WIDTH)`（§3-8）。
- 既存関数のシグネチャ・挙動は変えない。

### `keyseq/presentation/controllers/pane_layout_controller.py`

1. **既定幅の 780 基準**: `apply_initial_widths` で `default_pane_widths(main_width=...)` に渡す値を
   `default_basis_main_width(panes.winfo_width(), app.winfo_width())` にする（保存値がある場合の扱いは不変）。
2. **自動で決めた幅の記録**: 属性 `_auto_window_width: int | None`。初回適用（`apply_initial_widths` 経由の `apply_layout`）の後は常に
   `app.winfo_width()` を記録。`on_font_changed` / `on_full_view_shown` 経由の `apply_layout` では **geometry を変えた場合だけ**記録し直す。
   （`apply_layout` が geometry を変えたかを返す、または引数で初回かを渡す等、形は任せる。関数 30 行目安）
3. **保存するウィンドウ幅** `window_width_to_save() -> int | None`（§3-8）: 初回適用前 / `app.wm_state() == "zoomed"` → `None`。
   省略表示中（`app._compact_mode`）は `app._full_geometry` の幅（`"WxH+X+Y"` の W。取れなければ `None`）、フル表示中は `app.winfo_width()`。
   その値が `_auto_window_width` と同じなら `None`。
4. **ドラッグ保存に含める**: `_on_desired_changed` の `write_startup` 引数に、`window_width_to_save()` が `None` でなければ
   `WINDOW_WIDTH_KEY` を同じ dict で含める（書き込みは 1 回のまま）。
5. **終了時の保存** `save_window_width_on_close(width: int | None) -> None`: `width` が `None`、または
   `app._startup_settings.get(WINDOW_WIDTH_KEY) == width` なら何もしない。それ以外は `write_startup({WINDOW_WIDTH_KEY: width})`（戻り値は見ない）。
6. **移動イベントの間引き（案 L）**: `_on_motion` は最新の `event.x` を記録し、未予約なら `app.after_idle` で適用処理を 1 回予約して `"break"`。
   適用処理は既存の可動範囲計算（`drag_limits` + `clamp` + `paneconfigure`）を記録済みの位置で行い、予約 ID をクリアする。
   `_on_release` は予約中なら `after_cancel` して**即時に適用**してから既存の希望幅更新へ進む。
   `_on_press` 冒頭のドラッグ状態の破棄（task_05b F5）で予約も取り消す。
7. 250 行を超える場合は task_03 の方針（`controllers/pane_layout/` 親フォルダ方式）で分割し、`app.py` の import を更新して報告する。

### `keyseq/presentation/app.py`

1. `:90` の `self.geometry("780x820")` を、`parse_saved_window_width(self._startup_settings.get(WINDOW_WIDTH_KEY), self.winfo_screenwidth())`
   が `None` なら `DEFAULT_WINDOW_WIDTH`、そうでなければその値を幅にした `f"{width}x820"` にする（高さ 820 は現状どおり）。
2. `on_close`（`:535-549`）を §3-8 の順序にする:
   ①`confirm_save_if_dirty` が偽なら return ②`width = self.pane_layout.window_width_to_save()` ③`self.hook.begin_shutdown()`
   ④`try:` キーボードウィンドウ破棄（既存）→ `self.hook.stop_hook()` → `self.pane_layout.save_window_width_on_close(width)` `finally: self.destroy()`。
   保存が例外を投げても `destroy` に到達すること。

### `tests/test_pane_width_rules.py`（追記）

- `parse_saved_window_width`: `True` / `False` / `"900"` / `900.0` / `0` / `-1` / `None` → `None`、`900`（画面 1920）→ 900、
  `1920`（画面 1920）→ 1920、`2000`（画面 1920）→ 1920。
- `default_basis_main_width`: 780 のとき不変 / 1000 のとき −220 / 700 のとき +80。

### `tests_ui/test_pane_window_width_persistence.py`（新規）

既存 `tests_ui/test_pane_widths_persistence.py` の型（`App()` 構築中だけ `ConfigService.load_startup` を patch・後始末で状態を戻す・
`write_startup` を patch して実 config を書かない）に従う。起動値を変えるテストはクラス単位で App を作って破棄する（2 つ同時に持たない）。

1. **起動時の復元**（§5-15）: 保存値 1000 → `app.winfo_width() == 1000`。保存値が画面幅超（`App.winfo_screenwidth` を小さく patch）→ 画面幅で開く。
   不正値（`True` / `"900"` / `0`）→ 780。いずれも `write_startup` は呼ばれない。
2. **780 基準の既定幅**（§5-16）: ウィンドウ幅だけ 1000 を保存して起動した App の `pane_layout.desired` が、キー無しで起動した App の `desired` と一致し、
   トリガー一覧の幅が 220 広い。
3. **終了時の保存**（§5-16）: `confirm_save_if_dirty` → True、`destroy` / `stop_hook` / `write_startup` を記録用に patch（呼び出し順を 1 つの Mock で記録）。
   - 縁で幅を変えてから `on_close()` → `write_startup({"full_view_window_width": 変えた幅})` が 1 回・**`stop_hook` の後**・`destroy` が最後。
   - 幅を変えずに `on_close()` → `write_startup` は呼ばれない・`destroy` は呼ばれる。
   - 保存値と同じ幅 → 呼ばれない。`wm_state` を `"zoomed"` に patch → 呼ばれない。
   - `confirm_save_if_dirty` → False → `write_startup` も `destroy` も呼ばれない。
   - `write_startup` が例外を投げる → `destroy` は呼ばれる。
   - 省略表示中（`_full_geometry` を持つ状態）→ `_full_geometry` の幅が書かれる（自動決定幅と異なる場合）。
4. **自動で決めた幅を書かない**（§5-16）: 画面幅 patch で切り詰めて起動 → 何もせず `on_close()` → 呼ばれない。
   フォントを上げてウィンドウが自動で広がった → `on_close()` → 呼ばれない。縁で幅を変えた後にフォントを変えても広がらなかった → 変えた幅が書かれる。
5. **ドラッグ保存に含まれる**: 縁で幅を変えてからサッシュをドラッグ → 1 回の `write_startup` に `full_view_pane_widths` と `full_view_window_width` の両方。
   幅を変えずにドラッグ → `full_view_window_width` は含まれない。
6. **間引き**（§5-17）: `panes.paneconfigure` を `wraps` 付きで記録し、`<Button-1>` の後に `<B1-Motion>` を 5 回（`update` なし）→ 記録 0 回 →
   `update_idletasks()` → 幅の適用 1 回・最後の位置の幅。`<Button-1>` → `<B1-Motion>` → `<ButtonRelease-1>`（間に `update` なし）→
   最後の位置の幅が適用され `desired` も更新。サッシュで押して動かした直後にサッシュ以外で押す → `update` 後も幅は変わらない。

### 設計メモ / 制約

- 既存テスト（`tests_ui/test_full_view_panes.py` / `test_pane_drag_and_window_min.py` / `test_pane_widths_persistence.py` / `tests/test_pane_width_rules.py` の既存分）の
  **アサーション・期待値は変えない**。既存の `_drag` ヘルパは motion 後に `update()` を呼ぶので間引き後も通る見込み。落ちたら実装側を直す。
- `on_close` のテストで実際に `destroy` させない（共有 App を壊さない）。`write_startup` 以外で `config.json` を書かない。
- 780 は `DEFAULT_WINDOW_WIDTH` だけを参照し、`app.py` に数値を残さない（高さ 820 は現状どおり直書きでよい）。

## 読むファイル

- 編集対象（全体）: `keyseq/presentation/pane_width_rules.py` / `keyseq/presentation/controllers/pane_layout_controller.py`
- `keyseq/presentation/app.py:55-95`（`__init__` 冒頭・起動設定読込と初期 geometry）/ `:330-385`（表示切替・`_full_geometry`）/ `:535-549`（`on_close`）
- 仕様: `instructions/history/16_full_view_resizable_panes.md` の §3-2「ドラッグ中の表示」・§3-6・§3-8・§5-15〜18（`rg -n "§3-8|ドラッグ中の表示"` で位置特定）
- 手本（範囲のみ）: `tests_ui/test_pane_widths_persistence.py:14-104`（共有 App・patch・後始末・`_drag`）/ `:250-310`（起動値を変えるクラス）/
  `tests/test_pane_width_rules.py:1-40`（import と書き方）
- `keyseq/presentation/controllers/config_io/startup_io.py:39-59`（`write_startup`）

## 含まない

- ヘッダ幅（idea_21）/ 縦方向の最小サイズ（idea_22）/ ウィンドウの高さ・位置・最大化状態の保存（§6）
- 正本 `features.md` / `data_schema.md` / `codebase_map.md` の更新（**task_06**）
- 実機目視（本タスク完了後に **task_05 で再実施**: 9 の再確認・ドラッグの見え方・狭い画面での起動終了）

## 確認

python は `../../../.venv/Scripts/python.exe`。実測は `verifier`。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest tests.test_pane_width_rules -v` が全 pass（追加分を含む）。
3. `-m unittest tests_ui.test_pane_window_width_persistence -v` が全 pass（上記 1〜6）。
4. `-m unittest tests_ui.test_full_view_panes tests_ui.test_pane_drag_and_window_min tests_ui.test_pane_widths_persistence -v` が 6 / 12 / 13 pass（無変更）。
5. `-m unittest discover -s tests` が 441 + 追加分 OK（skip 7）/ `-m unittest discover -s tests_ui` が 382 + 追加分 OK。
6. `-m tests.smoke_app` が SMOKE OK。`git status --short config` が空。
7. `reviewer` が `on_close` の順序（フック停止 → 保存 → `finally: destroy`）と「自動で決めた幅を書かない」の記録条件をコードで確認する。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。
- 実機目視は **task_05 で再実施**（9・ドラッグの見え方・狭い画面の起動終了）。

## 完了記録（2026-09-17）

- 実装は `codex-implementer`（「読むファイル」節の初適用）。**Codex 使用量**: 実装 9 ターン・入力 37.0 万 / 分割 8 ターン・入力 26.1 万
  （以前の実装 1 回 = 56 万〜103 万）。
- コントローラが 299 行 → 親フォルダ方式で分割: `controllers/pane_layout/`（`__init__.py` 再輸出 / `pane_layout_controller.py` 243 行 /
  `pane_measure.py` 76 行 = 最小幅の実測）。旧 `controllers/pane_layout_controller.py` は削除（横流しモジュールなし）。
- `verifier` 1 回目: 既存 `test_pane_widths_persistence` の 4 件が失敗。準備処理の +200 拡幅が v0.4 どおり「ユーザーが変えた幅」と判定され
  保存内容に `full_view_window_width` が加わったため（実装は仕様どおり）。**メイン判断**: アサーション不変・準備で `_auto_window_width` を拡幅後の幅にし、後始末で復元。
- `reviewer` = 完了可。軽微 2 件（`app.py` 先頭 BOM の削除 / import 位置）をメインで修正。
- `verifier` 2 回目: compileall clean / pane 系 4 モジュール 6・12・13・23 OK / `tests` 445 OK（skip 7）/ `tests_ui` 405 OK / smoke OK / config 差分なし。
