from __future__ import annotations

import logging

from app.config import get_settings

logger = logging.getLogger("autorocket_ai_assistant.db")

try:
    import asyncpg
    _ASYNCPG_AVAILABLE = True
except ImportError:
    _ASYNCPG_AVAILABLE = False
    logger.warning("asyncpg not installed — tenant key lookups will not work.")

_pool = None


async def get_pool():
    global _pool
    if not _ASYNCPG_AVAILABLE:
        raise RuntimeError("asyncpg is not installed. Run: pip install asyncpg")
    if _pool is None:
        dsn = get_settings().database_url
        if not dsn:
            raise RuntimeError("DATABASE_URL is not set in environment.")
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
        logger.info("Database connection pool created.")
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed.")


# ─────────────────────────────────────────────────────────────────────────────
# Per-tenant OpenAI key — read-only lookup (plain text, no decryption)
# Same Tenant.openaiApiKey column that AI Boardroom (agent-botivateOS) reads.
# ─────────────────────────────────────────────────────────────────────────────

async def get_tenant_api_key(tenant_id: str) -> str | None:
    """
    Fetch the OpenAI API key for a tenant from the Tenant table.
    Key is stored as plain text — no decryption needed.
    Returns the key string, or None if not set / tenant not found.
    """
    logger.info("[KEY] Fetching openaiApiKey for tenant=%s", tenant_id)

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT "openaiApiKey" FROM "Tenant" WHERE id = $1 AND "isActive" = true',
                tenant_id,
            )
    except Exception as exc:
        logger.error("[KEY] DB error while fetching key for tenant=%s: %s", tenant_id, exc)
        return None

    if not row:
        logger.warning("[KEY] Tenant not found in DB: tenant=%s", tenant_id)
        return None

    key = row["openaiApiKey"]

    if not key:
        logger.info("[KEY] openaiApiKey is NULL for tenant=%s — key not configured", tenant_id)
        return None

    logger.info("[KEY] Key found in DB for tenant=%s ✅", tenant_id)
    return key
