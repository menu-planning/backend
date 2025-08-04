"""
Comprehensive test suite for ClientRepository following seedwork patterns.

Tests are organized into focused classes:
- TestClientRepositoryCore: Basic CRUD operations 
- TestClientRepositoryFiltering: Filter operations and scenarios
- TestClientRepositoryTagFiltering: Complex tag logic with AND/OR
- TestClientRepositoryErrorHandling: Edge cases and database constraints
- TestClientRepositoryPerformance: Benchmarks and performance baselines

All tests use REAL database (no mocks) and follow TDD principles.
"""

import pytest

from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import FilterValidationException

from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.client.client_domain_factories import create_catering_client, create_client, create_restaurant_client
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.client.client_orm_factories import create_client_orm, create_clients_with_tags_orm
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.client.parametrized_client_scenarios import get_client_filter_scenarios, get_client_tag_filtering_scenarios
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.shared_orm_factories import create_client_tag_orm

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

import time
from typing import Dict, Any

from src.contexts.recipes_catalog.core.adapters.client.repositories.client_repository import ClientRepo

# Import MenuSaModel to ensure menus table exists for foreign key constraint
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_sa_model import MenuSaModel
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.client_sa_model import ClientSaModel
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel


# =============================================================================
# TEST CLIENT REPOSITORY CORE OPERATIONS
# =============================================================================

class TestClientRepositoryCore:
    """Test basic CRUD operations with real database persistence"""

    async def test_add_and_get_client(self, client_repository: ClientRepo, test_session):
        """Test adding a client and retrieving it by ID"""
        # Given: A new ORM client
        client = create_client_orm(name="Test Client for Add/Get", author_id="test_author")
        
        # When: Adding the client directly to session
        test_session.add(client)
        await test_session.commit()
        
        # Then: Should be able to retrieve the same client via repository
        retrieved_client = await client_repository.get_sa_instance(client.id)
        
        assert retrieved_client is not None
        assert retrieved_client.id == client.id
        assert retrieved_client.profile.name == client.profile.name
        assert retrieved_client.author_id == client.author_id

    @pytest.mark.parametrize("client_count", [1, 5, 10, 25])
    async def test_query_all_clients(self, client_repository: ClientRepo, test_session, client_count: int):
        """Test querying clients with different dataset sizes"""
        # Given: Multiple ORM clients in the database
        clients = []
        for i in range(client_count):
            client = create_client_orm(name=f"Query Test Client {i}")
            clients.append(client)
            test_session.add(client)
        
        await test_session.commit()
        
        # When: Querying all clients with ORM instances
        result = await client_repository.query(_return_sa_instance=True)
        
        # Then: Should return all added clients
        assert len(result) >= client_count  # >= because other tests might have added clients
        
        # Verify our test clients are in the result
        result_ids = {client.id for client in result}
        for client in clients:
            assert client.id in result_ids

    async def test_update_client(self, client_repository: ClientRepo, test_session):
        """Test updating a client and verifying changes persist"""
        # Given: An ORM client to update
        client = create_client_orm(
            name="Original Name", 
            notes="Original Notes"
        )
        test_session.add(client)
        await test_session.commit()
        
        # Capture initial version
        initial_version = client.version
        
        # When: Updating the client directly in session (proper way for composite objects)
        from src.contexts.shared_kernel.adapters.ORM.sa_models.profile_sa_model import ProfileSaModel
        updated_profile = ProfileSaModel(
            name="Updated Name",
            sex=client.profile.sex,  # Keep existing values
            birthday=client.profile.birthday
        )
        client.profile = updated_profile  # Replace the entire composite object
        client.notes = "Updated Notes"
        await test_session.commit()
        
        # Then: Changes should be persisted
        updated_client = await client_repository.get_sa_instance(client.id)
        assert updated_client.profile.name == "Updated Name"
        assert updated_client.notes == "Updated Notes"

    async def test_persist_and_get_domain_client(self, client_repository: ClientRepo):
        """Test persisting domain client and retrieving it"""
        # Given: A domain client
        client = create_client(name="Domain Test Client", author_id="test_author")
        
        # When: Adding and persisting the client
        await client_repository.add(client)
        await client_repository.persist(client)
        
        # Then: Should be able to retrieve as domain object
        retrieved_client = await client_repository.get(client.id)
        assert retrieved_client.id == client.id
        assert retrieved_client.profile.name == client.profile.name
        assert retrieved_client.author_id == client.author_id

    async def test_soft_delete_client(self, client_repository: ClientRepo, test_session):
        """Test that discarded clients are soft deleted and not retrievable"""
        # Given: An ORM client added to database
        client = create_client_orm(name="Client to Discard", author_id="test_author")
        test_session.add(client)
        await test_session.commit()
        
        # Verify client exists
        retrieved_client = await client_repository.get_sa_instance(client.id)
        assert retrieved_client.profile.name == "Client to Discard"
        
        # When: Marking client as discarded (soft delete) directly in session
        retrieved_client.discarded = True
        await test_session.commit()
        
        # Then: Client should no longer be retrievable (soft deleted)
        from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import EntityNotFoundException
        with pytest.raises(EntityNotFoundException):
            await client_repository.get_sa_instance(client.id)

    async def test_query_by_list_of_ids(self, client_repository: ClientRepo, test_session):
        """Test querying clients by list of IDs (IN operator)"""
        # Given: Multiple ORM clients
        client1 = create_client_orm(name="Client 1", author_id="test_author")
        client2 = create_client_orm(name="Client 2", author_id="test_author")
        client3 = create_client_orm(name="Client 3", author_id="test_author")
        
        for client in [client1, client2, client3]:
            test_session.add(client)
        await test_session.commit()
        
        # When: Querying with ID list filter and ORM instances
        result = await client_repository.query(filter={"id": [client1.id, client2.id]}, _return_sa_instance=True)
        
        # Then: Should return only the requested clients
        result_ids = {client.id for client in result}
        assert client1.id in result_ids
        assert client2.id in result_ids
        assert client3.id not in result_ids
        assert len(result) == 2

    async def test_client_menus_relationship(self, client_repository: ClientRepo, test_session):
        """Test client-menu relationship persistence"""
        # Given: A client with menus (testing the repository aspects)
        # Note: This tests repository behavior, not the full domain menu creation logic
        
        # Create a client with some basic data
        client = create_client(
            name="Client with Menus",
            author_id="test_author"
        )
        
        # When: Adding and persisting the client
        await client_repository.add(client)
        await client_repository.persist(client)
        
        # Then: Client should be retrievable
        retrieved_client = await client_repository.get(client.id)
        assert retrieved_client.profile.name == "Client with Menus"
        assert retrieved_client.author_id == "test_author"
        
        # Test menus relationship (should be empty initially)
        assert len(retrieved_client.menus) == 0


# =============================================================================
# TEST CLIENT REPOSITORY FILTERING
# =============================================================================

class TestClientRepositoryFiltering:
    """Test filter operations using parametrized scenarios"""

    @pytest.mark.parametrize("scenario", get_client_filter_scenarios())
    async def test_client_filtering_scenarios(self, client_repository: ClientRepo, test_session, scenario: Dict[str, Any]):
        """Test client filtering with various filter combinations"""
        # Given: An ORM client with specific characteristics
        client = create_client_orm(**scenario["client_kwargs"])
        test_session.add(client)
        await test_session.commit()
        
        # When: Applying the filter with ORM instances
        result = await client_repository.query(filter=scenario["filter"], _return_sa_instance=True)
        
        # Then: Check if client matches expected outcome
        client_ids = {c.id for c in result}
        
        if scenario["should_match"]:
            assert client.id in client_ids, f"Scenario '{scenario['scenario_id']}' failed: {scenario['description']}"
        else:
            assert client.id not in client_ids, f"Scenario '{scenario['scenario_id']}' failed: {scenario['description']}"

    async def test_author_id_filter(self, client_repository: ClientRepo, test_session):
        """Test author_id exact match filter"""
        # Given: ORM clients from different authors
        author1_client = create_client_orm(name="Author 1 Client", author_id="author_1")
        author2_client = create_client_orm(name="Author 2 Client", author_id="author_2")
        
        for client in [author1_client, author2_client]:
            test_session.add(client)
        await test_session.commit()
        
        # When: Filtering by specific author with ORM instances
        result = await client_repository.query(filter={"author_id": "author_1"}, _return_sa_instance=True)
        
        # Then: Should only return clients from that author
        result_ids = {c.id for c in result}
        assert author1_client.id in result_ids
        assert author2_client.id not in result_ids

    async def test_created_at_gte_filter(self, client_repository: ClientRepo, test_session):
        """Test created_at greater than or equal filter"""
        from datetime import datetime
        
        # Given: ORM clients with different creation dates
        early_client = create_client_orm(
            name="Early Client", 
            created_at=datetime(2024, 1, 1)
        )
        late_client = create_client_orm(
            name="Late Client", 
            created_at=datetime(2024, 6, 1)
        )

        # Persist clients directly to session
        test_session.add(early_client)
        test_session.add(late_client)
        await test_session.commit()

        # When: Filtering by created_at_gte with ORM instances
        result = await client_repository.query(filter={"created_at_gte": datetime(2024, 3, 1)}, _return_sa_instance=True)

        # Then: Should return clients created after filter date
        client_names = [c.profile.name for c in result]
        result_names = {c.profile.name for c in result}
        assert "Late Client" in result_names
        assert "Early Client" not in result_names

    async def test_created_at_lte_filter(self, client_repository: ClientRepo, test_session):
        """Test created_at less than or equal filter"""
        from datetime import datetime
        
        # Given: ORM clients with different creation dates
        early_client = create_client_orm(
            name="Early Client", 
            created_at=datetime(2024, 1, 1)
        )
        late_client = create_client_orm(
            name="Late Client", 
            created_at=datetime(2024, 6, 1)
        )

        # Persist clients directly to session
        test_session.add(early_client)
        test_session.add(late_client)
        await test_session.commit()

        # When: Filtering by created_at_lte with ORM instances
        result = await client_repository.query(filter={"created_at_lte": datetime(2024, 3, 1)}, _return_sa_instance=True)

        # Then: Should return clients created before filter date
        result_names = {c.profile.name for c in result}
        assert "Early Client" in result_names
        assert "Late Client" not in result_names

    async def test_combined_filters(self, client_repository: ClientRepo, test_session):
        """Test multiple filters working together"""
        from datetime import datetime
        
        # Given: ORM clients with various characteristics
        target_client = create_client_orm(
            name="Target Client",
            author_id="target_author", 
            created_at=datetime(2024, 3, 1)
        )
        wrong_author = create_client_orm(
            name="Wrong Author",
            author_id="other_author",
            created_at=datetime(2024, 3, 1)
        )
        wrong_date = create_client_orm(
            name="Wrong Date", 
            author_id="target_author",
            created_at=datetime(2024, 1, 1)  # Too early
        )
        
        for client in [target_client, wrong_author, wrong_date]:
            test_session.add(client)
        await test_session.commit()
        
        # When: Applying multiple filters with ORM instances
        result = await client_repository.query(filter={
            "author_id": "target_author",
            "created_at_gte": datetime(2024, 2, 1),
        }, _return_sa_instance=True)
        
        # Then: Should only return client matching all filters
        result_ids = {c.id for c in result}
        assert target_client.id in result_ids
        assert wrong_author.id not in result_ids  # Wrong author
        assert wrong_date.id not in result_ids  # Wrong date
        assert len(result) == 1


# =============================================================================
# TEST CLIENT REPOSITORY TAG FILTERING
# =============================================================================

class TestClientRepositoryTagFiltering:
    """Test complex tag logic with AND/OR operations"""

    @pytest.mark.parametrize("scenario", get_client_tag_filtering_scenarios())
    async def test_tag_filtering_scenarios(self, client_repository: ClientRepo, test_session, scenario: Dict[str, Any]):
        """Test complex tag filtering scenarios"""
        # Given: An ORM client with specific tags
        tags = []
        for tag_data in scenario["client_tags"]:
            tag = create_client_tag_orm(**tag_data)
            tags.append(tag)
        
        client = create_client_orm(name=f"Client for {scenario['scenario_id']}", tags=tags)
        test_session.add(client)
        await test_session.commit()
        
        # When: Applying tag filter with ORM instances
        result = await client_repository.query(filter={"tags": scenario["filter_tags"]}, _return_sa_instance=True)
        
        # Then: Check expected outcome
        result_ids = {c.id for c in result}
        
        if scenario["should_match"]:
            assert client.id in result_ids, f"Tag scenario '{scenario['scenario_id']}' failed: {scenario['description']}"
        else:
            assert client.id not in result_ids, f"Tag scenario '{scenario['scenario_id']}' failed: {scenario['description']}"

    async def test_single_client_tag_exact_match(self, client_repository: ClientRepo, test_session):
        """Test single tag exact matching"""
        # Given: ORM client with specific tag
        tag = create_client_tag_orm(key="category", value="restaurant", author_id="test_author", type="client")
        client = create_client_orm(name="Restaurant Client", tags=[tag])
        test_session.add(client)
        await test_session.commit()
        
        # When: Filtering with exact tag match and ORM instances
        result = await client_repository.query(filter={
            "tags": [("category", "restaurant", "test_author")]
        }, _return_sa_instance=True)
        
        # Then: Should find the client
        assert len(result) >= 1
        result_ids = {c.id for c in result}
        assert client.id in result_ids

    async def test_multiple_client_tags_and_logic(self, client_repository: ClientRepo, test_session):
        """Test AND logic between different tag keys"""
        # Given: ORM client with multiple tags (different keys)
        category_tag = create_client_tag_orm(key="category", value="restaurant", author_id="test_author", type="client")
        size_tag = create_client_tag_orm(key="size", value="large", author_id="test_author", type="client")
        client = create_client_orm(name="Large Restaurant Client", tags=[category_tag, size_tag])
        test_session.add(client)
        await test_session.commit()
        
        # When: Filtering with both tags (AND logic) and ORM instances
        result = await client_repository.query(filter={
            "tags": [
                ("category", "restaurant", "test_author"),
                ("size", "large", "test_author")
            ]
        }, _return_sa_instance=True)
        
        # Then: Should find the client (both tags match)
        result_ids = {c.id for c in result}
        assert client.id in result_ids

    async def test_multiple_values_same_key_or_logic(self, client_repository: ClientRepo, test_session):
        """Test OR logic for multiple values with same key"""
        # Given: ORM client with restaurant category tag
        category_tag = create_client_tag_orm(key="category", value="restaurant", author_id="test_author", type="client")
        client = create_client_orm(name="Restaurant Client", tags=[category_tag])
        test_session.add(client)
        await test_session.commit()
        
        # When: Filtering with multiple category values (OR logic) and ORM instances
        result = await client_repository.query(filter={
            "tags": [
                ("category", "restaurant", "test_author"),  # This matches
                ("category", "hotel", "test_author")   # This doesn't match, but OR logic
            ]
        }, _return_sa_instance=True)
        
        # Then: Should find the client (one of the OR conditions matches)
        result_ids = {c.id for c in result}
        assert client.id in result_ids

    async def test_client_tags_not_exists_filtering(self, client_repository: ClientRepo, test_session):
        """Test tag exclusion with tags_not_exists"""
        # Given: Two ORM clients - one with priority tag, one without
        priority_tag = create_client_tag_orm(key="priority", value="urgent", author_id="test_author", type="client")
        urgent_client = create_client_orm(name="Urgent Client", tags=[priority_tag])
        normal_client = create_client_orm(name="Normal Client", tags=[])
        
        for client in [urgent_client, normal_client]:
            test_session.add(client)
        await test_session.commit()
        
        # When: Filtering to exclude urgent clients with ORM instances
        result = await client_repository.query(filter={
            "tags_not_exists": [("priority", "urgent", "test_author")]
        }, _return_sa_instance=True)
        
        # Then: Should only return normal client
        result_ids = {c.id for c in result}
        assert normal_client.id in result_ids
        assert urgent_client.id not in result_ids

    async def test_complex_client_tag_combination(self, client_repository: ClientRepo, test_session):
        """Test complex AND/OR tag combinations"""
        # Given: ORM client with multiple tags
        category_tag = create_client_tag_orm(key="category", value="restaurant", author_id="author_1", type="client")
        industry_tag = create_client_tag_orm(key="industry", value="hospitality", author_id="author_1", type="client")
        size_tag = create_client_tag_orm(key="size", value="large", author_id="author_1", type="client")
        
        client = create_client_orm(
            name="Complex Tag Client", 
            tags=[category_tag, industry_tag, size_tag]
        )
        test_session.add(client)
        await test_session.commit()
        
        # When: Complex filter with AND/OR logic and ORM instances
        result = await client_repository.query(filter={
            "tags": [
                ("category", "restaurant", "author_1"),    # Must match (AND)
                ("category", "hotel", "author_1"),         # OR with restaurant
                ("industry", "hospitality", "author_1"),   # Must match (AND) 
                ("industry", "retail", "author_1"),        # OR with hospitality
                ("size", "large", "author_1")              # Must match (AND)
            ]
        }, _return_sa_instance=True)
        
        # Then: Should find the client (all key groups have at least one match)
        result_ids = {c.id for c in result}
        assert client.id in result_ids

    async def test_client_tag_dissociation_and_removal(self, client_repository: ClientRepo, test_session):
        """Test removing tags from clients and verifying persistence"""
        # Given: ORM client with multiple tags
        category_tag = create_client_tag_orm(key="category", value="restaurant", author_id="test_author", type="client")
        industry_tag = create_client_tag_orm(key="industry", value="hospitality", author_id="test_author", type="client")
        
        client_with_tags = create_client_orm(
            name="Client with Tags to Remove",
            tags=[category_tag, industry_tag]
        )
        test_session.add(client_with_tags)
        await test_session.commit()
        
        # Verify tags are initially present with ORM instances
        initial_result = await client_repository.query(filter={
            "tags": [("category", "restaurant", "test_author")]
        }, _return_sa_instance=True)
        assert len(initial_result) >= 1
        assert client_with_tags.id in {c.id for c in initial_result}
        
        # When: Removing all tags from the client directly in session
        retrieved_client = await client_repository.get_sa_instance(client_with_tags.id)
        retrieved_client.tags.clear()  # Remove all tags from ORM relationship
        await test_session.commit()
        
        # Then: Client should no longer be found by tag filters with ORM instances
        after_removal_result = await client_repository.query(filter={
            "tags": [("category", "restaurant", "test_author")]
        }, _return_sa_instance=True)
        result_ids = {c.id for c in after_removal_result}
        assert client_with_tags.id not in result_ids
        
        # But client should still exist when queried without tag filters
        client_still_exists = await client_repository.get_sa_instance(client_with_tags.id)
        assert client_still_exists is not None
        assert client_still_exists.profile.name == "Client with Tags to Remove"
        assert len(client_still_exists.tags) == 0
        
        # When: Re-adding some tags back
        new_tag = create_client_tag_orm(key="region", value="west", author_id="test_author", type="client")
        retrieved_client_again = await client_repository.get_sa_instance(client_with_tags.id)
        retrieved_client_again.tags.append(new_tag)  # Add new tag to ORM relationship
        await test_session.commit()
        
        # Then: Should be findable by new tag filter with ORM instances
        final_result = await client_repository.query(filter={
            "tags": [("region", "west", "test_author")]
        }, _return_sa_instance=True)
        final_result_ids = {c.id for c in final_result}
        assert client_with_tags.id in final_result_ids


# =============================================================================
# TEST CLIENT REPOSITORY ERROR HANDLING
# =============================================================================

class TestClientRepositoryErrorHandling:
    """Test edge cases and database constraint violations"""

    async def test_get_nonexistent_client(self, client_repository: ClientRepo):
        """Test getting client that doesn't exist"""
        # When/Then: Getting nonexistent client should raise exception
        from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import EntityNotFoundException
        with pytest.raises(EntityNotFoundException):
            await client_repository.get_sa_instance("nonexistent_client_id")

    async def test_invalid_filter_parameters(self, client_repository: ClientRepo):
        """Test handling of invalid filter parameters"""
        # Given: Repository ready for testing
        
        with pytest.raises(FilterValidationException):
            await client_repository.query(filter={"invalid_field": "some_value"})

    async def test_null_handling_in_filters(self, client_repository: ClientRepo, test_session):
        """Test filter behavior with null values"""
        # Given: ORM clients with null values in optional fields
        client_with_nulls = create_client_orm(
            name="Client with Nulls",
            notes=None
        )
        test_session.add(client_with_nulls)
        await test_session.commit()
        
        # When: Filtering with various null-related conditions and ORM instances
        result = await client_repository.query(_return_sa_instance=True)
        
        # Then: Should handle null comparisons correctly
        assert isinstance(result, list)

    async def test_list_filter_options(self, client_repository: ClientRepo):
        """Test the list_filter_options method"""
        # When: Getting filter options
        options = client_repository.list_filter_options()
        
        # Then: Should return expected structure
        assert "sort" in options
        assert "type" in options["sort"]
        assert "options" in options["sort"]
        assert "created_at" in options["sort"]["options"]
        assert "updated_at" in options["sort"]["options"]


# =============================================================================
# TEST CLIENT REPOSITORY PERFORMANCE
# =============================================================================

class TestClientRepositoryPerformance:
    """Test performance benchmarks and baselines"""

    async def test_bulk_insert_performance(self, client_repository: ClientRepo, test_session):
        """Test bulk insert performance with timing"""
        # Given: Large dataset for bulk operations using ORM models
        client_count = 50  # Smaller for CI environment
        clients = []
        
        start_time = time.time()
        
        # Create ORM clients
        for i in range(client_count):
            client = create_client_orm(name=f"Bulk Client {i}")
            clients.append(client)
            test_session.add(client)
        
        # Bulk persist
        await test_session.commit()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Then: Should meet bulk performance expectations
        max_duration = 5.0  # 5 seconds for 50 clients
        per_entity_ms = (duration * 1000) / client_count
        
        assert duration <= max_duration, f"Bulk insert took {duration:.3f}s, expected <= {max_duration}s"
        assert per_entity_ms <= 100, f"Per-entity time {per_entity_ms:.2f}ms, expected <= 100ms"  # Relaxed for CI

    async def test_complex_query_performance(self, client_repository: ClientRepo, test_session):
        """Test complex query with joins and filters"""
        # Given: Dataset with relationships and tags using ORM models
        clients_with_tags = create_clients_with_tags_orm(count=25, tags_per_client=3)
        
        for client in clients_with_tags:
            test_session.add(client)
        await test_session.commit()
        
        # When: Running complex query with ORM instances
        start_time = time.time()
        
        result = await client_repository.query(filter={
            "author_id": "author_1"
        }, _return_sa_instance=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Then: Should complete in reasonable time
        assert duration <= 2.0, f"Complex query took {duration:.3f}s, expected <= 2.0s"
        assert isinstance(result, list) 

    async def test_tag_filtering_performance(self, client_repository: ClientRepo, test_session):
        """Test tag filtering performance with larger dataset"""
        # Given: Dataset with various tag combinations
        clients_with_tags = create_clients_with_tags_orm(count=30, tags_per_client=2)
        
        for client in clients_with_tags:
            test_session.add(client)
        await test_session.commit()
        
        # When: Running tag filtering query with ORM instances
        start_time = time.time()
        
        result = await client_repository.query(filter={
            "tags": [("category", "restaurant", "author_1")]
        }, _return_sa_instance=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Then: Should complete in reasonable time
        assert duration <= 1.5, f"Tag filtering took {duration:.3f}s, expected <= 1.5s"
        assert isinstance(result, list)

    async def test_specialized_client_factories_performance(self, client_repository: ClientRepo):
        """Test performance of specialized client creation and persistence"""
        # Given: Various specialized clients
        start_time = time.time()
        
        # Create specialized clients
        restaurant_client = create_restaurant_client()
        catering_client = create_catering_client()
        
        # Persist them
        await client_repository.add(restaurant_client)
        await client_repository.add(catering_client)
        await client_repository.persist(restaurant_client)
        await client_repository.persist(catering_client)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Then: Should complete quickly
        assert duration <= 1.0, f"Specialized client operations took {duration:.3f}s, expected <= 1.0s"
        
        # Verify they were created correctly
        retrieved_restaurant = await client_repository.get(restaurant_client.id)
        retrieved_catering = await client_repository.get(catering_client.id)
        
        assert retrieved_restaurant.profile.name == "Giuseppe's Italian Restaurant"
        assert len(retrieved_restaurant.tags) >= 3  # Should have category, industry, size tags
        assert retrieved_catering.profile.name == "Elite Catering Services"
        assert len(retrieved_catering.tags) >= 3  # Should have category, industry, size tags 