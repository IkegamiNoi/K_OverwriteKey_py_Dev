import logging
import tkinter as tk
from collections import deque

from keyseq.presentation import modal
from keyseq.presentation.tk_platform import is_aqua


class MenuCommandQueue:
    def __init__(self, widget):
        self.widget = widget
        self.commands = deque()
        self.after_id = None
        self.running = False

    def defer(self, command):
        if not is_aqua(self.widget):
            return command

        def enqueue():
            self.commands.append(command)
            self._schedule(0)
        return enqueue

    def _schedule(self, delay):
        if self.after_id is None and not self.running and self.commands:
            self.after_id = self.widget.after(delay, self._run_one)

    def _run_one(self):
        self.after_id = None
        if self.running or not self.commands:
            return
        if modal.is_modal_active():
            self._schedule(100)
            return
        command = self.commands.popleft()
        self.running = True
        try:
            command()
        except Exception:
            logging.getLogger(__name__).exception("Deferred menu command failed")
        finally:
            self.running = False
            self._schedule(0)

    def cancel_all(self):
        self.commands.clear()
        if self.after_id is not None:
            try:
                self.widget.after_cancel(self.after_id)
            except tk.TclError:
                pass
            self.after_id = None
