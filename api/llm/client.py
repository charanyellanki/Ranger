"""Thin LiteLLM wrapper used by every agent node.

Responsibilities:
  - Read the active provider+model from Postgres
  - Decrypt the API key
  - Call litellm.acompletion with normalized params
  - Return both the text response and a usage record

Token counts are Optional — not every provider/model reliably reports usage
(esp. Gemini streaming, Ollama), so callers must treat `tokens_used=0` as "unknown."
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import litellm
from litellm import acompletion
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import LLMProvider
from db.session import session_scope
from llm.encryption import decrypt
from llm.providers import PROVIDERS, get_provider, litellm_model_string

log = logging.getLogger(__name__)

# Suppress LiteLLM's chatty INFO logs; our audit logger is the signal.
litellm.suppress_debug_info = True


class LLMNotConfiguredError(RuntimeError):
    """Raised when the caller invokes the agent but no provider is active."""


@dataclass
class LLMResult:
    text: str
    tokens_used: int
    model: str
    provider: str
    latency_ms: int
    raw_json: dict[str, Any] | None = None


async def _load_active_provider(session: AsyncSession) -> LLMProvider:
    result = await session.execute(
        select(LLMProvider).where(LLMProvider.is_active.is_(True))
    )
    provider = result.scalar_one_or_none()
    if provider is None:
        raise LLMNotConfiguredError(
            "No active LLM provider. Configure one at /admin/settings."
        )
    return provider


def _build_kwargs(
    provider_name: str,
    model: str,
    messages: list[dict[str, str]],
    api_key: str | None,
    base_url: str | None,
    json_mode: bool,
    max_tokens: int | None,
    temperature: float,
) -> dict[str, Any]:
    provider_def = get_provider(provider_name)
    kwargs: dict[str, Any] = {
        "model": litellm_model_string(provider_name, model),
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if provider_def.needs_api_key and api_key:
        kwargs["api_key"] = api_key
    if provider_def.needs_base_url and base_url:
        kwargs["api_base"] = base_url
    if json_mode and provider_name in {"openai", "anthropic"}:
        # Only these have reliably uniform JSON mode support in LiteLLM.
        kwargs["response_format"] = {"type": "json_object"}
    return kwargs


async def complete(
    messages: list[dict[str, str]],
    *,
    json_mode: bool = False,
    max_tokens: int | None = 1024,
    temperature: float = 0.2,
) -> LLMResult:
    """Make a completion using the currently-active provider."""
    async with session_scope() as session:
        provider = await _load_active_provider(session)
        api_key = decrypt(provider.encrypted_api_key) if provider.encrypted_api_key else None
        base_url = provider.base_url
        active_model = provider.active_model
        provider_name = provider.name

    if not active_model:
        raise LLMNotConfiguredError(f"Provider {provider_name} has no active model set.")

    kwargs = _build_kwargs(
        provider_name, active_model, messages, api_key, base_url,
        json_mode, max_tokens, temperature,
    )

    start = time.perf_counter()
    response = await acompletion(**kwargs)
    latency_ms = int((time.perf_counter() - start) * 1000)

    text = response.choices[0].message.content or ""
    tokens = 0
    try:
        usage = getattr(response, "usage", None)
        if usage:
            tokens = int(getattr(usage, "total_tokens", 0) or 0)
    except Exception:  # pragma: no cover — defensive, Gemini sometimes returns odd shapes
        tokens = 0

    return LLMResult(
        text=text,
        tokens_used=tokens,
        model=active_model,
        provider=provider_name,
        latency_ms=latency_ms,
    )


async def test_provider(
    *,
    provider_name: str,
    model: str,
    api_key: str | None,
    base_url: str | None,
) -> LLMResult:
    """Lightweight probe used by the admin UI's 'Test' button.

    Does not read DB state — accepts the (possibly unsaved) credentials directly.
    """
    if provider_name not in PROVIDERS:
        raise ValueError(f"Unknown provider {provider_name}")

    messages = [
        {"role": "user", "content": "Reply with the single word: ok"},
    ]
    kwargs = _build_kwargs(
        provider_name, model, messages, api_key, base_url,
        json_mode=False, max_tokens=5, temperature=0.0,
    )

    start = time.perf_counter()
    response = await acompletion(**kwargs)
    latency_ms = int((time.perf_counter() - start) * 1000)

    text = response.choices[0].message.content or ""
    tokens = 0
    try:
        usage = getattr(response, "usage", None)
        if usage:
            tokens = int(getattr(usage, "total_tokens", 0) or 0)
    except Exception:
        tokens = 0

    return LLMResult(
        text=text,
        tokens_used=tokens,
        model=model,
        provider=provider_name,
        latency_ms=latency_ms,
    )


def safe_json_loads(text: str) -> dict[str, Any] | None:
    """Tolerant JSON parser for LLM output. Handles fenced code blocks."""
    candidate = text.strip()
    if candidate.startswith("```"):
        # Strip ```json fences.
        lines = [l for l in candidate.splitlines() if not l.startswith("```")]
        candidate = "\n".join(lines).strip()
    try:
        obj = json.loads(candidate)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        # Try to find the first balanced {...} substring.
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end > start:
            try:
                obj = json.loads(candidate[start : end + 1])
                return obj if isinstance(obj, dict) else None
            except json.JSONDecodeError:
                return None
        return None
