from __future__ import annotations

import logging

from .input_source import InputSourceAPI


_LOG = logging.getLogger(__name__)


class MacImeBackend:
    def __init__(self, *, tis=None) -> None:
        self._tis = tis
        self._load_failure_logged = False
        self._capture_sources: tuple[object, object] | None = None

    def _native_api(self):
        if self._tis is None:
            try:
                self._tis = InputSourceAPI()
            except Exception:
                if not self._load_failure_logged:
                    _LOG.exception("Could not load keyboard input source API")
                    self._load_failure_logged = True
                return None
        return self._tis

    def disable_for_text(self): return None
    def restore_after_text(self, reservation, character_count): pass
    def restore_ime_now(self): pass

    def get_own_open_status(self, window) -> bool | None:
        try:
            tis = self._native_api()
            if tis is None: return None
            source = tis.current()
            if source is None:
                return None
            try:
                ascii_capable = tis.is_ascii_capable(source)
                return None if ascii_capable is None else not ascii_capable
            finally:
                tis.release(source)
        except Exception:
            _LOG.exception("Could not read keyboard input source")
            return None

    def set_own_open_status(self, window, is_open: bool) -> bool:
        sources = self._capture_sources
        try:
            tis = self._native_api()
            if tis is None: return False
            if is_open:
                self._capture_sources = None
                try:
                    return self._restore_capture_source(tis, sources)
                finally:
                    if sources is not None:
                        tis.release(sources[0]); tis.release(sources[1])
            self._release_capture(tis)
            original = tis.current()
            target = tis.ascii_source()
            if original is None or target is None:
                if original: tis.release(original)
                if target: tis.release(target)
                return False
            status = tis.select(target)
            current = tis.current()
            matches = current is not None and tis.source_id(current) == tis.source_id(target)
            if current: tis.release(current)
            if status != 0 or not matches:
                tis.release(original); tis.release(target)
                return False
            self._capture_sources = (original, target)
            return True
        except Exception:
            _LOG.exception("Could not switch keyboard input source")
            return False

    def _restore_capture_source(self, tis, sources: tuple[object, object] | None) -> bool:
        if sources is None:
            return False
        original, target = sources
        current = tis.current()
        if current is None: return False
        try:
            matches = tis.source_id(current) == tis.source_id(target)
        finally:
            tis.release(current)
        if not matches:
            return False
        status = tis.select(original)
        return status == 0

    def _release_capture(self, tis) -> None:
        sources, self._capture_sources = self._capture_sources, None
        if sources is not None:
            tis.release(sources[0]); tis.release(sources[1])
