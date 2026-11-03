#!/usr/bin/env python3
"""Read-only inventory of remote Git branch reachability.

A reachable branch is a candidate for *human* retention review, not an
automatic deletion recommendation. No refs, worktrees or remotes are mutated.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def _git(repo: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode:
        raise RuntimeError(
            f"git {args[0]} failed (exit={process.returncode}): "
            f"{process.stderr.strip()}"
        )
    return process.stdout.strip()


def snapshot(repo: Path, remote: str = "origin", main: str = "main") -> dict:
    """Return a point-in-time, read-only audit of locally fetched refs."""
    root = Path(_git(repo, "rev-parse", "--show-toplevel"))
    main_ref = f"refs/remotes/{remote}/{main}"
    main_sha = _git(root, "rev-parse", "--verify", f"{main_ref}^{{commit}}")
    ref_lines = _git(
        root,
        "for-each-ref",
        "--format=%(refname:short)%09%(objectname)",
        f"refs/remotes/{remote}/",
    )
    branches = []
    for line in ref_lines.splitlines():
        if not line.strip():
            continue
        name, sha = line.split("\t", 1)
        if name in (f"{remote}/{main}", f"{remote}/HEAD"):
            continue
        ancestry = subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", sha, main_sha],
            capture_output=True,
            check=False,
        )
        if ancestry.returncode not in (0, 1):
            raise RuntimeError(f"git merge-base failed for {name}")
        merged = ancestry.returncode == 0
        unique = 0 if merged else int(
            _git(root, "rev-list", "--count", f"{main_sha}..{sha}")
        )
        branches.append({
            "branch": name,
            "head_sha": sha,
            "reachable_from_main": merged,
            "unique_commits": unique,
            "decision": "REVIEW_RETENTION" if merged else "PRESERVE_UNMERGED",
        })
    branches.sort(key=lambda row: row["branch"])
    return {
        "remote": remote,
        "main_ref": main_ref,
        "main_sha": main_sha,
        "branch_count": len(branches),
        "reachable_count": sum(row["reachable_from_main"] for row in branches),
        "unmerged_count": sum(not row["reachable_from_main"] for row in branches),
        "branches": branches,
        "warning": (
            "Local tracking refs may be stale: fetch first. Reachability alone "
            "never authorizes deletion; review PRs, docs and scientific evidence."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--main", default="main")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = snapshot(args.repo, args.remote, args.main)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            f"{report['main_ref']} @ {report['main_sha']} | "
            f"{report['reachable_count']} reachable, "
            f"{report['unmerged_count']} unmerged"
        )
        for row in report["branches"]:
            print(
                f"{row['decision']:20} {row['branch']:58} "
                f"{row['unique_commits']:>3} unique {row['head_sha']}"
            )
        print(report["warning"])


if __name__ == "__main__":
    main()
