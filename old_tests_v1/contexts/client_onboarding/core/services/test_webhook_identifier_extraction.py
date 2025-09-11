"""
Unit-level tests for client identifier extraction in the webhook processor.

These tests validate that identifiers are extracted from field types (email/phone)
and Portuguese titles/refs (e.g., 'nome', 'WhatsApp').
"""

import json
from typing import List, cast

import pytest
from src.contexts.client_onboarding.core.services.webhooks.processor import (
    WebhookPayloadProcessor,
)
from tests.contexts.client_onboarding.data_factories import (
    create_onboarding_form,
)
from tests.contexts.client_onboarding.fakes.fake_unit_of_work import (
    FakeUnitOfWork,
)
from tests.utils.counter_manager import get_next_onboarding_form_id

pytestmark = pytest.mark.anyio


async def test_identifier_extraction_from_type_and_portuguese_titles():
    # Arrange: fake UoW and a registered form
    fake_uow = FakeUnitOfWork()
    processor = WebhookPayloadProcessor(fake_uow)

    typeform_id = "tf_TEST_FORM_1234"
    form_id = get_next_onboarding_form_id()
    onboarding_form = create_onboarding_form(id=form_id, typeform_id=typeform_id)
    await fake_uow.onboarding_forms.add(onboarding_form)

    payload = {
        "event_id": "evt_123",
        "event_type": "form_response",
        "form_response": {
            "form_id": typeform_id,
            "token": "resp_123",
            "submitted_at": "2025-08-12T20:59:49Z",
            "answers": [
                {
                    "field": {
                        "id": "ersPKA2XlBqe",
                        "type": "short_text",
                        "ref": "b28ff946-e48a-4872-8742-bb2d89eddbc1",
                        "title": "Qual o seu nome completo?",
                    },
                    "type": "text",
                    "text": "Fulano de Tal",
                },
                {
                    "field": {
                        "id": "JALu71iSG9UV",
                        "type": "phone_number",
                        "ref": "f051b67b-3394-4569-8f53-b244f2150e74",
                        "title": "Qual o seu WhatsApp?",
                    },
                    "type": "text",
                    "phone_number": "+5511999999999",
                    "text": "+5511999999999",
                },
                {
                    "field": {
                        "id": "Ac107y4SwXHc",
                        "type": "email",
                        "ref": "34c2b406-0bef-4185-9a50-305fe9afd65d",
                        "title": "Qual o seu email?",
                    },
                    "type": "email",
                    "email": "user@example.com",
                },
            ],
        },
    }

    # Act: process and store
    processed = await processor.process_webhook_payload(payload)
    response_id = await processor.store_form_response(processed)

    # Assert
    assert response_id == "resp_123"
    stored = cast(list, await fake_uow.form_responses.get_all())[0]
    assert stored.client_identifiers is not None
    assert stored.client_identifiers.get("email") == "user@example.com"
    assert stored.client_identifiers.get("phone") == "+5511999999999"
    assert stored.client_identifiers.get("name") == "Fulano de Tal"
