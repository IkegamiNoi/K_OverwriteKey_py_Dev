from __future__ import annotations

import logging

_LOG = logging.getLogger(__name__)
_observer_class = None
_failure_logged = False


def create_minimize_observer():
    """Create the cached PyObjC observer class without importing Cocoa at module load."""
    global _observer_class
    if _observer_class is None:
        from Foundation import NSObject

        class MinimizeObserver(NSObject):
            def willMiniaturize_(self, note):
                global _failure_logged

                def detach(window):
                    for child in list(window.childWindows() or []):
                        detach(child)
                        window.removeChildWindow_(child)

                try:
                    detach(note.object())
                except Exception:
                    if not _failure_logged:
                        _LOG.exception("Could not detach child windows before minimizing")
                        _failure_logged = True

        _observer_class = MinimizeObserver
    return _observer_class.alloc().init()
