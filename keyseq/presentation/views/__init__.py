from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from keyseq.presentation.app import App


class FullView(ttk.Frame):
    """フル画面UI"""
    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app

        # header
        self.header_area = ttk.Frame(self, padding=0)
        self.header_area.pack(fill="x", expand=False, pady=(12, 0))

        # フックラベルフレーム
        self.hook_frame = ttk.LabelFrame(self.header_area, text="フック", padding=10)
        self.hook_frame.pack(side="left", fill="y")
        
        # フックラベルフレーム1行目
        self.full_hook_line1 = ttk.Frame(self.hook_frame)
        self.full_hook_line1.pack(side="top", fill="x")
        app.hook_toggle_btn = ttk.Button(self.full_hook_line1, text="開始（フックON）", command=app.hook.toggle_hook)
        app.trigger_toggle_btn = ttk.Button(self.full_hook_line1, text="通常トリガー無効化", command=app.hook.toggle_triggers_enabled, state="disabled")
        app.hook_toggle_btn.grid(row=0, column=0, padx=(0, 8), sticky="w")
        app.trigger_toggle_btn.grid(row=0, column=1, padx=(8, 0), sticky="w")
        
        # フックラベルフレーム2行目
        self.full_hook_line2 = ttk.Frame(self.hook_frame)
        self.full_hook_line2.pack(side="top", fill="x")
        # フック停止トリガー（フル：取得/クリアあり）
        ttk.Label(self.full_hook_line2, text="フック停止トリガー: ").grid(row=0, column=0, sticky="w")
        app.stop_key_entry = ttk.Entry(self.full_hook_line2, textvariable=app.ui_vars.stop_key_var, width=8, state="readonly")
        app.stop_key_entry.grid(row=0, column=1, sticky="w", padx=(0, 0))
        app.stop_key_capture_btn = ttk.Button(self.full_hook_line2, text="キー入力で取得", command=app.toggle_stop_key_capture)
        app.stop_key_capture_btn.grid(row=0, column=2, sticky="w", padx=(8, 0))
        app.stop_key_clear_btn = ttk.Button(self.full_hook_line2, text="クリア", command=app.stop_key_capture.clear)
        app.stop_key_clear_btn.grid(row=0, column=3, sticky="w", padx=(8, 0))

        # 通常トリガー有効/無効トグルキー（フル：取得/クリアあり）
        ttk.Label(self.full_hook_line2, text="有効/無効トグルキー: ").grid(row=1, column=0, sticky="w")
        app.toggle_key_entry = ttk.Entry(self.full_hook_line2, textvariable=app.ui_vars.toggle_key_var, width=8, state="readonly")
        app.toggle_key_entry.grid(row=1, column=1, sticky="w", padx=(0, 0))
        app.toggle_key_capture_btn = ttk.Button(self.full_hook_line2, text="キー入力で取得", command=app.toggle_toggle_key_capture)
        app.toggle_key_capture_btn.grid(row=1, column=2, sticky="w", padx=(8, 0))
        app.toggle_key_clear_btn = ttk.Button(self.full_hook_line2, text="クリア", command=app.toggle_key_capture.clear)
        app.toggle_key_clear_btn.grid(row=1, column=3, sticky="w", padx=(8, 0))
        # 表示ラベルフレーム
        self.display_frame = ttk.LabelFrame(self.header_area, text="表示", padding=(10, 6))
        self.display_frame.pack(side="left", fill="both", expand=True, padx=(12, 0))
        app.topmost_chk = ttk.Checkbutton(
            self.display_frame,
            text="常に手前",
            variable=app.ui_vars.always_on_top_var,
            command=app._apply_always_on_top,
        )
        app.topmost_chk.grid(row=0, column=0, sticky="w")
        # 省略表示へ
        app.compact_btn = ttk.Button(self.display_frame, text="省略表示", command=app.show_compact_view)
        app.compact_btn.grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Button(self.display_frame, text="キーボードUI", command=app.layout.open_keyboard_window).grid(
            row=2, column=0, sticky="w", pady=(10, 0)
        )
        app.keyboard_layout_combo = ttk.Combobox(
            self.display_frame,
            textvariable=app.ui_vars.keyboard_layout_var,
            state="readonly",
            width=18,
        )
        app.keyboard_layout_combo.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(10, 0))
        app.keyboard_layout_combo.bind("<<ComboboxSelected>>", app.layout.on_keyboard_layout_selected)

        # ファイル操作（表示フレームの右側）
        self.file_frame = ttk.LabelFrame(self.header_area, text="ファイル", padding=(10, 6))
        self.file_frame.pack(side="right", fill="y", padx=(12, 0))

        ttk.Button(self.file_frame, text="保存", width=18, command=app.config_io.save_keymap_set).pack(fill="x", pady=(0, 4))
        ttk.Button(self.file_frame, text="別名で保存...", width=18, command=app.config_io.save_as).pack(fill="x", pady=4)
        ttk.Button(self.file_frame, text="読込...", width=18, command=app.config_io.load_keymap_set_from).pack(fill="x", pady=4)

        ttk.Button(self.file_frame, text="新規作成", width=18, command=app.config_io.new_config).pack(fill="x", pady=4)

        # main
        self.main_area = ttk.Frame(self)
        self.main_area.pack(fill="both", expand=True, pady=(12, 0))

        self.keymap_box = ttk.LabelFrame(self.main_area, text="キーマップ管理", padding=10)
        self.keymap_box.pack(side="left", fill="y")

        keymap_list_frame = ttk.Frame(self.keymap_box)
        keymap_list_frame.pack(side="top", fill="y", expand=False)
        app.keymap_listbox = tk.Listbox(keymap_list_frame, height=12, width=26, exportselection=False)
        app.keymap_listbox.pack(side="left", fill="y", expand=False)
        app.keymap_listbox.bind("<<ListboxSelect>>", app.keymap_panel.on_keymap_list_select)
        app.keymap_listbox.bind("<KeyRelease>", app.keymap_panel.on_keymap_list_focus_index_change)
        app.keymap_listbox.bind("<Double-Button-1>", app.keymap_panel.on_keymap_list_double_click)
        keymap_list_scrollbar = ttk.Scrollbar(keymap_list_frame, orient="vertical", command=app.keymap_listbox.yview)
        keymap_list_scrollbar.pack(side="left", fill="y")
        app.keymap_listbox.configure(yscrollcommand=keymap_list_scrollbar.set)

        keymap_btns = ttk.Frame(self.keymap_box)
        keymap_btns.pack(fill="x", pady=(6, 0))
        app.keymap_add_btn = ttk.Button(keymap_btns, text="追加", command=app.keymap_panel.add_keymap)
        app.keymap_add_btn.pack(fill="x", pady=(0, 3))
        app.keymap_edit_btn = ttk.Button(keymap_btns, text="キーマップ変更", command=app.keymap_panel.edit_selected_keymap)
        app.keymap_edit_btn.pack(fill="x", pady=3)
        app.keymap_delete_btn = ttk.Button(keymap_btns, text="削除", command=app.keymap_panel.delete_keymap)
        app.keymap_delete_btn.pack(fill="x", pady=3)
        app.keymap_select_btn = ttk.Button(keymap_btns, text="選択", command=app.keymap_panel.select_keymap)
        app.keymap_select_btn.pack(fill="x", pady=3)
        ttk.Separator(keymap_btns).pack(fill="x", pady=6)
        ttk.Button(keymap_btns, text="保存", command=app.config_io.save_selected_keymap).pack(fill="x", pady=3)
        ttk.Button(keymap_btns, text="別名で保存", command=app.config_io.save_selected_keymap_as).pack(fill="x", pady=3)
        ttk.Button(keymap_btns, text="読込", command=app.config_io.load_keymap_file).pack(fill="x", pady=3)

        self.trigger_box = ttk.LabelFrame(self.main_area, text="トリガー一覧（選択して編集）", padding=10)
        self.trigger_box.pack(side="left", fill="y", padx=(12, 0))

        # トリガー一覧（スクロール）
        tl_frame = ttk.Frame(self.trigger_box)
        tl_frame.pack(side="top", fill="y", expand=False)
        self.trigger_list = tk.Listbox(tl_frame, height=12, width=26, exportselection=False)
        self.trigger_list.pack(side="left", fill="y", expand=False)
        sb = ttk.Scrollbar(tl_frame, orient="vertical", command=self.trigger_list.yview)
        sb.pack(side="left", fill="y")
        self.trigger_list.configure(yscrollcommand=sb.set)
        self.trigger_list.bind("<<ListboxSelect>>", app.trigger_panel.on_trigger_list_focus_index_change)
        self.trigger_list.bind("<KeyRelease>", app.trigger_panel.on_trigger_list_focus_index_change)
        self.trigger_list.bind("<Double-Button-1>", app.trigger_panel.on_trigger_double_click)

        tbtns = ttk.Frame(self.trigger_box)
        tbtns.pack(fill="x", pady=(6, 0))
        ttk.Button(tbtns, text="追加", command=app.trigger_panel.add_trigger).pack(fill="x", pady=(0, 3))
        ttk.Button(tbtns, text="トリガー変更", command=app.trigger_panel.rename_trigger).pack(fill="x", pady=3)
        ttk.Button(tbtns, text="削除", command=app.trigger_panel.delete_trigger).pack(fill="x", pady=3)
        ttk.Separator(tbtns).pack(fill="x", pady=6)
        ttk.Button(tbtns, text="保存", command=app.config_io.save_trigger_set_file).pack(fill="x", pady=3)
        ttk.Button(tbtns, text="別名で保存", command=app.config_io.save_trigger_set_file_as).pack(fill="x", pady=3)
        ttk.Button(tbtns, text="読込", command=app.config_io.load_trigger_set_file).pack(fill="x", pady=3)

        app.suppress_chk = ttk.Checkbutton(
            self.trigger_box,
            text="トリガーキーを抑止（suppress）",
            variable=app.ui_vars.suppress_var,
            command=app.trigger_panel.update_suppress,
        )
        app.suppress_chk.pack(anchor="w", pady=(6, 0))

        self.sequence_box = ttk.LabelFrame(self.main_area, text="出力シーケンス（選択中トリガーの内容）", padding=10)
        self.sequence_box.pack(side="left", fill="both", expand=True, padx=(12, 0))

        self.action_list = tk.Listbox(self.sequence_box, height=18, exportselection=False)
        self.action_list.pack(side="left", fill="both", expand=True)
        self.action_list.bind("<<ListboxSelect>>", app.trigger_panel.on_action_list_select)
        self.action_list.bind("<KeyRelease>", app.trigger_panel.on_action_list_focus_index_change)
        self.action_list.bind("<Double-Button-1>", app.trigger_panel.on_action_double_click)
        asb = ttk.Scrollbar(self.sequence_box, orient="vertical", command=self.action_list.yview)
        asb.pack(side="left", fill="y")
        self.action_list.configure(yscrollcommand=asb.set)

        abtns = ttk.Frame(self.sequence_box)
        abtns.pack(side="left", fill="y", padx=(12, 0))
        ttk.Button(abtns, text="追加", width=16, command=app.trigger_panel.add_action).pack(pady=(0, 6))
        ttk.Button(abtns, text="編集", width=16, command=app.trigger_panel.edit_action).pack(pady=6)
        ttk.Button(abtns, text="削除", width=16, command=app.trigger_panel.delete_action).pack(pady=6)
        ttk.Separator(abtns).pack(fill="x", pady=10)
        ttk.Button(abtns, text="上へ", width=16, command=lambda: app.trigger_panel.move_action(-1)).pack(pady=6)
        ttk.Button(abtns, text="下へ", width=16, command=lambda: app.trigger_panel.move_action(+1)).pack(pady=6)
        ttk.Separator(abtns).pack(fill="x", pady=10)
        ttk.Button(abtns, text="保存", width=16, command=app.config_io.save_selected_sequence).pack(pady=6)
        ttk.Button(abtns, text="別名で保存", width=16, command=app.config_io.save_selected_sequence_as).pack(pady=6)
        ttk.Button(abtns, text="読込", width=16, command=app.config_io.load_sequence_file).pack(pady=6)
        ttk.Separator(abtns).pack(fill="x", pady=10)
        # 連続実行（run_to_end）
        app.run_to_end_chk = ttk.Checkbutton(
            abtns,
            text="連続実行",
            variable=app.ui_vars.run_to_end_var,
            command=app.trigger_panel.update_run_to_end,
        )
        app.run_to_end_chk.pack(anchor="w", pady=(8, 0))

        # 連続実行 間隔（ms） ※トリガーごと / デフォルト300
        delay_line = ttk.Frame(abtns)
        delay_line.pack(fill="x", pady=(6, 0))
        ttk.Label(delay_line, text="間隔(ms)").pack(side="left")
        app.run_to_end_delay_entry = ttk.Entry(delay_line, width=8, textvariable=app.ui_vars.run_to_end_delay_var)
        app.run_to_end_delay_entry.pack(side="left", padx=(8, 0))
        # Enter / フォーカスアウトで保存
        app.run_to_end_delay_entry.bind("<Return>", app.trigger_panel.update_run_to_end_delay)
        app.run_to_end_delay_entry.bind("<FocusOut>", app.trigger_panel.update_run_to_end_delay)


# Temporary migration re-export; remove in W6.
from keyseq.presentation.views.compact_view.compact_view import CompactView

