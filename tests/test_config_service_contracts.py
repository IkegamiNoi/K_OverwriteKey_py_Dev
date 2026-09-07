import ast
from pathlib import Path
import unittest

from keyseq.application.config_service import (
    contracts, orphan_scan, parent_refs_cleanup, quarantine, quarantine_manage,
    reference_scan,
)


CONFIG_SERVICE_PACKAGE = "keyseq.application.config_service"
INTERNAL_MODULE_NAMES = frozenset({
    "candidate_dirs", "orphan_scan", "parent_refs_cleanup", "path_boundary",
    "quarantine", "quarantine_manage", "reference_scan", "save_path_resolution",
    "save_plan_execution", "split_loading", "split_payloads",
})


def collect_forbidden_refs(source: str) -> list[str]:
    """静的な config_service 内部参照を、行番号と違反経路付きで返す。

    動的import（importlib / __import__）や変数経由の間接参照は検出できない。
    """
    forbidden = []
    prefix = CONFIG_SERVICE_PACKAGE + "."
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == CONFIG_SERVICE_PACKAGE:
                for alias in node.names:
                    if alias.name not in {"ConfigService", "contracts"}:
                        forbidden.append(f"{node.lineno}: R1 {module}.{alias.name}")
            elif module.startswith(prefix) and module[len(prefix):].split(".")[0] != "contracts":
                forbidden.append(f"{node.lineno}: R2 {module}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if (alias.name.startswith(prefix)
                        and alias.name[len(prefix):].split(".")[0] != "contracts"):
                    forbidden.append(f"{node.lineno}: R3 {alias.name}")
        elif (isinstance(node, ast.Attribute)
              and isinstance(node.value, ast.Name)
              and node.value.id == "config_service"
              and node.attr in INTERNAL_MODULE_NAMES):
            forbidden.append(f"{node.lineno}: attribute config_service.{node.attr}")
    return forbidden


class ConfigServiceContractsTest(unittest.TestCase):
    def test_implementation_modules_use_contracts_without_legacy_aliases(self):
        constant_names = {name for name in vars(contracts) if name.isupper()}
        type_names = {
            name for name, value in vars(contracts).items()
            if isinstance(value, type) and value.__module__ == contracts.__name__
        }
        self.assertEqual(len(constant_names), 34)
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
        presentation = Path(__file__).resolve().parents[1] / "keyseq" / "presentation"
        sources = sorted(presentation.rglob("*.py"))
        self.assertTrue(sources, "presentation の走査対象が見つかりません")
        forbidden = [
            f"{path.relative_to(presentation)}:{ref}"
            for path in sources
            for ref in collect_forbidden_refs(path.read_text(encoding="utf-8-sig"))
        ]
        self.assertEqual(forbidden, [], "\n".join(forbidden))

    def test_collect_forbidden_refs_detects_each_route_and_allows_public_imports(self):
        forbidden_sources = (
            "from keyseq.application.config_service import orphan_scan",
            "from keyseq.application.config_service.orphan_scan import ORPHAN_CANDIDATE",
            "import keyseq.application.config_service.orphan_scan",
            "from keyseq.application import config_service\nconfig_service.orphan_scan",
        )
        for source in forbidden_sources:
            with self.subTest(forbidden_source=source):
                self.assertTrue(collect_forbidden_refs(source))
        allowed_sources = (
            "from keyseq.application.config_service import ConfigService, contracts",
            "from keyseq.application.config_service.contracts import ORPHAN_CANDIDATE",
            "import keyseq.application.config_service.contracts",
            "from keyseq.application import config_service\nconfig_service.contracts",
            "from keyseq.application.save_plan import ACTION_SAVE",
        )
        for source in allowed_sources:
            with self.subTest(allowed_source=source):
                self.assertEqual(collect_forbidden_refs(source), [])
