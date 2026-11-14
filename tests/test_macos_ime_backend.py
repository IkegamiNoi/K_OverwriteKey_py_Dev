import unittest
from unittest.mock import patch

from keyseq.infrastructure.os_backend.macos.backend import MacImeBackend


class Source:
    def __init__(self, identifier, ascii_capable):
        self.identifier = identifier
        self.ascii_capable = ascii_capable


class FakeInputSourceAPI:
    def __init__(self, current, target, status=0, auto_select=True):
        self.current_source, self.target = current, target
        self.status, self.auto_select = status, auto_select
        self.selected, self.released = [], []

    def current(self): return self.current_source
    def ascii_source(self): return self.target
    def is_ascii_capable(self, source): return source.ascii_capable
    def source_id(self, source): return source.identifier
    def select(self, source):
        self.selected.append(source)
        if self.status == 0 and self.auto_select: self.current_source = source
        return self.status
    def release(self, source): self.released.append(source)


class MacImeBackendTests(unittest.TestCase):
    def setUp(self):
        self.original = Source("original", False)
        self.target = Source("ascii", True)
        self.api = FakeInputSourceAPI(self.original, self.target)
        self.backend = MacImeBackend(tis=self.api)

    def test_status_reads_ascii_capability(self):
        self.assertIs(self.backend.get_own_open_status(None), True)
        self.api.current_source = Source("ascii", True)
        self.assertIs(self.backend.get_own_open_status(None), False)

    def test_switch_verifies_readback_id_and_restores(self):
        self.assertTrue(self.backend.set_own_open_status(None, False))
        self.assertEqual(self.api.selected, [self.target])
        self.assertTrue(self.backend.set_own_open_status(None, True))
        self.assertEqual(self.api.selected, [self.target, self.original])
        # Copy で得た参照 4 つを 1 回ずつ解放: 切替後の読み直し（target）・戻す前の確認（target）・記録の元と切替先
        self.assertEqual(self.api.released,
                         [self.target, self.target, self.original, self.target])

    def test_switch_fails_without_record_when_id_unchanged_or_select_fails(self):
        self.api.auto_select = False
        self.assertFalse(self.backend.set_own_open_status(None, False))
        self.assertFalse(self.backend.set_own_open_status(None, True))
        self.api.auto_select, self.api.status = True, 1
        self.assertFalse(self.backend.set_own_open_status(None, False))
        self.assertFalse(self.backend.set_own_open_status(None, True))

    def test_restore_only_if_current_id_is_capture_target(self):
        self.assertTrue(self.backend.set_own_open_status(None, False))
        self.api.current_source = Source("user-choice", False)
        self.assertFalse(self.backend.set_own_open_status(None, True))
        self.assertEqual(self.api.selected, [self.target])
        self.assertIn(self.original, self.api.released)
        self.assertIn(self.target, self.api.released)

    def test_exceptions_return_none_or_false(self):
        class Broken(FakeInputSourceAPI):
            def current(self): raise RuntimeError("unavailable")
        backend = MacImeBackend(tis=Broken(self.original, self.target))
        self.assertIsNone(backend.get_own_open_status(None))
        self.assertFalse(backend.set_own_open_status(None, False))

    def test_native_api_load_failure_logs_once(self):
        backend = MacImeBackend()
        with patch("keyseq.infrastructure.os_backend.macos.backend.InputSourceAPI", side_effect=OSError("missing")), \
             patch("keyseq.infrastructure.os_backend.macos.backend._LOG.exception") as log:
            self.assertIsNone(backend.get_own_open_status(None))
            self.assertFalse(backend.set_own_open_status(None, False))
            self.assertEqual(log.call_count, 1)


if __name__ == "__main__":
    unittest.main()
