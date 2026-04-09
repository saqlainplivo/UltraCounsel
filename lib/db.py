"""
lib/db.py
asyncpg connection pool singleton for UltraCounsel.
"""

import asyncpg
import os
from typing import Optional, Any


_pool: Optional[asyncpg.Pool] = None


async def create_pool() -> asyncpg.Pool:
    """Create the database connection pool."""
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=os.getenv("DATABASE_URL"),
        min_size=2,
        max_size=10,
        command_timeout=30,
    )
    return _pool


async def close_pool() -> None:
    """Close the database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    """Return the active pool (raises if not initialised)."""
    if _pool is None:
        raise RuntimeError("Database pool not initialised. Call create_pool() first.")
    return _pool


async def fetch_one(query: str, *args) -> Optional[asyncpg.Record]:
    """Execute a query and return the first row, or None."""
    async with get_pool().acquire() as conn:
        return await conn.fetchrow(query, *args)


async def fetch_all(query: str, *args) -> list[asyncpg.Record]:
    """Execute a query and return all rows."""
    async with get_pool().acquire() as conn:
        return await conn.fetch(query, *args)


async def execute(query: str, *args) -> str:
    """Execute a statement and return the status string."""
    async with get_pool().acquire() as conn:
        return await conn.execute(query, *args)


async def executemany(query: str, args: list) -> None:
    """Execute a statement for each set of args."""
    async with get_pool().acquire() as conn:
        await conn.executemany(query, args)
