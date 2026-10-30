"""EXP-002 integration tests against the same ARC-like contract as EXP-001."""
from __future__ import annotations

import importlib
import json
import sys
import types
import unittest
from unittest.mock import patch

from test_agent_contract import FakeAgent, FakeFrameData, FakeGameAction, FakeGameState, FakeModel


class Exp002AgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        arcengine = types.ModuleType("arcengine")
        arcengine.FrameData = FakeFrameData
        arcengine.GameAction = FakeGameAction
        arcengine.GameState = FakeGameState
        agents = types.ModuleType("agents")
        agent_mod = types.ModuleType("agents.agent")
        agent_mod.Agent = FakeAgent
        agents.agent = agent_mod
        cls._patch = patch.dict(sys.modules, {
            "arcengine": arcengine, "agents": agents, "agents.agent": agent_mod
        })
        cls._patch.start()
        sys.modules.pop("agent.exp002_agent", None)
        cls.agent_module = importlib.import_module("agent.exp002_agent")

    @classmethod
    def tearDownClass(cls) -> None:
        sys.modules.pop("agent.exp002_agent", None)
        cls._patch.stop()

    def make_agent(self, response: str = '{"action":1,"data":{},"reason":"move"}'):
        agent = self.agent_module.MyAgent(game_id="smoke")
        model = FakeModel(response)
        agent._model = model
        return agent, model

    def test_stuck_action_is_redirected_without_another_model_call(self) -> None:
        agent, model = self.make_agent()
        frame = FakeFrameData(frame=[[[1, 1]]], available_actions=[1, 2])
        self.assertIs(agent.choose_action([], frame), FakeGameAction.ACTION1)
        action = agent.choose_action([], frame)
        self.assertIs(action, FakeGameAction.ACTION2)
        self.assertTrue(action.reasoning["redirected"])
        self.assertEqual(action.reasoning["proven_noops"], 1)
        self.assertEqual(agent.model_calls, 2)
        feedback = json.loads(model.prompts[-1])
        self.assertTrue(feedback["recent_transitions"][-1]["proven_noop"])
        self.assertEqual(feedback["proven_noop_actions_here"], [{"action": 1, "data": {}}])

    def test_effectful_action_is_not_blocked(self) -> None:
        agent, model = self.make_agent()
        first = FakeFrameData(frame=[[[1, 0]]], available_actions=[1, 2])
        second = FakeFrameData(frame=[[[1, 1]]], available_actions=[1, 2])
        self.assertIs(agent.choose_action([], first), FakeGameAction.ACTION1)
        next_action = agent.choose_action([], second)
        self.assertIs(next_action, FakeGameAction.ACTION1)
        self.assertFalse(next_action.reasoning["redirected"])
        self.assertEqual(next_action.reasoning["proven_noops"], 0)

    def test_invalid_actions_do_not_repeat_first_fallback(self) -> None:
        agent, model = self.make_agent("not-json")
        frame = FakeFrameData(frame=[[[1]]], available_actions=[1, 2])
        self.assertIs(agent.choose_action([], frame), FakeGameAction.ACTION1)
        self.assertIs(agent.choose_action([], frame), FakeGameAction.ACTION2)
        self.assertEqual(agent.validation_fallbacks, 2)

    def test_game_over_resets_without_model_call(self) -> None:
        agent, model = self.make_agent()
        frame = FakeFrameData(state=FakeGameState.GAME_OVER)
        self.assertIs(agent.choose_action([], frame), FakeGameAction.RESET)
        self.assertEqual(agent.model_calls, 0)


if __name__ == "__main__":
    unittest.main()
