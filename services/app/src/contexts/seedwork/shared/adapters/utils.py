from typing import Any, Awaitable, Iterable, List

import anyio
from sqlalchemy import Table, inspect, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.associations import (
    recipes_tags_association,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.recipe import (
    RecipeSaModel,
)
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag import TagSaModel
from src.db.base import SaBase
from src.logging.logger import logger


def get_entity_id(instance: SaBase | Entity) -> str | None:
    return getattr(instance, "id", getattr(instance, "name", None))


def get_type_of_related_model(
    sa_instance: SaBase, relationship_attr: str
) -> type[SaBase]:
    # Use SQLAlchemy's inspection system to find the related model class
    mapper = inspect(sa_instance.__class__)
    return mapper.relationships[relationship_attr].mapper.class_


def check_table_exists_sync(connection, table_name, schema=None) -> bool:
    inspector = inspect(connection)
    return inspector.has_table(table_name, schema=schema)


async def check_table_exists(
    session: AsyncSession, table_name: str, schema: str = None
) -> bool:
    async with session.bind.connect() as connection:
        return await connection.run_sync(check_table_exists_sync, table_name, schema)


def map_sa_attr_name_to_domain_attr_name(
    *,
    sa_instance: SaBase,
    domain_obj: Entity,
    postfix_on_domain_attribute: list[str] | None = None,
):
    sa_instance_inspector = inspect(sa_instance.__class__)
    relationships = sa_instance_inspector.relationships
    sa_attr_name_to_domain_attr_name = {}
    if postfix_on_domain_attribute is None:
        postfix_on_domain_attribute = []
    for sa_attr_name in relationships.keys():
        for postfix in postfix_on_domain_attribute:
            if getattr(domain_obj, sa_attr_name + postfix, None):
                sa_attr_name_to_domain_attr_name[sa_attr_name] = sa_attr_name + postfix
    return sa_attr_name_to_domain_attr_name


import anyio
from typing import Any, Awaitable, Iterable, List

async def gather_results_with_timeout(
    aws: Iterable[Awaitable[Any]],
    *,
    timeout: float,
    timeout_message: str,
) -> List[Any]:
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
    sa_model_type: SaBase,
    filter: dict,
) -> SaBase | None:
    stmt = select(sa_model_type).filter_by(**filter)
    try:
        query = await session.execute(stmt)
        result = query.scalar_one()
    except NoResultFound as e:
        logger.info(f"Entity not found: {e}")
        return None
    else:
        return result


async def delete_sa_entity(
    *,
    session: AsyncSession,
    sa_model_type: SaBase,
    filter: dict,
) -> None:
    entity = await get_sa_entity(session=session, sa_model_type=sa_model_type, filter=filter)
    if entity:
        await session.delete(entity)
        await session.commit()
    else:
        logger.info(f"Entity not found for deletion: {filter}")


def get_inclusion_subcondition(
    sa_model_type: type[SaBase], association_table: Table, key, values
):
    """
    Return an EXISTS subquery that ensures a recipe has
    a Tag with (key=the_key) and (value in values).
    Because we allow 'OR' among values, the recipe must
    have at least one matching value for that key.
    """
    # For key=allergen and values=['peanut','gluten'], we do TagSaModel.value.in_(...)
    subq = (
        select(sa_model_type.id)
        .join(association_table, sa_model_type.id == association_table.c.recipe_id)
        .join(TagSaModel, TagSaModel.id == recipes_tags_association.c.tag_id)
        .where(
            TagSaModel.key == key,
            TagSaModel.value.in_(values),
            RecipeSaModel.id == RecipeSaModel.id,  # We'll correlate later
        )
        .exists()
    )
    return subq
