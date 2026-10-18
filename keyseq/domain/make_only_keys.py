"""押下だけが届くキーの走査コード。"""

MAKE_ONLY_SCAN_CODES: frozenset[int] = frozenset({241, 242})


def is_make_only_scan_code(scan_code: object) -> bool:
    try:
        return int(scan_code) in MAKE_ONLY_SCAN_CODES
    except (TypeError, ValueError, OverflowError):
        return False
