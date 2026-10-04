from __future__ import annotations

from keyseq.application.keymap_switch_batch import validate_switch_batch
from keyseq.domain.config import normalize_key_name
from keyseq.domain.keymap_triggers import duplicate_keymap, keymap_trigger_list
from keyseq.domain.list_editing import numbered_labels
from keyseq.presentation.dialogs import KeymapSwitchBatchDialog


class KeymapAddFlow:
    """追加・個別読込・貼り付けの切替キーをまとめて確定する。"""

    def __init__(self, keymap_panel) -> None:
        self._keymap_panel = keymap_panel
        self._app = keymap_panel._app

    def add_keymap(self) -> None:
        if not self._app.keymap_service.get_keymaps(self._app.data):
            created = self._app.keymap_service.create_keymap(self._app.data)
            self._app.mark_keymap_dirty(created)
            self._keymap_panel._refresh_after_keymap_change()
        else:
            candidates = self._make_candidates("新規", [{}])
            if not self._run_batch("新規", candidates):
                return
            created = candidates[0]
        self._app._set_flash_message(
            f"キーマップを追加しました: {normalize_key_name(created.get('id', ''))}"
        )

    def add_imported_keymap(self, keymap: dict) -> bool:
        # 読込側で採番済みの dict を保ち、共有トリガー一覧や読込元の情報を維持する。
        return self._run_batch("読込", [keymap])

    def paste_keymaps(self, sources: list[dict]) -> tuple[int, int] | None:
        if not sources:
            return None
        start = len(self._app.keymap_service.get_keymaps(self._app.data))
        candidates = self._make_candidates("貼り付け", sources)
        if not self._run_batch("貼り付け", candidates):
            return None
        return start, start + len(candidates) - 1

    def _make_candidates(self, kind: str, sources: list[dict]) -> list[dict]:
        existing = self._app.keymap_service.get_keymaps(self._app.data)
        planned = {**self._app.data, "keymaps": list(existing)}
        labels = numbered_labels(
            [str(source.get("label") or "") for source in sources],
            [str(keymap.get("label") or "") for keymap in existing],
        )
        candidates: list[dict] = []
        for source, label in zip(sources, labels):
            keymap_id = self._app.keymap_service.next_keymap_id(planned)
            candidate = (
                duplicate_keymap(source, keymap_id, label) if kind == "貼り付け"
                else {"id": keymap_id, "label": "", "mappings": {}}
            )
            candidates.append(candidate)
            planned["keymaps"].append(candidate)
        return candidates

    def _run_batch(self, kind: str, new_keymaps: list[dict]) -> bool:
        existing = self._app.keymap_service.get_keymaps(self._app.data)
        if not existing:
            for keymap in new_keymaps:
                self._append_keymap(keymap)
            self._keymap_panel._refresh_after_keymap_change()
            return True
        missing = [
            keymap for keymap in existing
            if not self._app.keymap_service.find_switch_key_for_keymap(
                self._app.data, keymap.get("id", "")
            )
        ]
        targets = missing + new_keymaps
        rows = self._make_rows(kind, missing, new_keymaps)
        titles = {"新規": "キーマップ追加", "読込": "読込キーマップの追加",
                  "貼り付け": "キーマップ貼り付け"}
        dialog = KeymapSwitchBatchDialog(
            self._app, title=titles[kind], rows=rows,
            validate=lambda values: self._validate_values(values, targets, rows, new_keymaps),
        )
        dialog.wait_window()
        values = dialog.result
        if values is None:
            return False
        self._commit_batch(kind, missing, new_keymaps, values)
        self._keymap_panel._refresh_after_keymap_change()
        return True

    def _make_rows(self, kind: str, missing: list[dict], new_keymaps: list[dict]) -> list[tuple[str, str, str, str]]:
        return [
            (row_kind, self._keymap_panel.format_keymap_display_name(keymap)
             or normalize_key_name(keymap.get("id", "")),
             str(keymap.get("label") or ""), "")
            for row_kind, keymaps in (("既存", missing), (kind, new_keymaps))
            for keymap in keymaps
        ]

    def _validate_values(self, values: list[dict], targets: list[dict],
                         rows: list[tuple[str, str, str, str]], new_keymaps: list[dict]) -> tuple[int, str] | None:
        error = validate_switch_batch(
            self._app.data, self._app.data.get("hook_stop_key", ""),
            self._app.data.get("hook_toggle_key", ""), new_keymaps,
            [value["key"] for value in values],
            [keymap["id"] for keymap in targets],
        )
        if error is not None:
            index, reason = error
            return index, f"{rows[index][1]}: {reason}"
        for index, value in enumerate(values):
            try:
                self._app.input_gateway.validate_key_name(value["key"])
            except Exception as exc:
                return index, f"{rows[index][1]}: 不明なキー名です:\n{value['key']}\n\n{exc}"
        return None

    def _commit_batch(self, kind: str, missing: list[dict], new_keymaps: list[dict],
                      values: list[dict]) -> None:
        targets = missing + new_keymaps
        for keymap, value in zip(targets, values):
            keymap["label"] = value["label"]
        for keymap in new_keymaps:
            self._append_keymap(keymap)
        for keymap, value in zip(targets, values):
            self._app.keymap_service.set_keymap_switch_key(
                self._app.data, value["key"], keymap["id"]
            )
            self._app.mark_keymap_dirty(keymap)
        if kind == "貼り付け":
            for keymap in new_keymaps:
                self._app.dirty_tracker.mark_trigger_set_dirty(keymap["id"])
                for row in keymap_trigger_list(keymap) or []:
                    self._app.mark_sequence_dirty(row)

    def _append_keymap(self, keymap: dict) -> None:
        keymaps = self._app.data.get("keymaps")
        if not isinstance(keymaps, list):
            keymaps = []
            self._app.data["keymaps"] = keymaps
        if not keymaps:
            self._app.data["active_keymap_id"] = normalize_key_name(keymap.get("id", ""))
        keymaps.append(keymap)
