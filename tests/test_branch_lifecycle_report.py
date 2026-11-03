"""Local-only contract tests for read-only remote branch inventory."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.report_branch_lifecycle import snapshot


class BranchLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Local Test")
        self.git("commit", "--allow-empty", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/remotes/origin/merged-history", self.base)
        self.git("commit", "--allow-empty", "-qm", "next")
        self.main_sha = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/remotes/origin/main", self.main_sha)
        self.git("checkout", "-q", "-b", "isolated", self.base)
        self.git("commit", "--allow-empty", "-qm", "independent")
        self.unique_sha = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/remotes/origin/experiment", self.unique_sha)
        self.git("checkout", "-q", "main")

    def git(self, *args):
        p = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            text=True, capture_output=True, check=True,
        )
        return p.stdout.strip()

    def test_reachability_and_unique_commit_count(self):
        report = snapshot(self.repo)
        self.assertEqual(report["main_sha"], self.main_sha)
        self.assertEqual((report["branch_count"], report["reachable_count"],
                          report["unmerged_count"]), (2, 1, 1))
        rows = {r["branch"]: r for r in report["branches"]}
        self.assertEqual(rows["origin/merged-history"]["decision"], "REVIEW_RETENTION")
        self.assertEqual(rows["origin/merged-history"]["unique_commits"], 0)
        self.assertTrue(rows["origin/merged-history"]["reachable_from_main"])
        self.assertEqual(rows["origin/experiment"]["decision"], "PRESERVE_UNMERGED")
        self.assertEqual(rows["origin/experiment"]["unique_commits"], 1)
        self.assertFalse(rows["origin/experiment"]["reachable_from_main"])

    def test_does_not_mutate_refs_or_worktree(self):
        before_refs = self.git("show-ref")
        before_status = self.git("status", "--porcelain")
        snapshot(self.repo)
        self.assertEqual(self.git("show-ref"), before_refs)
        self.assertEqual(self.git("status", "--porcelain"), before_status)

    def test_missing_main_ref_is_an_explicit_error(self):
        with self.assertRaisesRegex(RuntimeError, "rev-parse failed"):
            snapshot(self.repo, main="does-not-exist")

    def test_cli_json_is_machine_readable(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "report_branch_lifecycle.py"
        p = subprocess.run(
            [sys.executable, str(script), "--repo", str(self.repo), "--json"],
            text=True, capture_output=True, check=True,
        )
        report = json.loads(p.stdout)
        self.assertEqual(report["main_sha"], self.main_sha)
        self.assertEqual(report["unmerged_count"], 1)
        self.assertIn("never authorizes deletion", report["warning"])


if __name__ == "__main__":
    unittest.main()
