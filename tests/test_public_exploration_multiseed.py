"""Public-only evaluation seed control and accurate move count."""
from __future__ import annotations

import importlib.util
from enum import Enum
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_public_exploration.py"


class PublicEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        arc_agi=types.ModuleType("arc_agi")
        arc_agi.Arcade=object
        arc_agi.OperationMode=object
        engine=types.ModuleType("arcengine")
        engine.GameAction=object
        class FakeGameState(Enum):
            WIN = 1
            NOT_PLAYED = 2
            GAME_OVER = 3
        win = FakeGameState.WIN
        engine.GameState = FakeGameState
        cls.modules=patch.dict(sys.modules,{"arc_agi":arc_agi,"arcengine":engine})
        cls.modules.start()
        spec=importlib.util.spec_from_file_location("_arc_public_eval_test",SRC)
        cls.module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.win=win

    @classmethod
    def tearDownClass(cls):
        cls.modules.stop()

    def test_policy_seed_is_reproducible_and_independent(self):
        a=self.module.Policy("public","random",seed=0).rng
        b=self.module.Policy("public","random",seed=0).rng
        c=self.module.Policy("public","random",seed=1).rng
        self.assertEqual([a.randrange(1000000) for _ in range(10)],
                         [b.randrange(1000000) for _ in range(10)])
        self.assertNotEqual([a.randrange(1000000) for _ in range(10)],
                            [c.randrange(1000000) for _ in range(10)])

    def test_already_won_game_counts_zero_actions_and_preserves_seed(self):
        class Env:
            def reset(_): return types.SimpleNamespace(state=self.win,levels_completed=0)
        class Arc:
            def make(_,game,seed,save_recording):
                self.assertEqual(seed,7)
                return Env()
        row=self.module.run_game(Arc(),"pub0","novelty",80,seed=7)
        self.assertEqual(row["actions"],0)
        self.assertEqual(row["seed"],7)

    def test_first_action_win_counts_exactly_one_action(self):
        class Action:
            def __init__(self): self.action_data=types.SimpleNamespace(model_dump=lambda:{})
            def set_data(self,data): pass
        class Policy:
            def __init__(self,*args,**kwargs):
                self.effects=0
                self.detected_noops=0
            def choose(self,raw): return Action(),{}
        class Array:
            def tolist(self): return [[1]]
        class Env:
            def reset(_): return types.SimpleNamespace(state="ONGOING",levels_completed=0)
            def step(_,action,data):
                return types.SimpleNamespace(state=self.win,levels_completed=1,frame=[Array()])
        class Arc:
            def make(_,game,seed,save_recording): return Env()
        with patch.object(self.module,"Policy",Policy):
            row=self.module.run_game(Arc(),"pub0","random",80,seed=5)
        self.assertEqual(row["actions"],1)
        self.assertEqual(row["levels"],1)


if __name__=="__main__":
    unittest.main()
