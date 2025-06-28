"""
Comprehensive test suite for MenuRepository following established seedwork testing patterns.

The tests are grouped into logical classes mirroring those used for MealRepository:
1. TestMenuRepositoryCore – CRUD basics and soft–delete behaviour
2. TestMenuRepositoryFiltering – generic column filters
3. TestMenuRepositoryTagFiltering – complex tag logic (AND / OR / NOT-EXISTS)
4. TestMenuRepositoryErrorHandling – invalid queries & edge-cases
5. TestMenuRepositoryPerformance – basic performance baselines

All tests hit a REAL PostgreSQL database (no mocks) to ensure end-to-end correctness of the repository implementation.
"""

import pytest
import time
from typing import Dict, Any

from sqlalchemy.exc import IntegrityError

from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import (
    FilterValidationException,
)
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import EntityNotFoundException

from src.contexts.recipes_catalog.core.adapters.client.repositories.menu_repository import MenuRepo


# Import necessary SA models to ensure database tables exist
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import RecipeSaModel
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.client_sa_model import ClientSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import TagSaModel

from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.client.client_orm_factories import create_client_orm
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.menu.menu_orm_factories import create_menu_orm, create_menus_with_tags_orm
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.menu.parametrized_menu_scenarios import get_menu_filter_scenarios, get_menu_tag_filtering_scenarios
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.shared_orm_factories import create_menu_tag_orm

# Data-factories


pytestmark = [pytest.mark.anyio, pytest.mark.integration]

# =============================================================================
# TEST MENU REPOSITORY – CORE OPERATIONS
# =============================================================================


class TestMenuRepositoryCore:
    """Basic CRUD operations using ORM instances."""

    async def test_add_and_get_menu(self, menu_repository: MenuRepo, test_session, test_clients):
        # Given
        menu = create_menu_orm(description="Add/Get Menu Test")
        test_session.add(menu)
        await test_session.commit()

        # When
        retrieved = await menu_repository.get_sa_instance(menu.id)

        # Then
        assert retrieved is not None
        assert retrieved.id == menu.id
        assert retrieved.description == "Add/Get Menu Test"

    @pytest.mark.parametrize("menu_count", [1, 5, 15])
    async def test_query_all_menus(self, menu_repository: MenuRepo, test_session, test_clients, menu_count: int):
        # Given
        menus = [create_menu_orm(description=f"Query Menu {i}") for i in range(menu_count)]
        for m in menus:
            test_session.add(m)
        await test_session.commit()

        # When
        result = await menu_repository.query(_return_sa_instance=True)

        # Then
        assert len(result) >= menu_count
        result_ids = {m.id for m in result}
        for m in menus:
            assert m.id in result_ids

    async def test_update_menu(self, menu_repository: MenuRepo, test_session, test_clients):
        # Given
        menu = create_menu_orm(description="Original Description")
        test_session.add(menu)
        await test_session.commit()
        original_version = menu.version

        # When
        menu.description = "Updated Description"
        await test_session.commit()

        # Then
        updated = await menu_repository.get_sa_instance(menu.id)
        assert updated.description == "Updated Description"
        assert updated.version == original_version  # simple optimistic-lock check

    async def test_soft_delete_menu(self, menu_repository: MenuRepo, test_session, test_clients):
        # Given
        menu = create_menu_orm(description="Soft Delete Test")
        test_session.add(menu)
        await test_session.commit()

        # When – mark as discarded and commit
        retrieved = await menu_repository.get_sa_instance(menu.id)
        retrieved.discarded = True
        await test_session.commit()

        # Then – regular get_sa_instance should now raise
        with pytest.raises(EntityNotFoundException):
            await menu_repository.get_sa_instance(menu.id)

    async def test_query_by_list_of_ids(self, menu_repository: MenuRepo, test_session, test_clients):
        # Given
        m1 = create_menu_orm(description="Menu 1")
        m2 = create_menu_orm(description="Menu 2")
        m3 = create_menu_orm(description="Menu 3")
        test_session.add_all([m1, m2, m3])
        await test_session.commit()

        # When
        result = await menu_repository.query(filter={"id": [m1.id, m2.id]}, _return_sa_instance=True)

        # Then
        result_ids = {m.id for m in result}
        assert m1.id in result_ids
        assert m2.id in result_ids
        assert m3.id not in result_ids
        assert len(result) == 2


# =============================================================================
# TEST MENU REPOSITORY – FILTERS
# =============================================================================


class TestMenuRepositoryFiltering:
    """Filter operations based on predefined scenarios."""

    @pytest.mark.parametrize("scenario", get_menu_filter_scenarios())
    async def test_filtering_scenarios(self, menu_repository: MenuRepo, test_session, test_clients, scenario: Dict[str, Any]):
        # Given
        # Handle scenarios that require specific client IDs by creating them first
        if "client_id" in scenario["menu_kwargs"] or "client_id" in scenario["filter"]:
                        
            # Extract client ID from scenario
            client_id = scenario["menu_kwargs"].get("client_id") or scenario["filter"].get("client_id")
            if client_id:
                # Create the required client
                required_client = create_client_orm(id=client_id)
                test_session.add(required_client)
                await test_session.commit()
        
        menu = create_menu_orm(**scenario["menu_kwargs"])
        test_session.add(menu)
        await test_session.commit()

        # When
        result = await menu_repository.query(filter=scenario["filter"], _return_sa_instance=True)

        # Then
        ids = {m.id for m in result}
        if scenario["should_match"]:
            assert menu.id in ids, f"Scenario {scenario['scenario_id']} failed – expected match"
        else:
            assert menu.id not in ids, f"Scenario {scenario['scenario_id']} failed – expected no match"

    async def test_author_and_client_filter(self, menu_repository: MenuRepo, test_session, test_clients):
        # Given
        # Use valid client IDs from test_clients fixture
        client_x_id = test_clients[0].id  # client_001
        client_y_id = test_clients[1].id  # client_002
        
        target = create_menu_orm(author_id="author_target", client_id=client_x_id)
        wrong_author = create_menu_orm(author_id="other", client_id=client_x_id)
        wrong_client = create_menu_orm(author_id="author_target", client_id=client_y_id)
        test_session.add_all([target, wrong_author, wrong_client])
        await test_session.commit()

        # When
        result = await menu_repository.query(filter={"author_id": "author_target", "client_id": client_x_id}, _return_sa_instance=True)

        # Then
        ids = {m.id for m in result}
        assert target.id in ids
        assert wrong_author.id not in ids
        assert wrong_client.id not in ids
        assert len(result) == 1


# =============================================================================
# TEST MENU REPOSITORY – TAG FILTERING
# =============================================================================


class TestMenuRepositoryTagFiltering:
    """AND / OR / NOT-EXISTS logic for tags."""

    @pytest.mark.parametrize("scenario", get_menu_tag_filtering_scenarios())
    async def test_tag_filtering_scenarios(self, menu_repository: MenuRepo, test_session, test_clients, scenario: Dict[str, Any]):
        # Given
        tags = [create_menu_tag_orm(**t) for t in scenario["menu_tags"]]
        menu = create_menu_orm(description=f"{scenario['scenario_id']} menu", tags=tags)
        test_session.add(menu)
        await test_session.commit()

        # When
        result = await menu_repository.query(filter={"tags": scenario["filter_tags"]}, _return_sa_instance=True)

        # Then
        ids = {m.id for m in result}
        if scenario["should_match"]:
            assert menu.id in ids
        else:
            assert menu.id not in ids

    async def test_tags_not_exists(self, menu_repository: MenuRepo, test_session, test_clients):
        # Given
        exclude_tag = create_menu_tag_orm(key="event", value="wedding", author_id="auth1", type="menu")
        menu_excluded = create_menu_orm(description="Excluded menu", tags=[exclude_tag])
        menu_included = create_menu_orm(description="Included menu", tags=[])
        test_session.add_all([menu_excluded, menu_included])
        await test_session.commit()

        # When
        result = await menu_repository.query(filter={"tags_not_exists": [("event", "wedding", "auth1")]}, _return_sa_instance=True)

        # Then
        ids = {m.id for m in result}
        assert menu_included.id in ids
        assert menu_excluded.id not in ids

    async def test_tag_dissociation_and_re_add(self, menu_repository: MenuRepo, test_session, test_clients):
        # Given
        tag = create_menu_tag_orm(key="season", value="summer", author_id="auth1", type="menu")
        menu = create_menu_orm(description="Menu with tag", tags=[tag])
        test_session.add(menu)
        await test_session.commit()

        # Confirm menu is retrievable by tag filter
        initial = await menu_repository.query(filter={"tags": [("season", "summer", "auth1")]}, _return_sa_instance=True)
        assert menu.id in {m.id for m in initial}

        # When – remove all tags
        sa_instance = await menu_repository.get_sa_instance(menu.id)
        sa_instance.tags.clear()
        await test_session.commit()

        # Then – tag filter should no longer find menu
        after_removal = await menu_repository.query(filter={"tags": [("season", "summer", "auth1")]}, _return_sa_instance=True)
        assert menu.id not in {m.id for m in after_removal}

        # But menu still exists in DB
        still_exists = await menu_repository.get_sa_instance(menu.id)
        assert still_exists is not None and len(still_exists.tags) == 0

        # When – add new tag
        new_tag = create_menu_tag_orm(key="season", value="winter", author_id="auth1", type="menu")
        still_exists.tags.append(new_tag)
        await test_session.commit()

        # Then – new tag filter should find it
        final = await menu_repository.query(filter={"tags": [("season", "winter", "auth1")]}, _return_sa_instance=True)
        assert menu.id in {m.id for m in final}


# =============================================================================
# TEST MENU REPOSITORY – ERROR HANDLING
# =============================================================================


class TestMenuRepositoryErrorHandling:

    async def test_get_nonexistent_menu(self, menu_repository: MenuRepo):
        with pytest.raises(EntityNotFoundException):
            await menu_repository.get_sa_instance("nonexistent_menu")

    async def test_invalid_filter_parameters(self, menu_repository: MenuRepo):
        with pytest.raises(FilterValidationException):
            await menu_repository.query(filter={"unknown_field": "value"})

    async def test_constraint_violation_on_duplicate_tag(self, menu_repository: MenuRepo, test_session, test_clients):
        # Given
        tag = create_menu_tag_orm(key="type", value="weekly", author_id="auth1", type="menu")
        m1 = create_menu_orm(description="Menu 1", tags=[tag])
        test_session.add(m1)
        await test_session.commit()

        duplicate_tag = create_menu_tag_orm(key="type", value="weekly", author_id="auth1", type="menu")
        m2 = create_menu_orm(description="Menu 2", tags=[duplicate_tag])
        test_session.add(m2)

        # Then
        with pytest.raises(IntegrityError):
            await test_session.commit()


# =============================================================================
# TEST MENU REPOSITORY – PERFORMANCE
# =============================================================================


_PERFORMANCE_SCENARIOS = [
    {
        "scenario_id": "basic_query_small",
        "entity_count": 30,
        "operation": "basic_query",
        "max_duration_seconds": 1.0,
    },
    {
        "scenario_id": "tag_filtering_medium",
        "entity_count": 50,
        "operation": "tag_filtering",
        "max_duration_seconds": 1.5,
    },
    {
        "scenario_id": "complex_query_large",
        "entity_count": 100,
        "operation": "complex_query",
        "max_duration_seconds": 3.0,
    },
]


class TestMenuRepositoryPerformance:

    @pytest.mark.parametrize("scenario", _PERFORMANCE_SCENARIOS)
    async def test_query_performance(self, menu_repository: MenuRepo, test_session, test_clients, scenario: Dict[str, Any]):
        # Prepare dataset using ORM models
        menus = create_menus_with_tags_orm(
            count=scenario["entity_count"],
            tags_per_menu=2 if scenario["operation"] != "basic_query" else 0,
            meals_per_menu=0,
        )
        test_session.add_all(menus)
        await test_session.commit()

        # Execute and time the operation
        start = time.perf_counter()
        if scenario["operation"] == "basic_query":
            await menu_repository.query(_return_sa_instance=True)
        elif scenario["operation"] == "tag_filtering":
            # use first tag from dataset for filtering
            first_tag = menus[0].tags[0] if menus and menus[0].tags else None
            filter_kwargs = {"tags": [(first_tag.key, first_tag.value, first_tag.author_id)]} if first_tag else {}
            await menu_repository.query(filter=filter_kwargs, _return_sa_instance=True)
        elif scenario["operation"] == "complex_query":
            await menu_repository.query(filter={"author_id": "author_1", "client_id": test_clients[0].id}, _return_sa_instance=True)
        else:
            pytest.skip(f"Unsupported operation: {scenario['operation']}")
        duration = time.perf_counter() - start

        assert duration <= scenario["max_duration_seconds"], (
            f"Performance scenario '{scenario['scenario_id']}' took {duration:.3f}s – "
            f"expected <= {scenario['max_duration_seconds']}s"
        )

    async def test_bulk_insert_performance(self, menu_repository: MenuRepo, test_session, test_clients):
        menu_count = 120
        start = time.perf_counter()
        menus = [create_menu_orm(description=f"Bulk Menu {i}") for i in range(menu_count)]
        test_session.add_all(menus)
        await test_session.commit()
        duration = time.perf_counter() - start
        max_total = 6.0  # seconds
        per_entity_ms = (duration * 1000) / menu_count
        assert duration <= max_total, f"Bulk insert took {duration:.3f}s – expected <= {max_total}s"
        assert per_entity_ms <= 60, f"Per-entity time {per_entity_ms:.2f}ms – expected <= 60ms"

    async def test_complex_query_performance(self, menu_repository: MenuRepo, test_session, test_clients):
        # Create 60 menus with tags for a moderately heavy query
        menus = create_menus_with_tags_orm(count=60, tags_per_menu=3, meals_per_menu=0)
        test_session.add_all(menus)
        await test_session.commit()

        start = time.perf_counter()
        await menu_repository.query(filter={"author_id": "author_1", "tags": [("type", "weekly", "author_1")]}, _return_sa_instance=True)
        duration = time.perf_counter() - start
        assert duration <= 2.0, f"Complex query took {duration:.3f}s – expected <= 2.0s" 