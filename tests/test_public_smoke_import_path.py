"""Regression: public-game smoke can import local code without PYTHONPATH.

Only SDK imports are stubbed; importing the local arc_agent package is real.
No game downloads, model credentials or network access are needed.
"""

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


class SmokePublicImportPathTest(unittest.TestCase):
    def test_direct_script_bootstraps_local_src_in_isolated_interpreter(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "smoke_public_games.py"
        # -I ignores PYTHONPATH and cwd. Mock only the external game SDK.
        snippet = textwrap.dedent("""
            import runpy
            import sys
            import types

            arc_agi = types.ModuleType("arc_agi")
            arc_agi.Arcade = object
            arc_agi.OperationMode = object
            sys.modules["arc_agi"] = arc_agi

            arcengine = types.ModuleType("arcengine")
            arcengine.FrameData = object
            arcengine.GameState = object
            sys.modules["arcengine"] = arcengine

            runpy.run_path(sys.argv[1], run_name="public_smoke_import_only")
            from arc_agent import actions
            assert actions is not None
            print("local import OK")
        """)
        with tempfile.TemporaryDirectory() as external_cwd:
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            completed = subprocess.run(
                [sys.executable, "-I", "-c", snippet, str(script)],
                cwd=external_cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("local import OK", completed.stdout)


if __name__ == "__main__":
    unittest.main()
