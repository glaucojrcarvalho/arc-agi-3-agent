from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from arc_agent.model import (
    DEFAULT_ENDPOINT,
    LocalModelConfig,
    ModelClientError,
    build_chat_payload,
    build_policy_prompt,
    extract_completion_content,
)


class LocalModelTests(unittest.TestCase):
    def test_config_defaults_to_loopback_and_requires_model_name(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ModelClientError):
                LocalModelConfig.from_env()

        with patch.dict(
            os.environ,
            {"ARC_MODEL_NAME": "Qwen/Qwen3.8-27B"},
            clear=True,
        ):
            config = LocalModelConfig.from_env()

        self.assertEqual(config.endpoint, DEFAULT_ENDPOINT)
        self.assertEqual(config.model, "Qwen/Qwen3.8-27B")

    def test_config_rejects_non_loopback_endpoint(self) -> None:
        with patch.dict(
            os.environ,
            {
                "ARC_MODEL_NAME": "test-model",
                "ARC_MODEL_ENDPOINT": "https://example.com/v1/chat/completions",
            },
            clear=True,
        ):
            with self.assertRaises(ModelClientError):
                LocalModelConfig.from_env()

    def test_policy_prompt_contains_only_current_contract(self) -> None:
        prompt = build_policy_prompt(
            frame=[[[1, 2], [3, 4]]],
            state="NOT_FINISHED",
            levels_completed=1,
            available_action_ids=[1, 6],
            complex_action_ids=[6],
            width=2,
            height=2,
        )
        payload = json.loads(prompt)

        self.assertEqual(payload["frame"], [[[1, 2], [3, 4]]])
        self.assertEqual(payload["available_action_ids"], [1, 6])
        self.assertNotIn("history", payload)
        self.assertNotIn("transitions", payload)

    def test_chat_payload_disables_thinking_for_direct_policy(self) -> None:
        payload = build_chat_payload(model="test-model", prompt="{}")

        self.assertEqual(payload["temperature"], 0.0)
        self.assertFalse(payload["chat_template_kwargs"]["enable_thinking"])
        self.assertFalse(payload["chat_template_kwargs"]["preserve_thinking"])

    def test_extract_completion_content(self) -> None:
        content = extract_completion_content(
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"action":1,"data":{},"reason":"move"}'
                        }
                    }
                ]
            }
        )
        self.assertEqual(content, '{"action":1,"data":{},"reason":"move"}')

    def test_extract_completion_rejects_empty_content(self) -> None:
        with self.assertRaises(ModelClientError):
            extract_completion_content({"choices": [{"message": {"content": ""}}]})


if __name__ == "__main__":
    unittest.main()
