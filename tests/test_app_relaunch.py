import sys
import unittest
from unittest.mock import patch

from keyseq.shared.i18n import fix_language

fix_language("ja")

from keyseq.infrastructure.os_backend.windows.app_relaunch import relaunch_app


class AppRelaunchTest(unittest.TestCase):
    def test_launches_original_command_in_startup_directory(self):
        with patch("keyseq.infrastructure.os_backend.windows.app_relaunch.subprocess.Popen") as popen:
            self.assertIsNone(relaunch_app("C:/work"))
        popen.assert_called_once_with([sys.executable, *sys.argv], cwd="C:/work")

    def test_failure_is_logged_and_returned(self):
        error = OSError("denied")
        with patch("keyseq.infrastructure.os_backend.windows.app_relaunch.subprocess.Popen", side_effect=error), \
                self.assertLogs("keyseq.infrastructure.os_backend.windows.app_relaunch", level="ERROR"):
            self.assertIs(relaunch_app("C:/work"), error)


if __name__ == "__main__":
    unittest.main()
