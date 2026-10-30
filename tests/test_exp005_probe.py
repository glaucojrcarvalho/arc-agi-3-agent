"""The Kaggle smoke harness must emulate the real Agent constructor."""
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


PROBE = Path(__file__).resolve().parents[1] / "scripts" / "kaggle_exp005_public_probe.py"


class EXP005ProbeTests(unittest.TestCase):
    def _load(self):
        fake_arc_agi = types.ModuleType("arc_agi")
        fake_arc_agi.Arcade = object
        fake_arc_agi.OperationMode = object
        fake_arcengine = types.ModuleType("arcengine")
        fake_arcengine.FrameData = object
        spec = importlib.util.spec_from_file_location("_exp005_probe_test", PROBE)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        return module, spec.loader, {"arc_agi": fake_arc_agi, "arcengine": fake_arcengine}

    def test_keyword_game_id_survives_base_constructor(self):
        module, loader, imports = self._load()
        with patch.dict(sys.modules, imports):
            loader.exec_module(module)
            cls = module.load_probe_agent(
                "from agents.agent import Agent\n"
                "class MyAgent(Agent):\n"
                "    def __init__(self, *args, **kwargs):\n"
                "        super().__init__(*args, **kwargs)\n"
                "        self.novelty_seed_key = self.game_id\n"
            )
            agent = cls(game_id="public-fixture")
            self.assertEqual(agent.game_id, "public-fixture")
            self.assertEqual(agent.novelty_seed_key, "public-fixture")

    def test_positional_game_id_and_missing_id(self):
        module, loader, imports = self._load()
        with patch.dict(sys.modules, imports):
            loader.exec_module(module)
            cls = module.load_probe_agent(
                "from agents.agent import Agent\nclass MyAgent(Agent):\n    pass\n"
            )
            self.assertEqual(cls("public-fixture").game_id, "public-fixture")
            with self.assertRaisesRegex(ValueError, "game_id"):
                cls()


if __name__ == "__main__":
    unittest.main()
