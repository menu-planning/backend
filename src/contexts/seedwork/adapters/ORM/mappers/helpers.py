"""Shared utilities for serialization, concurrency, and simple DB helpers.

This module centralizes:
- cattrs converter hooks for ``datetime``
- a JSON "custom_serializer" for non-standard types
- helpers for concurrent execution with timeouts
- a small SQLAlchemy helper to fetch a single entity
"""

from collections.abc import Awaitable, Iterable
from typing import Any

import anyio
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.base import SaBase
from src.logging.logger import get_logger


async def gather_results_with_timeout(
    aws: Iterable[Awaitable[Any]],
    *,
    timeout: float,
    timeout_message: str,
) -> list[Any]:
    """Execute multiple awaitables concurrently with a timeout.

    Args:
        aws: Iterable of awaitables to execute.
        timeout: Maximum time to wait in seconds.
        timeout_message: Error message for timeout exception.

    Returns:
        List of results in the same order as input awaitables.

    Raises:
        TimeoutError: If execution exceeds the timeout.
    """
    logger = get_logger(__name__)
    tasks = list(aws)
    results = [None] * len(tasks)

    logger.debug(
        "Starting concurrent execution with timeout",
        task_count=len(tasks),
        timeout_seconds=timeout,
    )

    async def run_and_collect(index: int, a: Awaitable[Any]):
        results[index] = await a

    with anyio.move_on_after(timeout) as scope:
        async with anyio.create_task_group() as tg:
            for i, a in enumerate(tasks):
                tg.start_soon(run_and_collect, i, a)

    if scope.cancel_called:
        logger.warning(
            "Concurrent execution timed out",
            task_count=len(tasks),
            timeout_seconds=timeout,
            timeout_message=timeout_message,
        )
        raise TimeoutError(timeout_message)

    logger.debug(
        "Concurrent execution completed successfully",
        task_count=len(tasks),
        timeout_seconds=timeout,
    )
    return results


async def get_sa_entity(
    *,
    session: AsyncSession,
    sa_model_type: type[SaBase],
    filters: dict,
) -> Any:
    """Get a single SQLAlchemy entity by filters.

    Args:
        session: Database session.
        sa_model_type: SQLAlchemy model class.
        filters: Filter criteria as key-value pairs.

    Returns:
        The entity if found, None otherwise.
    """
    logger = get_logger(__name__)
    stmt = select(sa_model_type).filter_by(**filters)

    try:
        query = await session.execute(stmt)
        result = query.scalar_one()
        logger.debug(
            "Entity retrieved successfully",
            entity_type=sa_model_type.__name__,
            filters=filters,
        )
        return result
    except NoResultFound:
        logger.debug(
            "Entity not found with given filters",
            entity_type=sa_model_type.__name__,
            filters=filters,
        )
        return None
