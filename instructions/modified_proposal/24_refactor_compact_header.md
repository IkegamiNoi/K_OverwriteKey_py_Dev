# 提案書 24: phase 58（画面サイズの調整）後のリファクタ

> 状態: **実施済**（2026-10-15・phase 58 task_07_refactor。見出しの文言を `_heading_text` に・区画の題名と pack の引数を登録時に受け取り `_title` / `("hook", "display")` / `pady=(8, 0)` の重複を削除・`_full_view_boxes` で 3 枠のタプルを 1 か所に・項目 0 のテスト追加・reviewer 採用）。

## 判定の要約

範囲 `git diff 33dea2a..HEAD -- keyseq/`（14 ファイル・+369 / -22）。メトリクスは verifier の実測、M3・M4・M6 はメインで裏取り（下記の ファイル:行）。

- **M3 該当**: 省略表示の上部の見出しの文言 `f"▾ {title}"` / `f"▸ {title}"` の組み立てが `controllers/compact_header_controller.py` 内に **4 か所**（`:30`・`:35-36`・`:89`・`:91-92`）。記号や書式を変えると 3 か所を直す形
- **M4 該当**: 区画の名前の列挙 `("hook", "display")` が 0 → **2 か所**（`compact_header_controller.py:40`・`:80`）+ 名前から見出しを決める分岐（`:45-46` `_title`）。区画を足すと 3 か所を直す形。
  あわせて `controllers/pane_layout/pane_measure.py` の 3 枠のタプル `(keymap_box, trigger_box, sequence_box)` が **2 か所**（`:40`・`:99`）
- **M3（責務）該当**: 「表示」の枠の上の余白 `pady=(8, 0)` が view（`views/compact_view/compact_view.py:31`）と controller（`compact_header_controller.py:55`・`:64`）に同値の直値で 3 か所。配置の知識が controller に漏れている（既存定数との重複ではないので厳密には M6 でなく同型の重複として扱う）
- 非該当: M1（600 行超は `app.py` 750 行 +13・`keymap_panel_controller.py` 654 行 +4・`trigger_panel_controller.py` 647 行 +9。いずれも +100 未満）/ M2（最長は `scroll_area.py` `_measure_scroll_area` 66 行）/ M5（0 件）/
  M6 の `scroll_area.py:57` の `120`（ホイールの 1 刻み。同値の既存定数なし・`grid_editor_panel.py` の同じ式は phase 57 の既存）
- 参考（提案書に含めない）: 既存の `views/compact_view/sequence_frame.py:40`・`views/full_view/call_view_frame.py:59-64` にも同じ `▾ / ▸` の見出しの形がある（phase 58 で触っていないコード）

## 項目 0: 安全網の確認

- 対象領域のテスト: `tests_ui/test_compact_header_view.py`（開閉・見出しの文言・並び順・保存・起動時の状態・フォーカス・最小の高さ）/ `tests/test_compact_header_view.py`（検証）/
  `tests_ui/test_full_view_min_height.py`・`test_full_view_min_size.py`・`test_full_view_scroll_areas.py`・`test_full_view_panes.py`（pane_measure）
- 完了条件: 着手前に `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` が全 pass（基準線）

## 項目 1: 見出しの文言を 1 つの関数で作る（M3）

- 対象: `controllers/compact_header_controller.py:30`・`:35-36`・`:89`・`:91-92`
- 変更:
  ```python
  @staticmethod
  def _heading_text(title: str, is_open: bool) -> str:
      return f"{'▾' if is_open else '▸'} {title}"
  # register_section / toggle の 4 か所をこの呼び出しに置き換える
  ```
- 完了条件: 項目 0 のコマンドが全 pass。`grep -c '▸ {' keyseq/presentation/controllers/compact_header_controller.py` が 0（記号は `_heading_text` の中の `'▸'` だけに残る）
- リスクと戻し方: 挙動不変（同じ文字列）。戻すなら直書きに戻す
- 依存: なし

## 項目 2: 区画の見出し・並び・配置を登録時に受け取る（M4・M6）

- 対象: `controllers/compact_header_controller.py:25-84`・`app.py:356-363`（登録の呼び出し 2 か所）
- 変更: `register_section(name, frame, heading, collapsed_heading, title)` で見出しの名前を view 側（app.py の登録）から受け取り、**登録の順を並び順**にする。
  **前提: 登録の時点で枠が pack 済み**（今は `compact_view.py:27`・`:31` で pack → `app.py:356` 以降で登録）。この前提を docstring に書く。
  枠の pack の引数（`side` / `fill` / `expand` / `pady`）は登録時に `frame.pack_info()` から写して持ち、閉じた見出し・開き直した枠の pack にそれを使う（`in` は除く）。
  `apply_initial_state` と `_section_order` は `self._sections` の順を回す。`_title` と `("hook", "display")` の 2 か所・`pady=(8, 0)` の 2 か所を消す（余白の正は view の `compact_view.py:31` だけ）
  ```python
  # 変更前: if name == "display": collapsed.pack_configure(pady=(8, 0))
  # 変更後: collapsed.pack(**section.pack_options, **before)
  ```
- 完了条件: 項目 0 のコマンドが全 pass。`grep -c '"hook", "display"\|(8, 0)' keyseq/presentation/controllers/compact_header_controller.py` が 0。
  `tests_ui/test_compact_header_view.py` に「閉じた見出し・開き直した枠の `pack_info()['pady']` と並び順が元と同じ」の確認が無ければ先に足す（項目 0 の安全網の補強）。
  対象外: `compact_header_view.py` の `parse_compact_header_view` のキーの列挙（保存形式の定義なのでそのまま）
- リスクと戻し方: 挙動不変（同じ並び・同じ余白・保存するキー名は `name` のまま）。戻すなら名前の列挙と直値に書き戻す
- 依存: 項目 1 の後（同じファイル）

## 項目 3: フル表示の 3 枠のタプルを 1 か所にする（M4）

- 対象: `controllers/pane_layout/pane_measure.py:40`・`:99`
- 変更: `def _full_view_boxes(app) -> tuple[...]: view = app.full_view; return (view.keymap_box, view.trigger_box, view.sequence_box)` を置き、2 か所をこれに置き換える（`measure_min_widths` の枠ごとの式は枠ごとに違うので対象外）
- 完了条件: 項目 0 のコマンドが全 pass。`grep -c "keymap_box, .*trigger_box, .*sequence_box" keyseq/presentation/controllers/pane_layout/pane_measure.py` が 1（`_full_view_boxes` の中だけ。`measure_min_widths` の `_stacked_width(app, view.keymap_box, ...)` は枠ごとの式なので数えない・実施時に訂正）
- リスクと戻し方: 挙動不変。戻すならタプルを 2 か所に書き戻す
- 依存: なし

## 実施の目安

- 3 項目とも presentation 内・挙動不変・合計の差分は数十行。`codex-implementer` で 1 タスク（`task_07_refactor`）にまとめられる
