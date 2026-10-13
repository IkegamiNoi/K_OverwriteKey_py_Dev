# task_02_grid_session_ops_and_nudge

## 目的

枠の表示中のキーの振り分けを操作キー（task_01 の `grid.ops`）で行い、クリック点と矢印による移動を加える（暫定 41 §5・§6）。
suppress する集合をセッションが状態の変化ごとに計算して 1 本で公開し、振り分けの `esc` の固定分岐と `esc_active` を廃止する。
**application 限定**（`screen_grid_session.py`・`input_router.py`）+ domain の純関数 2 つ（`geometry.py`）。presentation は変えない（描画は task_03）。スキーマ不変（task_01 で済み）。

## 対象範囲（application + domain の geometry のみ）

### `keyseq/domain/screen_grid/geometry.py`

* 定数 `NUDGE_MAX_PX = 16`・`NUDGE_DIVISOR = 8`（`models.py` の他の px 定数と並べてもよい）
* `nudge_step(length: int, fine: bool) -> int`: `fine` なら 1、そうでなければ `max(1, min(NUDGE_MAX_PX, length // NUDGE_DIVISOR))`
* `clamp_point(rect: Rect, x: int, y: int) -> tuple[int, int]`: `x` を `[left, max(left, right - 1)]`、`y` を `[top, max(top, bottom - 1)]` へ切り詰める（0px の枠では 1 点・暫定 41 §6）
* `__init__.py` へ再輸出

### `keyseq/application/screen_grid_session.py`

* **`GridRouteSnapshot` から `esc_active` を削除**（`visible` / `generation` / `suppress_keys` の 3 つ）
* **`GridView` に `click_point: tuple[int, int] | None = None` を足す**（選択があるときだけ値・task_03 の十字の描画が使う）
* 状態 `_click_point: tuple[int, int] | None` を持つ。枠を選んだとき・戻る（`_back`）で親の枠を選び直したとき = その枠の中心（`rect_center`）。
  選択が無くなる経路（`_set_monitor`・`_subdivide`・`_click_action` の後・`_next_monitor`・`_clear_state`）で `None`。**何もしないで返る経路では変えない**（暫定 41 §5）
* `handle(action)` を次の順に書き直す（キー名の固定分岐 enter / tab / esc・backspace / space をやめる）:
  1. 非表示・世代違いは何もしない（従来どおり）
  2. **今の深さの枠のキー**なら: リピートは無視 / その枠を選び、クリック点を中心にしてカーソルを移す（Shift は無視）
  3. 操作キーを引き当てる: `ops_of(self._grid)` の 8 操作を `GRID_OPS` の順で見て先に一致したもの・無ければ `FIXED_BACK_KEY` → back / `FIXED_CLICK_KEY` → click。どれでもなければ何もしない
  4. `deepen` / `back` / `next_screen`: リピートは無視・Shift は無視。back は `esc` かつ深さ 0 なら何もしない（集合で素通しになっているはずの守り）
  5. `click`: リピートはクリックしない。`action.shift` で右クリック。**クリック点**（選択なしで深さ ≥1 なら今の領域の中心）をクリックする
  6. `up` / `down` / `left` / `right`: 選択なしなら何もしない。リピートを受ける。
     移動量 = `nudge_step(枠の幅 or 高さ, action.shift)`、新しい点を選んだ枠の矩形で `clamp_point` し、変わったときだけカーソルを移して `_changed()`（変わらなければ何もしない）
* **実効の suppress 集合**（暫定 41 §5「suppress する集合」）:
  * `_rebuild_suppression` は従来の契機（表示の開始・列挙のやり直し）で**元の集合** = 全画面の最上段のキー ∪ 細分化のキー ∪ {deepen, back, click, next_screen の操作キー} ∪ {`num enter`} を作り、
    そこから `{esc} ∪ {up, down, left, right の操作キー}` を除いて持つ（ハードコードの enter / space / backspace / tab をやめる）
  * `_publish_snapshot` で実効の集合 = 元の集合 ∪（深さ ≥1 なら `{esc}`）∪（選択ありなら矢印の操作キー）∪（今の深さの枠のキー ∩（`{esc}` ∪ 矢印の操作キー））を計算して `suppress_keys` に入れる。非表示なら空
  * `_changed` は従来どおり `_publish_snapshot` を呼ぶので、選択・深さの変化のたびに集合が更新される

### `keyseq/application/input_router.py`

* `_route_grid_key` の `if key == "esc": ...` の分岐を削除し、**全キーを `key in snapshot.suppress_keys` だけで判定**する（ctrl / alt / windows 押下中・修飾キー単独の素通しと Shift の採取は従来どおり）

### テスト

* `tests/test_screen_grid.py` か新規 `tests/test_screen_grid_geometry_nudge.py`: `nudge_step`（大きい枠で 16・小さい枠で 1/8・最小 1・fine で 1）/ `clamp_point`（通常・0px の幅 / 高さ）
* `tests/test_screen_grid_session.py`（既存の esc_active・固定キーの期待を新しい定義へ書き換え + 追加）:
  * 既定の ops で従来の操作（Space / Esc / BackSpace / Enter / num enter / Shift+Enter / Tab）がそのまま効く
  * 付け替えた ops（例 deepen = `h`・click = `k`）で新しいキーが効き、元のキー（space / enter）は `suppress_keys` に入らない・`handle` しても何もしない
  * 枠のキー > 操作キー: 今の深さの枠のキーと同じ操作キーは枠の選択になる / 別の深さでは操作になる
  * 実効の集合: 最上段・選択なしで `esc` と矢印が入らない / 深さ ≥1 で `esc` が入る / 選択ありで矢印が入る / 手編集で細分化にだけ `esc` や `up` がある grid で、最上段・選択なしのとき入らず、深さ ≥1 では入る
  * クリック点: 選ぶと中心 / 矢印で移動量どおり・Shift で 1px・端で止まる・リピートで連続して動く / Enter・Shift+Enter がずらした点をクリック / 選び直し・Space・戻る・Tab・クリックで中心または None に戻る / 画面 1 つの Tab・4px 未満の Space・最上段の戻るではクリック点が変わらない / 0px の枠で枠の外へ出ない / 選択なしの矢印は何もしない
  * `view().click_point` が選択時だけ値を持つ
* `tests/test_input_router.py`: `esc_active` を使うテストを、`suppress_keys` に `esc` があるかどうかで素通し / 振り分けが決まる形へ書き換える

## 設計メモ / 制約

* フックのスレッドは `snapshot().suppress_keys` だけを見る（UI スレッドの状態を読まない）。集合の計算は UI スレッド（セッション）で行う
* `ops_of` は毎回呼んでよい（小さい dict）が、`_rebuild_suppression` と `handle` で同じ読み方をすること（`sync` で `self._grid` を保持した後の値）
* カーソル移動・クリックの失敗は従来どおり例外を上げ、`ScreenGridController.handle` が畳む（変更不要）
* presentation（`grid_overlay_window.py`・`screen_grid_controller.py`・`hook_controller.py`）は変えない。`GridView` のフィールド追加は既定値つきなので既存の利用側は壊れない

## 読むファイル

* `instructions/history/41_grid_crosshair_nudge.md`（§5・§6）
* `keyseq/application/screen_grid_session.py`（全体・編集対象）
* `keyseq/application/input_router.py`（:30-45 `GridKeyAction`・:153-179 `_route_grid_key`）
* `keyseq/domain/screen_grid/geometry.py`・`ops.py`・`__init__.py`（全体）
* `tests/test_screen_grid_session.py`（全体・編集対象）・`tests/test_input_router.py`（:55-110）

## 含まない

* 十字マークの描画・中央表示のキーの文字の置き換え（task_03）
* 編集の窓の操作キーの欄・`op_keys` の配線・取り込み（task_04）
* 編集の窓のドラッグ中の十字（task_05）
* 正本の改訂（task_07）

## 確認

* `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
* `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_screen_grid_session tests.test_input_router`（と新規ファイル）が全 pass
* `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass
* `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass（`tests_ui/test_screen_grid_overlay.py` を含む）
* `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` OK
* `grep -rn esc_active keyseq tests tests_ui` が 0 件

## 完了条件

* 上記確認 pass・**reviewer 採用**
* 実機目視は task_03（十字が出てから矢印の動きと合わせて確認）
