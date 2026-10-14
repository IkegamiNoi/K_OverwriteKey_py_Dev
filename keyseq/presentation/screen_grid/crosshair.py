from __future__ import annotations


CROSSHAIR_ARM_PX = 12
CROSSHAIR_WIDTH = 2
CROSSHAIR_TAG = "crosshair"


def draw_crosshair(canvas, rect, point, *, fill) -> None:
    """Draw the four clipped arms of a crosshair inside a canvas rectangle."""
    x1, y1, x2, y2 = rect
    px, py = point
    left = max(x1, px - CROSSHAIR_ARM_PX)
    right = min(max(x1, x2 - 1), px + CROSSHAIR_ARM_PX)
    top = max(y1, py - CROSSHAIR_ARM_PX)
    bottom = min(max(y1, y2 - 1), py + CROSSHAIR_ARM_PX)

    if left < right:
        canvas.create_line(
            left, py, right, py, fill=fill, width=CROSSHAIR_WIDTH, tags=CROSSHAIR_TAG,
        )
    if top < bottom:
        canvas.create_line(
            px, top, px, bottom, fill=fill, width=CROSSHAIR_WIDTH, tags=CROSSHAIR_TAG,
        )
