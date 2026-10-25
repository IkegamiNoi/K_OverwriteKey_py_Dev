# task_03_minimum_size_per_layout

## 目的

キーボードUIの最小サイズを、固定の幅 510 から「`w = 1.0` のキーが 27px 以上になる最小の大きさ」（レイアウトごと）へ替え、
レイアウトの切替で `layout_id`・比率・下限のいずれかが変わったら当て直す（暫定 52 §2-4・§2-7・§5）。
**presentation のキーボードUIの大きさ（`keyboard_window_size.py`・`keyboard_window.py`）と tests に限定。幅の記録（task_04）は含まない。スキーマ不変。**

## 対象範囲（キーボードUIの大きさの計算と当て直し・tests 限定）

### `keyseq/presentation/keyboard_window_size.py`

- 定数 `KEYBOARD_KEY_MIN_UNIT = 27`（1u のキーの最小 px）を足す
- 外接を返す純関数 `layout_extent(key_specs) -> tuple[float, float] | None`（`(max(x + w), max(y + h))`・キーが無い / 高さ 0 以下は None）を足し、`layout_aspect` はそれを使う形にしてよい
- `minimum_size(extent: tuple[float, float]) -> tuple[int, int]`（引数を比率から外接へ替える）:
  キャンバス幅の下限 `cw = ceil(27 × max_x)`・高の下限 `ch = ceil(27 × max_y)`、比率 `r = max_x / max_y`。
  `size_from_width(cw + 2 × 余白, r)` と `size_from_height(ch + 2 × 余白, r)` のうち、**幅も高さも両方の下限以上になる方**（どちらの辺も下限を割らない大きい方）を返す。
  丸めで 1px 足りない場合は 1px 足して比率から決め直す（`unit ≥ 26.9` を保てばよい）
- `corrected_size(base, current, ratio, minimum: tuple[int, int])`: 「下限を割ったら最小へ」の判定を、固定の 510 ではなく渡された `minimum` の幅で行い、割ったら `minimum` を返す
- `KEYBOARD_WINDOW_MIN_WIDTH` は**キーが無いレイアウトの既定の大きさ（510 × 210）専用**として残す（名前を `KEYBOARD_WINDOW_EMPTY_SIZE = (510, 210)` 等へ替えてよい。§5 の「キーが無いレイアウトは今どおり」）

### `keyseq/presentation/keyboard_window.py`

- 外接（`self._extent`）と最小（`self._minimum`）を比率と並べて持つ。生成時・`update_layout` で計算する
- 生成時: 大きさ = `self._minimum`（task_04 で記録の幅に替わる）・`minsize` も同じ。キーが無ければ今どおり 510 × 210
- `update_layout`: **`layout_id`・比率・最小のいずれかが変わったら**当て直す（今は比率だけ・`:128`）。
  最大化 / 最小化中は今どおり保留（`_ratio_pending`）し、通常へ戻った後に当てる
- `_apply_ratio_to_base`: 目標の幅 = `max(今の基準の幅, 最小の幅)`（task_04 で「そのレイアウトの記録の幅、無ければ最小」へ替わる。本タスクでは記録が無い前提の形でよいが、目標の幅を決める箇所は 1 か所にまとめる）から比率で決め、`minsize(*self._minimum)`
- `_settle_size`: `minimum_size(...)` / `corrected_size(...)` の呼び出しを新しい引数へ
- 同じ `layout_id` で比率も最小も変わらないとき（選び直し・読み直し）は大きさに触らない（今どおり）

### tests

- `tests/test_keyboard_window_size.py`: 既存の `minimum_size(2)`・`corrected_size(..., 2)` を新しい引数へ追従（意図は変えない）。追加:
  - US TKL（内蔵の外接 18.25 × 6.2）と JIS 見本（14.0 × 6.2）の最小で、キャンバスの unit ≥ 26.9・幅も高さも下限以上・例 ≒ 515 × 188 / 399 × 188（暫定 52 §5 の例。丸めで ±1 は許す）
  - `corrected_size` が渡された最小を割る幅を最小へ引き上げる
- `tests_ui/test_app_ui_flows.py:2612` 付近の `minimum_size(window._ratio)` を新しい引数へ追従
- tests_ui 追加（既存のキーボードUIのテストにならう）:
  - JIS 見本のレイアウトで開くと最小 ≒ 399 幅（510 ではない）
  - JIS を最小まで縮めた状態で US TKL へ切り替えると、目標の幅が US TKL の最小以上で比率どおり（暫定 52 §9-5）
  - 配置が同じ別の `layout_id` へ切り替えると当て直しが呼ばれる / 同じ `layout_id` の選び直しでは大きさに触らない

### 設計メモ / 制約

- 縦横比の補正（phase 55・`features.md` §4.6「縦横比の固定」）の既存の規則（約 150ms・ボタン判定・自分が当てた大きさの受け入れ・最大化 / 最小化中）は変えない
- `ceil` / 四捨五入の扱いは上の規定どおり。テストの期待値は暫定 52 §5 の例と計算から導く

## 読むファイル

- `keyseq/presentation/keyboard_window_size.py`（編集対象・全体）
- `keyseq/presentation/keyboard_window.py`（編集対象・`:69-141`・`:228-353`）
- `tests/test_keyboard_window_size.py`（編集対象・全体）
- `tests_ui/test_app_ui_flows.py:2560-2700`（キーボードUIの大きさのテストの手本と追従箇所）
- `instructions/history/52_keyboard_ui_key_labels.md` §2・§5

## 含まない

- 幅の記録（`keyboard_window_widths`）・記録の幅で開く・切替で記録の幅へ替える（task_04）
- 文字合わせ（task_02）
- 正本の更新（task_06）

## 確認

- compileall clean
- `tests.test_keyboard_window_size` pass・追加した tests_ui の単体 pass
- tests 全体 / tests_ui 全体（同時に 1 本だけ）/ smoke pass・件数が減らない
- `grep -n "KEYBOARD_WINDOW_MIN_WIDTH" -r keyseq tests tests_ui` で、最小の判定に 510 が残っていない（キーが無いレイアウトの既定だけ）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_06 でまとめて実施
