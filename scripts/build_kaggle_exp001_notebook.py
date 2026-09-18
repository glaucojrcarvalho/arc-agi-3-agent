#!/usr/bin/env python3
"""Generate the EXP-001 Kaggle deployment notebook and kernel metadata.

Generated files are written under dist/ and are intentionally not committed.
The notebook uses only offline Kaggle inputs during competition rerun:
- ARC-AGI-3 competition assets;
- the public ARC3 vLLM wheelhouse;
- a pinned Qwen3.8-27B-FP8 Kaggle model mirror.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AGENT = ROOT / "dist" / "my_agent.py"
DEFAULT_OUTPUT_DIR = ROOT / "dist" / "kaggle-exp001"

COMPETITION_SLUG = "arc-prize-2026-arc-agi-3"
VLLM_DATASET = "driessmit1/arc3-vllm-h100-wheelhouse-v3"
MODEL_SOURCE = "mikedan7/qwen3-8-27b-fp8-official/PyTorch/hf-fp8/1"
MODEL_SLUG = "qwen3-8-27b-fp8-official"
MODEL_PATH = (
    "/kaggle/input/models/mikedan7/qwen3-8-27b-fp8-official/"
    "pytorch/hf-fp8/1"
)
SERVED_MODEL_NAME = "Qwen/Qwen3.8-27B"
VLLM_ENDPOINT = "http://127.0.0.1:8000/v1/chat/completions"


def code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {"trusted": True},
        "outputs": [],
        "execution_count": None,
        "source": source,
    }


def markdown_cell(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source}


def build_notebook(agent_source: str) -> dict:
    validation_request_payload = {
        "model": SERVED_MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "Return exactly one JSON object.",
            },
            {
                "role": "user",
                "content": "Return one short JSON object for validation.",
            },
        ],
        "temperature": 0.0,
        "max_tokens": 64,
        "chat_template_kwargs": {
            "enable_thinking": False,
            "preserve_thinking": False,
        },
    }

    setup_source = dedent(
        f"""\
        import json
        import os
        import shutil
        import subprocess
        import sys
        import time
        import urllib.request
        from pathlib import Path

        TRUE_SUBMISSION = bool(os.getenv("KAGGLE_IS_COMPETITION_RERUN"))
        BOOT_MODEL = True

        if BOOT_MODEL:
            competition_root = Path(
                "/kaggle/input/competitions/{COMPETITION_SLUG}"
            )
            wheelhouse = Path(
                "/kaggle/input/datasets/{VLLM_DATASET}"
            )
            expected_model_path = Path({MODEL_PATH!r})

            if not wheelhouse.exists():
                raise RuntimeError(f"Missing vLLM wheelhouse: {{wheelhouse}}")

            if expected_model_path.exists():
                model_path = expected_model_path
            else:
                models_root = Path("/kaggle/input/models")
                candidates = sorted(
                    set(
                        config.parent
                        for config in models_root.glob("**/config.json")
                        if "{MODEL_SLUG}" in config.parts
                        and any(config.parent.glob("*.safetensors"))
                    )
                )

                if len(candidates) == 1:
                    model_path = candidates[0]
                    print(
                        "Resolved Qwen model from attached Kaggle model input: "
                        f"{{model_path}}"
                    )
                elif not candidates:
                    model_entries = sorted(
                        str(path.relative_to(models_root))
                        for path in models_root.glob("*/*")
                        if path.is_dir()
                    )
                    raise RuntimeError(
                        "Could not resolve attached Qwen model. "
                        f"Expected {{expected_model_path}}; "
                        f"model entries={{model_entries}}"
                    )
                else:
                    raise RuntimeError(
                        "Ambiguous Qwen model mounts: "
                        f"{{[str(path) for path in candidates]}}"
                    )

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-index",
                    "--find-links",
                    str(competition_root / "arc_agi_3_wheels"),
                    "arc-agi",
                    "python-dotenv",
                ],
                check=True,
            )
            requirements = wheelhouse / "requirements.lock"
            if not requirements.exists():
                raise RuntimeError(
                    "Missing vLLM requirements.lock: "
                    + str(requirements)
                )

            vllm_site_packages = Path(
                "/kaggle/temp/vllm-site-packages"
            )
            shutil.rmtree(vllm_site_packages, ignore_errors=True)
            vllm_site_packages.mkdir(parents=True, exist_ok=True)

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-index",
                    "--find-links",
                    str(wheelhouse),
                    "--requirement",
                    str(requirements),
                    "--target",
                    str(vllm_site_packages),
                    "--upgrade",
                    "--ignore-installed",
                    "--only-binary",
                    ":all:",
                    "--no-compile",
                    "--disable-pip-version-check",
                    "--no-warn-conflicts",
                ],
                check=True,
            )

            server_env = os.environ.copy()
            existing_pythonpath = server_env.get("PYTHONPATH", "")
            server_env["PYTHONPATH"] = str(vllm_site_packages)
            if existing_pythonpath:
                server_env["PYTHONPATH"] += (
                    os.pathsep + existing_pythonpath
                )
            server_env["USE_TF"] = "0"
            server_env["TRANSFORMERS_NO_TF"] = "1"
            server_env["TRANSFORMERS_NO_TORCHVISION"] = "1"
            server_env["VLLM_NO_USAGE_STATS"] = "1"
            server_env["HF_HUB_OFFLINE"] = "1"
            server_env["TRANSFORMERS_OFFLINE"] = "1"
            server_env["VLLM_LOGGING_LEVEL"] = "DEBUG"

            cuda_probe = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import torch, vllm; "
                        "print('vLLM', vllm.__version__); "
                        "print('torch', torch.__version__); "
                        "print('torch cuda', torch.version.cuda); "
                        "print('cuda available', torch.cuda.is_available()); "
                        "print('cuda count', torch.cuda.device_count()); "
                        "assert torch.cuda.is_available(); "
                        "assert torch.cuda.device_count() == 1; "
                        "device = torch.cuda.get_device_name(0); "
                        "print('cuda device', device); "
                        "assert 'rtx pro 6000' in device.lower(), device"
                    ),
                ],
                env=server_env,
                capture_output=True,
                text=True,
            )
            print(cuda_probe.stdout)
            if cuda_probe.returncode != 0:
                raise RuntimeError(
                    "Isolated vLLM CUDA preflight failed. stdout="
                    + cuda_probe.stdout.strip()
                    + " stderr="
                    + cuda_probe.stderr.strip()
                )

            log_path = Path("/kaggle/working/vllm-openai-server.log")
            log_handle = log_path.open("w")
            server = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "vllm.entrypoints.openai.api_server",
                    "--model",
                    str(model_path),
                    "--served-model-name",
                    {SERVED_MODEL_NAME!r},
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8000",
                    "--gpu-memory-utilization",
                    "0.92",
                ],
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                env=server_env,
            )

            health_url = "http://127.0.0.1:8000/v1/models"
            deadline = time.time() + 900
            last_error = None
            while time.time() < deadline:
                if server.poll() is not None:
                    raise RuntimeError(
                        f"vLLM exited early with code {{server.returncode}}; "
                        f"see {{log_path}}"
                    )
                try:
                    with urllib.request.urlopen(health_url, timeout=5) as response:
                        if response.status == 200:
                            break
                except Exception as exc:
                    last_error = exc
                time.sleep(5)
            else:
                server.terminate()
                raise RuntimeError(
                    f"vLLM did not become healthy before timeout: {{last_error}}"
                )

            os.environ["ARC_MODEL_NAME"] = {SERVED_MODEL_NAME!r}
            os.environ["ARC_MODEL_ENDPOINT"] = {VLLM_ENDPOINT!r}
            os.environ["ARC_MODEL_TIMEOUT_SECONDS"] = "180"

            if not TRUE_SUBMISSION:
                validation_payload = {validation_request_payload!r}
                validation_request = urllib.request.Request(
                    "http://127.0.0.1:8000/v1/chat/completions",
                    data=json.dumps(validation_payload).encode("utf-8"),
                    headers={{"Content-Type": "application/json"}},
                    method="POST",
                )
                with urllib.request.urlopen(
                    validation_request,
                    timeout=180,
                ) as response:
                    validation_response = json.loads(
                        response.read().decode("utf-8")
                    )
                choices = validation_response.get("choices")
                if not isinstance(choices, list) or not choices:
                    raise RuntimeError(
                        "EXP-001 validation inference returned no choices"
                    )
                print("EXP-001 model validation inference succeeded")
        """
    )

    write_agent_source = "%%writefile /tmp/my_agent.py\n" + agent_source

    registry_text = (
        "from typing import Type\n"
        "from dotenv import load_dotenv\n"
        "from .agent import Agent, Playback\n"
        "from .swarm import Swarm\n"
        "from .templates.random_agent import Random\n"
        "from .templates.my_agent import MyAgent\n\n"
        "load_dotenv()\n\n"
        "AVAILABLE_AGENTS: dict[str, Type[Agent]] = {\n"
        "    'random': Random,\n"
        "    'myagent': MyAgent,\n"
        "}\n"
    )
    env_text = (
        "SCHEME=http\n"
        "HOST=gateway\n"
        "PORT=8001\n"
        "ARC_API_KEY=test-key-123\n"
        "ARC_BASE_URL=http://gateway:8001/\n"
        "OPERATION_MODE=online\n"
        "ENVIRONMENTS_DIR=\n"
        "RECORDINGS_DIR=/kaggle/working/server_recording\n"
        f"ARC_MODEL_NAME={SERVED_MODEL_NAME}\n"
        f"ARC_MODEL_ENDPOINT={VLLM_ENDPOINT}\n"
        "ARC_MODEL_TIMEOUT_SECONDS=180\n"
    )

    run_source = dedent(
        f"""\
        import os
        import shutil
        import subprocess
        import sys
        from pathlib import Path

        if os.getenv("KAGGLE_IS_COMPETITION_RERUN"):
            gateway_url = "http://gateway:8001/api/games"
            subprocess.run(
                [
                    "curl",
                    "--fail",
                    "--retry",
                    "999",
                    "--retry-all-errors",
                    "--retry-delay",
                    "5",
                    "--retry-max-time",
                    "600",
                    gateway_url,
                ],
                check=True,
            )

            source_framework = Path(
                "/kaggle/input/competitions/{COMPETITION_SLUG}/ARC-AGI-3-Agents"
            )
            framework = Path("/kaggle/working/ARC-AGI-3-Agents")
            if framework.exists():
                shutil.rmtree(framework)
            shutil.copytree(source_framework, framework)

            target_agent = framework / "agents" / "templates" / "my_agent.py"
            shutil.copy2("/tmp/my_agent.py", target_agent)

            registry = framework / "agents" / "__init__.py"
            registry.write_text({registry_text!r})

            env_file = framework / ".env"
            env_file.write_text({env_text!r})

            subprocess.run(
                [sys.executable, "main.py", "--agent", "myagent"],
                cwd=framework,
                env={{**os.environ, "MPLBACKEND": "agg"}},
                check=True,
            )
        """
    )

    dummy_source = dedent(
        """\
        import os

        if not os.getenv("KAGGLE_IS_COMPETITION_RERUN"):
            import pandas as pd

            submission = pd.DataFrame(
                data=[["1_0", "1", True, 1]],
                columns=["row_id", "game_id", "end_of_game", "score"],
            )
            submission.to_parquet(
                "/kaggle/working/submission.parquet",
                index=False,
            )
        """
    )

    return {
        "metadata": {
            "kernelspec": {
                "language": "python",
                "display_name": "Python 3",
                "name": "python3",
            },
            "language_info": {"name": "python"},
            "kaggle": {
                "accelerator": "nvidiaRtx6000",
                "isInternetEnabled": False,
                "isGpuEnabled": True,
                "language": "python",
                "sourceType": "notebook",
            },
        },
        "nbformat_minor": 4,
        "nbformat": 4,
        "cells": [
            markdown_cell(
                "# ARC-AGI-3 EXP-001\n\n"
                "Direct Qwen3.8-27B FP8 policy generated from the public "
                "arc-agi-3-agent research repository."
            ),
            code_cell(setup_source),
            code_cell(write_agent_source),
            code_cell(run_source),
            code_cell(dummy_source),
        ],
    }


def build_metadata(*, username: str, kernel_slug: str) -> dict:
    if not username or "/" in username:
        raise ValueError("username must be a Kaggle username slug")
    if not kernel_slug or "/" in kernel_slug:
        raise ValueError("kernel_slug must be one slug, not owner/slug")

    return {
        "id": f"{username}/{kernel_slug}",
        "title": "ARC-AGI-3 EXP-001 Direct Model Policy",
        "code_file": "submission.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "machine_shape": "NvidiaRtxPro6000",
        "keywords": [],
        "dataset_sources": [VLLM_DATASET],
        "kernel_sources": [],
        "competition_sources": [COMPETITION_SLUG],
        "model_sources": [MODEL_SOURCE],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True, help="Kaggle username slug")
    parser.add_argument(
        "--kernel-slug",
        default="arc-agi-3-exp-001-direct-model-policy",
    )
    parser.add_argument("--agent", type=Path, default=DEFAULT_AGENT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.agent.is_file():
        raise SystemExit(
            f"Standalone agent not found: {args.agent}. "
            "Run scripts/build_standalone_agent.py first."
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    notebook = build_notebook(args.agent.read_text(encoding="utf-8"))
    metadata = build_metadata(
        username=args.username,
        kernel_slug=args.kernel_slug,
    )

    notebook_path = args.output_dir / "submission.ipynb"
    metadata_path = args.output_dir / "kernel-metadata.json"
    notebook_path.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
    metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"built Kaggle notebook: {notebook_path}")
    print(f"built Kaggle metadata: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
