import unittest
from unittest.mock import patch

import main as main_module
from keyseq.shared.i18n import fix_language, tr

fix_language("ja")


class MainRestartTest(unittest.TestCase):
    def _run_main(self, restart_requested, relaunch_result=None):
        app = unittest.mock.Mock()
        app.restart_requested = restart_requested
        backend = unittest.mock.Mock()
        backend.app.relaunch.return_value = relaunch_result
        with patch.object(main_module, "get_backend", return_value=backend), patch.object(
            main_module.os, "getcwd", return_value="C:/startup"
        ), patch.object(main_module, "App", return_value=app) as create_app, patch.object(
            main_module.messagebox, "showerror"
        ) as showerror:
            main_module.main()
            create_app.assert_called_once_with(first_launch_welcome=True)
            backend.app.apply_process_identity.assert_called_once_with(main_module.APP_USER_MODEL_ID)
        return app, backend.app.relaunch, showerror

    def test_relaunches_only_when_restart_was_requested(self):
        app, relaunch, showerror = self._run_main(True)
        app.mainloop.assert_called_once_with()
        relaunch.assert_called_once_with("C:/startup")
        showerror.assert_not_called()

        _app, relaunch, _showerror = self._run_main(False)
        relaunch.assert_not_called()

    def test_relaunch_failure_is_shown(self):
        error = OSError("denied")
        _app, relaunch, showerror = self._run_main(True, error)
        relaunch.assert_called_once_with("C:/startup")
        showerror.assert_called_once_with(
            tr("dialog.language_restart.title"),
            tr("dialog.language_restart.failed", error=error),
        )


if __name__ == "__main__":
    unittest.main()
