"""
Comprehensive behavior-focused tests for Client Onboarding domain commands.

Tests focus on command creation behaviors, field validation, defaults,
and domain rule compliance. No mocks - only actual command behaviors.
"""

import uuid

import pytest
from src.contexts.client_onboarding.core.domain.commands.setup_onboarding_form import (
    SetupOnboardingFormCommand,
)
from src.contexts.client_onboarding.core.domain.commands.update_webhook_url import (
    UpdateWebhookUrlCommand,
)
from tests.contexts.client_onboarding.data_factories.domain_factories import (
    create_setup_onboarding_form_command,
    create_setup_onboarding_form_command_kwargs,
    create_update_webhook_url_command,
    create_update_webhook_url_command_kwargs,
)


class TestSetupOnboardingFormCommandBehaviors:
    """Test SetupOnboardingFormCommand instantiation and validation behaviors."""

    def test_setup_onboarding_form_with_required_fields(self):
        """SetupOnboardingFormCommand should accept all required fields."""
        user_id = uuid.uuid4().hex
        command = SetupOnboardingFormCommand(
            user_id=user_id,
            typeform_id="typeform_001",
            webhook_url="https://api.example.com/webhooks/onboarding/123",
        )

        assert command.user_id == user_id
        assert command.typeform_id == "typeform_001"
        assert command.webhook_url == "https://api.example.com/webhooks/onboarding/123"

    def test_setup_onboarding_form_with_minimal_fields(self):
        """SetupOnboardingFormCommand should work with minimal required fields."""
        user_id = uuid.uuid4().hex
        command = SetupOnboardingFormCommand(
            user_id=user_id, typeform_id="typeform_002"
        )

        assert command.user_id == user_id
        assert command.typeform_id == "typeform_002"
        assert command.webhook_url is None

    def test_setup_onboarding_form_with_optional_webhook_url(self):
        """SetupOnboardingFormCommand should handle optional webhook_url."""
        user_id = uuid.uuid4().hex
        command = SetupOnboardingFormCommand(
            user_id=user_id, typeform_id="typeform_003", webhook_url=None
        )

        assert command.user_id == user_id
        assert command.typeform_id == "typeform_003"
        assert command.webhook_url is None

    def test_setup_onboarding_form_requires_essential_fields(self):
        """SetupOnboardingFormCommand should require user_id and typeform_id."""
        with pytest.raises(TypeError):  # Missing required arguments
            SetupOnboardingFormCommand()  # type: ignore[call-arg]

        with pytest.raises(TypeError):  # Missing some required arguments
            SetupOnboardingFormCommand(user_id=uuid.uuid4().hex)  # type: ignore[call-arg]

        with pytest.raises(TypeError):  # Missing some required arguments
            SetupOnboardingFormCommand(typeform_id="typeform_001")  # type: ignore[call-arg]

    def test_setup_onboarding_form_with_factory(self):
        """SetupOnboardingFormCommand should work with factory functions."""
        command = create_setup_onboarding_form_command()

        assert command.user_id is not None
        assert command.typeform_id is not None
        assert command.webhook_url is not None
        assert isinstance(command.user_id, int)
        assert isinstance(command.typeform_id, str)
        assert isinstance(command.webhook_url, str)

    def test_setup_onboarding_form_factory_with_overrides(self):
        """SetupOnboardingFormCommand factory should accept overrides."""
        custom_user_id = uuid.uuid4().hex
        custom_typeform_id = "custom_typeform"
        custom_webhook_url = "https://custom.webhook.url"

        command = create_setup_onboarding_form_command(
            user_id=custom_user_id,
            typeform_id=custom_typeform_id,
            webhook_url=custom_webhook_url,
        )

        assert command.user_id == custom_user_id
        assert command.typeform_id == custom_typeform_id
        assert command.webhook_url == custom_webhook_url

    def test_setup_onboarding_form_kwargs_factory(self):
        """SetupOnboardingFormCommand kwargs factory should provide valid data."""
        kwargs = create_setup_onboarding_form_command_kwargs()
        command = SetupOnboardingFormCommand(**kwargs)

        assert command.user_id == kwargs["user_id"]
        assert command.typeform_id == kwargs["typeform_id"]
        assert command.webhook_url == kwargs["webhook_url"]


class TestUpdateWebhookUrlCommandBehaviors:
    """Test UpdateWebhookUrlCommand instantiation and validation behaviors."""

    def test_update_webhook_url_with_required_fields(self):
        """UpdateWebhookUrlCommand should accept all required fields."""
        command = UpdateWebhookUrlCommand(
            form_id="form_001",
            new_webhook_url="https://api.example.com/webhooks/updated/001",
        )

        assert command.form_id == "form_001"
        assert command.new_webhook_url == "https://api.example.com/webhooks/updated/001"

    def test_update_webhook_url_requires_essential_fields(self):
        """UpdateWebhookUrlCommand should require form_id and new_webhook_url."""
        with pytest.raises(TypeError):  # Missing required arguments
            UpdateWebhookUrlCommand()  # type: ignore[call-arg]

        with pytest.raises(TypeError):  # Missing some required arguments
            UpdateWebhookUrlCommand(form_id="form_001")  # type: ignore[call-arg]

        with pytest.raises(TypeError):  # Missing some required arguments
            UpdateWebhookUrlCommand(new_webhook_url="https://example.com")  # type: ignore[call-arg]

    def test_update_webhook_url_with_factory(self):
        """UpdateWebhookUrlCommand should work with factory functions."""
        command = create_update_webhook_url_command()

        assert command.form_id is not None
        assert command.new_webhook_url is not None
        assert isinstance(command.form_id, str)
        assert isinstance(command.new_webhook_url, str)

    def test_update_webhook_url_factory_with_overrides(self):
        """UpdateWebhookUrlCommand factory should accept overrides."""
        custom_form_id = "custom_form_123"
        custom_webhook_url = "https://custom.webhook.updated.url"

        command = create_update_webhook_url_command(
            form_id=custom_form_id, new_webhook_url=custom_webhook_url
        )

        assert command.form_id == custom_form_id
        assert command.new_webhook_url == custom_webhook_url

    def test_update_webhook_url_kwargs_factory(self):
        """UpdateWebhookUrlCommand kwargs factory should provide valid data."""
        kwargs = create_update_webhook_url_command_kwargs()
        command = UpdateWebhookUrlCommand(**kwargs)

        assert command.form_id == kwargs["form_id"]
        assert command.new_webhook_url == kwargs["new_webhook_url"]


class TestCommandFieldValidationBehaviors:
    """Test command field validation and edge cases."""

    def test_commands_with_empty_string_fields(self):
        """Commands should handle empty string fields appropriately."""
        # Empty strings should be accepted but not recommended
        setup_command = SetupOnboardingFormCommand(
            user_id=uuid.uuid4().hex,
            typeform_id="",  # Empty string
            webhook_url="",  # Empty string
        )

        assert setup_command.typeform_id == ""
        assert setup_command.webhook_url == ""

        update_command = UpdateWebhookUrlCommand(
            form_id="", new_webhook_url=""  # Empty string  # Empty string
        )

        assert update_command.form_id == ""
        assert update_command.new_webhook_url == ""

    def test_commands_with_various_data_types(self):
        """Commands should work with various appropriate data types."""
        # Test with different user_id types
        setup_command_int = SetupOnboardingFormCommand(
            user_id=uuid.uuid4().hex, typeform_id="typeform_001"
        )
        assert setup_command_int.user_id == uuid.uuid4().hex

        # Test with string form_id variations
        update_command = UpdateWebhookUrlCommand(
            form_id="form-with-dashes-123",
            new_webhook_url="https://api.example.com/webhooks/special-chars_test",
        )
        assert "dashes" in update_command.form_id
        assert "special-chars" in update_command.new_webhook_url

    def test_command_factories_produce_consistent_data(self):
        """Command factories should produce consistent, deterministic data."""
        # Multiple calls should produce different but consistent data
        command1 = create_setup_onboarding_form_command()
        command2 = create_setup_onboarding_form_command()

        # Should be different instances with different counter-based data
        assert command1.user_id != command2.user_id
        assert command1.typeform_id != command2.typeform_id
        assert command1.webhook_url != command2.webhook_url

        # But format should be consistent
        assert "typeform_" in command1.typeform_id
        assert "typeform_" in command2.typeform_id
        assert (
            command1.webhook_url is not None
            and "webhooks/onboarding" in command1.webhook_url
        )
        assert (
            command2.webhook_url is not None
            and "webhooks/onboarding" in command2.webhook_url
        )

    def test_command_factory_validation_integration(self):
        """Command factories should integrate with validation utilities."""
        # Test that factories produce valid kwargs that pass validation
        setup_kwargs = create_setup_onboarding_form_command_kwargs()
        update_kwargs = create_update_webhook_url_command_kwargs()

        # Should not raise any validation errors
        setup_command = SetupOnboardingFormCommand(**setup_kwargs)
        update_command = UpdateWebhookUrlCommand(**update_kwargs)

        assert setup_command is not None
        assert update_command is not None
