from collections.abc import Awaitable, Iterable
from datetime import datetime
from typing import Any

import anyio
from cattrs import Converter
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.base import SaBase
from src.logging.logger import logger

converter = Converter()

converter.register_unstructure_hook(datetime, lambda dt: dt.isoformat())
converter.register_structure_hook(datetime, lambda ts, _: datetime.fromisoformat(ts))


def custom_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    error_msg = f"Type not serializable: {type(obj)}"
    raise TypeError(error_msg)


async def gather_results_with_timeout(
    aws: Iterable[Awaitable[Any]],
    *,
    timeout: float,
    timeout_message: str,
) -> list[Any]:
    tasks = list(aws)
    results = [None] * len(tasks)

    async def run_and_collect(index: int, a: Awaitable[Any]):
        results[index] = await a

    with anyio.move_on_after(timeout) as scope:
        async with anyio.create_task_group() as tg:
            for i, a in enumerate(tasks):
                tg.start_soon(run_and_collect, i, a)
    if scope.cancel_called:
        raise TimeoutError(timeout_message)
    return results


async def get_sa_entity(
    *,
    session: AsyncSession,
    sa_model_type: type[SaBase],
    filters: dict,
) -> Any:
    stmt = select(sa_model_type).filter_by(**filters)
    try:
        query = await session.execute(stmt)
        result = query.scalar_one()
    except NoResultFound as e:
        logger.info(f"{sa_model_type.__name__} not found: {e}")
        return None
    else:
        return result
