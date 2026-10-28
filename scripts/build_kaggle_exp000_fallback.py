#!/usr/bin/env python3
"""Generate a deadline-safe Kaggle notebook for the EXP-000 fallback baseline.

The generated notebook intentionally avoids model serving, GPU dependencies,
network APIs, and non-competition datasets. Its purpose is to preserve a
minimal valid submission path while EXP-001 remains experimental.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AGENT = ROOT / "dist" / "my_agent.py"
DEFAULT_OUTPUT_DIR = ROOT / "dist" / "kaggle-exp000-fallback"

COMPETITION_SLUG = "arc-prize-2026-arc-agi-3"


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
    setup_source = dedent(
        f"""\
        import os
        import subprocess
        import sys
        from pathlib import Path

        TRUE_SUBMISSION = bool(os.getenv("KAGGLE_IS_COMPETITION_RERUN"))
        competition_root = Path(
            "/kaggle/input/competitions/{COMPETITION_SLUG}"
        )
        wheel_dir = competition_root / "arc_agi_3_wheels"

        if not competition_root.exists():
            raise RuntimeError(
                f"Missing competition input: {{competition_root}}"
            )
        if not wheel_dir.exists():
            raise RuntimeError(
                f"Missing ARC wheel directory: {{wheel_dir}}"
            )

        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-index",
                "--find-links",
                str(wheel_dir),
                "arc-agi",
                "python-dotenv",
            ],
            check=True,
        )
        print("EXP-000 fallback ARC runtime installed")
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
        else:
            print("EXP-000 fallback save-and-run validation succeeded")
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
                "accelerator": "none",
                "isInternetEnabled": False,
                "isGpuEnabled": False,
                "language": "python",
                "sourceType": "notebook",
            },
        },
        "nbformat_minor": 4,
        "nbformat": 4,
        "cells": [
            markdown_cell(
                "# ARC-AGI-3 EXP-000 Deadline Fallback\n\n"
                "Minimal reproducible random-policy submission path."
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
        "title": "ARC-AGI-3 EXP-000 Deadline Fallback",
        "code_file": "submission.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": False,
        "enable_tpu": False,
        "enable_internet": False,
        "keywords": [],
        "dataset_sources": [],
        "kernel_sources": [],
        "competition_sources": [COMPETITION_SLUG],
        "model_sources": [],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument(
        "--kernel-slug",
        default="arc-agi-3-exp-000-deadline-fallback",
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

    print(f"built fallback notebook: {notebook_path}")
    print(f"built fallback metadata: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
