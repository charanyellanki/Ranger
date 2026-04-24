"""Curated provider / model registry.

Single source of truth for what the admin UI shows and what the LLM client
accepts. LiteLLM model strings follow the pattern `<provider>/<model>` for
non-OpenAI providers (OpenAI models are bare, e.g. `gpt-4o-mini`).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderDef:
    name: str
    label: str
    models: tuple[str, ...]
    needs_api_key: bool
    needs_base_url: bool
    # Prefix to prepend to model name when passing to litellm.acompletion.
    # e.g. "anthropic/" → "anthropic/claude-sonnet-4-6"
    litellm_prefix: str


PROVIDERS: dict[str, ProviderDef] = {
    "openai": ProviderDef(
        name="openai",
        label="OpenAI",
        models=(
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4.1-mini",
            "gpt-4.1",
        ),
        needs_api_key=True,
        needs_base_url=False,
        litellm_prefix="",
    ),
    "anthropic": ProviderDef(
        name="anthropic",
        label="Anthropic",
        models=(
            "claude-haiku-4-5",
            "claude-sonnet-4-6",
            "claude-opus-4-7",
        ),
        needs_api_key=True,
        needs_base_url=False,
        litellm_prefix="anthropic/",
    ),
    "gemini": ProviderDef(
        name="gemini",
        label="Google Gemini",
        models=(
            "gemini-2.0-flash",
            "gemini-2.0-pro",
            "gemini-1.5-flash",
        ),
        needs_api_key=True,
        needs_base_url=False,
        litellm_prefix="gemini/",
    ),
    "grok": ProviderDef(
        name="grok",
        label="xAI Grok",
        models=(
            "grok-2-latest",
            "grok-beta",
        ),
        needs_api_key=True,
        needs_base_url=False,
        litellm_prefix="xai/",
    ),
    "ollama": ProviderDef(
        name="ollama",
        label="Ollama (local)",
        models=(
            "llama3.1",
            "llama3.2",
            "qwen2.5",
            "mistral",
        ),
        needs_api_key=False,
        needs_base_url=True,
        litellm_prefix="ollama/",
    ),
}


def get_provider(name: str) -> ProviderDef:
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {name}")
    return PROVIDERS[name]


def litellm_model_string(provider_name: str, model: str) -> str:
    """Convert (provider, model) → litellm model string."""
    provider = get_provider(provider_name)
    return f"{provider.litellm_prefix}{model}"


def catalog() -> list[dict]:
    """Shape for the frontend catalog endpoint."""
    return [
        {
            "name": p.name,
            "label": p.label,
            "models": list(p.models),
            "needs_api_key": p.needs_api_key,
            "needs_base_url": p.needs_base_url,
        }
        for p in PROVIDERS.values()
    ]
