from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from arc_agent.model import (
    LocalModelConfig, ModelClientError, build_chat_payload, build_policy_prompt,
)


class PlanningModelTests(unittest.TestCase):
    def test_planner_mode_is_opt_in(self):
        prompt='{"state":"NOT_FINISHED"}'
        base=build_chat_payload(model="Qwen",prompt=prompt)
        self.assertEqual(base["max_tokens"],128)
        self.assertNotIn("next_actions",base["messages"][0]["content"])
        extended=build_chat_payload(model="Qwen",prompt=prompt,max_tokens=320,planning_enabled=True)
        self.assertEqual(extended["max_tokens"],320)
        self.assertIn("next_actions",extended["messages"][0]["content"])
        self.assertFalse(extended["chat_template_kwargs"]["enable_thinking"])

    def test_config_planning_vars_and_safety_validation(self):
        with patch.dict(os.environ,{
            "ARC_MODEL_NAME":"Qwen",
            "ARC_MODEL_MAX_TOKENS":"320",
            "ARC_MODEL_PLANNING_ENABLED":"true"
        },clear=True):
            config=LocalModelConfig.from_env()
        self.assertEqual(config.max_tokens,320)
        self.assertTrue(config.planning_enabled)
        with patch.dict(os.environ,{"ARC_MODEL_NAME":"Qwen",
                                     "ARC_MODEL_MAX_TOKENS":"not-a-number"},clear=True):
            with self.assertRaises(ModelClientError):
                LocalModelConfig.from_env()
        with patch.dict(os.environ,{"ARC_MODEL_NAME":"Qwen",
                                     "ARC_MODEL_MAX_TOKENS":"600"},clear=True):
            with self.assertRaises(ModelClientError):
                LocalModelConfig.from_env()

    def test_state_is_compact_and_included_in_prompt(self):
        frame=[[[1,2]]]
        context={"unverified_goal_hypothesis":"reach exit",
                 "unverified_dynamics_hypothesis":"arrow movement"}
        payload=json.loads(build_policy_prompt(
            frame=frame,state="PLAYING",levels_completed=0,
            available_action_ids=[1],complex_action_ids=[],
            width=2,height=1,reasoning_context=context,
            frame_representation="symbol_grid"
        ))
        self.assertEqual(payload["agent_belief_state"],context)


if __name__=="__main__":
    unittest.main()
