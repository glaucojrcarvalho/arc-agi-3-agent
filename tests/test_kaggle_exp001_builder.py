from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_kaggle_exp001_notebook.py"

spec = importlib.util.spec_from_file_location("build_kaggle_exp001_notebook", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class KaggleExp001BuilderTests(unittest.TestCase):
    def test_metadata_pins_required_offline_inputs(self) -> None:
        metadata = module.build_metadata(
            username="example-user",
            kernel_slug="arc-exp001",
        )

        self.assertEqual(metadata["machine_shape"], "NvidiaRtxPro6000")
        self.assertFalse(metadata["enable_internet"])
        self.assertEqual(metadata["dataset_sources"], [module.VLLM_DATASET])
        self.assertEqual(metadata["model_sources"], [module.MODEL_SOURCE])
        self.assertEqual(
            metadata["competition_sources"],
            [module.COMPETITION_SLUG],
        )

    def test_notebook_starts_loopback_model_server(self) -> None:
        notebook = module.build_notebook("VALUE = 1\n")
        source = "\n".join(cell.get("source", "") for cell in notebook["cells"])

        self.assertIn("127.0.0.1", source)
        self.assertIn(module.SERVED_MODEL_NAME, source)
        self.assertIn(module.MODEL_PATH, source)
        self.assertIn(module.MODEL_SLUG, source)
        self.assertIn("config.json", source)
        self.assertIn("*.safetensors", source)
        self.assertIn("/kaggle/input/models", source)
        self.assertIn("model entries=", source)
        self.assertIn("import sys", source)
        self.assertIn("sys.executable", source)
        self.assertNotIn("nvidia-smi", source)
        self.assertIn("requirements.lock", source)
        self.assertIn("/kaggle/temp/vllm-site-packages", source)
        self.assertIn("--target", source)
        self.assertIn("--ignore-installed", source)
        self.assertIn("server_env", source)
        self.assertIn("torch.cuda.is_available()", source)
        self.assertIn("torch.cuda.get_device_name(0)", source)
        self.assertIn("rtx pro 6000", source.lower())
        self.assertIn("VLLM_LOGGING_LEVEL", source)
        self.assertNotIn("https://api.openai.com", source)

    def test_expected_model_mount_uses_kaggle_input_slug(self) -> None:
        self.assertEqual(
            module.MODEL_PATH,
            "/kaggle/input/models/mikedan7/qwen3-8-27b-fp8-official/pytorch/hf-fp8/1",
        )

    def test_generated_python_cells_compile(self) -> None:
        notebook = module.build_notebook("VALUE = 1\\n")

        for index, cell in enumerate(notebook["cells"]):
            if cell.get("cell_type") != "code":
                continue
            source = cell.get("source", "")
            if source.lstrip().startswith("%"):
                continue
            compile(source, f"<generated-cell-{index}>", "exec")

    def test_vllm_install_is_isolated_from_kaggle_system_python(self) -> None:
        notebook = module.build_notebook("VALUE = 1\\n")
        source = "\\n".join(
            cell.get("source", "")
            for cell in notebook["cells"]
            if cell.get("cell_type") == "code"
        )

        self.assertIn("--requirement", source)
        self.assertIn("requirements.lock", source)
        self.assertIn("--target", source)
        self.assertIn("vllm-site-packages", source)
        self.assertIn("--ignore-installed", source)
        self.assertIn('env=server_env', source)

    def test_save_and_run_performs_model_inference_validation(self) -> None:
        notebook = module.build_notebook("VALUE = 1\\n")
        source = "\\n".join(
            cell.get("source", "")
            for cell in notebook["cells"]
            if cell.get("cell_type") == "code"
        )

        self.assertIn("BOOT_MODEL = True", source)
        self.assertIn("validation inference succeeded", source)
        self.assertIn("/v1/chat/completions", source)

    def test_metadata_rejects_owner_embedded_in_slug(self) -> None:
        with self.assertRaises(ValueError):
            module.build_metadata(
                username="example-user",
                kernel_slug="other/slug",
            )


if __name__ == "__main__":
    unittest.main()
