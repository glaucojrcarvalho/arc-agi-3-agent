#!/usr/bin/env python3
"""Capture reproducibility metadata for an ARC-AGI-3 experiment.

The script reports only public-safe revision/version identifiers and hashes.
It intentionally omits local filesystem paths, usernames, credentials, and
other machine-specific information.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STARTER = ROOT.parent / "ARC-AGI-3-Kaggle-Starter"
DEFAULT_AGENT = ROOT / "dist" / "my_agent.py"


def git_revision(path: Path) -> str | None:
    if not path.exists():
        return None
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    revision = result.stdout.strip()
    return revision or None


def git_is_dirty(path: Path) -> bool | None:
    if not path.exists():
        return None
    result = subprocess.run(
        ["git", "-C", str(path), "status", "--porcelain"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return bool(result.stdout.strip())


def starter_python(starter: Path) -> Path | None:
    candidates = (
        starter / ".venv" / "bin" / "python",
        starter / ".venv" / "Scripts" / "python.exe",
    )
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def runtime_metadata(python: Path | None) -> dict[str, str | None]:
    if python is None:
        return {"arc_agi_version": None, "python_version": None}

    probe = """
import importlib.metadata
import json
import sys

try:
    arc_agi_version = importlib.metadata.version("arc-agi")
except importlib.metadata.PackageNotFoundError:
    arc_agi_version = None

print(json.dumps({
    "arc_agi_version": arc_agi_version,
    "python_version": sys.version.split()[0],
}))
"""
    result = subprocess.run(
        [str(python), "-c", probe],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {"arc_agi_version": None, "python_version": None}

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"arc_agi_version": None, "python_version": None}

    return {
        "arc_agi_version": payload.get("arc_agi_version"),
        "python_version": payload.get("python_version"),
    }


def file_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect(starter: Path, agent: Path) -> dict[str, str | bool | None]:
    framework = starter / "vendor" / "ARC-AGI-3-Agents"
    runtime = runtime_metadata(starter_python(starter))
    return {
        "revision": git_revision(ROOT),
        "project_dirty": git_is_dirty(ROOT),
        "starter_revision": git_revision(starter),
        "framework_revision": git_revision(framework),
        "arc_agi_version": runtime["arc_agi_version"],
        "python_version": runtime["python_version"],
        "agent_sha256": file_sha256(agent),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--starter",
        type=Path,
        default=DEFAULT_STARTER,
        help="path to the local ARC-AGI-3-Kaggle-Starter checkout",
    )
    parser.add_argument(
        "--agent",
        type=Path,
        default=DEFAULT_AGENT,
        help="standalone agent artifact that will actually be evaluated",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metadata = collect(args.starter, args.agent)
    print(json.dumps(metadata, indent=2, sort_keys=True))

    required = (
        "revision",
        "starter_revision",
        "framework_revision",
        "arc_agi_version",
        "python_version",
        "agent_sha256",
    )
    missing = [key for key in required if metadata.get(key) in (None, "")]
    if missing:
        print(
            "capture_environment: incomplete provenance: " + ", ".join(missing),
            file=__import__("sys").stderr,
        )
        return 2

    if metadata["project_dirty"]:
        print(
            "capture_environment: warning: project working tree has uncommitted changes",
            file=__import__("sys").stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
