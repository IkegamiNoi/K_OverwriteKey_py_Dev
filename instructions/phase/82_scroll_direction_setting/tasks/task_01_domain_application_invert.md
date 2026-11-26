# task_01_domain_application_invert

## 目的

`mouse_scroll` の行が送る向きを、縦・横別の設定で反転できるようにする土台を作る（暫定 62 §3・§4）。
domain に反転の値の型と、正規化・反転の純関数を置き、application の `ActionExecutor` が呼び出し時に読む callable で反転を受けて適用する。
**domain + application 限定・presentation / infrastructure 不変・config.json の読み書きはしない（task_02）**。

## 対象範囲（domain・application 限定）

### `keyseq/domain/mouse_scroll.py`

- `@dataclass(frozen=True) class ScrollInvert`: `vertical: bool = False` / `horizontal: bool = False`。モジュール定数 `NO_SCROLL_INVERT = ScrollInvert()`。
- `coerce_scroll_invert(value: object) -> ScrollInvert`（§3）: `value` が dict（`Mapping`）でなければ `NO_SCROLL_INVERT`。dict なら `vertical` / `horizontal` を**値ごとに**判定し、値が `bool` そのもの（`type(x) is bool`。`1` / `"true"` は不可）なら採用、欠け・bool 以外は False。未知のキーは無視。
- `scroll_invert_to_json(invert: ScrollInvert) -> dict[str, bool]`: `{"vertical": ..., "horizontal": ...}`（task_02 の保存で使う。キーは常に両方）。
- `apply_scroll_invert(vertical: bool, deltas: tuple[int, ...], invert: ScrollInvert) -> tuple[int, ...]`（§4）: `vertical` が True なら `invert.vertical`、False なら `invert.horizontal` を見て、True のとき全要素の符号を入れ替えた tuple を返す。False なら `deltas` をそのまま返す。量・個数・順は変えない。
- `scroll_deltas` は変えない。

### `keyseq/application/action_executor.py`

- `ActionExecutor.__init__` に任意のキーワード引数 `get_scroll_invert: Callable[[], ScrollInvert] | None = None` を足し、`self._get_scroll_invert` に持つ（None = 反転なし）。
- `_execute_mouse_scroll` の try の中で、`scroll_deltas(parsed)` の後に `invert = self._get_scroll_invert() if self._get_scroll_invert is not None else NO_SCROLL_INVERT` を**行の実行のたびに 1 回**読み、`deltas = apply_scroll_invert(vertical, deltas, invert)` を当ててから `self.input_gateway.scroll_mouse(...)` へ渡す。callable の例外は既存の `except Exception` に入り、送信の例外と同じ扱い（止まる系）になる（追加の分岐は書かない）。
- `position`・検証・通知の文言・send guard の扱いは変えない。

### テスト

- `tests/test_mouse_scroll.py` の**末尾に**テストを足す（既存テストの途中に差し込まない）:
  - `coerce_scroll_invert`: `None` / list / 文字列 → 両方 False / `{}` → 両方 False / `{"vertical": True}` → 縦だけ True / `{"vertical": True, "horizontal": "true"}` → 縦だけ True（§7-1 の片方だけ不正）/ `{"vertical": 1, "horizontal": True}` → 横だけ True / 未知のキーがあっても無視 / 戻り値が frozen（代入で `FrozenInstanceError`）。
  - `scroll_invert_to_json`: 両方のキーを常に返す。
  - `apply_scroll_invert`: 縦の行 + 縦だけ反転 → 符号が入れ替わる / 縦の行 + 横だけ反転 → 不変 / 横の行 + 横だけ反転 → 入れ替わる / 生の値の分け方 `(120, 120, 60)` → `(-120, -120, -60)`（§7-3）/ 空の tuple → 空。
- `tests/test_action_executor_mouse_scroll.py` の**末尾に**テストを足す（既存の setUp・テストは変えない）:
  - `get_scroll_invert` を渡さないとき今までどおり（既存の `test_success_passes_axis_deltas_and_position` が担保。追加不要）。
  - `get_scroll_invert=lambda: ScrollInvert(vertical=True)` で `down` 3 ノッチ → `deltas=(120, 120, 120)`・`right` 300 delta → `(120, 120, 60)`（横は不変）（§7-2）。
  - `ScrollInvert(horizontal=True)` で `right` 300 delta + 座標 → `deltas=(-120, -120, -60)`・`position=(10, 20)` は不変（§7-2・3）。
  - callable を行ごとに読む: 呼び出しのたびに値を返す Mock（1 回目 `NO_SCROLL_INVERT`・2 回目 `ScrollInvert(vertical=True)`）で `up` を 2 回実行 → 1 回目は正・2 回目は負（§7-6）。
  - callable が例外を投げる → `execute` は False・`scroll_mouse` は呼ばれない・`on_action_error` が呼ばれる（既存の送信の例外のテストの組み立てに合わせる）。

### 設計メモ / 制約

- `ScrollInvert` を domain に置くのは application が型を使うため（前例の `parse_compact_header_view` は presentation だが、本設定は application が読む・暫定 62 §3）。
- executor は Tk の変数を読まない。callable が返すのは不変の `ScrollInvert`（§4）。
- macOS の backend の横の符号の入れ替え（`macos/mouse_backend.py`）は変えない（反転は gateway の手前だけ・§3 の符号の 3 段）。

## 読むファイル

- `keyseq/domain/mouse_scroll.py`（全体・125 行）
- `keyseq/application/action_executor.py:1-50`（import）・`:69-108`（`__init__`）・`:330-355`（`_execute_mouse_scroll`）
- `tests/test_mouse_scroll.py`（全体・135 行）・`tests/test_action_executor_mouse_scroll.py`（全体・70 行）
- `instructions/history/62_scroll_direction_setting.md` §3・§4・§7

## 含まない

- config.json の読込・保存・起動時の値の保持・`App` から `get_scroll_invert` を渡す配線・設定メニュー・`ui_vars`・文言・ヘルプ（task_02）
- `tests/test_menu_bar_deferral.py` の期待値の変更（task_02）
- 統合確認・実機目視（task_03）・正本 / `codebase_map.md` の反映（task_04）
- infrastructure（gateway・両 OS の backend）の変更

## 確認

- `../../../.venv/bin/python -m compileall -q keyseq tests` が clean
- `../../../.venv/bin/python -m unittest tests.test_mouse_scroll tests.test_action_executor_mouse_scroll -v` が pass（追加分を含む）
- `../../../.venv/bin/python -m unittest discover -s tests` が全 pass（既存の期待値は変わらない）
- 差分が上記 4 ファイルに限られる（`git diff --stat`）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_03 でまとめて実施。
