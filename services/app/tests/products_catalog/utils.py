import random
import traceback
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.shared.adapters.name_search import StrProcessor
from tests.products_catalog.random_refs import DietTypeNames, SourceNames, random_attr


async def insert_food_product(
    session: AsyncSession,
    id: str,
    source: str | None = None,
    name: str | None = None,
    barcode: str | None = "",
    version: int = 1,
):
    if not source:
        source = random.choice([i.value for i in SourceNames if i.value != "auto"])
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
        is_food, barcode, discarded, version) VALUES (:id, :source_id, :name, 
        :preprocessed_name, :is_food, :barcode, :discarded, :version) 
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
    }
    await session.execute(text(stmt), dict)


async def insert_diet_type(session: AsyncSession, id: str, version: int = 1):
    if not id:
        id = random.choice([i.value for i in DietTypeNames])
    stmt = """INSERT INTO shared_kernel.diet_types (id, name, author_id,
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
    try:
        await session.execute(text(stmt), dict)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        pass


async def add_diet_type_to_product(
    session: AsyncSession, product_id: str, diet_type_id: str
):
    stmt = """INSERT INTO products_catalog.products_diet_types_association (product_id, diet_type_id) 
        VALUES (:product_id, :diet_type_id) ON CONFLICT (product_id, diet_type_id) DO NOTHING"""
    dict = {
        "product_id": product_id,
        "diet_type_id": diet_type_id,
    }
    await session.execute(text(stmt), dict)


async def clean_db(session: AsyncSession):
    await session.execute(
        text("DELETE FROM products_catalog.products_diet_types_association")
    )
    await session.execute(text("DELETE FROM products_catalog.products"))
    await session.execute(text("DELETE FROM products_catalog.sources"))
    await session.execute(text("DELETE FROM shared_kernel.diet_types"))
    await session.commit()
