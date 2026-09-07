"""孤児判定の対象範囲と復元先ガードの許可範囲を共有する。
片方だけの変更による「隔離はできるが復元できない」ズレを防ぐ。"""

CANDIDATE_DIRS: tuple[str, ...] = (
    "user/keymaps", "user/trigger_sets", "user/sequences", "user/hotkey_presets",
)
RESERVED_DIR: str = "user/hotkey_presets/global"
