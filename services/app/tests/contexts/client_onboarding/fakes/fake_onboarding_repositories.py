"""
Fake repository implementations for client onboarding testing.

These fake repositories use in-memory storage and implement the same interfaces
as the real repositories for isolated testing.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from src.contexts.client_onboarding.models.onboarding_form import OnboardingForm, OnboardingFormStatus
from src.contexts.client_onboarding.models.form_response import FormResponse


class FakeOnboardingFormRepository:
    """In-memory fake implementation of OnboardingFormRepo for testing."""
    
    def __init__(self):
        self._forms: Dict[int, OnboardingForm] = {}
        self._typeform_lookup: Dict[str, int] = {}  # typeform_id -> id mapping
        self._next_id = 1
        self.seen: set[OnboardingForm] = set()

    async def add(self, onboarding_form: OnboardingForm) -> OnboardingForm:
        """Add a new onboarding form."""
        if not onboarding_form.id:
            onboarding_form.id = self._next_id
            self._next_id += 1
        
        self._forms[onboarding_form.id] = onboarding_form
        self._typeform_lookup[onboarding_form.typeform_id] = onboarding_form.id
        self.seen.add(onboarding_form)
        return onboarding_form

    async def get_by_id(self, form_id: int) -> Optional[OnboardingForm]:
        """Get onboarding form by ID."""
        form = self._forms.get(form_id)
        if form:
            self.seen.add(form)
        return form

    async def get_by_typeform_id(self, typeform_id: str) -> Optional[OnboardingForm]:
        """Get onboarding form by TypeForm ID."""
        form_id = self._typeform_lookup.get(typeform_id)
        if form_id:
            form = self._forms.get(form_id)
            if form and form.status != OnboardingFormStatus.DELETED:
                self.seen.add(form)
                return form
        return None

    async def get_by_user_id(self, user_id: int) -> List[OnboardingForm]:
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
        self._responses: Dict[int, FormResponse] = {}
        self._response_id_lookup: Dict[str, int] = {}  # response_id -> id mapping
        self._form_responses: Dict[int, List[int]] = {}  # form_id -> [response_ids]
        self._next_id = 1
        self.seen: set[FormResponse] = set()

    async def create(self, form_response_data: Dict[str, Any]) -> FormResponse:
        """Create a new FormResponse from dictionary data."""
        # Create FormResponse model from dictionary
        form_response = FormResponse(
            id=self._next_id,
            form_id=form_response_data["form_id"],
            response_data=form_response_data["response_data"],
            client_identifiers=form_response_data.get("client_identifiers"),
            response_id=form_response_data["response_id"],
            submission_id=form_response_data.get("submission_id"),
            submitted_at=form_response_data["submitted_at"],
            processed_at=form_response_data.get("processed_at", datetime.now()),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Use the existing add method to store it
        return await self.add(form_response)

    async def add(self, form_response: FormResponse) -> FormResponse:
        """Add a new form response."""
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

    async def get_by_id(self, response_id: int) -> Optional[FormResponse]:
        """Get form response by ID."""
        response = self._responses.get(response_id)
        if response:
            self.seen.add(response)
        return response

    async def get_by_response_id(self, response_id: str) -> Optional[FormResponse]:
        """Get form response by TypeForm response ID."""
        internal_id = self._response_id_lookup.get(response_id)
        if internal_id:
            response = self._responses.get(internal_id)
            if response:
                self.seen.add(response)
                return response
        return None

    async def get_by_form_id(self, form_id: int) -> List[FormResponse]:
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