"""
E2E tests for client identifier extraction with Portuguese Typeform fields.

Validates that email, phone (WhatsApp), and name are extracted and persisted
to `client_identifiers` even when refs don't contain English keywords.
"""

import json
from typing import List, cast

import pytest
from old_tests_v0.contexts.client_onboarding.data_factories import (
    create_onboarding_form,
)
from old_tests_v0.contexts.client_onboarding.utils.e2e_test_helpers import (
    setup_e2e_test_environment,
)
from old_tests_v0.utils.counter_manager import get_next_onboarding_form_id
from src.contexts.client_onboarding.core.services.webhooks.processor import (
    process_typeform_webhook,
)

pytestmark = [pytest.mark.anyio, pytest.mark.e2e]


class TestWebhookClientIdentifiersPortuguese:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.fake_uow = setup_e2e_test_environment()
        self.uow_factory = lambda: self.fake_uow

    async def test_extracts_email_phone_and_name_from_portuguese_titles(self):
        # Given: a registered onboarding form with the same Typeform ID as the payload
        typeform_id = "tf_TEST_FORM_1234"
        form_id = get_next_onboarding_form_id()
        onboarding_form = create_onboarding_form(id=form_id, typeform_id=typeform_id)
        await self.fake_uow.onboarding_forms.add(onboarding_form)

        # And: a realistic payload (trimmed to essentials) with Portuguese field titles
        payload = {
            "event_id": "01K2G1A24HN0AAGB8KKDKYDT2R",
            "event_type": "form_response",
            "form_response": {
                "form_id": typeform_id,
                "token": "u4m537hfer2ww4ru4m537lusgr3f4kuy",
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

        payload_json = json.dumps(payload)
        headers = {"Content-Type": "application/json"}

        # When: processing the webhook
        success, error, response_id = await process_typeform_webhook(
            payload=payload_json, headers=headers, uow_factory=self.uow_factory
        )

        # Then: processing succeeds and identifiers are stored
        assert success is True, f"processing failed: {error}"
        stored_responses = cast(list, await self.fake_uow.form_responses.get_all())
        assert len(stored_responses) == 1

        stored = stored_responses[0]
        assert stored.client_identifiers is not None
        # Validate specific values
        assert stored.client_identifiers.get("email") == "user@example.com"
        assert stored.client_identifiers.get("phone") == "+5511999999999"
        # Name comes from Portuguese title via keyword 'nome'
        assert (
            "nome" in payload["form_response"]["answers"][0]["field"]["title"].lower()
        )
        assert stored.client_identifiers.get("name") == "Fulano de Tal"
