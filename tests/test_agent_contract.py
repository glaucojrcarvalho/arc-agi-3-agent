from __future__ import annotations

import importlib
import json
import sys
import types
import unittest
from enum import IntEnum

from arc_agent.model import ModelClientError


class FakeGameState(IntEnum):
    NOT_PLAYED = 0
    NOT_FINISHED = 1
    GAME_OVER = 2
    WIN = 3


class FakeGameAction(IntEnum):
    RESET = 0
    ACTION1 = 1
    ACTION2 = 2
    ACTION6 = 6

    @classmethod
    def from_id(cls, action_id: int) -> "FakeGameAction":
        try:
            return cls(action_id)
        except ValueError as exc:
            raise ValueError(f"unknown action: {action_id}") from exc

    def is_complex(self) -> bool:
        return self is FakeGameAction.ACTION6

    def set_data(self, data: dict[str, int]) -> None:
        self.action_data = dict(data)


class FakeFrameData:
    def __init__(
        self,
        *,
        state: FakeGameState = FakeGameState.NOT_FINISHED,
        frame: list[list[list[int]]] | None = None,
        available_actions: list[object] | None = None,
        levels_completed: int = 0,
    ) -> None:
        self.state = state
        self.frame = frame if frame is not None else [[[0]]]
        self.available_actions = available_actions or []
        self.levels_completed = levels_completed


class FakeAgent:
    def __init__(self, *args, **kwargs) -> None:
        self.game_id = kwargs.get("game_id", "test-game")


class FakeModel:
    model = "test-model"

    def __init__(self, response: str) -> None:
        self.response = response
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


class FailingModel(FakeModel):
    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        raise ModelClientError("test transport failure")


class AgentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        arcengine = types.ModuleType("arcengine")
        arcengine.FrameData = FakeFrameData
        arcengine.GameAction = FakeGameAction
        arcengine.GameState = FakeGameState

        agents = types.ModuleType("agents")
        agent_module = types.ModuleType("agents.agent")
        agent_module.Agent = FakeAgent
        agents.agent = agent_module

        cls._previous_modules = {
            name: sys.modules.get(name)
            for name in ("arcengine", "agents", "agents.agent")
        }
        sys.modules["arcengine"] = arcengine
        sys.modules["agents"] = agents
        sys.modules["agents.agent"] = agent_module

        sys.modules.pop("agent.my_agent", None)
        cls.module = importlib.import_module("agent.my_agent")

    @classmethod
    def tearDownClass(cls) -> None:
        sys.modules.pop("agent.my_agent", None)
        for name, previous in cls._previous_modules.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous

    def make_agent(self, response: str = '{"action":1,"data":{},"reason":"move"}'):
        agent = self.module.MyAgent(game_id="test-game")
        model = FakeModel(response)
        agent._model = model
        return agent, model

    def test_resets_without_model_call_when_game_has_not_started(self) -> None:
        agent, model = self.make_agent()
        frame = FakeFrameData(state=FakeGameState.NOT_PLAYED)

        self.assertIs(agent.choose_action([], frame), FakeGameAction.RESET)
        self.assertEqual(model.prompts, [])

    def test_resets_without_model_call_after_game_over(self) -> None:
        agent, model = self.make_agent()
        frame = FakeFrameData(state=FakeGameState.GAME_OVER)

        self.assertIs(agent.choose_action([], frame), FakeGameAction.RESET)
        self.assertEqual(model.prompts, [])

    def test_stops_only_on_win(self) -> None:
        agent, _ = self.make_agent()

        self.assertFalse(
            agent.is_done([], FakeFrameData(state=FakeGameState.NOT_FINISHED))
        )
        self.assertTrue(agent.is_done([], FakeFrameData(state=FakeGameState.WIN)))

    def test_executes_valid_model_action(self) -> None:
        agent, _ = self.make_agent(
            '{"action":2,"data":{},"reason":"try action two"}'
        )
        frame = FakeFrameData(available_actions=[1, 2])

        action = agent.choose_action([], frame)

        self.assertIs(action, FakeGameAction.ACTION2)
        self.assertFalse(action.reasoning["fallback"])
        self.assertEqual(agent.validation_fallbacks, 0)

    def test_invalid_output_uses_deterministic_legal_fallback(self) -> None:
        agent, _ = self.make_agent("not-json")
        frame = FakeFrameData(available_actions=[2, 1])

        action = agent.choose_action([], frame)

        self.assertIs(action, FakeGameAction.ACTION1)
        self.assertTrue(action.reasoning["fallback"])
        self.assertEqual(agent.validation_fallbacks, 1)

    def test_complex_action_uses_validated_coordinates(self) -> None:
        agent, _ = self.make_agent(
            '{"action":6,"data":{"x":2,"y":1},"reason":"inspect"}'
        )
        frame = FakeFrameData(
            frame=[[[0, 0, 0], [0, 0, 0]]],
            available_actions=[6],
        )

        action = agent.choose_action([], frame)

        self.assertIs(action, FakeGameAction.ACTION6)
        self.assertEqual(action.action_data, {"x": 2, "y": 1})
        self.assertFalse(action.reasoning["fallback"])

    def test_invalid_complex_coordinates_fallback_to_origin(self) -> None:
        agent, _ = self.make_agent(
            '{"action":6,"data":{"x":99,"y":99},"reason":"inspect"}'
        )
        frame = FakeFrameData(
            frame=[[[0, 0], [0, 0]]],
            available_actions=[6],
        )

        action = agent.choose_action([], frame)

        self.assertIs(action, FakeGameAction.ACTION6)
        self.assertEqual(action.action_data, {"x": 0, "y": 0})
        self.assertTrue(action.reasoning["fallback"])

    def test_prompt_contains_current_state_without_history(self) -> None:
        agent, model = self.make_agent()
        frame = FakeFrameData(
            frame=[[[1, 2], [3, 4]]],
            available_actions=[1],
            levels_completed=2,
        )

        agent.choose_action([FakeFrameData()], frame)
        prompt = json.loads(model.prompts[0])

        self.assertEqual(prompt["frame"], [[[1, 2], [3, 4]]])
        self.assertEqual(prompt["levels_completed"], 2)
        self.assertNotIn("history", prompt)
        self.assertNotIn("transitions", prompt)

    def test_malformed_available_action_ids_are_ignored(self) -> None:
        agent, _ = self.make_agent(
            '{"action":2,"data":{},"reason":"move"}'
        )
        frame = FakeFrameData(available_actions=[True, "2", 999, 2])

        self.assertIs(agent.choose_action([], frame), FakeGameAction.ACTION2)

    def test_no_executable_actions_fails_fast(self) -> None:
        agent, model = self.make_agent()
        frame = FakeFrameData(available_actions=[])

        with self.assertRaises(RuntimeError):
            agent.choose_action([], frame)
        self.assertEqual(model.prompts, [])

    def test_transport_failure_is_not_silently_converted_to_fallback(self) -> None:
        agent = self.module.MyAgent(game_id="test-game")
        agent._model = FailingModel("")
        frame = FakeFrameData(available_actions=[1])

        with self.assertRaises(ModelClientError):
            agent.choose_action([], frame)


if __name__ == "__main__":
    unittest.main()
