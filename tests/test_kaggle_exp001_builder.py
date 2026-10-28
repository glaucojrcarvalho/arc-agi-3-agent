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
        self.assertIn(str(module.VLLM_PORT), source)
        self.assertIn(module.SERVED_MODEL_NAME, source)
        self.assertIn(module.MODEL_PATH, source)
        self.assertIn(module.MODEL_SLUG, source)
        self.assertIn(module.VLLM_DATASET_SLUG, source)
        self.assertIn("requirements.lock", source)
        self.assertIn("/kaggle/working/vllm-site-packages", source)
        self.assertIn("--target", source)
        self.assertIn("--ignore-installed", source)
        self.assertIn("--enable-prefix-caching", source)
        self.assertIn("--tool-call-parser", source)
        self.assertIn("qwen3_coder", source)
        self.assertIn("--reasoning-parser", source)
        self.assertIn("qwen3", source)
        self.assertIn("--max-model-len", source)
        self.assertIn("65536", source)
        self.assertIn("server_env", source)
        self.assertNotIn("https://api.openai.com", source)

    def test_host_gpu_preflight_matches_taaf_bootstrap(self) -> None:
        notebook = module.build_notebook("VALUE = 1\n")
        source = "\n".join(
            cell.get("source", "")
            for cell in notebook["cells"]
            if cell.get("cell_type") == "code"
        )

        self.assertIn("nvidia-smi", source)
        self.assertIn("--query-gpu=name", source)
        self.assertIn("rtx pro 6000", source.lower())
        self.assertIn("CUDA GPU check passed", source)
        self.assertNotIn("torch.cuda.is_available()", source)
        self.assertNotIn("torch.cuda.device_count()", source)

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

    def test_vllm_install_is_isolated_and_cleaned_after_validation(self) -> None:
        notebook = module.build_notebook("VALUE = 1\\n")
        source = "\\n".join(
            cell.get("source", "")
            for cell in notebook["cells"]
            if cell.get("cell_type") == "code"
        )

        self.assertIn("/kaggle/working/vllm-site-packages", source)
        self.assertIn("PYTHONPATH", source)
        self.assertIn("env=server_env", source)
        self.assertIn("shutil.rmtree(site_packages", source)
        self.assertNotIn("/kaggle/temp/vllm-e975732-rootfs", source)
        self.assertNotIn("runtime-manifest.json", source)

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
