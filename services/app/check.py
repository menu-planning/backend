import asyncio
import importlib
import sys

# import os
# import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from src.config.app_config import app_settings
from src.db.base import SaBase

modules = [
    "src.contexts.iam.adapters.ORM.sa_models",
    "src.contexts._receipt_tracker.adapters.ORM.sa_models",
    "src.contexts.products_catalog.adapters.ORM.sa_models",
    "src.contexts.food_tracker.adapters.ORM.sa_models",
    "src.contexts.recipes_catalog.adapters.ORM.sa_models",
    "src.contexts.shared_kernel.adapters.ORM.sa_models",
]


def check_circular_imports():
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"Successfully imported {module}")
        except Exception as e:
            print(f"Error importing {module}: {e}")


if __name__ == "__main__":
    check_circular_imports()
    sys.exit(0)
