import unittest
from unittest.mock import patch

import main as main_module
from keyseq.shared.i18n import fix_language, tr

fix_language("ja")


class MainRestartTest(unittest.TestCase):
    def _run_main(self, restart_requested, relaunch_result=None):
        app = unittest.mock.Mock()
        app.restart_requested = restart_requested
        with patch.object(main_module, "set_app_user_model_id"), patch.object(
            main_module.os, "getcwd", return_value="C:/startup"
        ), patch.object(main_module, "App", return_value=app), patch.object(
            main_module, "relaunch_app", return_value=relaunch_result
        ) as relaunch, patch.object(main_module.messagebox, "showerror") as showerror:
            main_module.main()
        return app, relaunch, showerror

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
