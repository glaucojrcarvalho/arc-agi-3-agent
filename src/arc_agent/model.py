"""Local OpenAI-compatible model client for EXP-001."""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse


DEFAULT_ENDPOINT = "http://127.0.0.1:8000/v1/chat/completions"
_ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}

_SYSTEM_PROMPT = """You control an ARC-AGI-3 environment.
Choose exactly one currently legal action from the provided action ids.
Return exactly one JSON object with keys: action, data, reason.
For complex actions, data must contain integer x and y coordinates within the provided bounds.
For non-complex actions, data must be an empty object.
Keep reason short. Do not include markdown or any text outside the JSON object."""


class ModelClientError(RuntimeError):
    """Raised when the local model runtime cannot provide a valid completion."""


@dataclass(frozen=True)
class LocalModelConfig:
    endpoint: str
    model: str
    timeout_seconds: float = 120.0

    @classmethod
    def from_env(cls) -> "LocalModelConfig":
        endpoint = os.getenv("ARC_MODEL_ENDPOINT", DEFAULT_ENDPOINT).strip()
        model = os.getenv("ARC_MODEL_NAME", "").strip()
        timeout_raw = os.getenv("ARC_MODEL_TIMEOUT_SECONDS", "120").strip()

        if not model:
            raise ModelClientError("ARC_MODEL_NAME must identify the locally served model")

        parsed = urlparse(endpoint)
        if parsed.scheme != "http" or parsed.hostname not in _ALLOWED_HOSTS:
            raise ModelClientError(
                "ARC_MODEL_ENDPOINT must use HTTP on localhost/loopback"
            )

        try:
            timeout_seconds = float(timeout_raw)
        except ValueError as exc:
            raise ModelClientError("ARC_MODEL_TIMEOUT_SECONDS must be numeric") from exc
        if timeout_seconds <= 0:
            raise ModelClientError("ARC_MODEL_TIMEOUT_SECONDS must be positive")

        return cls(
            endpoint=endpoint,
            model=model,
            timeout_seconds=timeout_seconds,
        )


def build_policy_prompt(
    *,
    frame: Any,
    state: str,
    levels_completed: int,
    available_action_ids: list[int],
    complex_action_ids: list[int],
    width: int,
    height: int,
) -> str:
    """Serialize only the current observation and action contract."""
    payload = {
        "state": state,
        "levels_completed": levels_completed,
        "available_action_ids": available_action_ids,
        "complex_action_ids": complex_action_ids,
        "coordinate_bounds": {
            "x_min": 0,
            "x_max_exclusive": width,
            "y_min": 0,
            "y_max_exclusive": height,
        },
        "frame": frame,
    }
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=True)


def build_chat_payload(*, model: str, prompt: str) -> dict[str, Any]:
    """Build a deterministic text-only Chat Completions request."""
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 128,
        "chat_template_kwargs": {
            "enable_thinking": False,
            "preserve_thinking": False,
        },
    }


def extract_completion_content(payload: Mapping[str, Any]) -> str:
    """Extract assistant content from an OpenAI-compatible response."""
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ModelClientError("model response contains no choices")

    first = choices[0]
    if not isinstance(first, dict):
        raise ModelClientError("model response choice is malformed")

    message = first.get("message")
    if not isinstance(message, dict):
        raise ModelClientError("model response message is malformed")

    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ModelClientError("model response content is empty")

    return content.strip()


class LocalChatModel:
    """Minimal client for a localhost OpenAI-compatible chat server."""

    def __init__(self, config: LocalModelConfig) -> None:
        self.config = config

    @classmethod
    def from_env(cls) -> "LocalChatModel":
        return cls(LocalModelConfig.from_env())

    @property
    def model(self) -> str:
        return self.config.model

    def complete(self, prompt: str) -> str:
        request_payload = build_chat_payload(model=self.model, prompt=prompt)
        request = urllib.request.Request(
            self.config.endpoint,
            data=json.dumps(request_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout_seconds,
            ) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise ModelClientError(
                f"local model server returned HTTP {exc.code}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            raise ModelClientError("local model server request failed") from exc

        try:
            response_payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ModelClientError("local model server returned invalid JSON") from exc

        if not isinstance(response_payload, dict):
            raise ModelClientError("local model server returned a non-object response")

        return extract_completion_content(response_payload)
