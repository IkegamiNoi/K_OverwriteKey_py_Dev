# task_03_header_width_in_window_min

## 目的

暫定仕様 17（v0.3）§3-1・§3-2 を結線する。①**ヘッダから算出したウィンドウ幅を測定・保持**し、②**一括適用（`_plan` → `resolve_layout`）とドラッグ後の最小幅**に使う。
③ヘッダの追加で期待値が変わる既存 `tests_ui` を、**暫定仕様17 §5-9 の条項で説明できる範囲だけ**見直す。
**presentation 限定**（`controllers/pane_layout/` + tests_ui）。純関数は task_01、ボタン幅の固定は task_02 で完了済み。起動時の保存値更新は task_04。スキーマ不変。

## 対象範囲（controllers/pane_layout 2 ファイル + tests_ui 3 既存 + 1 新規）

### `keyseq/presentation/controllers/pane_layout/pane_measure.py`

- 新規 `measure_header_window_width(app: App) -> int`（暫定仕様17 §3-1）: `app.full_view.update_idletasks()` の後、
  `header = app.full_view.header_area` として `header.winfo_reqwidth() + (app.winfo_width() - header.winfo_width())` を返す。

### `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py`

1. 属性 `header_window_width: int = 0`（`__init__`）。
2. **測定の一本化**: 最小幅を測っている 3 箇所（`apply_initial_widths` / `on_font_changed` の非省略表示経路 / `on_full_view_shown` の再測定経路）で、
   `self.min_widths = self.measure_min_widths()` の直後に `self.header_window_width = measure_header_window_width(self.app)` を行う
   （小さな private メソッド `_measure()` にまとめてよい）。省略表示中は測らない（従来どおり印だけ）。
3. `_plan`: `resolve_layout(..., header_window_width=self.header_window_width)` を渡す。
4. `_update_window_min_size`: `resolve_layout` を通さず `window_min_width_after_drag(displayed, self.min_widths, 2 * SASH_WIDTH, window_extra, self.header_window_width)` を `minsize` に当てる
   （`window_extra` は `_plan` と同じ式。暫定仕様17 §3-2 のドラッグ後の最小幅）。
5. 既定幅の 780 基準・自動決定幅の記録・保存予約の規則は変えない（初回適用でヘッダにより広がった幅は geometry 変更として自動決定幅に記録される）。
6. 本体が 256 行から増えて 270 行を超える場合は、測定の呼び出しを `pane_measure.py` 側へ寄せる等で抑え、分割が要るなら報告する（分割自体は行わない）。

### 既存テストの期待値見直し（暫定仕様17 §5-9。**これ以外のアサーションは変えない**）

- `tests_ui/test_full_view_panes.py` `test_02_default_layout_matches_original`（`:96-106`）:
  `self.assertEqual(self.app.winfo_width(), 780)` → `max(780, self.app.pane_layout.header_window_width)`。
  トリガー一覧の幅の期待値を「要求幅 + (ウィンドウ幅 − 780)」へ（広がった分はトリガー一覧が受ける・暫定仕様17 §3-5）。キーマップ管理・出力シーケンスの位置と幅のアサーションは変えない。
- `tests_ui/test_pane_window_width_persistence.py`:
  - `StartupAssertions.expected_width = DEFAULT_WINDOW_WIDTH` を使うキー無し / Bool / 文字列 / 0 の起動テストの期待値を `max(DEFAULT_WINDOW_WIDTH, app.pane_layout.header_window_width)` にする
    （クラス属性では App が無いので、アサーション側で算出する形に変える。保存値 1000・切り詰め 1000 のクラスは 1000 のまま）。
  - `SavedWidthStartupTest.test_defaults_use_default_window_basis` の `220`（= 1000 − 780）を「1000 − 既定起動した probe のウィンドウ幅」にする（probe もヘッダで広がるため）。`desired` の一致は変えない。
- `tests_ui/test_pane_drag_and_window_min.py` `_expected_window_min`（`:116-121`）: 戻り値を `max(<現行の式>, self.layout.header_window_width)` にする（test_07 / 08 / 09 / 12 の期待値がこれに追従）。
- 上記以外で落ちるテストが出た場合は**直さずに報告**する（メインが条項で説明できるか判断する）。

### `tests_ui/test_full_view_header_width.py`（新規）

`tests_ui/test_pane_window_width_persistence.py:12-50` の型（クラス単位で `load_startup`〔`{}`〕/ `write_startup` / `save_startup` を patch・フォントサイズの退避と復元・破棄前に `cancel_window_width_save()`）。
各テストの後始末で geometry・フォント 0・`_compact_mode` / `_full_geometry`・文言・`desired`・`_auto_window_width` を戻し、`cancel_window_width_save()` を呼ぶ。

1. **ヘッダが切れない**（§5-1）: フォント −3 / 0 / ＋3 のそれぞれで、`app.geometry("1x<高さ>")` → `update()` の後、`header_area` と子 3 枠（`hook_frame` / `display_frame` / `file_frame`）の `winfo_width() >= winfo_reqwidth()`。
   停止キーの取得ボタンの文言を `CAPTURE_ACTIVE_TEXT` にした状態でも同じ。
2. **ウィンドウ最小幅** = `max(メインの必要幅, header_window_width)`（§5-2）: 各フォントで `wm_minsize()[0]` が、`_plan()` の `window_min_width` と一致し、かつ `header_window_width` 以上。
3. **取得中にヘッダの要求幅が変わらない**（§5-5）: `stop_key_capture.start()` → `update_idletasks()` 後の `header_area.winfo_reqwidth()` が開始前と同じ → `stop(cancel=True)`。
4. **フォント変更**（§5-7）: ＋3 で `wm_minsize()[0]` が上がる → 0 に戻すと下がる。ウィンドウ幅は ＋3 のときの幅から縮まない。
   省略表示中（`show_compact_view()`）に ＋3 → `wm_minsize` はヘッダ由来に変わらない → `show_full_view()` 後に ＋3 の値になる。
5. **ドラッグ後の最小幅は縮小規則を通さない**（§5-3 後半）: `App.winfo_screenwidth` をその時点のウィンドウ幅より小さい値に patch → サッシュ 1 を左へ動かして離す →
   `wm_minsize()[0] == window_min_width_after_drag(表示幅, min_widths, 2*SASH_WIDTH, window_extra, header_window_width)`。
   続けてウィンドウをその最小幅まで縮めても、キーマップ管理・出力シーケンスの `winfo_width()` は離した直後と同じ。
6. **自動で広がった幅を保存しない**（§5-8 前半）: キー無しで起動した App で `_save_window_width()` を直接呼んでも `write_startup` が呼ばれない。

### 設計メモ / 制約

- `FullView` の構造・配置は変えない。`MinWidths` にヘッダ幅を足さない。
- 期待値の見直しは上記の列挙だけ。**変える理由を暫定仕様17 の条項（§3-2・§3-5・§5-9）で説明できない変更をしない**。
- `resolve_layout` / `window_min_width_after_drag` は task_01 の純関数をそのまま使う（変更しない）。

## 読むファイル

- 編集対象（全体）: `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py` / `pane_measure.py`
- `keyseq/presentation/pane_width_rules.py:134-176`（`resolve_layout` / `window_min_width_after_drag`）
- `keyseq/presentation/views/full_view/full_view.py:26-40`（`header_area` と 3 枠の属性名）
- 既存テスト（範囲のみ）: `tests_ui/test_full_view_panes.py:1-60,94-110` / `tests_ui/test_pane_window_width_persistence.py:1-135` / `tests_ui/test_pane_drag_and_window_min.py:1-60,100-125`
- 仕様: `instructions/history/17_full_view_header_width.md` §3-1・§3-2・§3-5・§5-1〜§5-3・§5-5・§5-7〜§5-9
- 文言定数: `keyseq/presentation/hook_button_texts.py`

## 含まない

- 起動時の保存値更新（§3-5 後半・§5-8 後半 = **task_04**）
- ボタン幅・ドロップダウン（task_02 で完了）/ 純関数の変更（task_01 で完了）
- 実機目視（**task_05**）/ 正本反映（**task_06**）

## 確認

python は `../../../.venv/Scripts/python.exe`。実測は `verifier`。

1. `-m compileall -q keyseq tests_ui` が clean。
2. `-m unittest tests_ui.test_full_view_header_width -v` が全 pass。
3. `-m unittest tests_ui.test_full_view_panes tests_ui.test_pane_drag_and_window_min tests_ui.test_pane_widths_persistence tests_ui.test_pane_window_width_persistence tests_ui.test_header_button_widths -v` が全 pass（件数を報告）。
4. `-m unittest discover -s tests` が 450 OK（skip 7）/ `-m unittest discover -s tests_ui` が全 OK / `-m tests.smoke_app` が SMOKE OK / `config/config.json` の mtime 不変。
5. `git diff -- tests_ui/test_full_view_panes.py tests_ui/test_pane_window_width_persistence.py tests_ui/test_pane_drag_and_window_min.py` の変更が、上記「既存テストの期待値見直し」の列挙だけ（`reviewer` が確認）。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**（期待値変更が §5-9 の列挙に限られ弱化がないことを含む）。
- 実機目視は task_05 でまとめて実施。

## 完了記録（2026-09-17）

- 実装は `codex-implementer`（controllers/pane_layout 2 ファイル + 既存 tests_ui 3 ファイルの列挙分 + 新規 7 テスト）。本体 265 行。
- `verifier` 1 回目: `test_full_view_panes.test_02` 1 件（`279 != 220`）+ discover 一括時だけ `WindowWidthPersistenceTest` 12 件が失敗。
- **メインで原因特定・テスト基盤のみ修正**（タスク定義外・アサーション不変）:
  ①`test_full_view_panes._restore_layout`: トリガー一覧が要求幅より広い状態で同じ座標へ `sash_place` すると Tk がサッシュを 59px ずらす（実測 433 → 492）→ 位置が同じなら置き直さない。
  ②`WindowWidthPersistenceTest.setUp`: 実時間 500ms の保存予約が負荷下でテスト中に発火し余分な書き込み → 遅延定数を patch で延ばし開始時に予約取消（各テストは予約を直接実行する設計）。
- `verifier` 2 回目: `tests` 450 OK（skip 7）/ `tests_ui` 425 OK を 2 回連続（揺れなし）/ smoke OK / config mtime 不変。
- `reviewer` = 完了可（既存テストの変更は §5-9 の列挙のみ・弱化なし）/ 基盤修正 2 件の追加レビュー = 採用（遅延定数 500 の検査は別クラスで無効化されていない）。
  運用指摘: 列挙外の失敗は修正前に報告してから着手する。
