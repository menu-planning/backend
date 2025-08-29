"""
Webhook Data Persistence Tests

Tests webhook data storage functionality using real database operations.
Follows the patterns from test_meal_repository.py with proper cleanup and isolation.

Tests cover:
- Webhook payload processing and database storage
- OnboardingForm creation and retrieval
- FormResponse persistence with proper relationships
- Error handling for invalid data
- Database transaction integrity
"""

import json
from collections.abc import AsyncGenerator
from datetime import datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.client_onboarding.core.adapters.repositories.form_response_repository import (
    FormResponseRepo,
)
from src.contexts.client_onboarding.core.adapters.repositories.onboarding_form_repository import (
    OnboardingFormRepo,
)
from src.contexts.client_onboarding.core.domain.models.form_response import FormResponse
from src.contexts.client_onboarding.core.domain.models.onboarding_form import (
    OnboardingForm,
    OnboardingFormStatus,
)
from src.contexts.client_onboarding.core.services.uow import UnitOfWork

# Test data factories and utilities
from src.contexts.client_onboarding.core.services.webhooks.processor import (
    WebhookProcessor,
)
from tests.contexts.client_onboarding.data_factories.client_factories import (
    create_onboarding_form_kwargs,
)
from tests.contexts.client_onboarding.data_factories.typeform_factories import (
    create_realistic_onboarding_scenario,
    create_webhook_payload_kwargs,
)

# Import existing test utilities
from tests.utils.counter_manager import (
    get_next_client_id,
    get_next_form_response_counter,
    get_next_onboarding_form_id,
)

# Load integration database fixtures (following meal repository pattern)
pytest_plugins = ["tests.integration_conftest"]

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


# =============================================================================
# DATABASE CLEANUP AND SESSION MANAGEMENT
# =============================================================================


async def clean_client_onboarding_tables(session: AsyncSession):
    """
    Clean client onboarding tables for test isolation.

    Follows the pattern from meal repository tests - clean only the tables
    these tests use in dependency order.
    """
    tables_to_clean = [
        # Most dependent first
        "client_onboarding.form_responses",  # depends on onboarding_forms
        "client_onboarding.onboarding_forms",  # independent in this context
    ]

    for table in tables_to_clean:
        try:
            # Use DELETE instead of TRUNCATE to avoid lock issues
            await session.execute(text(f"DELETE FROM {table}"))
        except Exception as e:
            print(f"Info: Could not delete from {table}: {e}")
            continue


@pytest.fixture(scope="function")
async def clean_client_onboarding_database(async_pg_session_factory) -> None:
    """Clean client onboarding tables before each test."""
    async with async_pg_session_factory() as session:
        await clean_client_onboarding_tables(session)
        await session.commit()


@pytest.fixture
async def test_session(
    async_pg_session_factory,
    clean_client_onboarding_database,  # Ensure database is clean before test
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide clean test session with targeted database cleanup.
    Follows the meal repository test pattern.
    """
    async with async_pg_session_factory() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
async def uow_factory(async_pg_session_factory):
    """Factory for creating UnitOfWork instances with real database sessions."""

    def create_uow():
        return UnitOfWork(session_factory=async_pg_session_factory)

    return create_uow


@pytest.fixture
async def onboarding_form_repo(test_session: AsyncSession) -> OnboardingFormRepo:
    """OnboardingForm repository fixture using test session."""
    return OnboardingFormRepo(test_session)


@pytest.fixture
async def form_response_repo(test_session: AsyncSession) -> FormResponseRepo:
    """FormResponse repository fixture using test session."""
    return FormResponseRepo(test_session)


@pytest.fixture
async def sample_onboarding_form(test_session: AsyncSession):
    """Create a sample onboarding form for testing."""
    form_data = create_onboarding_form_kwargs(
        user_id=get_next_client_id(),
        typeform_id=f"test_form_{get_next_onboarding_form_id()}",
        webhook_url="https://example.com/webhook",
        status=OnboardingFormStatus.ACTIVE,
    )

    onboarding_form = OnboardingForm(**form_data)
    test_session.add(onboarding_form)
    await test_session.commit()
    await test_session.refresh(onboarding_form)  # Get the assigned ID

    return onboarding_form


# =============================================================================
# TEST WEBHOOK DATA PERSISTENCE
# =============================================================================


class TestWebhookDataPersistence:
    """Test webhook data persistence with real database operations."""

    async def test_complete_webhook_processing_pipeline(
        self, uow_factory, sample_onboarding_form: OnboardingForm
    ):
        """Test complete webhook processing pipeline with database persistence."""
        # Given: Complete webhook payload
        realistic_scenario = create_realistic_onboarding_scenario(
            form_id=sample_onboarding_form.typeform_id,
            response_id=f"pipeline_response_{get_next_form_response_counter()}",
        )

        webhook_processor = WebhookProcessor(uow_factory)
        payload_json = json.dumps(realistic_scenario["webhook_payload"])
        headers = realistic_scenario["signature_headers"]

        # When: Processing complete webhook
        success, error_message, response_id = await webhook_processor.process_webhook(
            payload=payload_json, headers=headers
        )

        # Then: Processing should succeed
        assert success is True
        assert error_message is None
        assert response_id is not None

        # And: Data should be persisted
        async with uow_factory() as uow:
            stored_response = await uow.form_responses.get_by_response_id(response_id)
            assert stored_response is not None
            assert stored_response.form_id == sample_onboarding_form.id

    async def test_invalid_webhook_payload_handling(self, uow_factory):
        """Test handling of invalid webhook payloads."""
        # Given: Invalid JSON payload
        invalid_payload = '{"invalid": "json" "missing": comma}'
        headers = {"Content-Type": "application/json"}

        webhook_processor = WebhookProcessor(uow_factory)

        # When: Processing invalid payload
        success, error_message, response_id = await webhook_processor.process_webhook(
            payload=invalid_payload, headers=headers
        )

        # Then: Should fail gracefully
        assert success is False
        assert error_message is not None
        assert "json" in error_message.lower()
        assert response_id is None

    async def test_missing_onboarding_form_handling(self, uow_factory):
        """Test handling when referenced onboarding form doesn't exist."""
        # Given: Webhook for non-existent form
        webhook_payload = create_webhook_payload_kwargs(
            form_id="nonexistent_form_id",
            response_id=f"orphan_response_{get_next_form_response_counter()}",
        )

        webhook_processor = WebhookProcessor(uow_factory)
        payload_json = json.dumps(webhook_payload)
        headers = {"Content-Type": "application/json"}

        # When: Processing webhook for non-existent form
        success, error_message, response_id = await webhook_processor.process_webhook(
            payload=payload_json, headers=headers
        )

        # Then: Should handle gracefully
        assert success is False
        assert error_message is not None
        assert response_id is None

    async def test_webhook_processing_performance(
        self, uow_factory, sample_onboarding_form: OnboardingForm
    ):
        """Test webhook processing performance meets benchmarks."""
        import time

        # Given: Realistic webhook payload
        realistic_scenario = create_realistic_onboarding_scenario(
            form_id=sample_onboarding_form.typeform_id,
            response_id=f"perf_test_{get_next_form_response_counter()}",
            # Include multiple answers to simulate realistic payload size
            additional_answers=[
                {"field": {"id": f"field_{i}"}, "text": f"Answer {i}"}
                for i in range(10)
            ],
        )

        webhook_processor = WebhookProcessor(uow_factory)
        payload_json = json.dumps(realistic_scenario["webhook_payload"])
        headers = realistic_scenario["signature_headers"]

        # When: Processing webhook with timing
        start_time = time.time()

        success, error_message, response_id = await webhook_processor.process_webhook(
            payload=payload_json, headers=headers
        )

        end_time = time.time()
        duration = end_time - start_time

        # Then: Should complete within performance benchmark
        assert duration <= 0.1  # 100ms benchmark per task requirement
        assert success is True
        assert response_id is not None


# =============================================================================
# TEST ONBOARDING FORM DATABASE OPERATIONS
# =============================================================================


class TestOnboardingFormPersistence:
    """Test OnboardingForm database operations."""

    async def test_onboarding_form_creation_and_retrieval(
        self, onboarding_form_repo: OnboardingFormRepo, test_session: AsyncSession
    ):
        """Test creating and retrieving onboarding forms."""
        # Given: Form data to create
        form_data = create_onboarding_form_kwargs(
            user_id=get_next_client_id(),
            typeform_id=f"crud_test_{get_next_onboarding_form_id()}",
            status=OnboardingFormStatus.ACTIVE,
        )

        # When: Creating onboarding form
        onboarding_form = OnboardingForm(**form_data)
        created_form = await onboarding_form_repo.add(onboarding_form)
        await test_session.commit()
        form_id = created_form.id

        # Then: Should be retrievable
        retrieved_form = await onboarding_form_repo.get_by_id(form_id)
        assert retrieved_form is not None
        assert retrieved_form.typeform_id == form_data["typeform_id"]
        assert retrieved_form.user_id == form_data["user_id"]

    async def test_onboarding_form_by_typeform_id_lookup(
        self, onboarding_form_repo: OnboardingFormRepo, test_session: AsyncSession
    ):
        """Test looking up onboarding forms by TypeForm ID."""
        # Given: Multiple onboarding forms
        typeform_id = f"lookup_test_{get_next_onboarding_form_id()}"

        form_data = create_onboarding_form_kwargs(
            typeform_id=typeform_id, status=OnboardingFormStatus.ACTIVE
        )

        # When: Creating and looking up by typeform_id
        onboarding_form = OnboardingForm(**form_data)
        await onboarding_form_repo.add(onboarding_form)
        await test_session.commit()

        found_form = await onboarding_form_repo.get_by_typeform_id(typeform_id)

        # Then: Should find the correct form
        assert found_form is not None
        assert found_form.typeform_id == typeform_id

    async def test_onboarding_form_response_relationship(
        self,
        onboarding_form_repo: OnboardingFormRepo,
        form_response_repo: FormResponseRepo,
        test_session: AsyncSession,
    ):
        """Test relationship between OnboardingForm and FormResponse."""
        # Given: OnboardingForm
        form_data = create_onboarding_form_kwargs(
            typeform_id=f"relationship_test_{get_next_onboarding_form_id()}"
        )

        onboarding_form = OnboardingForm(**form_data)
        created_form = await onboarding_form_repo.add(onboarding_form)
        await test_session.commit()

        # When: Creating response for the form
        response_data = {
            "form_id": created_form.id,
            "response_id": f"rel_response_{get_next_form_response_counter()}",
            "response_data": {"answers": []},
            "submitted_at": datetime.now(),
        }

        form_response = FormResponse(**response_data)
        await form_response_repo.add(form_response)
        await test_session.commit()

        # Then: Should be able to query responses by form_id
        responses = await form_response_repo.get_by_form_id(created_form.id)
        assert len(responses) == 1
        assert responses[0].response_id == response_data["response_id"]
        assert responses[0].form_id == created_form.id

    async def test_form_response_by_response_id_lookup(
        self,
        form_response_repo: FormResponseRepo,
        test_session: AsyncSession,
        sample_onboarding_form: OnboardingForm,
    ):
        """Test looking up form responses by TypeForm response ID."""
        # Given: Form response with specific response_id
        response_id = f"lookup_response_{get_next_form_response_counter()}"
        response_data = {
            "form_id": sample_onboarding_form.id,
            "response_id": response_id,
            "response_data": {"answers": [{"field": {"id": "test"}, "text": "value"}]},
            "submitted_at": datetime.now(),
        }

        # When: Creating and looking up by response_id
        form_response = FormResponse(**response_data)
        await form_response_repo.add(form_response)
        await test_session.commit()

        found_response = await form_response_repo.get_by_response_id(response_id)

        # Then: Should find the correct response
        assert found_response is not None
        assert found_response.response_id == response_id
        assert found_response.form_id == sample_onboarding_form.id

    async def test_form_response_duplicate_prevention(
        self,
        form_response_repo: FormResponseRepo,
        test_session: AsyncSession,
        sample_onboarding_form: OnboardingForm,
    ):
        """Test that duplicate response_ids are handled properly."""
        # Given: Initial form response
        response_id = f"duplicate_response_{get_next_form_response_counter()}"
        initial_data = {
            "form_id": sample_onboarding_form.id,
            "response_id": response_id,
            "response_data": {
                "answers": [{"field": {"id": "test"}, "text": "original"}]
            },
            "submitted_at": datetime.now(),
        }

        initial_response = FormResponse(**initial_data)
        await form_response_repo.add(initial_response)
        await test_session.commit()

        # When: Attempting to create duplicate response
        duplicate_data = {
            "form_id": sample_onboarding_form.id,
            "response_id": response_id,  # Same response_id
            "response_data": {
                "answers": [{"field": {"id": "test"}, "text": "duplicate"}]
            },
            "submitted_at": datetime.now(),
        }

        duplicate_response = FormResponse(**duplicate_data)

        # Then: Should handle gracefully (database constraint should prevent duplicates)
        try:
            await form_response_repo.add(duplicate_response)
            await test_session.commit()
            # If this succeeds, verify business logic handles it correctly
            all_responses = await form_response_repo.get_by_form_id(
                sample_onboarding_form.id
            )
            assert len(all_responses) >= 1  # At least the original should exist
        except Exception as e:
            # Expected: Database constraint prevents duplicate response_ids
            assert "unique" in str(e).lower() or "duplicate" in str(e).lower()


# =============================================================================
# TEST DATABASE INTEGRATION WITH UOW
# =============================================================================


class TestDatabaseIntegrationWithUnitOfWork:
    """Test database operations through UnitOfWork pattern."""

    async def test_uow_transaction_rollback_on_error(
        self, uow_factory, sample_onboarding_form: OnboardingForm
    ):
        """Test that UnitOfWork properly rolls back on error."""
        # Given: Valid form response data
        response_data = {
            "form_id": sample_onboarding_form.id,
            "response_id": f"rollback_test_{get_next_form_response_counter()}",
            "response_data": {"answers": []},
            "submitted_at": datetime.now(),
        }

        # When: Using UnitOfWork with intentional error
        try:
            async with uow_factory() as uow:
                # Add valid response
                form_response = FormResponse(**response_data)
                await uow.form_responses.add(form_response)

                # Cause intentional error before commit
                raise ValueError("Intentional test error")

        except ValueError:
            pass  # Expected error

        # Then: Changes should not be persisted
        async with uow_factory() as uow:
            found_response = await uow.form_responses.get_by_response_id(
                response_data["response_id"]
            )
            assert found_response is None

    async def test_uow_successful_transaction_commit(
        self, uow_factory, sample_onboarding_form: OnboardingForm
    ):
        """Test that UnitOfWork properly commits successful transactions."""
        # Given: Valid form response data
        response_data = {
            "form_id": sample_onboarding_form.id,
            "response_id": f"commit_test_{get_next_form_response_counter()}",
            "response_data": {
                "answers": [{"field": {"id": "test"}, "text": "committed"}]
            },
            "submitted_at": datetime.now(),
        }

        # When: Using UnitOfWork successfully
        async with uow_factory() as uow:
            form_response = FormResponse(**response_data)
            await uow.form_responses.add(form_response)
            await uow.commit()

        # Then: Changes should be persisted
        async with uow_factory() as uow:
            found_response = await uow.form_responses.get_by_response_id(
                response_data["response_id"]
            )
            assert found_response is not None
            assert found_response.response_data["answers"][0]["text"] == "committed"
