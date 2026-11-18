"""同梱ライセンス一覧の形式と版を検査する。"""

import importlib.metadata
import json
from pathlib import Path
import platform
import tkinter
import unittest
from contextlib import contextmanager
import tempfile

from keyseq.presentation import bundled_paths
from keyseq.presentation.help.third_party import load_license_text, load_third_party


class ThirdPartyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.directory = bundled_paths.third_party_dir()

    def test_bundled_notices_are_complete_unique_and_ordered(self) -> None:
        windows_names = [
            "keyboard", "pyautogui", "pynput", "pyscreeze", "pymsgbox",
            "pytweening", "mouseinfo", "pygetwindow", "pyrect", "pyperclip",
            "six", "Python", "Tcl", "Tk", "PyInstaller",
        ]
        # task_13b adds Mac-specific rows; update this interim eleven-row expectation then.
        mac_names = [name for name in windows_names if name not in {"keyboard", "Python", "Tcl", "Tk"}]
        for platform_key, expected in (("win32", windows_names), ("darwin", mac_names)):
            with self.subTest(platform=platform_key):
                notices, error = load_third_party(platform=platform_key)
                self.assertEqual(error, "")
                self.assertEqual([notice.entry.name for notice in notices], expected)
                self.assertTrue(all(notice.text for notice in notices))
                filenames = [notice.entry.file for notice in notices]
                self.assertEqual(len(set(filenames)), len(filenames))

    def test_library_versions_match_installed_distributions(self) -> None:
        notices, error = load_third_party()
        self.assertEqual(error, "")
        for notice in notices:
            if notice.entry.name in {"Python", "Tcl", "Tk"}:
                continue
            with self.subTest(name=notice.entry.name):
                try:
                    actual = importlib.metadata.version(notice.entry.name)
                except importlib.metadata.PackageNotFoundError:
                    self.skipTest(f"{notice.entry.name} is not installed")
                self.assertEqual(notice.entry.version, actual)

    def test_python_tcl_and_tk_versions_match_runtime(self) -> None:
        notices, error = load_third_party()
        self.assertEqual(error, "")
        versions = {notice.entry.name: notice.entry.version for notice in notices}
        if not {"Python", "Tcl", "Tk"} <= versions.keys():
            self.skipTest("Python/Tcl/Tk rows are not bundled for this platform yet")
        self.assertEqual(versions["Python"], platform.python_version())
        self.assertEqual(versions["Tcl"], tkinter.Tcl().eval("info patchlevel"))
        # Tk は Tcl だけのインタプリタでは読み込めないため、窓を出さないルートで版を引く。
        try:
            root = tkinter.Tk()
        except tkinter.TclError as error:
            self.skipTest(f"Tk is unavailable: {error}")
        try:
            root.withdraw()
            tk_patchlevel = root.call("package", "provide", "Tk")
        finally:
            root.destroy()
        self.assertEqual(versions["Tk"], tk_patchlevel)

    def test_invalid_or_missing_manifest_returns_reason_without_raising(self) -> None:
        with self.subTest("missing directory"):
            notices, error = load_third_party(self.directory / "missing")
            self.assertEqual(notices, [])
            self.assertTrue(error)
        cases = (
            ("broken json", "{"),
            ("missing key", json.dumps([{"name": "x", "version": "1", "license": "MIT"}])),
            ("unsafe filename", json.dumps([
                {"name": "x", "version": "1", "license": "MIT", "file": "../x.txt"},
            ])),
            ("unknown platform", json.dumps([{"name": "x", "version": "1", "license": "MIT", "file": "x.txt", "platforms": ["linux"]}])),
            ("empty platforms", json.dumps([{"name": "x", "version": "1", "license": "MIT", "file": "x.txt", "platforms": []}])),
            ("non-string platform", json.dumps([{"name": "x", "version": "1", "license": "MIT", "file": "x.txt", "platforms": [1]}])),
            ("duplicate platform", json.dumps([{"name": "x", "version": "1", "license": "MIT", "file": "x.txt", "platforms": ["win32", "win32"]}])),
            ("extra key", json.dumps([{"name": "x", "version": "1", "license": "MIT", "file": "x.txt", "extra": True}])),
        )
        for label, content in cases:
            with self.subTest(label=label), self._manifest_directory(content) as directory:
                notices, error = load_third_party(directory)
                self.assertEqual(notices, [])
                self.assertTrue(error)

    def test_platform_filter_keeps_unrestricted_rows_and_selects_matching_rows(self) -> None:
        content = json.dumps([
            {"name": "both", "version": "1", "license": "MIT", "file": "both.txt"},
            {"name": "windows", "version": "1", "license": "MIT", "file": "windows.txt", "platforms": ["win32"]},
            {"name": "mac", "version": "1", "license": "MIT", "file": "mac.txt", "platforms": ["darwin"]},
        ])
        with self._manifest_directory(content) as directory:
            for key, expected in (("win32", ["both", "windows"]), ("darwin", ["both", "mac"])):
                notices, error = load_third_party(directory, platform=key)
                self.assertEqual(error, "")
                self.assertEqual([notice.entry.name for notice in notices], expected)

    def test_missing_license_document_only_marks_that_notice(self) -> None:
        with self._manifest_directory(json.dumps([
            {"name": "present", "version": "1", "license": "MIT", "file": "present.txt"},
            {"name": "missing", "version": "2", "license": "BSD", "file": "missing.txt"},
        ])) as directory:
            (directory / "present.txt").write_text("notice", encoding="utf-8")
            notices, error = load_third_party(directory)
        self.assertEqual(error, "")
        self.assertEqual(notices[0].text, "notice")
        self.assertIsNone(notices[1].text)
        self.assertTrue(notices[1].error)

    def _manifest_directory(self, content: str):
        @contextmanager
        def directory_context():
            with tempfile.TemporaryDirectory() as temp_dir:
                directory = Path(temp_dir)
                (directory / "third_party.json").write_text(content, encoding="utf-8")
                yield directory

        return directory_context()

    def test_license_is_loaded_from_the_single_root_copy(self) -> None:
        text = load_license_text()
        self.assertIsNotNone(text)
        self.assertIn("GNU GENERAL PUBLIC LICENSE", text)
        self.assertEqual(bundled_paths.license_path().name, "LICENSE")
        keyseq_dir = Path(__file__).resolve().parents[1] / "keyseq"
        self.assertEqual(list(keyseq_dir.rglob("LICENSE")), [])
