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
Keep reason short. If recent transitions or proven no-op actions are supplied, use them to avoid repeating actions that were confirmed ineffective in the exact same state. A changing frame does not necessarily indicate progress. Do not include markdown or any text outside the JSON object."""


_PLANNING_SYSTEM_PROMPT = """You are controlling a previously unseen ARC-AGI-3 puzzle game.
The game has no instructions. Infer which object moves, what controls do, and what likely
completes a LEVEL; visible pixel changes are not a score. Learn from recent transitions,
retain and revise beliefs, avoid unproductive cycles. Avoid assuming color meanings.
Return exactly one JSON object with required keys:
"action": integer legal action ID,
"data": {} for keyboard actions or {"x": int, "y": int} for coordinate actions,
"reason": short action explanation.
Also include optional concise fields:
"goal": the current guessed objective (<=25 words),
"hypothesis": one falsifiable hypothesis about game dynamics (<=35 words),
"next_actions": an array of 0-2 follow-up legal KEYBOARD actions with {"action": int, "data": {}}.
Plans are optional and must be safe to interrupt on new observations. When uncertain,
explore distinct hypotheses; when stuck, explicitly revise the goal/hypothesis.
No markdown, no text outside the JSON object."""


class ModelClientError(RuntimeError):
    """Raised when the local model runtime cannot provide a valid completion."""


@dataclass(frozen=True)
class LocalModelConfig:
    endpoint: str
    model: str
    timeout_seconds: float = 120.0
    max_tokens: int = 128
    planning_enabled: bool = False

    @classmethod
    def from_env(cls) -> "LocalModelConfig":
        endpoint = os.getenv("ARC_MODEL_ENDPOINT", DEFAULT_ENDPOINT).strip()
        model = os.getenv("ARC_MODEL_NAME", "").strip()
        timeout_raw = os.getenv("ARC_MODEL_TIMEOUT_SECONDS", "120").strip()
        tokens_raw = os.getenv("ARC_MODEL_MAX_TOKENS", "128").strip()
        planner_raw = os.getenv("ARC_MODEL_PLANNING_ENABLED", "0").strip().lower()

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
        try:
            max_tokens = int(tokens_raw)
        except ValueError as exc:
            raise ModelClientError("ARC_MODEL_MAX_TOKENS must be an integer") from exc
        if not 32 <= max_tokens <= 512:
            raise ModelClientError("ARC_MODEL_MAX_TOKENS must be 32..512")
        if planner_raw not in {"0", "1", "false", "true"}:
            raise ModelClientError("ARC_MODEL_PLANNING_ENABLED must be boolean")

        return cls(
            endpoint=endpoint,
            model=model,
            timeout_seconds=timeout_seconds,
            max_tokens=max_tokens,
            planning_enabled=planner_raw in {"1", "true"},
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
    transition_feedback: list[dict[str, Any]] | None = None,
    blocked_actions: list[dict[str, Any]] | None = None,
    frame_representation: str = "raw",
    click_candidates: list[dict[str, int]] | None = None,
    recent_click_cooldowns: list[dict[str, int]] | None = None,
    reasoning_context: dict[str, Any] | None = None,
) -> str:
    """Serialize the observation, actions and optional bounded feedback."""
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
    }
    if frame_representation == "raw":
        payload["frame"] = frame
    elif frame_representation == "symbol_grid":
        from .perception import symbol_grid
        payload["visual_observation"] = symbol_grid(frame)
        payload["pixel_coordinate_convention"] = (
            "x is column 0..width-1, y is row 0..height-1; "
            "a hex character is an exact pixel color index, not a text character."
        )
    elif frame_representation == "bounded_animation":
        from .perception import bounded_animation_observation
        payload["visual_observation"] = bounded_animation_observation(frame)
        payload["animation_note"] = (
            "The first dimension is an ordered animation sequence, not layers. "
            "The settled board is the final frame. Frame dictionary and runs "
            "encode an exact sequence; sampled keyframes omit intervening frames "
            "and must not be treated as full evidence of dynamics. "
            "Rows are exact pixel-color indices; x is column and y is row."
        )
    else:
        raise ValueError("unsupported frame_representation")
    if click_candidates is not None:
        payload["candidate_click_pixels"] = click_candidates[:24]
        payload["candidate_click_note"] = (
            "Candidate pixels belong to visible color regions, not verified targets; "
            "they are suggestions only. Choose legal x/y within the frame."
        )
    if recent_click_cooldowns is not None:
        payload["recent_click_cooldowns"] = recent_click_cooldowns[:16]
        payload["cooldown_note"] = (
            "These click locations were already attempted recently without "
            "level progress. Prefer exploring another visible location. "
            "This is a temporary exploration cooldown, not proof of failure."
        )
    if transition_feedback is not None:
        payload["recent_transitions"] = transition_feedback[-6:]
    if blocked_actions is not None:
        payload["proven_noop_actions_here"] = blocked_actions[:24]
    if reasoning_context is not None:
        payload["agent_belief_state"] = reasoning_context
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=True)


def build_chat_payload(
    *, model: str, prompt: str, max_tokens: int = 128,
    planning_enabled: bool = False,
) -> dict[str, Any]:
    """Build a deterministic text-only Chat Completions request."""
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": (
                _PLANNING_SYSTEM_PROMPT if planning_enabled else _SYSTEM_PROMPT
            )},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": max_tokens,
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
        request_payload = build_chat_payload(
            model=self.model,
            prompt=prompt,
            max_tokens=self.config.max_tokens,
            planning_enabled=self.config.planning_enabled,
        )
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
