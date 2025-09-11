"""
Pytest fixtures for products_catalog integration tests

This conftest.py provides the core fixtures for integration testing of the
ProductRepo, following "Architecture Patterns with Python" principles:

- Real database connections (no mocks)
- Test behavior, not implementation
- Known DB states via fixtures
- Real DB errors and constraints
- Uses ORM models directly to bypass mapper logic

Key improvements:
- Independent database setup and fixtures
- Direct ORM model usage for bypassing domain model mappers
- Real database constraints and relationships for edge case testing
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.sa_models.product import (
    ProductSaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.source import (
    SourceSaModel,
)
from src.contexts.products_catalog.core.adapters.repositories.product_repository import (
    ProductRepo,
)
from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import (
    create_ORM_required_sources_for_products,
)

# Load integration database fixtures
pytest_plugins = ["tests.integration_conftest"]

# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.anyio, pytest.mark.integration]


@pytest.fixture
async def create_required_sources_orm(clean_async_pg_session: AsyncSession):
    """Create the source entities required by ORM product data factories with proper cleanup"""
    sources_data = create_ORM_required_sources_for_products()

    for source_data in sources_data:
        try:
            # Create SourceSaModel directly and add to session
            source_sa = SourceSaModel(**source_data)
            clean_async_pg_session.add(source_sa)
        except IntegrityError:
            # If source already exists, rollback and continue
            await clean_async_pg_session.rollback()
            # Try to get existing source instead
            existing_source = await clean_async_pg_session.get(
                SourceSaModel, source_data["id"]
            )
            if not existing_source:
                # If we can't get it, re-raise the error
                raise

    try:
        await clean_async_pg_session.commit()  # Use commit instead of flush to persist sources
    except IntegrityError:
        # If there are still integrity errors, rollback and continue
        await clean_async_pg_session.rollback()

    return sources_data


@pytest.fixture
async def product_repository_orm(
    clean_async_pg_session: AsyncSession, create_required_sources_orm
) -> ProductRepo:
    """Create ProductRepository instance for testing with required sources (ORM focused)"""
    return ProductRepo(db_session=clean_async_pg_session)


@pytest.fixture
async def test_session_with_sources(
    clean_async_pg_session: AsyncSession, create_required_sources_orm
):
    """Provide test session with required sources already created"""
    return clean_async_pg_session
