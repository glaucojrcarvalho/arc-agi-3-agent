"""EXP-005 model-independent tests for per-game plans and novelty fallback."""
from __future__ import annotations

import importlib
import json
import sys
import types
import unittest
from unittest.mock import patch

from test_agent_contract import (
    FakeAgent, FakeFrameData, FakeGameAction, FakeGameState, FakeModel
)


class Exp005AgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        arcengine=types.ModuleType("arcengine")
        arcengine.FrameData=FakeFrameData
        arcengine.GameAction=FakeGameAction
        arcengine.GameState=FakeGameState
        agents=types.ModuleType("agents")
        agent_mod=types.ModuleType("agents.agent")
        agent_mod.Agent=FakeAgent
        agents.agent=agent_mod
        cls._patch=patch.dict(sys.modules, {
            "arcengine":arcengine,"agents":agents,"agents.agent":agent_mod
        })
        cls._patch.start()
        sys.modules.pop("agent.exp005_agent",None)
        cls.module=importlib.import_module("agent.exp005_agent")

    @classmethod
    def tearDownClass(cls):
        sys.modules.pop("agent.exp005_agent",None)
        cls._patch.stop()

    def agent(self, response):
        agent=self.module.MyAgent(game_id="public-test")
        model=FakeModel(response)
        agent._model=model
        return agent,model

    def test_keeps_goal_and_hypothesis_in_next_turn(self):
        agent,model=self.agent(json.dumps({
            "action":1,"data":{},"reason":"test a move",
            "goal":"reach the exit", "hypothesis":"1 moves right"
        }))
        first=FakeFrameData(frame=[[[1]]],available_actions=[1,2])
        second=FakeFrameData(frame=[[[2]]],available_actions=[1,2])
        agent.choose_action([],first)
        action=agent.choose_action([],second)
        self.assertEqual(agent.model_calls,2)
        self.assertEqual(action.reasoning["policy"],"exp-005-belief-and-novelty")
        memory=json.loads(model.prompts[-1])["agent_belief_state"]
        self.assertEqual(memory["unverified_goal_hypothesis"],"reach the exit")
        self.assertEqual(memory["unverified_dynamics_hypothesis"],"1 moves right")

    def test_keyboard_plan_saves_a_model_call(self):
        agent,model=self.agent(json.dumps({
            "action":1,"data":{},"reason":"move",
            "goal":"seek exit",
            "next_actions":[{"action":2,"data":{}}]
        }))
        f1=FakeFrameData(frame=[[[1]]],available_actions=[1,2])
        f2=FakeFrameData(frame=[[[2]]],available_actions=[1,2])
        self.assertIs(agent.choose_action([],f1),FakeGameAction.ACTION1)
        planned=agent.choose_action([],f2)
        self.assertIs(planned,FakeGameAction.ACTION2)
        self.assertTrue(planned.reasoning["planned_action"])
        self.assertEqual(agent.model_calls,1)
        self.assertEqual(agent._belief.plan_actions_taken,1)

    def test_invalid_action_cannot_queue_a_plan(self):
        agent,model=self.agent(json.dumps({
            "action":999,"data":{},"reason":"wrong",
            "next_actions":[{"action":2,"data":{}}]
        }))
        frame=FakeFrameData(frame=[[[1]]],available_actions=[1,2])
        a=agent.choose_action([],frame)
        self.assertTrue(a.reasoning["redirected"])
        self.assertIsNone(agent._belief.take_plan(legal_actions=[1,2]))
        self.assertEqual(agent.validation_fallbacks,1)

    def test_switches_to_model_free_after_prolonged_stagnation(self):
        agent,model=self.agent('{"action":1,"data":{},"reason":"test"}')
        for turn in range(20):
            frame=FakeFrameData(frame=[[[turn%3]]],available_actions=[1,2])
            action=agent.choose_action([],frame)
            self.assertIn(action,[FakeGameAction.ACTION1,FakeGameAction.ACTION2])
        self.assertGreater(agent._explorer.heuristic_calls,0)
        self.assertLess(agent.model_calls,20)
        self.assertEqual(agent._belief.progress_events if hasattr(agent._belief,"progress_events") else 0,0)
        self.assertEqual(agent._feedback.progress_events,0)

    def test_model_call_refresh_after_heuristic_blocks(self):
        agent,model=self.agent('{"action":1,"data":{},"reason":"move"}')
        calls=[]
        for turn in range(31):
            action=agent.choose_action([],
                FakeFrameData(frame=[[[turn%4]]],available_actions=[1,2]))
            calls.append(agent.model_calls)
        self.assertTrue(any(calls[i]==calls[i-1] for i in range(17,30)))
        self.assertTrue(any(calls[i]>calls[i-1] for i in range(17,30)))

    def test_level_progress_clears_belief_and_novelty_visits(self):
        agent,model=self.agent('{"action":1,"data":{},"reason":"move","goal":"finish puzzle"}')
        f1=FakeFrameData(frame=[[[1]]],available_actions=[1,2],levels_completed=0)
        f2=FakeFrameData(frame=[[[2]]],available_actions=[1,2],levels_completed=1)
        agent.choose_action([],f1)
        agent.choose_action([],f2)
        self.assertEqual(agent._belief.steps_without_progress,0)
        self.assertEqual(agent._belief.goal,"finish puzzle")
        self.assertEqual(agent._explorer.progress_resets,1)


if __name__ == "__main__":
    unittest.main()
