"""テストで生成するクリックがダブルクリックとみなされないよう、押下ごとに離れた時刻を返す。

`event_generate` で作るイベントは時刻が既定で 0 のため、同じ位置を 2 回押すと Tk は
（`sleep` を挟んでも）ダブルクリックとして扱い、`<ButtonPress-1>` のバインドを呼ばない。
"""

from itertools import count

_times = count(10_000, 10_000)


def next_click_time() -> int:
    return next(_times)
