"""
Fake repository implementations for client onboarding testing.

These fake repositories use in-memory storage and implement the same interfaces
as the real repositories for isolated testing.
"""

import threading
from datetime import datetime
from typing import Any

from src.contexts.client_onboarding.core.domain.models.form_response import FormResponse
from src.contexts.client_onboarding.core.domain.models.onboarding_form import (
    OnboardingForm,
    OnboardingFormStatus,
)


class FakeOnboardingFormRepository:
    """In-memory fake implementation of OnboardingFormRepo for testing."""

    def __init__(self):
        self._forms: dict[int, OnboardingForm] = {}
        self._typeform_lookup: dict[str, int] = {}  # typeform_id -> id mapping
        self._next_id = 1
        self.seen: set[OnboardingForm] = set()

    def _create_dynamic_form(
        self,
        typeform_id: str,
        webhook_url: str | None = None,
        user_id: int | None = None,
    ) -> OnboardingForm | None:
        """Create a dynamic onboarding form for test scenarios with proper factory pattern."""
        from datetime import datetime

        from old_tests_v0.utils.counter_manager import get_next_onboarding_form_id

        # Use deterministic ID from counter manager instead of internal counter
        form_id = get_next_onboarding_form_id()

        # Use provided webhook_url or generate deterministic one
        if webhook_url is None:
            webhook_url = f"https://api.example.com/webhooks/form/{form_id}"

        # Use provided user_id or default
        if user_id is None:
            user_id = 1  # Default test user

        onboarding_form = OnboardingForm(
            id=form_id,
            user_id=user_id,
            typeform_id=typeform_id,
            webhook_url=webhook_url,
            status=OnboardingFormStatus.ACTIVE,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 30, 0),
        )

        # Store it in the repository
        self._forms[form_id] = onboarding_form
        self._typeform_lookup[typeform_id] = form_id
        self.seen.add(onboarding_form)

        # Update next_id to stay consistent with internal counter
        self._next_id = max(self._next_id, form_id + 1)

        return onboarding_form

    def _should_create_dynamic_form(self, typeform_id: str) -> bool:
        """
        Determine if we should create a dynamic form for this typeform_id.

        Only create dynamic forms for very specific security test scenarios that need
        high-volume form generation. Most tests should explicitly add forms via add().

        This should be VERY restrictive to avoid masking proper error handling.
        """
        # Only auto-create for very specific security test patterns that need it
        # These are typically penetration/stress tests that generate many forms
        if (
            typeform_id.startswith("stress_test_form_")
            or typeform_id.startswith("security_test_form_")
            or typeform_id.startswith("penetration_form_")
        ):
            return True

        # Don't auto-create for any other patterns - tests should explicitly add forms
        # This ensures proper testing of error handling for nonexistent forms
        return False

    async def add(self, onboarding_form: OnboardingForm) -> OnboardingForm:
        """Add a new onboarding form."""
        if not onboarding_form.id:
            onboarding_form.id = self._next_id
            self._next_id += 1

        self._forms[onboarding_form.id] = onboarding_form
        self._typeform_lookup[onboarding_form.typeform_id] = onboarding_form.id
        self.seen.add(onboarding_form)
        return onboarding_form

    async def get_all(self) -> list[OnboardingForm]:
        """Get all onboarding forms."""
        return list(self._forms.values())

    async def get_by_id(self, form_id: int) -> OnboardingForm | None:
        """Get onboarding form by ID."""
        form = self._forms.get(form_id)
        if form:
            self.seen.add(form)
        return form

    async def get_by_typeform_id(self, typeform_id: str) -> OnboardingForm | None:
        """Get onboarding form by TypeForm ID."""
        form_id = self._typeform_lookup.get(typeform_id)
        if form_id:
            form = self._forms.get(form_id)
            if form and form.status != OnboardingFormStatus.DELETED:
                self.seen.add(form)
                return form

        # If not found, create a dynamic form ONLY for test scenarios that need it
        # This handles cases where security tests generate unique form IDs
        # Don't auto-create for webhook manager tests - they should handle creation through add() flow
        if (
            not form_id
            and typeform_id
            and self._should_create_dynamic_form(typeform_id)
        ):
            dynamic_form = self._create_dynamic_form(typeform_id)
            if dynamic_form:
                return dynamic_form

        return None

    async def get_by_user_id(self, user_id: int) -> list[OnboardingForm]:
        """Get all onboarding forms for a specific user."""
        results = []
        for form in self._forms.values():
            if form.user_id == user_id and form.status != OnboardingFormStatus.DELETED:
                results.append(form)
                self.seen.add(form)
        return results

    async def update(self, onboarding_form: OnboardingForm) -> OnboardingForm:
        """Update an existing onboarding form."""
        if onboarding_form.id in self._forms:
            # Update the typeform lookup if typeform_id changed
            old_form = self._forms[onboarding_form.id]
            if old_form.typeform_id != onboarding_form.typeform_id:
                # Remove old mapping
                if old_form.typeform_id in self._typeform_lookup:
                    del self._typeform_lookup[old_form.typeform_id]
                # Add new mapping
                self._typeform_lookup[onboarding_form.typeform_id] = onboarding_form.id

            self._forms[onboarding_form.id] = onboarding_form
            self.seen.add(onboarding_form)
        return onboarding_form

    async def delete(self, onboarding_form: OnboardingForm) -> None:
        """Soft delete an onboarding form."""
        onboarding_form.status = OnboardingFormStatus.DELETED
        self.seen.add(onboarding_form)


class FakeFormResponseRepository:
    """In-memory fake implementation of FormResponseRepo for testing."""

    def __init__(self):
        self._responses: dict[int, FormResponse] = {}
        self._response_id_lookup: dict[str, int] = {}  # response_id -> id mapping
        self._form_responses: dict[int, list[int]] = {}  # form_id -> [response_ids]
        self._next_id = 1
        self.seen: set[FormResponse] = set()
        self._id_lock = threading.Lock()  # Thread safety for ID generation

    async def create(self, form_response_data: dict[str, Any]) -> FormResponse:
        """Create a new FormResponse from dictionary data."""
        # Thread-safe ID generation for create method
        with self._id_lock:
            next_id = self._next_id
            self._next_id += 1

        # Create FormResponse model from dictionary
        form_response = FormResponse(
            id=next_id,
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

        # Store it (skip ID generation in add since we already have an ID)
        self._responses[form_response.id] = form_response
        self._response_id_lookup[form_response.response_id] = form_response.id

        # Add to form responses lookup
        if form_response.form_id not in self._form_responses:
            self._form_responses[form_response.form_id] = []
        self._form_responses[form_response.form_id].append(form_response.id)

        self.seen.add(form_response)
        return form_response

    async def add(self, form_response: FormResponse) -> FormResponse:
        """Add a new form response."""
        # Thread-safe ID generation
        with self._id_lock:
            if not form_response.id:
                form_response.id = self._next_id
                self._next_id += 1

        self._responses[form_response.id] = form_response
        self._response_id_lookup[form_response.response_id] = form_response.id

        # Add to form responses lookup
        if form_response.form_id not in self._form_responses:
            self._form_responses[form_response.form_id] = []
        self._form_responses[form_response.form_id].append(form_response.id)

        self.seen.add(form_response)
        return form_response

    async def get_all(self) -> list[FormResponse]:
        """Get all form responses."""
        return list(self._responses.values())

    async def get_by_id(self, response_id: int) -> FormResponse | None:
        """Get form response by ID."""
        response = self._responses.get(response_id)
        if response:
            self.seen.add(response)
        return response

    async def get_by_response_id(self, response_id: str) -> FormResponse | None:
        """Get form response by TypeForm response ID."""
        internal_id = self._response_id_lookup.get(response_id)
        if internal_id:
            response = self._responses.get(internal_id)
            if response:
                self.seen.add(response)
                return response
        return None

    async def get_by_form_id(self, form_id: int) -> list[FormResponse]:
        """Get all responses for a specific onboarding form."""
        results = []
        response_ids = self._form_responses.get(form_id, [])

        for response_id in response_ids:
            response = self._responses.get(response_id)
            if response:
                results.append(response)
                self.seen.add(response)

        return results

    async def update(self, form_response: FormResponse) -> FormResponse:
        """Update an existing form response."""
        if form_response.id in self._responses:
            # Update response_id lookup if it changed
            old_response = self._responses[form_response.id]
            if old_response.response_id != form_response.response_id:
                # Remove old mapping
                if old_response.response_id in self._response_id_lookup:
                    del self._response_id_lookup[old_response.response_id]
                # Add new mapping
                self._response_id_lookup[form_response.response_id] = form_response.id

            self._responses[form_response.id] = form_response
            self.seen.add(form_response)

        return form_response
