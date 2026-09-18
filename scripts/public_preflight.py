#!/usr/bin/env python3
"""Lightweight public-repository safety scanner.

By default the script scans staged changes. Use ``--all`` to scan every tracked
file, which is useful in CI. This is a guardrail, not a replacement for a
dedicated secret-scanning product or manual diff review.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

FORBIDDEN_PATH_PREFIXES = (
    ".kaggle/",
    "data/",
    "environment_files/",
    "recordings/",
    "reference/",
    "vendor/",
    "outputs/",
    "artifacts/",
    "checkpoints/",
    "models/",
    "logs/",
)

FORBIDDEN_FILENAMES = {
    ".env",
    "credentials.json",
    "kaggle.json",
    "submission.json",
    "submission.csv",
    "submission.parquet",
}

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("OpenAI-style API key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
    ("Kaggle access token", re.compile(r"\bKGAT_[A-Za-z0-9_-]{20,}\b")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
)


def run_git(*args: str, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], check=False, capture_output=True, text=text)


def staged_paths() -> list[str]:
    result = run_git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Unable to inspect staged files")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def tracked_paths() -> list[str]:
    result = run_git("ls-files")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Unable to inspect tracked files")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def staged_bytes(path: str) -> bytes | None:
    result = run_git("show", f":{path}", text=False)
    return result.stdout if result.returncode == 0 else None


def tracked_bytes(path: str) -> bytes | None:
    try:
        return Path(path).read_bytes()
    except OSError:
        return None


def path_violations(path: str) -> list[str]:
    normalized = PurePosixPath(path).as_posix()
    name = PurePosixPath(normalized).name
    problems: list[str] = []

    if normalized.startswith(FORBIDDEN_PATH_PREFIXES):
        problems.append("local/generated artifact path")
    if name in FORBIDDEN_FILENAMES:
        problems.append("forbidden local/credential filename")
    if name.startswith(".env.") and name != ".env.example":
        problems.append("environment file")
    if normalized == "notebooks/submission.ipynb":
        problems.append("generated submission notebook")
    if name.endswith((".pem", ".key")):
        problems.append("key material filename")

    return problems


def content_violations(data: bytes) -> list[str]:
    if b"\x00" in data:
        return []
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return []
    return [label for label, pattern in SECRET_PATTERNS if pattern.search(text)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="scan every tracked file instead of only staged changes")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        paths = tracked_paths() if args.all else staged_paths()
    except RuntimeError as exc:
        print(f"preflight error: {exc}", file=sys.stderr)
        return 2

    mode = "tracked" if args.all else "staged"
    if not paths:
        print(f"public-preflight: no {mode} files")
        return 0

    failures: list[tuple[str, str]] = []
    for path in paths:
        for problem in path_violations(path):
            failures.append((path, problem))
        data = tracked_bytes(path) if args.all else staged_bytes(path)
        if data is None:
            failures.append((path, "could not inspect content"))
            continue
        for problem in content_violations(data):
            failures.append((path, problem))

    if failures:
        print("public-preflight: BLOCKED")
        for path, problem in failures:
            print(f"  - {path}: {problem}")
        print("Review the repository contents before publishing changes.")
        return 1

    print(f"public-preflight: clean ({len(paths)} {mode} file(s) checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
