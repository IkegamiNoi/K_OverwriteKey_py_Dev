import ast
from pathlib import Path
import unittest

from keyseq.application.config_service import (
    contracts, orphan_scan, parent_refs_cleanup, quarantine, quarantine_manage,
    reference_scan,
)


CONFIG_SERVICE_PACKAGE = "keyseq.application.config_service"
_INTERNAL_SEGMENT = CONFIG_SERVICE_PACKAGE.rsplit(".", 1)[-1]
_PACKAGE_PREFIX = CONFIG_SERVICE_PACKAGE + "."
INTERNAL_MODULE_NAMES = frozenset({
    "candidate_dirs", "keymap_set_history", "orphan_scan", "parent_refs_cleanup", "path_boundary",
    "quarantine", "quarantine_manage", "reference_scan", "save_path_resolution",
    "save_plan_execution", "split_loading", "split_payloads",
})


def _resolve_relative_module(package: str, node: ast.ImportFrom) -> str | None:
    """相対 import の絶対モジュール名を返す。解決不能なら None。"""
    package_parts = package.split(".") if package else []
    if not 0 < node.level <= len(package_parts):
        return None
    # level=1 は自身、level=2 は親。末尾を level-1 個だけ落とす。
    base = package_parts[:len(package_parts) - (node.level - 1)]
    return ".".join(base + ([node.module] if node.module else []))


def _build_alias_map(tree: ast.AST, package: str) -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound_name = alias.asname or alias.name.split(".")[0]
                aliases.setdefault(bound_name, set()).add(
                    alias.name if alias.asname else bound_name,
                )
        elif isinstance(node, ast.ImportFrom):
            module = (_resolve_relative_module(package, node)
                      if node.level > 0 else node.module)
            if not module:
                continue
            for alias in node.names:
                if alias.name != "*":
                    aliases.setdefault(alias.asname or alias.name, set()).add(
                        f"{module}.{alias.name}",
                    )
    return aliases


def _check_import_node(node: ast.AST, package: str) -> list[str]:
    forbidden: list[str] = []
    if isinstance(node, ast.ImportFrom):
        module = node.module or ""
        if module == CONFIG_SERVICE_PACKAGE:
            for alias in node.names:
                if alias.name not in {"ConfigService", "contracts"}:
                    forbidden.append(f"{node.lineno}: R1 {module}.{alias.name}")
        elif module.startswith(_PACKAGE_PREFIX) and module[len(_PACKAGE_PREFIX):].split(".")[0] != "contracts":
            forbidden.append(f"{node.lineno}: R2 {module}")
        if node.level > 0:
            resolved_module = _resolve_relative_module(package, node)
            if resolved_module is not None:
                relative_prefix = _PACKAGE_PREFIX
                relative_package = CONFIG_SERVICE_PACKAGE
            else:
                # 解決不能時だけ config_service セグメント以降で判定する。
                module_parts = module.split(".")
                if _INTERNAL_SEGMENT not in module_parts:
                    return forbidden
                resolved_module = ".".join(
                    module_parts[module_parts.index(_INTERNAL_SEGMENT):],
                )
                relative_package = _INTERNAL_SEGMENT
                relative_prefix = relative_package + "."
            if resolved_module == relative_package:
                for alias in node.names:
                    if alias.name not in {"ConfigService", "contracts"}:
                        forbidden.append(f"{node.lineno}: R4 {resolved_module}.{alias.name}")
            elif (resolved_module.startswith(relative_prefix)
                    and resolved_module[len(relative_prefix):].split(".")[0] != "contracts"):
                forbidden.append(f"{node.lineno}: R4 {resolved_module}")
    elif isinstance(node, ast.Import):
        for alias in node.names:
            if (alias.name.startswith(_PACKAGE_PREFIX)
                    and alias.name[len(_PACKAGE_PREFIX):].split(".")[0] != "contracts"):
                forbidden.append(f"{node.lineno}: R3 {alias.name}")
    return forbidden


def _check_attribute(
    node: ast.Attribute, aliases: dict[str, set[str]],
) -> list[tuple[tuple[int, str], str]]:
    attribute_refs: list[tuple[tuple[int, str], str]] = []
    # import 由来でない config_service も従来どおり検査する。
    if (isinstance(node.value, ast.Name)
            and node.value.id == "config_service"
            and node.attr in INTERNAL_MODULE_NAMES):
        key = (node.lineno, _PACKAGE_PREFIX + node.attr)
        attribute_refs.append((
            key, f"{node.lineno}: attribute config_service.{node.attr}",
        ))
    parts = []
    root = node
    while isinstance(root, ast.Attribute):
        parts.append(root.attr)
        root = root.value
    if isinstance(root, ast.Name) and root.id in aliases:
        # スコープを分けず、同名の束縛先をすべて保守的に検査する。
        for target in sorted(aliases[root.id]):
            resolved = ".".join([target, *reversed(parts)])
            if resolved.startswith(_PACKAGE_PREFIX):
                internal_name = resolved[len(_PACKAGE_PREFIX):].split(".")[0]
                if internal_name in INTERNAL_MODULE_NAMES:
                    module = _PACKAGE_PREFIX + internal_name
                    key = (node.lineno, module)
                    attribute_refs.append((
                        key, f"{node.lineno}: attribute {module}",
                    ))
    return attribute_refs


def collect_forbidden_refs(source: str, package: str = "") -> list[str]:
    """静的な config_service 内部参照を、行番号と違反経路付きで返す。

    相対 import も、source の所属パッケージ package から絶対名へ解決して検査する。
    package を渡さない場合や相対階層が深すぎる場合は、末尾パターン一致に縮退する。
    縮退時はエイリアスを登録せず、末尾一致に module 名が要るため
    from . import X 形（module が空）は判定できない
    （presentation の走査では package を必ず渡すので、この縮退は起きない）。
    動的import（importlib / __import__）や実行時に組み立てた名前による参照
    （getattr(pkg, name) / 文字列連結で作ったモジュール名）は検出できない。
    エイリアスの解決対象は import / from import が束縛した名前だけで、
    代入で再束縛した変数（x = config_service の x）は解決できない。
    逆に、スコープを分けないため、同名が別スコープで再束縛されると
    実行時には許可される記述でも違反になる（過検出側・意図的）。
    """
    forbidden = []
    tree = ast.parse(source)
    aliases = _build_alias_map(tree, package)
    attribute_refs: dict[tuple[int, str], str] = {}
    for node in ast.walk(tree):
        forbidden.extend(_check_import_node(node, package))
        if isinstance(node, ast.Attribute):
            for key, message in _check_attribute(node, aliases):
                attribute_refs.setdefault(key, message)
    forbidden.extend(attribute_refs.values())
    return forbidden


class ConfigServiceContractsTest(unittest.TestCase):
    def test_implementation_modules_use_contracts_without_legacy_aliases(self):
        constant_names = {name for name in vars(contracts) if name.isupper()}
        type_names = {
            name for name, value in vars(contracts).items()
            if isinstance(value, type) and value.__module__ == contracts.__name__
        }
        self.assertEqual(len(constant_names), 37)
        self.assertEqual(len(type_names), 9)
        for module in (parent_refs_cleanup, reference_scan, orphan_scan,
                       quarantine, quarantine_manage):
            with self.subTest(module=module.__name__):
                self.assertIs(module.contracts, contracts)
            for name in sorted(constant_names | type_names):
                with self.subTest(module=module.__name__, name=name):
                    self.assertFalse(hasattr(module, name))
        for name in ("QUARANTINE_DIR_NAME", "MANIFEST_FILE_NAME", "UNIT_ID_PATTERN",
                     "ENTRY_PLANNED", "ENTRY_MOVED", "ENTRY_FAILED"):
            with self.subTest(internal_name=name):
                self.assertTrue(hasattr(quarantine, name))

    def test_presentation_uses_only_config_service_public_surface(self):
        package = Path(contracts.__file__).parent
        self.assertEqual(
            INTERNAL_MODULE_NAMES,
            {path.stem for path in package.glob("*.py")} - {"__init__", "contracts"},
            "config_service のモジュールが増減したら INTERNAL_MODULE_NAMES を更新する"
            "（更新しないと属性アクセス経路だけ検査を素通りする）",
        )
        repository_root = Path(__file__).resolve().parents[1]
        presentation = repository_root / "keyseq" / "presentation"
        sources = sorted(presentation.rglob("*.py"))
        self.assertTrue(sources, "presentation の走査対象が見つかりません")
        forbidden = [
            f"{path.relative_to(presentation)}:{ref}"
            for path in sources
            for ref in collect_forbidden_refs(
                path.read_text(encoding="utf-8-sig"),
                ".".join(path.parent.relative_to(repository_root).parts),
            )
        ]
        self.assertEqual(forbidden, [], "\n".join(forbidden))

    def test_collect_forbidden_refs_detects_each_route_and_allows_public_imports(self):
        forbidden_sources = (
            ("from keyseq.application.config_service import orphan_scan",
             ["1: R1 keyseq.application.config_service.orphan_scan"]),
            ("from keyseq.application.config_service.orphan_scan import ORPHAN_CANDIDATE",
             ["1: R2 keyseq.application.config_service.orphan_scan"]),
            ("import keyseq.application.config_service.orphan_scan",
             ["1: R3 keyseq.application.config_service.orphan_scan"]),
            ("from keyseq.application import config_service\nconfig_service.orphan_scan",
             ["2: attribute config_service.orphan_scan"]),
            ("import keyseq.application.config_service\nkeyseq.application.config_service.orphan_scan.scan()",
             ["2: attribute keyseq.application.config_service.orphan_scan"]),
            ("from keyseq import application\napplication.config_service.orphan_scan",
             ["2: attribute keyseq.application.config_service.orphan_scan"]),
            ("from keyseq.application import config_service as cs\ncs.orphan_scan",
             ["2: attribute keyseq.application.config_service.orphan_scan"]),
        )
        for source, expected in forbidden_sources:
            with self.subTest(forbidden_source=source):
                self.assertEqual(collect_forbidden_refs(source), expected)
        for source, package, expected in (
            ("from ..application.config_service import orphan_scan", "keyseq.presentation",
             ["1: R4 keyseq.application.config_service.orphan_scan"]),
            ("from ..application.config_service.orphan_scan import ORPHAN_CANDIDATE",
             "keyseq.presentation",
             ["1: R4 keyseq.application.config_service.orphan_scan"]),
            ("from ..application.config_service import orphan_scan", "",
             ["1: R4 config_service.orphan_scan"]),
            ("from ..application import config_service as cs\ncs.orphan_scan",
             "keyseq.presentation",
             ["2: attribute keyseq.application.config_service.orphan_scan"]),
            ("from .. import application as app\napp.config_service.orphan_scan",
             "keyseq.presentation",
             ["2: attribute keyseq.application.config_service.orphan_scan"]),
            ("import keyseq.application.config_service as cs\n"
             "from keyseq.application.config_service import contracts as cs\n"
             "cs.orphan_scan", "",
             ["3: attribute keyseq.application.config_service.orphan_scan"]),
        ):
            with self.subTest(forbidden_source=source, package=package):
                self.assertEqual(collect_forbidden_refs(source, package), expected)
        allowed_sources = (
            "from keyseq.application.config_service import ConfigService, contracts",
            "from keyseq.application.config_service.contracts import ORPHAN_CANDIDATE",
            "import keyseq.application.config_service.contracts",
            "from keyseq.application import config_service\nconfig_service.contracts",
            "from keyseq.application.save_plan import ACTION_SAVE",
            "import keyseq.application.config_service\nkeyseq.application.config_service.contracts.ORPHAN_CANDIDATE",
            "from keyseq import application\napplication.config_service.contracts",
            "from keyseq.application import config_service as cs\ncs.contracts",
        )
        for source in allowed_sources:
            with self.subTest(allowed_source=source):
                self.assertEqual(collect_forbidden_refs(source), [])
        for source, package in (
            ("from ..application.config_service import ConfigService, contracts",
             "keyseq.presentation"),
            ("from ..application.config_service.contracts import ORPHAN_CANDIDATE",
             "keyseq.presentation"),
            ("from .io_dialogs import IoDialogs", "keyseq.presentation.controllers.config_io"),
            ("from ..application.config_service import contracts as c\nc.ORPHAN_CANDIDATE",
             "keyseq.presentation"),
            ("from .. import application as app\napp.config_service.contracts",
             "keyseq.presentation"),
        ):
            with self.subTest(allowed_source=source, package=package):
                self.assertEqual(collect_forbidden_refs(source, package), [])
