from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from typing import Any

from keyseq.application.file_line_loader import (
    FileLineLoader,
    file_line_load_key,
)
from keyseq.application.file_line_reader import FileLineError


class FileLineLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workers: list[Any] = []
        self.now = 0.0
        self.stat_value = SimpleNamespace(st_size=4, st_mtime_ns=10)
        self.stat_calls = 0
        self.load_calls = 0
        self.loader = self._loader()

    def _loader(self, **overrides: Any) -> FileLineLoader:
        options: dict[str, Any] = {
            "start_worker": self.workers.append,
            "clock": lambda: self.now,
            "stat": self._stat,
            "load": self._load,
        }
        options.update(overrides)
        return FileLineLoader(**options)

    def _stat(self, _path: str) -> Any:
        self.stat_calls += 1
        if isinstance(self.stat_value, BaseException):
            raise self.stat_value
        return self.stat_value

    def _load(self, _path: str, *, encoding: str) -> list[str]:
        self.load_calls += 1
        return [encoding, str(self.load_calls)]

    def _run(self, index: int = 0) -> None:
        self.workers[index]()

    def test_confirmation_1_normalizes_path_and_separates_encoding(self) -> None:
        first = file_line_load_key("Folder//sub/../Lines.txt", "utf-8")
        second = file_line_load_key("folder/Lines.txt", "utf-8")
        self.assertEqual(first[0], os.path.normcase(os.path.normpath("Folder/Lines.txt")))
        self.assertEqual(first[0], second[0])
        self.assertEqual(first, file_line_load_key("Folder/Lines.txt", "utf-8"))
        self.assertNotEqual(first, file_line_load_key("Folder/Lines.txt", "cp932"))

    def test_confirmation_2_worker_completion_and_load_error_are_returned(self) -> None:
        request = self.loader.request("lines.txt", "utf-8")
        self.assertEqual(self.loader.poll(request).status, "pending")
        self._run()
        result = self.loader.poll(request)
        self.assertEqual((result.status, result.lines), ("done", ["utf-8", "1"]))

        error = ValueError("read failed")
        loader = self._loader(load=lambda *_args, **_kwargs: (_ for _ in ()).throw(error))
        failed_request = loader.request("bad.txt", "utf-8")
        self.workers[-1]()
        failed = loader.poll(failed_request)
        self.assertEqual(failed.status, "error")
        self.assertIs(failed.error, error)

    def test_confirmation_3_cache_hits_changes_and_errors_invalidate(self) -> None:
        error = OSError("read failed")
        should_fail = False
        calls = 0

        def tracked_load(_path: str, *, encoding: str) -> list[str]:
            nonlocal calls
            calls += 1
            if should_fail:
                raise error
            return [encoding, str(calls)]

        loader = self._loader(load=tracked_load)
        first = loader.request("lines.txt", "utf-8")
        self._run()
        self.assertEqual(loader.poll(first).lines, ["utf-8", "1"])
        cached = loader.request("lines.txt", "utf-8")
        self._run(1)
        self.assertEqual(loader.poll(cached).lines, ["utf-8", "1"])
        self.assertEqual(calls, 1)

        self.stat_value = SimpleNamespace(st_size=5, st_mtime_ns=11)
        changed = loader.request("lines.txt", "utf-8")
        self._run(2)
        self.assertEqual(loader.poll(changed).lines, ["utf-8", "2"])
        self.assertEqual(calls, 2)

        self.stat_value = SimpleNamespace(st_size=6, st_mtime_ns=12)
        should_fail = True
        failed = loader.request("lines.txt", "utf-8")
        self._run(3)
        self.assertIs(loader.poll(failed).error, error)
        should_fail = False
        retried = loader.request("lines.txt", "utf-8")
        self._run(4)
        self.assertEqual(loader.poll(retried).lines, ["utf-8", "4"])
        self.assertEqual(calls, 4)

        self.stat_value = OSError("stat failed")
        stat_error = RuntimeError("load after stat failure")
        stat_loader = self._loader(
            load=lambda *_args, **_kwargs: (_ for _ in ()).throw(stat_error)
        )
        stat_request = stat_loader.request("missing.txt", "utf-8")
        self.workers[-1]()
        self.assertIs(stat_loader.poll(stat_request).error, stat_error)
        self.assertEqual(calls, 4)

    def test_confirmation_4_cache_uses_stat_values_from_before_loading(self) -> None:
        current = SimpleNamespace(st_size=4, st_mtime_ns=10)
        calls = 0

        def changing_stat(_path: str) -> Any:
            return current

        def changing_load(_path: str, *, encoding: str) -> list[str]:
            nonlocal current, calls
            calls += 1
            current = SimpleNamespace(st_size=9, st_mtime_ns=20)
            return [encoding, str(calls)]

        loader = self._loader(stat=changing_stat, load=changing_load)
        request = loader.request("lines.txt", "utf-8")
        self._run()
        self.assertEqual(loader.poll(request).status, "done")
        next_request = loader.request("lines.txt", "utf-8")
        self._run(1)
        self.assertEqual(loader.poll(next_request).lines, ["utf-8", "2"])
        self.assertEqual(calls, 2)

    def test_confirmation_5_clear_cache_blocks_old_job_cache_write(self) -> None:
        request = self.loader.request("lines.txt", "utf-8")
        self.loader.clear_cache()
        self._run()
        self.assertEqual(self.loader.poll(request).lines, ["utf-8", "1"])

        next_request = self.loader.request("lines.txt", "utf-8")
        self._run(1)
        self.assertEqual(self.loader.poll(next_request).lines, ["utf-8", "2"])
        self.assertEqual(self.load_calls, 2)

    def test_confirmation_6_waiter_starts_new_job_after_first_finishes(self) -> None:
        first = self.loader.request("lines.txt", "utf-8")
        second = self.loader.request("lines.txt", "utf-8")
        self.assertEqual(len(self.workers), 1)
        self._run()
        self.assertEqual(self.loader.poll(first).lines, ["utf-8", "1"])
        self.stat_value = SimpleNamespace(st_size=5, st_mtime_ns=11)
        self.assertEqual(self.loader.poll(second).status, "pending")
        self.assertEqual(len(self.workers), 2)
        self._run(1)
        self.assertEqual(self.loader.poll(second).lines, ["utf-8", "2"])
        self.assertEqual(self.load_calls, 2)

    def test_confirmation_7_timeout_marks_only_its_job_and_releases_on_finish(self) -> None:
        request = self.loader.request("lines.txt", "utf-8")
        self.now = 5.0
        result = self.loader.poll(request)
        self.assertEqual(result.status, "error")
        self.assertEqual(
            str(result.error),
            "ファイルの読込が 5 秒以内に終わりませんでした（ファイル: lines.txt）",
        )
        with self.assertRaisesRegex(FileLineError, "前回のファイル読込が終わっていません"):
            self.loader.request("lines.txt", "utf-8")
        self.loader.request("other.txt", "utf-8")
        self.assertEqual(len(self.workers), 2)
        self._run(0)
        self.loader.request("lines.txt", "utf-8")
        self.assertEqual(len(self.workers), 3)

    def test_confirmation_8_completed_result_wins_at_timeout_boundary(self) -> None:
        request = self.loader.request("lines.txt", "utf-8")
        self._run()
        self.now = 5.0
        result = self.loader.poll(request)
        self.assertEqual(result.status, "done")
        self.assertEqual(len(self.workers), 1)
        self.loader.request("lines.txt", "utf-8")
        self.assertEqual(len(self.workers), 2)

    def test_confirmation_9_waiting_request_timeout_does_not_mark_active_job(self) -> None:
        first = self.loader.request("lines.txt", "utf-8")
        waiting = self.loader.request("lines.txt", "utf-8")
        self.now = 5.0
        self.assertEqual(self.loader.poll(waiting).status, "error")
        third = self.loader.request("lines.txt", "utf-8")
        self.assertEqual(len(self.workers), 1)
        self._run()
        self.assertEqual(self.loader.poll(first).status, "done")
        self.assertEqual(self.loader.poll(third).status, "pending")
        self.assertEqual(len(self.workers), 2)

    def test_confirmation_10_terminal_poll_is_stable_and_does_not_restart(self) -> None:
        request = self.loader.request("lines.txt", "utf-8")
        self._run()
        first = self.loader.poll(request)
        second = self.loader.poll(request)
        self.assertIs(second, first)
        self.assertEqual(len(self.workers), 1)

        error = RuntimeError("failed")
        failed_loader = self._loader(
            load=lambda *_args, **_kwargs: (_ for _ in ()).throw(error)
        )
        failed_request = failed_loader.request("bad.txt", "utf-8")
        self.workers[-1]()
        failed_first = failed_loader.poll(failed_request)
        failed_second = failed_loader.poll(failed_request)
        self.assertIs(failed_second, failed_first)
        self.assertIs(failed_second.error, error)


    def test_start_worker_failure_releases_registration(self) -> None:
        def fail_to_start(_fn: Any) -> None:
            raise RuntimeError("cannot start")

        loader = self._loader(start_worker=fail_to_start)
        with self.assertRaises(RuntimeError):
            loader.request("lines.txt", "utf-8")
        loader._start_worker = self.workers.append
        request = loader.request("lines.txt", "utf-8")
        self.assertEqual(len(self.workers), 1)
        self._run()
        self.assertEqual(loader.poll(request).status, "done")

if __name__ == "__main__":
    unittest.main()
