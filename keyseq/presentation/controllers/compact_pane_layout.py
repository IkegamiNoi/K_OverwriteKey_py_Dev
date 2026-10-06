"""省略表示の縦ペインの配置・ドラッグ・高さ保存を受け持つ。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from keyseq.presentation.call_view_heights import CALL_VIEW_HEIGHTS_KEY, default_call_view_height
from keyseq.presentation.compact_pane_heights import COMPACT_SEQUENCE_VIEW_KEY, plan_compact_heights
from keyseq.presentation.views.full_view.call_view_frame import list_minimum_height

if TYPE_CHECKING:
    from keyseq.presentation.app import App
    from keyseq.presentation.views.compact_view.sequence_frame import CompactSequenceFrame
    from keyseq.presentation.views.full_view.call_view_frame import CallViewFrame


class CompactPaneLayout:
    def __init__(self, app: App):
        self.app = app
        self.layout_id: str | None = None
        self._drag_heights: dict[str, int] | None = None

    @property
    def box(self):
        return self.app.compact_view.trigger_box

    def install(self) -> None:
        panes = self.box.trigger_panes
        panes.bind("<Configure>", self._on_configure, add="+")
        panes.bind("<Button-1>", self._on_press, add="+")
        panes.bind("<ButtonRelease-1>", self._on_release, add="+")
        for event in ("<Button-2>", "<B2-Motion>", "<ButtonRelease-2>"):
            panes.bind(event, lambda _event: "break", add="+")
        self.schedule_layout()

    def _open_frames(self) -> dict[str, CompactSequenceFrame | CallViewFrame]:
        frames = {}
        if self.app.compact_sequence.is_open:
            frames["sequence"] = self.box.sequence_frame
        if self.app.call_view.hosts["compact"].is_open:
            frames["call"] = self.box.call_view_frame
        return frames

    def _on_configure(self, event) -> None:
        if event.height > 1:
            self.schedule_layout()

    def schedule_layout(self) -> None:
        if self.layout_id is None and self.box.trigger_panes.winfo_ismapped():
            self.layout_id = self.app.after_idle(self._apply_height)

    def on_font_changed(self) -> None:
        box = self.box
        box.trigger_frame.update_idletasks()
        box.sequence_frame.heading.update_idletasks()
        # 下の枠は加算せず、閉じたシーケンスの見出し分はトリガー枠から差し引く。
        heading = 0 if self.app.compact_sequence.is_open else box.sequence_frame.heading.winfo_reqheight()
        pane_height = max(
            list_minimum_height(box.trigger_list),
            box.trigger_frame.winfo_reqheight() - heading,
        )
        box.trigger_panes.configure(width=box.trigger_frame.winfo_reqwidth(), height=pane_height)
        self.schedule_layout()

    def _ensure_desired(self) -> None:
        panes = self.box.trigger_panes
        total = panes.winfo_height()
        if total <= 1 or not panes.winfo_ismapped():
            return
        sequence = self.app.compact_sequence
        if sequence.is_open and sequence.desired_height is None:
            sequence.desired_height = default_call_view_height(total)
        if self.app.call_view.hosts["compact"].is_open:
            self.app.call_view.desired.setdefault("compact", default_call_view_height(total))

    def _apply_height(self) -> None:
        self.layout_id = None
        panes = self.box.trigger_panes
        if self._drag_heights is not None or not panes.winfo_ismapped():
            return
        panes.update_idletasks()
        # update_idletasks 中に登録された重複配置を取り消す。
        if self.layout_id is not None:
            self.app.after_cancel(self.layout_id)
            self.layout_id = None
        self._ensure_desired()
        if panes.winfo_height() <= 1:
            return
        frames = self._open_frames()
        specs = self._height_specs(frames)
        sash = int(panes.cget("sashwidth"))
        available = panes.winfo_height() - len(frames) * sash
        floor = (0 if self.app.compact_sequence.is_open
                 else self.box.sequence_frame.heading.winfo_reqheight())
        minimum = list_minimum_height(self.box.trigger_list) + floor
        heights = plan_compact_heights(available, minimum, floor, specs.get("sequence"), specs.get("call"))
        self._place_heights(frames, heights, available, floor, sash)

    def _height_specs(
        self, frames: dict[str, CompactSequenceFrame | CallViewFrame],
    ) -> dict[str, tuple[int, int, int]]:
        specs = {}
        for key, frame in frames.items():
            heading = frame.heading.winfo_reqheight()
            desired = (self.app.compact_sequence.desired_height if key == "sequence"
                       else self.app.call_view.desired["compact"])
            specs[key] = (desired, heading + frame.minimum_body_height(), heading)
        return specs

    def _place_heights(
        self, frames: dict[str, CompactSequenceFrame | CallViewFrame],
        heights: tuple[int | None, int | None], available: int, floor: int, sash: int,
    ) -> None:
        panes = self.box.trigger_panes
        displayed = dict(zip(("sequence", "call"), heights))
        trigger_height = max(floor, available - sum(height or 0 for height in heights))
        minimum = list_minimum_height(self.box.trigger_list) + floor
        panes.paneconfigure(self.box.trigger_frame, minsize=min(minimum, trigger_height))
        # 高さを明示しないと、子の要求の高さが変わったとき Tk が欄の大きさを決め直す。
        panes.paneconfigure(self.box.trigger_frame, height=trigger_height)
        for key, frame in frames.items():
            minimum = frame.heading.winfo_reqheight() + frame.minimum_body_height()
            panes.paneconfigure(frame.body, minsize=min(minimum, displayed[key]))
            panes.paneconfigure(frame.body, height=displayed[key])
        # 明示した高さで Tk が欄を並べ終えてから境界を置く（古い大きさで押さえ込まれないように）。
        panes.update_idletasks()
        position = trigger_height
        # frames は常にシーケンス、呼び出し先の順。
        for index, key in enumerate(frames):
            panes.sash_place(index, 0, position)
            position += sash + displayed[key]

    def sequence_settings(self) -> dict[str, bool | int]:
        sequence = self.app.compact_sequence
        settings: dict[str, bool | int] = {"open": sequence.is_open}
        if sequence.desired_height is not None:
            settings["height"] = sequence.desired_height
        return settings

    def save_sequence(self) -> None:
        self.app.startup_io.write_startup({COMPACT_SEQUENCE_VIEW_KEY: self.sequence_settings()})

    def _on_press(self, event) -> None:
        panes = self.box.trigger_panes
        if panes.identify(event.x, event.y):
            self._drag_heights = {
                key: frame.body.winfo_height() for key, frame in self._open_frames().items()
            }

    def _on_release(self, _event) -> None:
        before = self._drag_heights
        if before is None:
            return
        self.box.trigger_panes.update_idletasks()
        updates = {}
        for key, frame in self._open_frames().items():
            height = frame.body.winfo_height()
            if key not in before or height == before[key]:
                continue
            if key == "sequence":
                self.app.compact_sequence.desired_height = height
                updates[COMPACT_SEQUENCE_VIEW_KEY] = self.sequence_settings()
            else:
                self.app.call_view.desired["compact"] = height
                updates[CALL_VIEW_HEIGHTS_KEY] = dict(self.app.call_view.desired)
        self._drag_heights = None
        if updates:
            self.app.startup_io.write_startup(updates)
        self.schedule_layout()
