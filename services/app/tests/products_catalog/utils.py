import random
import traceback
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.shared.adapters.name_search import StrProcessor
from tests.products_catalog.random_refs import SourceTestEnum, random_attr

async def insert_food_product(
    session: AsyncSession,
    id: str,
    source: str | None = None,
    name: str | None = None,
    barcode: str | None = "",
    version: int = 1,
):
    if not source:
        source = random.choice([i.value for i in SourceTestEnum if i.value != "auto"])
    source_stmt = """INSERT INTO products_catalog.sources (id, name, author_id,
        description, created_at, updated_at, discarded, version) 
        VALUES (:id, :name, :author_id, :description, :created_at, :updated_at, 
        :discarded, :version) ON CONFLICT (id) DO NOTHING"""
    source_dict = {
        "id": source,
        "name": source,
        "author_id": "author_id",
        "description": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "discarded": False,
        "version": 1,
    }
    try:
        await session.execute(text(source_stmt), source_dict)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        pass
    stmt = """INSERT INTO products_catalog.products (id, source_id, name, preprocessed_name,
        is_food, barcode, discarded, version, shopping_name, store_department_name,
        recommended_brands_and_products, edible_yield, kg_per_unit, nutrition_group,
        cooking_factor, conservation_days, substitutes) VALUES (:id, :source_id, :name, 
        :preprocessed_name, :is_food, :barcode, :discarded, :version, :shopping_name, 
        :store_department_name, :recommended_brands_and_products, :edible_yield, 
        :kg_per_unit, :nutrition_group, :cooking_factor, :conservation_days, :substitutes) 
        ON CONFLICT (id) DO NOTHING"""
    dict = {
        "id": id,
        "name": random_attr("name") if not name else name,
        "preprocessed_name": (StrProcessor(name).output if name else name),
        "source_id": source,
        "is_food": True,
        "barcode": None if isinstance(barcode, str) and not barcode else barcode,
        "discarded": False,
        "version": version,
        "shopping_name": random_attr("shopping_name"),
        "store_department_name": random_attr("store_department_name"),
        "recommended_brands_and_products": random_attr("recommended_brands_and_products"),
        "edible_yield": random.uniform(0, 1),
        "kg_per_unit": random.uniform(1, 5),
        "nutrition_group": random_attr("nutrition_group"),
        "cooking_factor": random.uniform(0.5, 4),
        "conservation_days": random.randint(1, 100),
        "substitutes": random_attr("substitutes"),
    }
    await session.execute(text(stmt), dict)


async def insert_brand(session: AsyncSession, id: str, version: int = 1):
    stmt = """INSERT INTO products_catalog.brands (id, name, author_id,
        description, created_at, updated_at, discarded, version) 
        VALUES (:id, :name, :author_id, :description, :created_at, :updated_at, 
        :discarded, :version) ON CONFLICT (id) DO NOTHING"""
    dict = {
        "id": id,
        "name": id,
        "author_id": "author_id",
        "description": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "discarded": False,
        "version": version,
    }
    await session.execute(text(stmt), dict)


async def insert_category(session: AsyncSession, id: str, version: int = 1):
    stmt = """INSERT INTO products_catalog.classifications (id, name, author_id,
        description, created_at, updated_at, discarded, version, type) 
        VALUES (:id, :name, :author_id, :description, :created_at, :updated_at, 
        :discarded, :version, :type) ON CONFLICT (id) DO NOTHING"""
    dict = {
        "id": id,
        "name": id,
        "author_id": "author_id",
        "description": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "discarded": False,
        "version": version,
        "type": "category",
    }
    await session.execute(text(stmt), dict)


async def insert_parent_category(session: AsyncSession, id: str, version: int = 1):
    stmt = """INSERT INTO products_catalog.classifications (id, name, author_id,
        description, created_at, updated_at, discarded, version, type) 
        VALUES (:id, :name, :author_id, :description, :created_at, :updated_at, 
        :discarded, :version, :type) ON CONFLICT (id) DO NOTHING"""
    dict = {
        "id": id,
        "name": id,
        "author_id": "author_id",
        "description": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "discarded": False,
        "version": version,
        "type": "parent_category",
    }
    await session.execute(text(stmt), dict)


async def insert_food_group(session: AsyncSession, id: str, version: int = 1):
    stmt = """INSERT INTO products_catalog.classifications (id, name, author_id,
        description, created_at, updated_at, discarded, version, type) 
        VALUES (:id, :name, :author_id, :description, :created_at, :updated_at, 
        :discarded, :version, :type) ON CONFLICT (id) DO NOTHING"""
    dict = {
        "id": id,
        "name": id,
        "author_id": "author_id",
        "description": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "discarded": False,
        "version": version,
        "type": "food_group",
    }
    await session.execute(text(stmt), dict)


async def insert_process_type(session: AsyncSession, id: str, version: int = 1):
    stmt = """INSERT INTO products_catalog.classifications (id, name, author_id,
        description, created_at, updated_at, discarded, version, type) 
        VALUES (:id, :name, :author_id, :description, :created_at, :updated_at, 
        :discarded, :version, :type) ON CONFLICT (id) DO NOTHING"""
    dict = {
        "id": id,
        "name": id,
        "author_id": "author_id",
        "description": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "discarded": False,
        "version": version,
        "type": "process_type",
    }
    await session.execute(text(stmt), dict)
