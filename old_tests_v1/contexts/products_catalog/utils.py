import random
import traceback
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

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
