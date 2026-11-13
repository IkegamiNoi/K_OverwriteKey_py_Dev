"""Standalone listen-only probe: right Option/Control, CapsLock and repeat.

Run on Mac, press/release right Option and right Control, press/release
CapsLock twice, then hold a letter. Stop with Ctrl+C. This is never imported
by the application and does not suppress or post any input.
"""
from __future__ import annotations


def main() -> None:
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    from keyseq.infrastructure.os_backend.macos.event_tap import load_quartz

    quartz = load_quartz()

    def report(_proxy, kind, event, _refcon):
        if kind in (quartz.kCGEventTapDisabledByTimeout, quartz.kCGEventTapDisabledByUserInput):
            quartz.CGEventTapEnable(tap, True)
            return event
        vk = quartz.CGEventGetIntegerValueField(event, quartz.kCGKeyboardEventKeycode)
        if kind == quartz.kCGEventFlagsChanged:
            flags = quartz.CGEventGetFlags(event)
            print(f"flagsChanged vk={vk} flags=0x{flags:08x}", flush=True)
        else:
            repeat = quartz.CGEventGetIntegerValueField(event, quartz.kCGKeyboardEventAutorepeat)
            print(f"keyDown vk={vk} autorepeat={repeat}", flush=True)
        return event

    mask = (1 << quartz.kCGEventFlagsChanged) | (1 << quartz.kCGEventKeyDown)
    tap = quartz.CGEventTapCreate(quartz.kCGSessionEventTap, quartz.kCGHeadInsertEventTap,
                                   quartz.kCGEventTapOptionListenOnly, mask, report, None)
    if tap is None:
        raise OSError("Could not create listen-only tap; check Input Monitoring permission")
    source = quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
    run_loop = quartz.CFRunLoopGetCurrent()
    quartz.CFRunLoopAddSource(run_loop, source, quartz.kCFRunLoopCommonModes)
    quartz.CGEventTapEnable(tap, True)
    print("Listening: right Option, right Control, CapsLock twice, then hold a letter.", flush=True)
    try:
        while True:
            quartz.CFRunLoopRunInMode(quartz.kCFRunLoopDefaultMode, 0.1, False)
    except KeyboardInterrupt:
        pass
    finally:
        quartz.CGEventTapEnable(tap, False)
        quartz.CFRunLoopRemoveSource(run_loop, source, quartz.kCFRunLoopCommonModes)
        quartz.CFMachPortInvalidate(tap)


if __name__ == "__main__":
    main()
