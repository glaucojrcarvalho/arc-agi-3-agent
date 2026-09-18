from __future__ import annotations

import importlib
import sys
import types
import unittest
from enum import IntEnum


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
    ) -> None:
        self.state = state
        self.frame = frame if frame is not None else [[[0]]]
        self.available_actions = available_actions or []


class FakeAgent:
    def __init__(self, *args, **kwargs) -> None:
        self.game_id = kwargs.get("game_id", "test-game")


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

    def make_agent(self, game_id: str = "test-game"):
        return self.module.MyAgent(game_id=game_id)

    def test_resets_when_game_has_not_started(self) -> None:
        agent = self.make_agent()
        frame = FakeFrameData(state=FakeGameState.NOT_PLAYED)

        self.assertIs(agent.choose_action([], frame), FakeGameAction.RESET)

    def test_resets_after_game_over(self) -> None:
        agent = self.make_agent()
        frame = FakeFrameData(state=FakeGameState.GAME_OVER)

        self.assertIs(agent.choose_action([], frame), FakeGameAction.RESET)

    def test_stops_only_on_win(self) -> None:
        agent = self.make_agent()

        self.assertFalse(
            agent.is_done([], FakeFrameData(state=FakeGameState.NOT_FINISHED))
        )
        self.assertTrue(agent.is_done([], FakeFrameData(state=FakeGameState.WIN)))

    def test_chooses_only_from_available_actions(self) -> None:
        agent = self.make_agent()
        frame = FakeFrameData(available_actions=[2])

        self.assertIs(agent.choose_action([], frame), FakeGameAction.ACTION2)

    def test_invalid_available_action_ids_are_ignored(self) -> None:
        agent = self.make_agent()
        frame = FakeFrameData(available_actions=[999, 1])

        self.assertIs(agent.choose_action([], frame), FakeGameAction.ACTION1)

    def test_boolean_and_non_integer_action_ids_are_ignored(self) -> None:
        agent = self.make_agent()
        frame = FakeFrameData(available_actions=[True, "2", 2])

        self.assertIs(agent.choose_action([], frame), FakeGameAction.ACTION2)

    def test_complex_action_coordinates_respect_observed_bounds(self) -> None:
        agent = self.make_agent()
        frame = FakeFrameData(
            frame=[[[0, 0, 0], [0, 0, 0]]],
            available_actions=[6],
        )

        action = agent.choose_action([], frame)

        self.assertIs(action, FakeGameAction.ACTION6)
        self.assertGreaterEqual(action.action_data["x"], 0)
        self.assertLess(action.action_data["x"], 3)
        self.assertGreaterEqual(action.action_data["y"], 0)
        self.assertLess(action.action_data["y"], 2)

    def test_complex_action_coordinates_never_exceed_arc_limit(self) -> None:
        agent = self.make_agent()
        frame = FakeFrameData(
            frame=[[[0] * 80 for _ in range(80)]],
            available_actions=[6],
        )

        for _ in range(32):
            action = agent.choose_action([], frame)
            self.assertLess(action.action_data["x"], 64)
            self.assertLess(action.action_data["y"], 64)

    def test_same_game_id_produces_same_action_sequence(self) -> None:
        left = self.make_agent("stable-game")
        right = self.make_agent("stable-game")
        frame = FakeFrameData(available_actions=[1, 2])

        left_sequence = [int(left.choose_action([], frame)) for _ in range(8)]
        right_sequence = [int(right.choose_action([], frame)) for _ in range(8)]

        self.assertEqual(left_sequence, right_sequence)


if __name__ == "__main__":
    unittest.main()
