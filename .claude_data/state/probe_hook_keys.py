"""フックが受け取るキーの値を表示する確認用スクリプト（抑止しない・20 秒で終了）。

無変換・変換・半角/全角・かな を 1 回ずつ押す。
"""
import time

import keyboard


def on_event(event):
    if event.event_type != "down":
        return
    print(
        f"name={event.name!r} scan_code={event.scan_code!r} is_keypad={event.is_keypad!r}",
        flush=True,
    )


keyboard.hook(on_event)
print("20 秒間、無変換・変換・半角/全角・かな を 1 回ずつ押してください", flush=True)
time.sleep(20)
keyboard.unhook_all()
print("終了", flush=True)
