"""
Tests for Form Commands with URL Parsing

Test that API schemas correctly handle Typeform URLs and extract form IDs.
"""

import pytest
from pydantic import HttpUrl, ValidationError
# NOTE: CreateFormCommand import removed; test appears outdated relative to current schemas.
from src.contexts.client_onboarding.core.adapters.api_schemas.form_config import FormConfigurationRequest, FormValidationRequest
from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_setup_onboarding_form import ApiSetupOnboardingForm


class TestCreateFormCommandUrlParsing:
    """Test CreateFormCommand with URL parsing."""
    
    def test_create_form_with_typeform_url(self):
        """Test creating form command with Typeform URL."""
        command = ApiSetupOnboardingForm(
            typeform_url="https://example.typeform.com/to/rAndomFormID",
            webhook_url=HttpUrl("https://api.example.com/webhooks/typeform")
        ) # type: ignore[call-arg]
        
        # Should extract form ID from URL
        assert command.typeform_id == "rAndomFormID"
        assert command.typeform_url == "rAndomFormID"  # Validator returns the form ID
    
    def test_create_form_with_direct_form_id(self):
        """Test creating form command with direct form ID."""
        command = ApiSetupOnboardingForm(
            typeform_url="rAndomFormID",
            webhook_url=HttpUrl("https://api.example.com/webhooks/typeform")
        ) # type: ignore[call-arg]
        
        # Should accept direct form ID
        assert command.typeform_id == "rAndomFormID"
        assert command.typeform_url == "rAndomFormID"
    
    def test_create_form_with_complex_url(self):
        """Test with URL containing query parameters."""
        command = ApiSetupOnboardingForm(
            typeform_url="https://example.typeform.com/to/form123?embed=true&source=website",
            webhook_url=HttpUrl("https://api.example.com/webhooks/typeform")
        ) # type: ignore[call-arg]
        
        assert command.typeform_id == "form123"
        assert command.typeform_url == "form123"
    
    def test_create_form_invalid_url(self):
        """Test validation error for invalid URL."""
        with pytest.raises(ValidationError) as exc_info:
            ApiSetupOnboardingForm(
                typeform_url="https://not-typeform.com/form/123",
                webhook_url=HttpUrl("https://api.example.com/webhooks/typeform")
            ) # type: ignore[call-arg]
        
        error = exc_info.value.errors()[0]
        assert "Invalid Typeform URL or form ID" in error["msg"]
    
    def test_create_form_with_optional_fields(self):
        """Test creating form with all optional fields."""
        command = ApiSetupOnboardingForm(
            typeform_url="https://example.typeform.com/to/testForm456",
            webhook_url=HttpUrl("https://api.example.com/webhooks/typeform"),
            form_title="Test Onboarding Form",
            form_description="A test form for client onboarding",
            auto_activate=False,
        )
        
        assert command.typeform_id == "testForm456"
        assert command.form_title == "Test Onboarding Form"
        assert command.auto_activate is False


class TestFormConfigurationRequestUrlParsing:
    """Test FormConfigurationRequest with URL parsing."""
    
    def test_form_config_with_url(self):
        """Test form configuration with Typeform URL."""
        config = FormConfigurationRequest(
            typeform_url="https://example.typeform.com/to/configTest123",
            webhook_url=HttpUrl("https://api.example.com/webhooks/typeform"),
            form_title="Configuration Test Form"
        ) # type: ignore[call-arg]
        
        assert config.typeform_id == "configTest123"
        assert config.form_title == "Configuration Test Form"
    
    def test_form_config_with_direct_id(self):
        """Test form configuration with direct form ID."""
        config = FormConfigurationRequest(
            typeform_url="directId789",
            webhook_url=HttpUrl("https://api.example.com/webhooks/typeform")
        ) # type: ignore[call-arg]
        
        assert config.typeform_id == "directId789"


class TestFormValidationRequestUrlParsing:
    """Test FormValidationRequest with URL parsing."""
    
    def test_form_validation_with_url(self):
        """Test form validation with Typeform URL."""
        validation = FormValidationRequest(
            typeform_url="https://example.typeform.com/to/validateMe999"
        )
        
        assert validation.typeform_id == "validateMe999"
    
    def test_form_validation_with_id(self):
        """Test form validation with direct form ID."""
        validation = FormValidationRequest(
            typeform_url="validateDirect555"
        )
        
        assert validation.typeform_id == "validateDirect555"


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_typeform_url(self):
        """Test validation error for empty URL."""
        with pytest.raises(ValidationError) as exc_info:
            ApiSetupOnboardingForm(
                typeform_url="",
                webhook_url=HttpUrl("https://api.example.com/webhooks/typeform")
            ) # type: ignore[call-arg]
        
        error = exc_info.value.errors()[0]
        assert "String should have at least 1 character" in error["msg"]
    
    def test_whitespace_only_url(self):
        """Test validation error for whitespace-only URL."""
        with pytest.raises(ValidationError) as exc_info:
            ApiSetupOnboardingForm(
                typeform_url="   ",
                webhook_url=HttpUrl("https://api.example.com/webhooks/typeform")
            ) # type: ignore[call-arg]
        
        error = exc_info.value.errors()[0]
        assert "Invalid Typeform URL or form ID" in error["msg"]
    
    def test_invalid_form_id_characters(self):
        """Test validation error for invalid form ID characters."""
        with pytest.raises(ValidationError) as exc_info:
            ApiSetupOnboardingForm(
                typeform_url="invalid@form#id!",
                webhook_url=HttpUrl("https://api.example.com/webhooks/typeform")
            ) # type: ignore[call-arg]
        
        error = exc_info.value.errors()[0]
        assert "Invalid Typeform URL or form ID" in error["msg"]
    
    def test_form_id_too_short(self):
        """Test validation error for too short form ID."""
        with pytest.raises(ValidationError) as exc_info:
            ApiSetupOnboardingForm(
                typeform_url="ab",
                webhook_url=HttpUrl("https://api.example.com/webhooks/typeform")
            ) # type: ignore[call-arg]
        
        error = exc_info.value.errors()[0]
        assert "Invalid Typeform URL or form ID" in error["msg"]