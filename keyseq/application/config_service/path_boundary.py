"""実体パスの境界判定。"""

import os


def is_real_path_within(path: str, root: str) -> bool:
    """realpath で実体解決したうえで root 配下かを判定する。"""
    try:
        real_path = os.path.normcase(os.path.realpath(path))
        real_root = os.path.normcase(os.path.realpath(root))
        return os.path.commonpath((real_path, real_root)) == real_root
    except (OSError, ValueError):
        return False
