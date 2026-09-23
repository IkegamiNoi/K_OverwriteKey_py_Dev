"""フック停止カウントの遅延更新を待つ UI テスト用ヘルパ。"""

import time


def wait_for_hook_pause_count(test_case, app, expected, *, timeout=2.0):
    """期限まで Tk のイベントを処理し、フック停止カウントが expected になるのを待つ。"""
    started = time.monotonic()
    deadline = started + timeout
    while True:
        app.update()
        current = app.hook.get_hook_pause_count()
        if current == expected:
            return
        now = time.monotonic()
        if now >= deadline:
            test_case.fail(
                f"hook pause count: expected={expected}, current={current}; "
                f"elapsed={now - started:.3f}s; timeout={timeout}s"
            )
        time.sleep(min(0.001, deadline - now))
