from __future__ import annotations

import importlib.util
import runpy
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_standalone_agent.py"

spec = importlib.util.spec_from_file_location("build_standalone_agent", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
build_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_module)


class PackagingTests(unittest.TestCase):
    def test_agent_without_internal_import_is_unchanged(self) -> None:
        source = "from __future__ import annotations\nVALUE = 7\n"
        self.assertEqual(build_module.build_standalone_source(source), source)

    def test_internal_package_is_embedded_and_importable(self) -> None:
        source = (
            "from __future__ import annotations\n"
            "from arc_agent.actions import deterministic_fallback\n"
            "VALUE = deterministic_fallback([4, 2, 3])\n"
        )
        bundled = build_module.build_standalone_source(source)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "my_agent.py"
            path.write_text(bundled, encoding="utf-8")
            namespace = runpy.run_path(str(path))

        self.assertEqual(namespace["VALUE"], 2)

    def test_forced_bundle_is_deterministic(self) -> None:
        source = "VALUE = 1\n"
        first = build_module.build_standalone_source(
            source,
            force_support_bundle=True,
        )
        second = build_module.build_standalone_source(
            source,
            force_support_bundle=True,
        )
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
