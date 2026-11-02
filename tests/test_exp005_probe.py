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
        fake_arcengine.GameAction = types.SimpleNamespace(RESET=object())
        spec = importlib.util.spec_from_file_location("_exp005_probe_test", PROBE)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        return module, spec.loader, {"arc_agi": fake_arc_agi, "arcengine": fake_arcengine}

    def test_reset_without_reasoning_is_valid(self):
        module, loader, imports = self._load()
        with patch.dict(sys.modules, imports):
            loader.exec_module(module)
            reset = types.SimpleNamespace()
            class FakeActions:
                RESET = reset
            module.GameAction = FakeActions
            self.assertEqual(module._action_reasoning(reset), {})
            # Even if the singleton is contaminated by an earlier action,
            # a reset must never transport stale metadata to the game.
            reset.reasoning = {"stale_reasoning": True}
            self.assertEqual(module._action_reasoning(reset), {})

    def test_missing_reasoning_is_valid_but_bad_metadata_is_not(self):
        module, loader, imports = self._load()
        with patch.dict(sys.modules, imports):
            loader.exec_module(module)
            reset = types.SimpleNamespace()
            class FakeActions:
                RESET = reset
            module.GameAction = FakeActions
            other = types.SimpleNamespace()
            self.assertEqual(module._action_reasoning(other), {})
            other.reasoning = {"policy": "unit-test", "step": 2}
            copied = module._action_reasoning(other)
            self.assertEqual(copied, other.reasoning)
            self.assertIsNot(copied, other.reasoning)
            other.reasoning = "not a dictionary"
            with self.assertRaisesRegex(TypeError, "dict action reasoning"):
                module._action_reasoning(other)

    def test_partial_results_are_checkpointed_per_public_game(self):
        import json
        import tempfile

        module, loader, imports = self._load()
        with patch.dict(sys.modules, imports):
            loader.exec_module(module)
            with tempfile.TemporaryDirectory() as temp:
                path = str(Path(temp) / "probe.json")
                module._save_public_probe([{"game": "ls20", "levels_completed": 0}],
                                          complete=False, path=path)
                partial = json.loads(Path(path).read_text())
                self.assertFalse(partial["probe_complete"])
                self.assertEqual(partial["completed_games"], 1)
                self.assertEqual(partial["results"][0]["game"], "ls20")
                module._save_public_probe(
                    [{"game": "ls20", "levels_completed": 0},
                     {"game": "vc33", "levels_completed": 1}],
                    complete=True, path=path,
                )
                full = json.loads(Path(path).read_text())
                self.assertTrue(full["probe_complete"])
                self.assertEqual(full["completed_games"], 2)

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
