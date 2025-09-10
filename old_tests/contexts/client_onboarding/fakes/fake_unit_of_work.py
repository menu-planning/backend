"""
Fake Unit of Work implementation for Client Onboarding testing.

This fake UoW provides in-memory repositories for isolated testing without database dependencies.
Follows the same patterns as the products catalog fake implementations.
"""

from __future__ import annotations

from unittest.mock import Mock

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.contexts.client_onboarding.core.services.uow import UnitOfWork

from .fake_onboarding_repositories import (
    FakeFormResponseRepository,
    FakeOnboardingFormRepository,
)


class TransactionalRepository:
    """
    Wrapper that provides transaction semantics for fake repositories.

    Buffers operations until commit() is called, enabling proper rollback support.
    """

    def __init__(self, shared_repo):
        self._shared_repo = shared_repo
        self._operations = []
        self._committed = False

    def __getattr__(self, name):
        """
        Delegate operations to shared repo with transaction-aware behavior.
        """
        attr = getattr(self._shared_repo, name)

        # Buffer write operations
        if name in ["add", "create", "update", "delete"]:

            async def buffered_operation(*args, **kwargs):
                if self._committed:
                    # If already committed, operation goes directly to shared repo
                    return await attr(*args, **kwargs)
                # For 'create' operations, we need to actually execute them to get the entity
                # but without storing in the shared repository
                if name == "create":
                    # Call the method to create the entity but don't commit it yet
                    entity = await self._create_entity_without_storage(
                        attr, args, kwargs
                    )
                    # Buffer a custom add operation with the created entity
                    add_method = self._shared_repo.add
                    self._operations.append(("add", (entity,), {}, add_method))
                    return entity
                # Buffer the operation for later commit
                self._operations.append((name, args, kwargs, attr))
                # For 'add' operations, return the entity being added
                if name == "add" and args:
                    return args[0]
                return None

            return buffered_operation

        # For read operations that need transaction awareness
        if name in ["get_by_typeform_id", "get_by_id", "get_all"]:

            async def transaction_aware_read(*args, **kwargs):
                # First check shared repository
                result = await attr(*args, **kwargs)

                # If not found in shared repo, check buffered operations
                if not result and name == "get_by_typeform_id" and args:
                    typeform_id = args[0]
                    for op_name, op_args, op_kwargs, op_attr in self._operations:
                        if op_name == "add" and op_args:
                            entity = op_args[0]
                            if (
                                hasattr(entity, "typeform_id")
                                and entity.typeform_id == typeform_id
                            ):
                                return entity
                elif not result and name == "get_by_id" and args:
                    id = args[0]
                    for op_name, op_args, op_kwargs, op_attr in self._operations:
                        if op_name == "add" and op_args:
                            entity = op_args[0]
                            if hasattr(entity, "id") and entity.id == id:
                                return entity
                elif name == "get_all":
                    # For get_all, combine shared repo results with buffered entities
                    buffered_entities = []
                    for op_name, op_args, op_kwargs, op_attr in self._operations:
                        if op_name == "add" and op_args:
                            buffered_entities.append(op_args[0])
                    if buffered_entities:
                        return (result or []) + buffered_entities

                return result

            return transaction_aware_read

        # All other operations go directly to shared repo
        return attr

    async def _create_entity_without_storage(self, create_method, args, kwargs):
        """Create entity using repository logic but don't store in shared state."""
        from datetime import datetime

        from src.contexts.client_onboarding.core.domain.models.form_response import (
            FormResponse,
        )

        # This is specific to FormResponseRepository.create()
        # We replicate the logic without calling add() on the shared repository
        if args:
            form_response_data = args[0]

            # Thread-safe ID generation using the shared repository's lock
            with self._shared_repo._id_lock:
                next_id = self._shared_repo._next_id
                self._shared_repo._next_id += 1

            form_response = FormResponse(
                id=next_id,  # Use thread-safe ID
                form_id=form_response_data["form_id"],
                response_data=form_response_data["response_data"],
                client_identifiers=form_response_data.get("client_identifiers"),
                response_id=form_response_data["response_id"],
                submission_id=form_response_data.get("submission_id"),
                submitted_at=form_response_data["submitted_at"],
                processed_at=form_response_data.get("processed_at", datetime.now()),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            return form_response
        return None

    async def commit_operations(self):
        """Apply all buffered operations to the shared repository."""
        for name, args, kwargs, attr in self._operations:
            await attr(*args, **kwargs)
        self._operations.clear()
        self._committed = True

    def rollback_operations(self):
        """Discard all buffered operations."""
        self._operations.clear()


class FakeUnitOfWork(UnitOfWork):
    """
    Fake Unit of Work implementation for client onboarding testing.

    Provides the same interface as the real UnitOfWork but uses in-memory
    fake repositories instead of database-backed ones.

    Implements proper transaction semantics with buffering and rollback support.
    """

    # Class-level shared repositories for data persistence across instances
    _shared_onboarding_forms = None
    _shared_form_responses = None

    def __init__(self):
        # Create a mock session factory to satisfy parent class requirements
        mock_session_factory: async_sessionmaker[AsyncSession] = Mock()
        super().__init__(mock_session_factory)

        self.committed = False
        self.rolled_back = False

        # Initialize shared repositories if not already done
        if FakeUnitOfWork._shared_onboarding_forms is None:
            FakeUnitOfWork._shared_onboarding_forms = FakeOnboardingFormRepository()
            FakeUnitOfWork._shared_form_responses = FakeFormResponseRepository()

        # Create transaction-local repositories that wrap the shared ones
        self.onboarding_forms = TransactionalRepository(
            FakeUnitOfWork._shared_onboarding_forms
        )
        self.form_responses = TransactionalRepository(
            FakeUnitOfWork._shared_form_responses
        )

        # Pre-populate with test forms for testing (only on first initialization)
        if not hasattr(self, "_class_populated"):
            self._populate_test_data()
            FakeUnitOfWork._class_populated = True

        # Mock session for compatibility
        self.session = Mock()

    def _populate_test_data(self):
        """
        Pre-populate test data only for specific tests that need it.

        Following data factory patterns for proper test isolation, this method should only
        populate data for tests that explicitly require pre-existing data (like replay protection tests).

        Most tests should start with clean repositories and create their own data using
        factory patterns with deterministic counters for proper isolation.
        """
        # Only populate data for replay protection tests
        # Check if we're running security tests by looking at the call stack
        import inspect

        frame_names = [frame.filename for frame in inspect.stack()]
        is_security_test = any(
            "test_replay_protection" in frame_name for frame_name in frame_names
        )

        if is_security_test:
            # Only populate forms for security/replay protection tests
            self._populate_replay_protection_forms()

    def _populate_replay_protection_forms(self):
        """Create specific forms needed by replay protection tests."""
        from datetime import datetime

        from src.contexts.client_onboarding.core.domain.models.onboarding_form import (
            OnboardingForm,
            OnboardingFormStatus,
        )

        # Create forms referenced by replay protection tests and webhook scenarios
        # These use the same patterns as typeform_factories.py default form IDs
        replay_forms = [
            # Default factory pattern: onboarding_form_001, onboarding_form_002, etc.
            OnboardingForm(
                id=1,
                user_id=1,
                typeform_id="onboarding_form_001",
                webhook_url="https://api.example.com/webhooks/form/1",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime(2024, 1, 1, 12, 0, 0),
                updated_at=datetime(2024, 1, 1, 12, 30, 0),
            ),
            OnboardingForm(
                id=2,
                user_id=1,
                typeform_id="onboarding_form_002",
                webhook_url="https://api.example.com/webhooks/form/2",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime(2024, 1, 1, 13, 0, 0),
                updated_at=datetime(2024, 1, 1, 13, 30, 0),
            ),
            OnboardingForm(
                id=3,
                user_id=1,
                typeform_id="onboarding_form_003",
                webhook_url="https://api.example.com/webhooks/form/3",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime(2024, 1, 1, 14, 0, 0),
                updated_at=datetime(2024, 1, 1, 14, 30, 0),
            ),
            # Alternative pattern: form_1, form_2, etc. (used in some scenarios)
            OnboardingForm(
                id=10,
                user_id=1,
                typeform_id="form_1",
                webhook_url="https://api.example.com/webhooks/form/10",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime(2024, 1, 1, 15, 0, 0),
                updated_at=datetime(2024, 1, 1, 15, 30, 0),
            ),
            OnboardingForm(
                id=11,
                user_id=1,
                typeform_id="form_2",
                webhook_url="https://api.example.com/webhooks/form/11",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime(2024, 1, 1, 16, 0, 0),
                updated_at=datetime(2024, 1, 1, 16, 30, 0),
            ),
            OnboardingForm(
                id=12,
                user_id=1,
                typeform_id="form_3",
                webhook_url="https://api.example.com/webhooks/form/12",
                status=OnboardingFormStatus.ACTIVE,
                created_at=datetime(2024, 1, 1, 17, 0, 0),
                updated_at=datetime(2024, 1, 1, 17, 30, 0),
            ),
        ]

        # Add only these specific forms to the shared repository directly
        if FakeUnitOfWork._shared_onboarding_forms:
            for form in replay_forms:
                FakeUnitOfWork._shared_onboarding_forms._forms[form.id] = form
                FakeUnitOfWork._shared_onboarding_forms._typeform_lookup[
                    form.typeform_id
                ] = form.id

    async def __aenter__(self):
        """Support async context manager protocol."""
        # Override the abstract method - no need to create real session
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Gracefully handle context manager exit."""
        if exc_type is not None:
            await self.rollback()
        await self.close()

    async def commit(self):
        """Commit all buffered operations to the shared repositories."""
        await self.onboarding_forms.commit_operations()
        await self.form_responses.commit_operations()
        self.committed = True

    async def rollback(self):
        """Rollback all buffered operations (discard them)."""
        self.onboarding_forms.rollback_operations()
        self.form_responses.rollback_operations()
        self.rolled_back = True

    async def close(self):
        """Close the unit of work - no-op for fake implementation."""

    @classmethod
    def reset_all_data(cls):
        """
        Reset all test data to clean state for test isolation.

        Call this in test setup/teardown to ensure clean state between tests.
        """
        # Reset shared repositories to clean state
        if cls._shared_onboarding_forms is not None:
            cls._shared_onboarding_forms._forms.clear()
            cls._shared_onboarding_forms._typeform_lookup.clear()
            cls._shared_onboarding_forms._next_id = 1

        if cls._shared_form_responses is not None:
            cls._shared_form_responses._responses.clear()
            cls._shared_form_responses._response_id_lookup.clear()
            cls._shared_form_responses._form_responses.clear()
            cls._shared_form_responses._next_id = 1

        # Reset class state
        cls._shared_onboarding_forms = None
        cls._shared_form_responses = None

    def collect_new_events(self):
        """
        Collect domain events from all tracked entities.

        Yields events from all repositories' seen entities.
        """
        # Check all shared repositories for entities with events
        shared_repositories = [
            FakeUnitOfWork._shared_onboarding_forms,
            FakeUnitOfWork._shared_form_responses,
        ]

        for repo in shared_repositories:
            if repo:  # Check if repository is initialized
                for entity in repo.seen:
                    if hasattr(entity, "events"):
                        while entity.events:
                            yield entity.events.pop(0)
