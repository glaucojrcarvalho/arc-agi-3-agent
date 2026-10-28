from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_kaggle_exp000_fallback.py"

spec = importlib.util.spec_from_file_location(
    "build_kaggle_exp000_fallback",
    SCRIPT_PATH,
)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class KaggleExp000FallbackTests(unittest.TestCase):
    def test_metadata_uses_only_competition_input(self) -> None:
        metadata = module.build_metadata(
            username="example-user",
            kernel_slug="arc-exp000-fallback",
        )

        self.assertFalse(metadata["enable_gpu"])
        self.assertFalse(metadata["enable_internet"])
        self.assertEqual(
            metadata["competition_sources"],
            [module.COMPETITION_SLUG],
        )
        self.assertEqual(metadata["dataset_sources"], [])
        self.assertEqual(metadata["model_sources"], [])

    def test_notebook_has_no_model_runtime(self) -> None:
        notebook = module.build_notebook("VALUE = 1\n")
        source = "\n".join(
            cell.get("source", "")
            for cell in notebook["cells"]
        )

        self.assertIn("arc_agi_3_wheels", source)
        self.assertIn("--agent", source)
        self.assertIn("myagent", source)
        self.assertNotIn("vllm", source.lower())
        self.assertNotIn("ARC_MODEL_", source)
        self.assertNotIn("qwen", source.lower())

    def test_generated_python_cells_compile(self) -> None:
        notebook = module.build_notebook("VALUE = 1\n")

        for index, cell in enumerate(notebook["cells"]):
            if cell.get("cell_type") != "code":
                continue
            source = cell.get("source", "")
            if source.lstrip().startswith("%"):
                continue
            compile(source, f"<generated-cell-{index}>", "exec")

    def test_save_and_run_has_validation_marker(self) -> None:
        notebook = module.build_notebook("VALUE = 1\n")
        source = "\n".join(
            cell.get("source", "")
            for cell in notebook["cells"]
            if cell.get("cell_type") == "code"
        )

        self.assertIn(
            "EXP-000 fallback save-and-run validation succeeded",
            source,
        )
        self.assertIn("/kaggle/working/submission.parquet", source)

    def test_metadata_rejects_owner_embedded_in_slug(self) -> None:
        with self.assertRaises(ValueError):
            module.build_metadata(
                username="example-user",
                kernel_slug="other/slug",
            )


if __name__ == "__main__":
    unittest.main()
