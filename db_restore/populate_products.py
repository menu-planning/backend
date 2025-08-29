from typing import Any
from anyio import run
from pydantic import PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.contexts.products_catalog.core.adapters.name_search import StrProcessor


class DBSettings(BaseSettings):
    source_postgres_server: str = "localhost"
    source_postgres_user: str = "user-dev"
    source_postgres_password: str = "development"
    source_postgres_port: int = 54323
    source_postgres_db: str = "old-db-dev"
    source_db_uri: PostgresDsn | None = None
    sa_pool_size: int = 5

    @field_validator("source_db_uri", mode="before")
    def assemble_async_source_db_connection(
        cls, v: str | None, info: ValidationInfo
    ) -> str | PostgresDsn:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=info.data.get("source_postgres_user"),
            password=info.data.get("source_postgres_password"),
            host=info.data.get("source_postgres_server"),
            port=info.data.get("source_postgres_port"),
            path=info.data.get("source_postgres_db"),
        )

    target_postgres_server: str = "localhost"
    target_postgres_user: str = "user-dev"
    target_postgres_password: str = "development"
    target_postgres_port: int = 54321
    target_postgres_db: str = "appdb-dev"
    target_db_uri: PostgresDsn | None = None

    @field_validator("target_db_uri", mode="before")
    def assemble_async_target_db_connection(
        cls, v: str | None, info: ValidationInfo
    ) -> str | PostgresDsn:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=info.data.get("target_postgres_user"),
            password=info.data.get("target_postgres_password"),
            host=info.data.get("target_postgres_server"),
            port=info.data.get("target_postgres_port"),
            path=info.data.get("target_postgres_db"),
        )


db_settings = DBSettings()

db_settings = DBSettings()

source_engine = create_async_engine(
    str(db_settings.source_db_uri),
    # echo=True,
    isolation_level="REPEATABLE READ",
    pool_size=db_settings.sa_pool_size,
)
target_engine = create_async_engine(
    str(db_settings.target_db_uri),
    echo=True,
    isolation_level="REPEATABLE READ",
    pool_size=db_settings.sa_pool_size,
)

source_session = async_sessionmaker(
    bind=source_engine, expire_on_commit=False, class_=AsyncSession
)()
target_session = async_sessionmaker(
    bind=target_engine, expire_on_commit=False, class_=AsyncSession
)()


async def get_table_columns(
    engine: AsyncEngine, table_name: str, schema_name: str
) -> list:
    async with engine.connect() as conn:
        # Using run_sync to run synchronous code inside an async block
        result = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_columns(
                table_name, schema=schema_name
            )
        )
        await conn.close()
    return list(result)


async def get_products():
    async with source_session as session:
        products = await session.execute(
            text("SELECT * FROM receipt_tracking.products")
        )
    return products


async def main() -> None:
    source_columns = await get_table_columns(
        source_engine, "products", "receipt_tracking"
    )
    target_columns = await get_table_columns(
        target_engine, "products", "products_catalog"
    )
    # for column in [col["name"] for col in target_columns]:
    #     if column not in [col["name"] for col in source_columns]:
    #         print(column)

    source_column_names = [i["name"] for i in source_columns]
    type_index = source_column_names.index("type")
    source_column_names.pop(type_index)
    products = await get_products()
    values = []
    for product in products:
        product = list(product)
        product.pop(type_index)
        d = {}
        for i in range(len(source_column_names)):
            d[source_column_names[i]] = product[i]
        values.append(d)
    source_column_names.extend(
        [
            "discarded",
            "version",
            "process_type",
            "is_food_houses_choice",
            "preprocessed_name",
        ]
    )

    insert_string_1 = f"({', '.join(source_column_names)})"
    insert_string_2 = "(" + ", ".join(f":{item}" for item in source_column_names) + ")"
    insert_stmt = f"INSERT INTO products_catalog.products {insert_string_1} VALUES {insert_string_2}"

    async with target_session as session:
        for value in values:
            await session.execute(
                text(insert_stmt),
                value
                | {
                    "discarded": False,
                    "version": 1,
                    "process_type": None,
                    "is_food_houses_choice": None,
                    "preprocessed_name": StrProcessor(value["name"]).output,
                },
            )
        await session.commit()


if __name__ == "__main__":
    run(main)
