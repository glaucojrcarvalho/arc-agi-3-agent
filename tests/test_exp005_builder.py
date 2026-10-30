from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_kaggle_exp005_notebook as builder


class EXP005BuilderTests(unittest.TestCase):
    def test_metadata_and_inference_probe_are_exp005(self) -> None:
        notebook, metadata = builder.build_artifacts(
            agent_source="VALUE = 1\n",
            username="test-owner",
            kernel_slug=builder.DEFAULT_SLUG,
        )
        self.assertIn("EXP-005", metadata["title"])
        self.assertFalse(metadata["enable_internet"])
        self.assertTrue(metadata["enable_gpu"])
        self.assertTrue(metadata["is_private"])
        self.assertEqual(metadata["machine_shape"], "NvidiaRtxPro6000")
        self.assertEqual(metadata["docker_image"], builder.PY312_DOCKER_IMAGE)
        self.assertIn("EXP-005 Python runtime", notebook["cells"][1]["source"])
        self.assertIn("EXP-005", notebook["cells"][0]["source"])
        self.assertIn("EXP-005 model validation inference succeeded", notebook["cells"][1]["source"])
        self.assertIn("EXP-005 public probe result", notebook["cells"][1]["source"])
        self.assertIn('ARC_MODEL_PLANNING_ENABLED', notebook["cells"][1]["source"])
        self.assertIn('ARC_MODEL_MAX_TOKENS', notebook["cells"][1]["source"])
        self.assertIn('for game in ("ls20", "vc33", "r11l", "tn36")',
                      notebook["cells"][1]["source"])
        self.assertIn("action_trace", notebook["cells"][1]["source"])
        self.assertEqual(metadata["id"], "test-owner/arc-agi-3-exp-005-persistent-reasoning-policy")
        for index, cell in enumerate(notebook["cells"]):
            if cell.get("cell_type") == "code" and not cell["source"].startswith("%"):
                compile(cell["source"], f"cell-{index}", "exec")


if __name__ == "__main__":
    unittest.main()
