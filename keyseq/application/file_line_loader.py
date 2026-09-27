from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from keyseq.application.file_line_reader import FileLineError, load_file_lines


FILE_LINE_LOAD_TIMEOUT_SECONDS = 5.0


def file_line_load_key(path: str, encoding: str) -> tuple[str, str]:
    return os.path.normcase(os.path.normpath(path)), encoding


@dataclass(slots=True)
class FileLineLoadRequest:
    key: tuple[str, str]
    path: str
    encoding: str
    started_at: float
    _worker: _FileLineLoadJob | None = None
    _terminal: FileLinePoll | None = None


@dataclass(slots=True)
class FileLinePoll:
    status: Literal["pending", "done", "error"]
    lines: list[str] | None = None
    error: BaseException | None = None


@dataclass(slots=True)
class _FileLineLoadJob:
    key: tuple[str, str]
    path: str
    encoding: str
    generation: int
    done: bool = False
    lines: list[str] | None = None
    error: BaseException | None = None


@dataclass(slots=True)
class _FileLineRegistration:
    job: _FileLineLoadJob
    timed_out: bool = False


@dataclass(slots=True)
class _FileLineCacheEntry:
    size: int
    mtime_ns: int
    lines: list[str]


class FileLineLoader:
    def __init__(
        self,
        *,
        start_worker: Callable[[Callable[[], None]], None] | None = None,
        clock: Callable[[], float] = time.monotonic,
        stat: Callable[[str], os.stat_result] = os.stat,
        load: Callable[..., list[str]] = load_file_lines,
        timeout_seconds: float = FILE_LINE_LOAD_TIMEOUT_SECONDS,
    ) -> None:
        self._lock = threading.Lock()
        self._registrations: dict[tuple[str, str], _FileLineRegistration] = {}
        self._cache: dict[tuple[str, str], _FileLineCacheEntry] = {}
        self._generation = 0
        self._start_worker = start_worker if start_worker is not None else self._start_thread
        self._clock = clock
        self._stat = stat
        self._load = load
        self._timeout_seconds = timeout_seconds

    @staticmethod
    def _start_thread(fn: Callable[[], None]) -> None:
        threading.Thread(target=fn, daemon=True).start()

    def request(self, path: str, encoding: str) -> FileLineLoadRequest:
        key = file_line_load_key(path, encoding)
        started_at = self._clock()
        start_job: _FileLineLoadJob | None = None
        with self._lock:
            registration = self._registrations.get(key)
            if registration is not None and registration.timed_out:
                raise FileLineError(
                    f"前回のファイル読込が終わっていません（ファイル: {path}）"
                )
            request = FileLineLoadRequest(key, path, encoding, started_at)
            if registration is None:
                start_job = self._register_job_locked(request)
        if start_job is not None:
            self._launch_job(start_job)
        return request

    def poll(self, request: FileLineLoadRequest) -> FileLinePoll:
        start_job: _FileLineLoadJob | None = None
        with self._lock:
            if request._terminal is not None:
                return request._terminal

            job = request._worker
            if job is not None and job.done:
                result = self._job_result_locked(job)
                request._terminal = result
                return result

            if job is None:
                registration = self._registrations.get(request.key)
                if registration is not None and registration.timed_out:
                    result = FileLinePoll(
                        "error",
                        error=FileLineError(
                            f"前回のファイル読込が終わっていません（ファイル: {request.path}）"
                        ),
                    )
                    request._terminal = result
                    return result
                if registration is None:
                    start_job = self._register_job_locked(request)
                    job = start_job

            if self._clock() - request.started_at >= self._timeout_seconds:
                if job is not None and not job.done:
                    registration = self._registrations.get(request.key)
                    if registration is not None and registration.job is job:
                        registration.timed_out = True
                result = FileLinePoll(
                    "error",
                    error=FileLineError(
                        f"ファイルの読込が {self._timeout_seconds:g} 秒以内に終わりませんでした"
                        f"（ファイル: {request.path}）"
                    ),
                )
                request._terminal = result
            else:
                result = FileLinePoll("pending")

        if start_job is not None:
            self._launch_job(start_job)
        return result

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()
            self._generation += 1

    def _register_job_locked(self, request: FileLineLoadRequest) -> _FileLineLoadJob:
        job = _FileLineLoadJob(
            key=request.key,
            path=request.path,
            encoding=request.encoding,
            generation=self._generation,
        )
        request._worker = job
        self._registrations[request.key] = _FileLineRegistration(job)
        return job

    def _launch_job(self, job: _FileLineLoadJob) -> None:
        try:
            self._start_worker(lambda: self._run_job(job))
        except BaseException:
            with self._lock:
                registration = self._registrations.get(job.key)
                if registration is not None and registration.job is job:
                    del self._registrations[job.key]
            raise

    def _run_job(self, job: _FileLineLoadJob) -> None:
        stat_value: os.stat_result | None = None
        try:
            try:
                stat_value = self._stat(job.path)
            except OSError:
                with self._lock:
                    self._cache.pop(job.key, None)

            cached_lines: list[str] | None = None
            if stat_value is not None:
                with self._lock:
                    entry = self._cache.get(job.key)
                    if (
                        entry is not None
                        and entry.size == stat_value.st_size
                        and entry.mtime_ns == stat_value.st_mtime_ns
                    ):
                        cached_lines = list(entry.lines)

            if cached_lines is not None:
                lines = cached_lines
                loaded = False
            else:
                lines = self._load(job.path, encoding=job.encoding)
                loaded = True
        except BaseException as exc:
            with self._lock:
                self._cache.pop(job.key, None)
                job.error = exc
                job.done = True
                self._remove_registration_locked(job)
            return

        with self._lock:
            job.lines = list(lines)
            job.done = True
            if loaded and stat_value is not None and job.generation == self._generation:
                self._cache[job.key] = _FileLineCacheEntry(
                    stat_value.st_size,
                    stat_value.st_mtime_ns,
                    list(lines),
                )
            self._remove_registration_locked(job)

    def _remove_registration_locked(self, job: _FileLineLoadJob) -> None:
        registration = self._registrations.get(job.key)
        if registration is not None and registration.job is job:
            del self._registrations[job.key]

    @staticmethod
    def _job_result_locked(job: _FileLineLoadJob) -> FileLinePoll:
        if job.error is not None:
            return FileLinePoll("error", error=job.error)
        return FileLinePoll("done", lines=list(job.lines or []))
