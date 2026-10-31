"""Window icon images reflecting the hook display state."""

import logging
from pathlib import Path
import tkinter as tk

from keyseq.presentation.status_icon.badge_shapes import badge_pixels, pixel_runs
from keyseq.presentation.status_text import HookDisplayState

_logger = logging.getLogger(__name__)
_STATES: tuple[HookDisplayState, ...] = ("on", "off", "paused")


class StatusIcon:
    def __init__(self, root: tk.Misc, image_dir: Path) -> None:
        self._root = root
        self._images: dict[HookDisplayState, tuple[tk.PhotoImage, ...]] = {}
        self._last_state: HookDisplayState | None = None
        bases: dict[int, tk.PhotoImage] = {}
        try:
            paths = sorted(Path(image_dir).glob("app_icon_*.png"), key=lambda item: item.name)
        except Exception:
            _logger.exception("Unable to list status icon images in %s", image_dir)
            paths = []
        for path in paths:
            try:
                image = tk.PhotoImage(master=root, file=str(path))
                width, height = image.width(), image.height()
                if width != height or width not in (16, 32, 48):
                    _logger.warning("Ignoring unsupported status icon image %s (%sx%s)", path, width, height)
                    continue
                if width in bases:
                    _logger.warning("Ignoring duplicate status icon size: %s", path)
                    continue
                bases[width] = image
            except Exception:
                _logger.exception("Unable to load status icon image %s", path)
        for state in _STATES:
            try:
                self._images[state] = self._compose(state, bases, sorted(bases) if bases else [16, 32], not bases)
            except Exception:
                _logger.exception("Unable to compose status icon for %s", state)
                try:
                    self._images[state] = self._compose(state, {}, [16, 32], True)
                except Exception:
                    _logger.exception("Unable to create badge-only status icon for %s", state)
                    self._images[state] = ()

    def _compose(
        self,
        state: HookDisplayState,
        bases: dict[int, tk.PhotoImage],
        sizes: list[int],
        full: bool,
    ) -> tuple[tk.PhotoImage, ...]:
        images = []
        for size in sizes:
            image = tk.PhotoImage(master=self._root, width=size, height=size)
            if size in bases:
                image.tk.call(image, "copy", bases[size])
            for x, y, colors in pixel_runs(badge_pixels(size, state, full=full), size):
                image.put((colors,), to=(x, y))  # one row; a flat tuple would be read as one pixel per row
            images.append(image)
        return tuple(images)

    def apply(self, state: HookDisplayState) -> None:
        if state == self._last_state:
            return
        images = self._images.get(state)
        if not images:
            return
        self._last_state = None
        try:
            self._root.iconphoto(True, *images)
            self._last_state = state
        except Exception:
            _logger.exception("Unable to apply status icon")
