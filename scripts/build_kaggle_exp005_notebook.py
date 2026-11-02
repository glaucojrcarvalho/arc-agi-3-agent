"""Build EXP-005 Kaggle notebook using EXP-001's validated vLLM bootstrap."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import build_kaggle_exp001_notebook as base

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AGENT = ROOT / "dist" / "exp005_agent.py"
DEFAULT_OUTPUT = ROOT / "dist" / "kaggle-exp005"
DEFAULT_SLUG = "arc-agi-3-exp-005-persistent-reasoning-policy"
# Verified Python 3.12-compatible image from EXP-001 v15; default image moved to 3.13.
PY312_DOCKER_IMAGE = "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"


def build_artifacts(
    *, agent_source: str, username: str, kernel_slug: str,
    experiment_label: str = "EXP-005",
) -> tuple[dict, dict]:
    if re.fullmatch(r"EXP-[0-9]{3}", experiment_label) is None:
        raise ValueError("experiment label must be EXP-NNN")
    notebook = base.build_notebook(agent_source)
    notebook["cells"][0]["source"] = (
        f"# ARC-AGI-3 {experiment_label} — Persistent Reasoning Policy\n\n"
        "Qwen3.8-27B FP8 with persistent hypotheses, short validated plans, and novelty fallback."
    )
    notebook["cells"][1]["source"] = notebook["cells"][1]["source"].replace(
        "EXP-001 model validation", "EXP-005 model validation"
    )
    notebook["cells"][1]["source"] = notebook["cells"][1]["source"].replace(
        "if BOOT_MODEL:", "print(\"EXP-005 Python runtime:\", sys.version, flush=True)\nif BOOT_MODEL:", 1
    )
    # EXP-005 opt-in planning mode. Previous notebooks and direct-policy
    # baselines keep their original 128-token schema and behavior.
    setup = notebook["cells"][1]["source"]
    if setup.count("if BOOT_MODEL:") != 1:
        raise ValueError("EXP-001 bootstrap changed: model section missing")
    notebook["cells"][1]["source"] = setup.replace(
        "if BOOT_MODEL:",
        'os.environ["ARC_MODEL_PLANNING_ENABLED"] = "1"\n'
        'os.environ["ARC_MODEL_MAX_TOKENS"] = "320"\n'
        'if BOOT_MODEL:',
        1,
    )
    # After real model inference succeeds and before stopping vLLM, play a
    # bounded subset of PUBLIC games with the real EXP-005 agent.
    # This never runs in the hidden competition rerun.
    probe_source = (ROOT / "scripts" / "kaggle_exp005_public_probe.py").read_text(
        encoding="utf-8"
    )
    marker = '        print("EXP-005 model validation inference succeeded")\n        server.terminate()'
    setup_source = notebook["cells"][1]["source"]
    if setup_source.count(marker) != 1:
        raise ValueError("EXP-001 bootstrap changed: probe insertion point missing")
    probe_call = (
        "        _exp005_probe_source = " + repr(probe_source) + "\n"
        "        exec(compile(_exp005_probe_source, 'exp005_public_probe.py', 'exec'), globals(), globals())\n"
        "        run_public_probe(" + repr(agent_source) + ", str(competition_root / 'environment_files'))\n"
    )
    notebook["cells"][1]["source"] = setup_source.replace(
        marker, '        print("EXP-005 model validation inference succeeded")\n' + probe_call + '        server.terminate()'
    )
    metadata = base.build_metadata(username=username, kernel_slug=kernel_slug)
    metadata["title"] = f"ARC-AGI-3 {experiment_label} Persistent Reasoning Policy"
    # Kaggle derives the notebook URL slug from the title. Reject a mismatched
    # metadata id before pushing, rather than creating a surprise kernel.
    expected_slug = re.sub(r"[^a-z0-9]+", "-", metadata["title"].lower()).strip("-")
    if kernel_slug != expected_slug:
        raise ValueError(
            f"kernel_slug must equal the title-derived slug: {expected_slug}"
        )
    metadata["docker_image"] = PY312_DOCKER_IMAGE
    return notebook, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument("--kernel-slug", default=DEFAULT_SLUG)
    parser.add_argument("--experiment-label", default="EXP-005")
    parser.add_argument("--agent", type=Path, default=DEFAULT_AGENT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if not args.agent.is_file():
        raise SystemExit(f"Build the standalone agent first: {args.agent}")
    notebook, metadata = build_artifacts(
        agent_source=args.agent.read_text(encoding="utf-8"),
        username=args.username,
        kernel_slug=args.kernel_slug,
        experiment_label=args.experiment_label,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "submission.ipynb").write_text(
        json.dumps(notebook, indent=1), encoding="utf-8"
    )
    (args.output_dir / "kernel-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(f"EXP-005 notebook: {args.output_dir / 'submission.ipynb'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
