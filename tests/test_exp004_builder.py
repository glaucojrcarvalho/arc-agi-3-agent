from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_kaggle_exp004_notebook as builder


class EXP004BuilderTests(unittest.TestCase):
    def test_metadata_and_inference_probe_are_exp004(self) -> None:
        notebook, metadata = builder.build_artifacts(
            agent_source="VALUE = 1\n",
            username="test-owner",
            kernel_slug=builder.DEFAULT_SLUG,
        )
        self.assertIn("EXP-004", metadata["title"])
        self.assertFalse(metadata["enable_internet"])
        self.assertTrue(metadata["enable_gpu"])
        self.assertTrue(metadata["is_private"])
        self.assertEqual(metadata["machine_shape"], "NvidiaRtxPro6000")
        self.assertEqual(metadata["docker_image"], builder.PY312_DOCKER_IMAGE)
        self.assertIn("EXP-004 Python runtime", notebook["cells"][1]["source"])
        self.assertIn("EXP-004", notebook["cells"][0]["source"])
        self.assertIn("EXP-004 model validation inference succeeded", notebook["cells"][1]["source"])
        self.assertIn("EXP-004 public probe result", notebook["cells"][1]["source"])
        self.assertIn("action_trace", notebook["cells"][1]["source"])
        self.assertEqual(metadata["id"], "test-owner/arc-agi-3-exp-004-click-cooldown-policy")
        for index, cell in enumerate(notebook["cells"]):
            if cell.get("cell_type") == "code" and not cell["source"].startswith("%"):
                compile(cell["source"], f"cell-{index}", "exec")


if __name__ == "__main__":
    unittest.main()
