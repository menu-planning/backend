import uuid

import aio_pika
import pytest
import src.db.database as db
from sqlalchemy import text
from src.logging.logger import logger
from tenacity import RetryError
from tests.recipes_catalog.test_enums import MealPlanningTestEnum, MealTypeTestEnum


@pytest.fixture(scope="session", autouse=True)
async def populate_tags_table(anyio_backend, wait_for_postgres_to_come_up):
    async with db.async_db._engine.begin() as conn:
        try:
            values_list = []
            for meal_type in MealTypeTestEnum:
                values_list.append(
                    f"('Tipo de Refeição', '{meal_type}', 1, 'recipe')"
                )
            for plan in MealPlanningTestEnum:
                values_list.append(f"('Planejamento', '{plan.value}', 1, 'recipe')")
            # Join all value tuples with commas
            values_str = ",\n    ".join(values_list)
            raw_sql = f"""
                INSERT INTO shared_kernel.tags (key, value, author_id, type)
                VALUES 
                    {values_str}
                ON CONFLICT DO NOTHING;
            """
            await conn.execute(text(raw_sql))
            await conn.commit()
        except RetryError as e:
            logger.error(e)
            raise e
