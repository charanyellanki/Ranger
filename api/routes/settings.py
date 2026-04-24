"""Admin settings — LLM provider management.

All routes here are gated by the `X-Admin-Token` header. Token is the
ADMIN_TOKEN env var — documented as dev-only in the README.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from db.models import LLMProvider
from db.session import get_db
from llm.client import test_provider
from llm.encryption import encrypt, last4
from llm.providers import PROVIDERS, catalog, get_provider
from schemas import (
    ProviderActivateIn,
    ProviderStatus,
    ProviderTestIn,
    ProviderTestOut,
    ProviderUpdateIn,
)

log = logging.getLogger("ranger.routes.settings")

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not x_admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")


@router.get("/providers/catalog")
async def get_catalog() -> dict:
    """Static — no auth needed. Used by the UI to populate dropdowns."""
    return {"providers": catalog()}


@router.get("/providers", response_model=list[ProviderStatus], dependencies=[Depends(require_admin)])
async def list_provider_statuses(db: AsyncSession = Depends(get_db)) -> list[ProviderStatus]:
    result = await db.execute(select(LLMProvider))
    by_name = {p.name: p for p in result.scalars().all()}
    statuses: list[ProviderStatus] = []
    for name, definition in PROVIDERS.items():
        row = by_name.get(name)
        statuses.append(
            ProviderStatus(
                name=name,  # type: ignore[arg-type]
                configured=bool(row and (row.encrypted_api_key or row.base_url)),
                is_active=bool(row and row.is_active),
                api_key_last4=row.api_key_last4 if row else None,
                active_model=row.active_model if row else None,
                base_url=row.base_url if row else None,
            )
        )
    return statuses


@router.put(
    "/providers/{name}",
    response_model=ProviderStatus,
    dependencies=[Depends(require_admin)],
)
async def upsert_provider(
    name: str,
    body: ProviderUpdateIn,
    db: AsyncSession = Depends(get_db),
) -> ProviderStatus:
    if name not in PROVIDERS:
        raise HTTPException(404, detail=f"Unknown provider: {name}")
    definition = get_provider(name)

    result = await db.execute(select(LLMProvider).where(LLMProvider.name == name))
    row = result.scalar_one_or_none()
    if row is None:
        row = LLMProvider(name=name)
        db.add(row)

    if body.api_key:
        if not definition.needs_api_key:
            raise HTTPException(400, detail=f"{name} does not take an API key")
        row.encrypted_api_key = encrypt(body.api_key)
        row.api_key_last4 = last4(body.api_key)
    if body.base_url is not None:
        if not definition.needs_base_url:
            raise HTTPException(400, detail=f"{name} does not take a base URL")
        row.base_url = body.base_url
    if body.active_model is not None:
        if body.active_model not in definition.models:
            raise HTTPException(
                400,
                detail=f"Model {body.active_model} not available for {name}. Choices: {list(definition.models)}",
            )
        row.active_model = body.active_model

    await db.commit()
    await db.refresh(row)
    return ProviderStatus(
        name=name,  # type: ignore[arg-type]
        configured=bool(row.encrypted_api_key or row.base_url),
        is_active=row.is_active,
        api_key_last4=row.api_key_last4,
        active_model=row.active_model,
        base_url=row.base_url,
    )


@router.delete("/providers/{name}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_provider(name: str, db: AsyncSession = Depends(get_db)) -> None:
    if name not in PROVIDERS:
        raise HTTPException(404, detail=f"Unknown provider: {name}")
    result = await db.execute(select(LLMProvider).where(LLMProvider.name == name))
    row = result.scalar_one_or_none()
    if row is None:
        return
    await db.delete(row)
    await db.commit()


@router.post("/providers/activate", dependencies=[Depends(require_admin)])
async def activate_provider(
    body: ProviderActivateIn,
    db: AsyncSession = Depends(get_db),
) -> dict:
    definition = get_provider(body.name)
    if body.model not in definition.models:
        raise HTTPException(
            400,
            detail=f"Model {body.model} not available for {body.name}. Choices: {list(definition.models)}",
        )

    result = await db.execute(select(LLMProvider).where(LLMProvider.name == body.name))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(404, detail=f"Provider {body.name} is not configured")
    if definition.needs_api_key and not row.encrypted_api_key:
        raise HTTPException(400, detail=f"Provider {body.name} is missing an API key")
    if definition.needs_base_url and not row.base_url:
        raise HTTPException(400, detail=f"Provider {body.name} is missing a base URL")

    # Flip all to inactive, then activate the chosen one.
    await db.execute(update(LLMProvider).values(is_active=False))
    row.is_active = True
    row.active_model = body.model
    await db.commit()
    return {"active_provider": body.name, "active_model": body.model}


@router.post(
    "/providers/test",
    response_model=ProviderTestOut,
    dependencies=[Depends(require_admin)],
)
async def test(body: ProviderTestIn, db: AsyncSession = Depends(get_db)) -> ProviderTestOut:
    definition = get_provider(body.name)
    if body.model not in definition.models:
        raise HTTPException(
            400,
            detail=f"Model {body.model} not available for {body.name}. Choices: {list(definition.models)}",
        )

    api_key = body.api_key
    base_url = body.base_url

    # Fall back to saved creds if the UI didn't pass them (common: testing an
    # already-configured provider before switching active model).
    if (definition.needs_api_key and not api_key) or (definition.needs_base_url and not base_url):
        result = await db.execute(select(LLMProvider).where(LLMProvider.name == body.name))
        row = result.scalar_one_or_none()
        if row is None:
            raise HTTPException(400, detail="Provider not configured and no credentials supplied")
        if definition.needs_api_key and not api_key:
            from llm.encryption import decrypt
            if row.encrypted_api_key:
                api_key = decrypt(row.encrypted_api_key)
        if definition.needs_base_url and not base_url:
            base_url = row.base_url

    try:
        result = await test_provider(
            provider_name=body.name,
            model=body.model,
            api_key=api_key,
            base_url=base_url,
        )
        return ProviderTestOut(
            success=True,
            message=f"OK — model responded with {result.text!r}",
            latency_ms=result.latency_ms,
            tokens_used=result.tokens_used or None,
        )
    except Exception as e:
        log.warning("Provider test failed for %s: %s", body.name, e)
        return ProviderTestOut(success=False, message=f"{type(e).__name__}: {e}")


@router.get("/active")
async def get_active_provider(db: AsyncSession = Depends(get_db)) -> dict:
    """Public (no auth) — used by the header to show the active provider badge."""
    result = await db.execute(select(LLMProvider).where(LLMProvider.is_active.is_(True)))
    row = result.scalar_one_or_none()
    if row is None:
        return {"configured": False}
    return {
        "configured": True,
        "provider": row.name,
        "model": row.active_model,
    }
