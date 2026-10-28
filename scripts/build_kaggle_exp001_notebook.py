#!/usr/bin/env python3
"""Generate the EXP-001 Kaggle deployment notebook and kernel metadata.

Generated files are written under dist/ and are intentionally not committed.
The notebook uses only offline Kaggle inputs during competition rerun:
- ARC-AGI-3 competition assets;
- the public ARC3 e975732 vLLM runtime image layers;
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
VLLM_RUNTIME_DATASET = "lordhansolo/vllm-main-e975732-arc3"
VLLM_RUNTIME_SLUG = "vllm-main-e975732-arc3"
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
        import tarfile
        import time
        import urllib.request
        from pathlib import Path

        TRUE_SUBMISSION = bool(os.getenv("KAGGLE_IS_COMPETITION_RERUN"))
        BOOT_MODEL = True

        if BOOT_MODEL:
            competition_root = Path(
                "/kaggle/input/competitions/{COMPETITION_SLUG}"
            )
            runtime_mounts = [
                Path("/kaggle/input/{VLLM_RUNTIME_SLUG}"),
                Path("/kaggle/input/datasets/{VLLM_RUNTIME_DATASET}"),
            ]
            runtime_candidates = [
                candidate
                for candidate in runtime_mounts
                if candidate.is_dir()
                and (candidate / "runtime-manifest.json").is_file()
                and any(candidate.glob("layer-*.tar.gz.blob"))
            ]
            if len(runtime_candidates) == 1:
                runtime_dir = runtime_candidates[0]
            elif len(runtime_candidates) > 1:
                raise RuntimeError(
                    "Ambiguous direct e975732 runtime mounts: "
                    f"{{[str(path) for path in runtime_candidates]}}"
                )
            else:
                search_roots = [
                    Path("/kaggle/input"),
                    Path("/kaggle/input/datasets"),
                ]
                discovered = sorted(
                    set(
                        manifest.parent
                        for root in search_roots
                        if root.exists()
                        for manifest in root.glob("**/runtime-manifest.json")
                        if "{VLLM_RUNTIME_SLUG}" in manifest.parts
                        and any(manifest.parent.glob("layer-*.tar.gz.blob"))
                    )
                )
                if len(discovered) != 1:
                    raise RuntimeError(
                        "Could not uniquely resolve e975732 runtime: "
                        f"{{[str(path) for path in discovered]}}"
                    )
                runtime_dir = discovered[0]

            print(f"Resolved e975732 runtime dataset: {{runtime_dir}}")
            expected_model_path = Path({MODEL_PATH!r})
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
                    raise RuntimeError(
                        "Could not resolve attached Qwen model. "
                        f"Expected {{expected_model_path}}"
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

            py312_candidates = [
                Path("/usr/bin/python3.12"),
                Path("/usr/local/bin/python3.12"),
            ]
            path_python = shutil.which("python3.12")
            if path_python:
                py312_candidates.append(Path(path_python))
            py312 = next(
                (path for path in py312_candidates if path.is_file()),
                None,
            )
            if py312 is None:
                raise RuntimeError(
                    "CPython 3.12 is required for the e975732 runtime"
                )

            python_probe = subprocess.run(
                [
                    str(py312),
                    "-c",
                    (
                        "import sys; "
                        "print('%d.%d' % sys.version_info[:2]); "
                        "assert sys.version_info[:2] == (3, 12)"
                    ),
                ],
                capture_output=True,
                text=True,
            )
            print(python_probe.stdout)
            if python_probe.returncode != 0:
                raise RuntimeError(
                    "Python 3.12 runtime probe failed: "
                    + python_probe.stderr.strip()
                )

            manifest = json.loads(
                (runtime_dir / "runtime-manifest.json").read_text(
                    encoding="utf-8"
                )
            )

            def collect_layer_names(value):
                names = []
                if isinstance(value, dict):
                    for nested in value.values():
                        names.extend(collect_layer_names(nested))
                elif isinstance(value, list):
                    for nested in value:
                        names.extend(collect_layer_names(nested))
                elif isinstance(value, str):
                    name = Path(value).name
                    if (
                        name.startswith("layer-")
                        and name.endswith(".tar.gz.blob")
                    ):
                        names.append(name)
                return names

            manifest_layers = []
            for name in collect_layer_names(manifest):
                if name not in manifest_layers:
                    manifest_layers.append(name)

            def layer_number(path):
                try:
                    return int(path.name.split("-", 2)[1])
                except (IndexError, ValueError):
                    return 10**9

            if manifest_layers:
                layer_paths = [
                    runtime_dir / name
                    for name in manifest_layers
                    if (runtime_dir / name).is_file()
                ]
            else:
                layer_paths = sorted(
                    runtime_dir.glob("layer-*.tar.gz.blob"),
                    key=layer_number,
                )

            if not layer_paths:
                raise RuntimeError("No e975732 runtime layers were found")
            if len(layer_paths) != len(
                list(runtime_dir.glob("layer-*.tar.gz.blob"))
            ):
                layer_paths = sorted(
                    runtime_dir.glob("layer-*.tar.gz.blob"),
                    key=layer_number,
                )

            print(
                "e975732 runtime layers: "
                + ", ".join(path.name for path in layer_paths)
            )

            rootfs = Path("/kaggle/temp/vllm-e975732-rootfs")
            shutil.rmtree(rootfs, ignore_errors=True)
            rootfs.mkdir(parents=True, exist_ok=True)

            def remove_path(path):
                if path.is_symlink() or path.is_file():
                    path.unlink(missing_ok=True)
                elif path.is_dir():
                    shutil.rmtree(path)

            for layer_path in layer_paths:
                print(f"Extracting runtime layer: {{layer_path.name}}")
                with tarfile.open(layer_path, mode="r:gz") as archive:
                    members = archive.getmembers()
                    for member in members:
                        member_path = Path(member.name)
                        if not member_path.parts:
                            continue
                        name = member_path.name
                        if not name.startswith(".wh."):
                            continue
                        parent = rootfs.joinpath(*member_path.parts[:-1])
                        if name == ".wh..wh..opq":
                            if parent.is_dir():
                                for child in list(parent.iterdir()):
                                    remove_path(child)
                        else:
                            remove_path(parent / name[4:])

                    regular_members = [
                        member
                        for member in members
                        if not Path(member.name).name.startswith(".wh.")
                    ]
                    archive.extractall(
                        rootfs,
                        members=regular_members,
                        filter="data",
                    )

            python_paths = []
            for pattern in (
                "**/python3.12/site-packages",
                "**/python3.12/dist-packages",
            ):
                for path in rootfs.glob(pattern):
                    if path.is_dir() and path not in python_paths:
                        python_paths.append(path)

            vllm_paths = [
                path
                for path in python_paths
                if (path / "vllm" / "__init__.py").is_file()
            ]
            if len(vllm_paths) != 1:
                raise RuntimeError(
                    "Could not uniquely resolve vLLM site-packages: "
                    f"{{[str(path) for path in vllm_paths]}}"
                )
            vllm_site_packages = vllm_paths[0]
            print(f"e975732 vLLM site-packages: {{vllm_site_packages}}")

            server_env = os.environ.copy()
            existing_pythonpath = server_env.get("PYTHONPATH", "")
            server_env["PYTHONPATH"] = os.pathsep.join(
                [str(path) for path in python_paths]
                + ([existing_pythonpath] if existing_pythonpath else [])
            )

            library_paths = [
                rootfs / "usr/local/cuda/lib64",
                rootfs / "usr/local/lib",
                rootfs / "usr/local/nvidia/lib64",
                rootfs / "usr/lib/x86_64-linux-gnu",
                Path("/usr/local/nvidia/lib64"),
            ]
            existing_ld = server_env.get("LD_LIBRARY_PATH", "")
            server_env["LD_LIBRARY_PATH"] = os.pathsep.join(
                [str(path) for path in library_paths if path.is_dir()]
                + ([existing_ld] if existing_ld else [])
            )
            server_env["LIBRARY_PATH"] = os.pathsep.join(
                [
                    "/usr/local/nvidia/lib64",
                    server_env.get("LIBRARY_PATH", ""),
                ]
            ).strip(os.pathsep)
            server_env["USE_TF"] = "0"
            server_env["TRANSFORMERS_NO_TF"] = "1"
            server_env["TRANSFORMERS_NO_TORCHVISION"] = "1"
            server_env["VLLM_NO_USAGE_STATS"] = "1"
            server_env["HF_HUB_OFFLINE"] = "1"
            server_env["TRANSFORMERS_OFFLINE"] = "1"
            server_env["VLLM_LOGGING_LEVEL"] = "DEBUG"

            cuda_probe = subprocess.run(
                [
                    str(py312),
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
                    "e975732 CUDA preflight failed. stdout="
                    + cuda_probe.stdout.strip()
                    + " stderr="
                    + cuda_probe.stderr.strip()
                )

            log_path = Path("/kaggle/working/vllm-openai-server.log")
            log_handle = log_path.open("w")
            server = subprocess.Popen(
                [
                    str(py312),
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
                    "--load-format",
                    "safetensors",
                ],
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                env=server_env,
            )

            health_url = "http://127.0.0.1:8000/v1/models"
            deadline = time.time() + 1200
            last_error = None
            while time.time() < deadline:
                if server.poll() is not None:
                    raise RuntimeError(
                        f"vLLM exited early with code {{server.returncode}}; "
                        f"see {{log_path}}"
                    )
                try:
                    with urllib.request.urlopen(
                        health_url,
                        timeout=5,
                    ) as response:
                        if response.status == 200:
                            break
                except Exception as exc:
                    last_error = exc
                time.sleep(5)
            else:
                server.terminate()
                raise RuntimeError(
                    "vLLM did not become healthy before timeout: "
                    f"{{last_error}}"
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
        "dataset_sources": [VLLM_RUNTIME_DATASET],
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
