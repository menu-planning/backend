"""
Data factories for client onboarding domain objects.

This module provides factory functions for creating test instances of:
- Commands (SetupOnboardingFormCommand, UpdateWebhookUrlCommand)
- Events (FormResponseReceived, ClientDataExtracted, OnboardingFormWebhookSetup)

All factories use deterministic test data to ensure consistent test results.
Factories follow the established patterns from recipes_catalog and leverage
existing counter management from tests/utils/counter_manager.py.

Key Features:
- Deterministic test data generation using counter_manager
- Comprehensive attribute validation using check_missing_attributes
- Following recipes_catalog test patterns
- Support for data overrides through **kwargs
- Proper test isolation with counter reset integration

Usage:
    # Create command with defaults
    command = create_setup_onboarding_form_command()
    
    # Create command with overrides
    command = create_setup_onboarding_form_command(user_id=123)
    
    # Create kwargs dict for custom initialization
    kwargs = create_setup_onboarding_form_command_kwargs(user_id=456)
"""

from typing import Dict, Any, Optional

# Import data counters from centralized counter management
from tests.utils.counter_manager import (
    get_next_onboarding_form_id,
    get_next_client_id,
    get_next_webhook_id
)

# Import check_missing_attributes for validation
from tests.utils.utils import check_missing_attributes

# Import command and event classes for validation
from src.contexts.client_onboarding.core.domain.commands.setup_onboarding_form import SetupOnboardingFormCommand
from src.contexts.client_onboarding.core.domain.commands.update_webhook_url import UpdateWebhookUrlCommand
from src.contexts.client_onboarding.core.domain.events.form_response_received import FormResponseReceived
from src.contexts.client_onboarding.core.domain.events.client_data_extracted import ClientDataExtracted
from src.contexts.client_onboarding.core.domain.events.onboarding_form_webhook_setup import OnboardingFormWebhookSetup


def create_setup_onboarding_form_command_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create kwargs dict for SetupOnboardingFormCommand with deterministic data.
    
    Uses counter_manager for consistent test data generation.
    All required command attributes are guaranteed to be present.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required command creation parameters
    """
    form_counter = get_next_onboarding_form_id()
    
    final_kwargs = {
        "user_id": kwargs.get("user_id", form_counter),
        "typeform_id": kwargs.get("typeform_id", f"typeform_{form_counter:03d}"),
        "webhook_url": kwargs.get("webhook_url", f"https://api.example.com/webhooks/onboarding/{form_counter}")
    }
    
    # Validate all required attributes are present
    missing = check_missing_attributes(SetupOnboardingFormCommand, final_kwargs)
    if missing:
        raise ValueError(f"Missing required attributes: {missing}")
    
    return final_kwargs


def create_setup_onboarding_form_command(**kwargs) -> SetupOnboardingFormCommand:
    """
    Create a SetupOnboardingFormCommand with deterministic data and validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        SetupOnboardingFormCommand instance
    """
    command_kwargs = create_setup_onboarding_form_command_kwargs(**kwargs)
    return SetupOnboardingFormCommand(**command_kwargs)


def create_update_webhook_url_command_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create kwargs dict for UpdateWebhookUrlCommand with deterministic data.
    
    Uses counter_manager for consistent test data generation.
    All required command attributes are guaranteed to be present.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required command creation parameters
    """
    webhook_counter = get_next_webhook_id()
    
    final_kwargs = {
        "form_id": kwargs.get("form_id", f"form_{webhook_counter:03d}"),
        "new_webhook_url": kwargs.get("new_webhook_url", f"https://api.example.com/webhooks/updated/{webhook_counter}")
    }
    
    # Validate all required attributes are present
    missing = check_missing_attributes(UpdateWebhookUrlCommand, final_kwargs)
    if missing:
        raise ValueError(f"Missing required attributes: {missing}")
    
    return final_kwargs


def create_update_webhook_url_command(**kwargs) -> UpdateWebhookUrlCommand:
    """
    Create an UpdateWebhookUrlCommand with deterministic data and validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        UpdateWebhookUrlCommand instance
    """
    command_kwargs = create_update_webhook_url_command_kwargs(**kwargs)
    return UpdateWebhookUrlCommand(**command_kwargs)


# Event Factory Functions

def create_form_response_received_event_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create kwargs dict for FormResponseReceived event with deterministic data.
    
    Uses counter_manager for consistent test data generation.
    All required event attributes are guaranteed to be present.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required event creation parameters
    """
    form_counter = get_next_onboarding_form_id()
    
    default_response_data = {
        "form_id": f"typeform_{form_counter:03d}",
        "form_response": {
            "token": f"response_token_{form_counter}",
            "submitted_at": f"2024-01-{form_counter:02d}T10:00:00Z",
            "definition": {
                "id": f"typeform_{form_counter:03d}",
                "title": f"Test Onboarding Form {form_counter}"
            },
            "answers": [
                {
                    "field": {"id": "field_name", "type": "short_text"},
                    "text": f"Test Client {form_counter}"
                },
                {
                    "field": {"id": "field_email", "type": "email"},
                    "email": f"client{form_counter}@example.com"
                }
            ]
        }
    }
    
    final_kwargs = {
        "form_id": kwargs.get("form_id", form_counter),
        "typeform_response_id": kwargs.get("typeform_response_id", f"typeform_response_{form_counter}"),
        "response_data": kwargs.get("response_data", default_response_data),
        "webhook_timestamp": kwargs.get("webhook_timestamp", f"2024-01-{form_counter:02d}T10:00:00Z")
    }
    
    # Validate all required attributes are present
    missing = check_missing_attributes(FormResponseReceived, final_kwargs)
    if missing:
        raise ValueError(f"Missing required attributes: {missing}")
    
    return final_kwargs


def create_form_response_received_event(**kwargs) -> FormResponseReceived:
    """
    Create a FormResponseReceived event with deterministic data and validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        FormResponseReceived event instance
    """
    event_kwargs = create_form_response_received_event_kwargs(**kwargs)
    return FormResponseReceived(**event_kwargs)


def create_client_data_extracted_event_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create kwargs dict for ClientDataExtracted event with deterministic data.
    
    Uses counter_manager for consistent test data generation.
    All required event attributes are guaranteed to be present.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required event creation parameters
    """
    client_counter = get_next_client_id()
    
    default_extracted_data = {
        "client_preferences": {
            "dietary_restrictions": ["vegetarian"],
            "cooking_skill": "beginner",
            "meal_frequency": "daily"
        },
        "household_info": {
            "size": 2,
            "children": False
        }
    }
    
    default_client_identifiers = {
        "name": f"Test Client {client_counter}",
        "email": f"client{client_counter}@example.com",
        "phone": f"+1555{client_counter:04d}"
    }
    
    final_kwargs = {
        "form_response_id": kwargs.get("form_response_id", client_counter),
        "extracted_client_data": kwargs.get("extracted_client_data", default_extracted_data),
        "client_identifiers": kwargs.get("client_identifiers", default_client_identifiers),
        "user_id": kwargs.get("user_id", client_counter)
    }
    
    # Validate all required attributes are present
    missing = check_missing_attributes(ClientDataExtracted, final_kwargs)
    if missing:
        raise ValueError(f"Missing required attributes: {missing}")
    
    return final_kwargs


def create_client_data_extracted_event(**kwargs) -> ClientDataExtracted:
    """
    Create a ClientDataExtracted event with deterministic data and validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ClientDataExtracted event instance
    """
    event_kwargs = create_client_data_extracted_event_kwargs(**kwargs)
    return ClientDataExtracted(**event_kwargs)


def create_onboarding_form_webhook_setup_event_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create kwargs dict for OnboardingFormWebhookSetup event with deterministic data.
    
    Uses counter_manager for consistent test data generation.
    All required event attributes are guaranteed to be present.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required event creation parameters
    """
    form_counter = get_next_onboarding_form_id()
    
    final_kwargs = {
        "user_id": kwargs.get("user_id", form_counter),
        "typeform_id": kwargs.get("typeform_id", f"typeform_{form_counter:03d}"),
        "webhook_url": kwargs.get("webhook_url", f"https://api.example.com/webhooks/onboarding/{form_counter}"),
        "form_id": kwargs.get("form_id", form_counter)
    }
    
    # Validate all required attributes are present
    missing = check_missing_attributes(OnboardingFormWebhookSetup, final_kwargs)
    if missing:
        raise ValueError(f"Missing required attributes: {missing}")
    
    return final_kwargs


def create_onboarding_form_webhook_setup_event(**kwargs) -> OnboardingFormWebhookSetup:
    """
    Create an OnboardingFormWebhookSetup event with deterministic data and validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        OnboardingFormWebhookSetup event instance
    """
    event_kwargs = create_onboarding_form_webhook_setup_event_kwargs(**kwargs)
    return OnboardingFormWebhookSetup(**event_kwargs)


# Utility functions for testing consistency

def get_default_form_response_data(form_counter: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate default form response data structure for testing.
    
    Args:
        form_counter: Counter value for deterministic data, auto-generated if None
        
    Returns:
        Dict representing typical TypeForm response structure
    """
    if form_counter is None:
        form_counter = get_next_onboarding_form_id()
    
    return {
        "form_id": f"typeform_{form_counter:03d}",
        "form_response": {
            "token": f"response_token_{form_counter}",
            "submitted_at": f"2024-01-{form_counter:02d}T10:00:00Z",
            "definition": {
                "id": f"typeform_{form_counter:03d}",
                "title": f"Test Onboarding Form {form_counter}"
            },
            "answers": [
                {
                    "field": {"id": "field_name", "type": "short_text"},
                    "text": f"Test Client {form_counter}"
                },
                {
                    "field": {"id": "field_email", "type": "email"},
                    "email": f"client{form_counter}@example.com"
                }
            ]
        }
    }


def get_default_client_data(client_counter: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate default extracted client data structure for testing.
    
    Args:
        client_counter: Counter value for deterministic data, auto-generated if None
        
    Returns:
        Dict representing typical extracted client preferences
    """
    if client_counter is None:
        client_counter = get_next_client_id()
    
    return {
        "client_preferences": {
            "dietary_restrictions": ["vegetarian"] if client_counter % 2 == 0 else [],
            "cooking_skill": "beginner" if client_counter % 3 == 0 else "intermediate",
            "meal_frequency": "daily"
        },
        "household_info": {
            "size": 2 + (client_counter % 3),
            "children": client_counter % 4 == 0
        }
    } 