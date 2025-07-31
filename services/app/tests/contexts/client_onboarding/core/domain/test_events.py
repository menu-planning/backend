"""
Comprehensive behavior-focused tests for Client Onboarding domain events.

Tests focus on event creation behaviors, field validation, defaults,
and domain rule compliance. No mocks - only actual event behaviors.
"""

import pytest
import uuid

from src.contexts.client_onboarding.core.domain.events.form_response_received import FormResponseReceived
from src.contexts.client_onboarding.core.domain.events.client_data_extracted import ClientDataExtracted
from src.contexts.client_onboarding.core.domain.events.onboarding_form_webhook_setup import OnboardingFormWebhookSetup


class TestFormResponseReceivedEventBehaviors:
    """Test FormResponseReceived event instantiation and validation behaviors."""
    
    def test_form_response_received_with_required_fields(self):
        """FormResponseReceived should accept all required fields."""
        response_data = {
            "event_id": "event_001",
            "event_type": "form_response",
            "form_response": {
                "form_id": "typeform_001",
                "token": "token_12345678",
                "answers": [
                    {"field": {"id": "field_name", "type": "short_text"}, "type": "text", "text": "Test Client"}
                ]
            }
        }
        
        event = FormResponseReceived(
            form_id=123,
            typeform_response_id="typeform_resp_001",
            response_data=response_data,
            webhook_timestamp="2024-01-01T12:00:00Z"
        )
        
        assert event.form_id == 123
        assert event.typeform_response_id == "typeform_resp_001"
        assert event.response_data == response_data
        assert event.webhook_timestamp == "2024-01-01T12:00:00Z"
        assert event.id is not None
        # Verify UUID is valid
        uuid.UUID(event.id)
    
    def test_form_response_received_with_custom_id(self):
        """FormResponseReceived should accept custom ID."""
        custom_id = str(uuid.uuid4())
        response_data = {"test": "data"}
        
        event = FormResponseReceived(
            form_id=456,
            typeform_response_id="typeform_resp_002",
            response_data=response_data,
            webhook_timestamp="2024-01-01T12:30:00Z",
            id=custom_id
        )
        
        assert event.id == custom_id
    
    def test_form_response_received_requires_essential_fields(self):
        """FormResponseReceived should require form_id, typeform_response_id, response_data, and webhook_timestamp."""
        with pytest.raises(TypeError):  # Missing required arguments
            FormResponseReceived()  # type: ignore
        
        with pytest.raises(TypeError):  # Missing some required arguments
            FormResponseReceived(form_id=123)  # type: ignore
    
    def test_form_response_received_with_complex_response_data(self):
        """FormResponseReceived should handle complex TypeForm response structure."""
        complex_response_data = {
            "event_id": "event_complex_001",
            "event_type": "form_response",
            "form_response": {
                "form_id": "typeform_restaurant_form",
                "token": "token_complex_12345678",
                "landed_at": "2024-01-01T12:00:00Z",
                "submitted_at": "2024-01-01T12:05:30Z",
                "answers": [
                    {
                        "field": {"id": "field_name", "type": "short_text"},
                        "type": "text",
                        "text": "Restaurant ABC"
                    },
                    {
                        "field": {"id": "field_email", "type": "email"},
                        "type": "email",
                        "email": "owner@restaurantabc.com"
                    },
                    {
                        "field": {"id": "field_cuisine", "type": "multiple_choice"},
                        "type": "choice",
                        "choice": {"label": "Italian"}
                    }
                ]
            }
        }
        
        event = FormResponseReceived(
            form_id=789,
            typeform_response_id="typeform_resp_complex",
            response_data=complex_response_data,
            webhook_timestamp="2024-01-01T12:05:35Z"
        )
        
        assert event.response_data["form_response"]["token"] == "token_complex_12345678"
        assert len(event.response_data["form_response"]["answers"]) == 3
    
    def test_form_response_received_with_empty_response_data(self):
        """FormResponseReceived should handle empty response data."""
        event = FormResponseReceived(
            form_id=999,
            typeform_response_id="typeform_resp_empty",
            response_data={},
            webhook_timestamp="2024-01-01T12:00:00Z"
        )
        
        assert event.response_data == {}


class TestClientDataExtractedEventBehaviors:
    """Test ClientDataExtracted event instantiation and validation behaviors."""
    
    def test_client_data_extracted_with_required_fields(self):
        """ClientDataExtracted should accept all required fields."""
        extracted_data = {
            "name": "Restaurant XYZ",
            "email": "contact@restaurantxyz.com",
            "business_type": "restaurant",
            "cuisine_types": ["italian", "american"]
        }
        
        client_identifiers = {
            "name": "Restaurant XYZ",
            "email": "contact@restaurantxyz.com"
        }
        
        event = ClientDataExtracted(
            form_response_id=123,
            extracted_client_data=extracted_data,
            client_identifiers=client_identifiers,
            user_id=456
        )
        
        assert event.form_response_id == 123
        assert event.extracted_client_data == extracted_data
        assert event.client_identifiers == client_identifiers
        assert event.user_id == 456
        assert event.id is not None
        # Verify UUID is valid
        uuid.UUID(event.id)
    
    def test_client_data_extracted_with_custom_id(self):
        """ClientDataExtracted should accept custom ID."""
        custom_id = str(uuid.uuid4())
        
        event = ClientDataExtracted(
            form_response_id=789,
            extracted_client_data={"name": "Test"},
            client_identifiers={"name": "Test"},
            user_id=999,
            id=custom_id
        )
        
        assert event.id == custom_id
    
    def test_client_data_extracted_requires_essential_fields(self):
        """ClientDataExtracted should require form_response_id, extracted_client_data, client_identifiers, and user_id."""
        with pytest.raises(TypeError):  # Missing required arguments
            ClientDataExtracted()  # type: ignore
        
        with pytest.raises(TypeError):  # Missing some required arguments
            ClientDataExtracted(form_response_id=123)  # type: ignore
    
    def test_client_data_extracted_with_restaurant_data(self):
        """ClientDataExtracted should handle restaurant-specific data structure."""
        restaurant_data = {
            "name": "Mama's Italian Kitchen",
            "email": "info@mamasitalian.com",
            "phone": "+15551234567",
            "business_type": "restaurant",
            "cuisine_types": ["italian", "mediterranean"],
            "service_type": "dine_in",
            "seating_capacity": 45,
            "address": {
                "street": "123 Main St",
                "city": "Foodville",
                "state": "CA",
                "zip": "12345"
            },
            "preferences": {
                "dietary_accommodations": ["vegetarian", "gluten_free"],
                "meal_frequency": "daily",
                "menu_style": "traditional"
            }
        }
        
        client_identifiers = {
            "name": "Mama's Italian Kitchen",
            "email": "info@mamasitalian.com",
            "phone": "+15551234567"
        }
        
        event = ClientDataExtracted(
            form_response_id=101,
            extracted_client_data=restaurant_data,
            client_identifiers=client_identifiers,
            user_id=202
        )
        
        assert event.extracted_client_data["business_type"] == "restaurant"
        assert "italian" in event.extracted_client_data["cuisine_types"]
        assert event.client_identifiers["email"] == "info@mamasitalian.com"
    
    def test_client_data_extracted_with_catering_data(self):
        """ClientDataExtracted should handle catering-specific data structure."""
        catering_data = {
            "name": "Elite Catering Services",
            "email": "bookings@elitecatering.com",
            "business_type": "catering",
            "service_type": "delivery",
            "event_types": ["corporate", "wedding", "private"],
            "capacity": 500,
            "preferences": {
                "cuisine_specialties": ["asian_fusion", "american"],
                "service_areas": ["downtown", "business_district"]
            }
        }
        
        client_identifiers = {
            "name": "Elite Catering Services", 
            "email": "bookings@elitecatering.com"
        }
        
        event = ClientDataExtracted(
            form_response_id=301,
            extracted_client_data=catering_data,
            client_identifiers=client_identifiers,
            user_id=402
        )
        
        assert event.extracted_client_data["business_type"] == "catering"
        assert "corporate" in event.extracted_client_data["event_types"]


class TestOnboardingFormWebhookSetupEventBehaviors:
    """Test OnboardingFormWebhookSetup event instantiation and validation behaviors."""
    
    def test_onboarding_form_webhook_setup_with_required_fields(self):
        """OnboardingFormWebhookSetup should accept all required fields."""
        event = OnboardingFormWebhookSetup(
            user_id=123,
            typeform_id="typeform_001",
            webhook_url="https://api.example.com/webhooks/onboarding/123",
            form_id=456
        )
        
        assert event.user_id == 123
        assert event.typeform_id == "typeform_001"
        assert event.webhook_url == "https://api.example.com/webhooks/onboarding/123"
        assert event.form_id == 456
        assert event.id is not None
        # Verify UUID is valid
        uuid.UUID(event.id)
    
    def test_onboarding_form_webhook_setup_with_custom_id(self):
        """OnboardingFormWebhookSetup should accept custom ID."""
        custom_id = str(uuid.uuid4())
        
        event = OnboardingFormWebhookSetup(
            user_id=789,
            typeform_id="typeform_002",
            webhook_url="https://api.example.com/webhooks/custom",
            form_id=999,
            id=custom_id
        )
        
        assert event.id == custom_id
    
    def test_onboarding_form_webhook_setup_requires_essential_fields(self):
        """OnboardingFormWebhookSetup should require user_id, typeform_id, webhook_url, and form_id."""
        with pytest.raises(TypeError):  # Missing required arguments
            OnboardingFormWebhookSetup()  # type: ignore
        
        with pytest.raises(TypeError):  # Missing some required arguments
            OnboardingFormWebhookSetup(user_id=123)  # type: ignore
    
    def test_onboarding_form_webhook_setup_with_different_webhook_types(self):
        """OnboardingFormWebhookSetup should handle different webhook URL formats."""
        # Test restaurant webhook
        restaurant_event = OnboardingFormWebhookSetup(
            user_id=123,
            typeform_id="restaurant_onboarding_form",
            webhook_url="https://api.example.com/webhooks/restaurant/123",
            form_id=456
        )
        
        assert "restaurant" in restaurant_event.webhook_url
        assert restaurant_event.typeform_id == "restaurant_onboarding_form"
        
        # Test catering webhook
        catering_event = OnboardingFormWebhookSetup(
            user_id=789,
            typeform_id="catering_onboarding_form", 
            webhook_url="https://api.example.com/webhooks/catering/789",
            form_id=999
        )
        
        assert "catering" in catering_event.webhook_url
        assert catering_event.typeform_id == "catering_onboarding_form"


class TestEventFieldValidationBehaviors:
    """Test event field validation and edge cases."""
    
    def test_events_with_uuid_uniqueness(self):
        """Event UUID generation should produce unique IDs."""
        event1 = FormResponseReceived(
            form_id=1,
            typeform_response_id="resp_1",
            response_data={"test": "data1"},
            webhook_timestamp="2024-01-01T12:00:00Z"
        )
        
        event2 = FormResponseReceived(
            form_id=2,
            typeform_response_id="resp_2",
            response_data={"test": "data2"},
            webhook_timestamp="2024-01-01T12:01:00Z"
        )
        
        # UUIDs should be different
        assert event1.id != event2.id
        
        # Both should be valid UUIDs
        uuid.UUID(event1.id)
        uuid.UUID(event2.id)
    
    def test_events_with_large_data_structures(self):
        """Events should handle large data structures appropriately."""
        # Large response data
        large_response_data = {
            "event_id": "large_event_001",
            "form_response": {
                "answers": [
                    {"field": {"id": f"field_{i}"}, "text": f"Answer {i}"}
                    for i in range(100)  # 100 form fields
                ]
            }
        }
        
        event = FormResponseReceived(
            form_id=999,
            typeform_response_id="large_response",
            response_data=large_response_data,
            webhook_timestamp="2024-01-01T12:00:00Z"
        )
        
        assert len(event.response_data["form_response"]["answers"]) == 100
        
        # Large extracted data
        large_client_data = {
            f"field_{i}": f"value_{i}" for i in range(50)
        }
        
        client_event = ClientDataExtracted(
            form_response_id=999,
            extracted_client_data=large_client_data,
            client_identifiers={"name": "Large Data Client"},
            user_id=123
        )
        
        assert len(client_event.extracted_client_data) == 50
    
    def test_events_with_special_characters_in_data(self):
        """Events should handle special characters and encoding."""
        special_response_data = {
            "form_response": {
                "answers": [
                    {"text": "Café Münchën & Restaurant 🍝"},
                    {"email": "test@münchen-café.com"},
                    {"text": "Specialties: crème brûlée, naïve cuisine"}
                ]
            }
        }
        
        event = FormResponseReceived(
            form_id=123,
            typeform_response_id="special_chars_response",
            response_data=special_response_data,
            webhook_timestamp="2024-01-01T12:00:00Z"
        )
        
        # Should preserve special characters
        answers = event.response_data["form_response"]["answers"]
        assert "🍝" in answers[0]["text"]
        assert "münchen" in answers[1]["email"]
        assert "crème brûlée" in answers[2]["text"] 