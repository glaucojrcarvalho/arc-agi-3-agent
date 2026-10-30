"""Build EXP-002 Kaggle notebook using EXP-001's validated vLLM bootstrap."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import build_kaggle_exp001_notebook as base

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AGENT = ROOT / "dist" / "exp002_agent.py"
DEFAULT_OUTPUT = ROOT / "dist" / "kaggle-exp002"
DEFAULT_SLUG = "arc-agi-3-exp-002-transition-aware-policy"
# Verified Python 3.12-compatible image from EXP-001 v15; default image moved to 3.13.
PY312_DOCKER_IMAGE = "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"


def build_artifacts(*, agent_source: str, username: str, kernel_slug: str) -> tuple[dict, dict]:
    notebook = base.build_notebook(agent_source)
    notebook["cells"][0]["source"] = (
        "# ARC-AGI-3 EXP-002 — Transition-Aware Policy\n\n"
        "Qwen3.8-27B FP8 plus bounded transition memory and verified no-op handling."
    )
    notebook["cells"][1]["source"] = notebook["cells"][1]["source"].replace(
        "EXP-001 model validation", "EXP-002 model validation"
    )
    notebook["cells"][1]["source"] = notebook["cells"][1]["source"].replace(
        "if BOOT_MODEL:", "print(\"EXP-002 Python runtime:\", sys.version, flush=True)\nif BOOT_MODEL:", 1
    )
    # After real model inference succeeds and before stopping vLLM, play a
    # bounded subset of PUBLIC games with the real EXP-002 agent.
    # This never runs in the hidden competition rerun.
    probe_source = (ROOT / "scripts" / "kaggle_exp002_public_probe.py").read_text(
        encoding="utf-8"
    )
    marker = '        print("EXP-002 model validation inference succeeded")\n        server.terminate()'
    setup_source = notebook["cells"][1]["source"]
    if setup_source.count(marker) != 1:
        raise ValueError("EXP-001 bootstrap changed: probe insertion point missing")
    probe_call = (
        "        _exp002_probe_source = " + repr(probe_source) + "\n"
        "        exec(compile(_exp002_probe_source, 'exp002_public_probe.py', 'exec'), globals(), globals())\n"
        "        run_public_probe(" + repr(agent_source) + ", str(competition_root / 'environment_files'))\n"
    )
    notebook["cells"][1]["source"] = setup_source.replace(
        marker, '        print("EXP-002 model validation inference succeeded")\n' + probe_call + '        server.terminate()'
    )
    metadata = base.build_metadata(username=username, kernel_slug=kernel_slug)
    metadata["title"] = "ARC-AGI-3 EXP-002 Transition-Aware Policy"
    metadata["docker_image"] = PY312_DOCKER_IMAGE
    return notebook, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument("--kernel-slug", default=DEFAULT_SLUG)
    parser.add_argument("--agent", type=Path, default=DEFAULT_AGENT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if not args.agent.is_file():
        raise SystemExit(f"Build the standalone agent first: {args.agent}")
    notebook, metadata = build_artifacts(
        agent_source=args.agent.read_text(encoding="utf-8"),
        username=args.username,
        kernel_slug=args.kernel_slug,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "submission.ipynb").write_text(
        json.dumps(notebook, indent=1), encoding="utf-8"
    )
    (args.output_dir / "kernel-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(f"EXP-002 notebook: {args.output_dir / 'submission.ipynb'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
