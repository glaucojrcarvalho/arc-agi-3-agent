from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "capture_environment.py"

spec = importlib.util.spec_from_file_location("capture_environment", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
capture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture_module)


class CaptureEnvironmentTests(unittest.TestCase):
    def test_runtime_metadata_uses_requested_interpreter(self) -> None:
        metadata = capture_module.runtime_metadata(Path(sys.executable))

        self.assertEqual(metadata["python_version"], sys.version.split()[0])
        self.assertIn("arc_agi_version", metadata)

    def test_missing_runtime_returns_incomplete_metadata(self) -> None:
        metadata = capture_module.runtime_metadata(None)

        self.assertIsNone(metadata["python_version"])
        self.assertIsNone(metadata["arc_agi_version"])

    def test_file_sha256_hashes_exact_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "agent.py"
            path.write_bytes(b"abc")

            self.assertEqual(
                capture_module.file_sha256(path),
                hashlib.sha256(b"abc").hexdigest(),
            )

    def test_missing_artifact_has_no_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.py"
            self.assertIsNone(capture_module.file_sha256(path))


if __name__ == "__main__":
    unittest.main()
