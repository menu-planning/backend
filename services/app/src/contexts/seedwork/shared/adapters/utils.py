from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.db.base import SaBase


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
    postfix_on_domain_attribute: list[str] | None = None
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
