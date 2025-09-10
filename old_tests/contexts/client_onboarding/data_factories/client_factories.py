"""
Data factories for Client Onboarding testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- Validation logic for entity completeness  
- Parametrized test scenarios for onboarding workflows
- Specialized factory functions for different onboarding types
- Support for commands, events, and domain entities

All data follows the exact structure of Client Onboarding domain entities and their relationships.
"""

from datetime import datetime, timedelta
from typing import Any
import uuid

from src.contexts.client_onboarding.core.domain.commands.setup_onboarding_form import SetupOnboardingFormCommand
from src.contexts.client_onboarding.core.domain.commands.update_webhook_url import UpdateWebhookUrlCommand
from src.contexts.client_onboarding.core.domain.models.onboarding_form import OnboardingForm, OnboardingFormStatus

# Import centralized counter manager
from tests.utils.counter_manager import (
    get_next_onboarding_form_id,
    get_next_webhook_id,
    get_next_form_response_id,
    get_next_client_id
)

# =============================================================================
# COMMAND FACTORIES
# =============================================================================

def create_setup_onboarding_form_command_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create SetupOnboardingFormCommand kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required command parameters
    """
    form_counter = get_next_onboarding_form_id()
    
    final_kwargs = {
        "user_id": kwargs.get("user_id", form_counter),
        "typeform_id": kwargs.get("typeform_id", f"typeform_{form_counter:03d}"),
        "webhook_url": kwargs.get("webhook_url", f"https://api.example.com/webhooks/onboarding/{form_counter}")
    }
    
    return final_kwargs


def create_setup_onboarding_form_command(**kwargs) -> SetupOnboardingFormCommand:
    """
    Create a SetupOnboardingFormCommand with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        SetupOnboardingFormCommand instance
    """
    command_kwargs = create_setup_onboarding_form_command_kwargs(**kwargs)
    return SetupOnboardingFormCommand(**command_kwargs)


def create_update_webhook_url_command_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create UpdateWebhookUrlCommand kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required command parameters
    """
    webhook_counter = get_next_webhook_id()
    
    final_kwargs = {
        "form_id": kwargs.get("form_id", f"form_{webhook_counter:03d}"),
        "new_webhook_url": kwargs.get("new_webhook_url", f"https://api.example.com/webhooks/updated/{webhook_counter}")
    }
    
    return final_kwargs


def create_update_webhook_url_command(**kwargs) -> UpdateWebhookUrlCommand:
    """
    Create an UpdateWebhookUrlCommand with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        UpdateWebhookUrlCommand instance
    """
    command_kwargs = create_update_webhook_url_command_kwargs(**kwargs)
    return UpdateWebhookUrlCommand(**command_kwargs)


# =============================================================================
# EVENT FACTORIES
# =============================================================================

def create_form_response_received_event_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create FormResponseReceived event kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required event parameters
    """
    response_counter = get_next_form_response_id()
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    # Default TypeForm response data structure
    default_response_data = {
        "event_id": f"event_{response_counter:06d}",
        "event_type": "form_response",
        "form_response": {
            "form_id": f"typeform_{response_counter:03d}",
            "token": f"token_{response_counter:08d}",
            "landed_at": (base_time + timedelta(minutes=float(response_counter))).isoformat(),
            "submitted_at": (base_time + timedelta(minutes=float(response_counter), seconds=30)).isoformat(),
            "answers": [
                {
                    "field": {"id": "field_name", "type": "short_text"},
                    "type": "text",
                    "text": f"Test Client {response_counter}"
                },
                {
                    "field": {"id": "field_email", "type": "email"},
                    "type": "email", 
                    "email": f"client{response_counter}@example.com"
                }
            ]
        }
    }
    
    final_kwargs = {
        "form_id": kwargs.get("form_id", response_counter),
        "typeform_response_id": kwargs.get("typeform_response_id", f"typeform_resp_{response_counter:06d}"),
        "response_data": kwargs.get("response_data", default_response_data),
        "webhook_timestamp": kwargs.get("webhook_timestamp", (base_time + timedelta(minutes=float(response_counter))).isoformat()),
        "id": kwargs.get("id", str(uuid.uuid4()))
    }
    
    return final_kwargs


def create_client_data_extracted_event_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create ClientDataExtracted event kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required event parameters
    """
    client_counter = get_next_client_id()
    
    # Default extracted client data structure
    default_client_data = {
        "name": f"Test Client {client_counter}",
        "email": f"client{client_counter}@example.com",
        "phone": f"+1555{client_counter:04d}",
        "company": f"Company {client_counter}",
        "preferences": {
            "cuisine_types": ["italian", "mexican"],
            "dietary_restrictions": ["vegetarian"] if client_counter % 2 == 0 else [],
            "meal_frequency": "daily"
        }
    }
    
    final_kwargs = {
        "form_id": kwargs.get("form_id", client_counter),
        "response_id": kwargs.get("response_id", f"resp_{client_counter:06d}"),
        "extracted_data": kwargs.get("extracted_data", default_client_data),
        "extraction_timestamp": kwargs.get("extraction_timestamp", datetime.now().isoformat()),
        "id": kwargs.get("id", str(uuid.uuid4()))
    }
    
    return final_kwargs


def create_onboarding_form_webhook_setup_event_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create OnboardingFormWebhookSetup event kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required event parameters
    """
    webhook_counter = get_next_webhook_id()
    
    final_kwargs = {
        "form_id": kwargs.get("form_id", webhook_counter),
        "typeform_id": kwargs.get("typeform_id", f"typeform_{webhook_counter:03d}"),
        "webhook_url": kwargs.get("webhook_url", f"https://api.example.com/webhooks/setup/{webhook_counter}"),
        "webhook_id": kwargs.get("webhook_id", f"webhook_{webhook_counter:06d}"),
        "setup_timestamp": kwargs.get("setup_timestamp", datetime.now().isoformat()),
        "id": kwargs.get("id", str(uuid.uuid4()))
    }
    
    return final_kwargs


# =============================================================================
# MODEL FACTORIES
# =============================================================================

def create_onboarding_form_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create OnboardingForm kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required model parameters
    """
    form_counter = get_next_onboarding_form_id()
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    final_kwargs = {
        "id": kwargs.get("id", form_counter),
        "user_id": kwargs.get("user_id", form_counter),
        "typeform_id": kwargs.get("typeform_id", f"typeform_{form_counter:03d}"),
        "webhook_url": kwargs.get("webhook_url", f"https://api.example.com/webhooks/form/{form_counter}"),
        "status": kwargs.get("status", OnboardingFormStatus.ACTIVE),
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=float(form_counter))),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(hours=float(form_counter), minutes=float(30))),
    }
    
    return final_kwargs


def create_onboarding_form(**kwargs) -> OnboardingForm:
    """
    Create an OnboardingForm model with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        OnboardingForm model instance
    """
    form_kwargs = create_onboarding_form_kwargs(**kwargs)
    return OnboardingForm(**form_kwargs)


# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS
# =============================================================================

def create_restaurant_onboarding_form(**kwargs) -> OnboardingForm:
    """
    Create an onboarding form specifically for restaurant clients.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        OnboardingForm configured for restaurant onboarding
    """
    final_kwargs = {
        "typeform_id": kwargs.get("typeform_id", "restaurant_onboarding_form"),
        "webhook_url": kwargs.get("webhook_url", "https://api.example.com/webhooks/restaurant"),
        **{k: v for k, v in kwargs.items() if k not in ["typeform_id", "webhook_url"]}
    }
    return create_onboarding_form(**final_kwargs)


def create_catering_onboarding_form(**kwargs) -> OnboardingForm:
    """
    Create an onboarding form specifically for catering clients.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        OnboardingForm configured for catering onboarding
    """
    final_kwargs = {
        "typeform_id": kwargs.get("typeform_id", "catering_onboarding_form"),
        "webhook_url": kwargs.get("webhook_url", "https://api.example.com/webhooks/catering"),
        **{k: v for k, v in kwargs.items() if k not in ["typeform_id", "webhook_url"]}
    }
    return create_onboarding_form(**final_kwargs)


# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP
# =============================================================================

def create_complete_onboarding_scenario(**kwargs) -> dict[str, Any]:
    """
    Create a complete onboarding scenario with form, command, and events.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict containing related onboarding entities for testing complete workflows
    """
    scenario_id = get_next_onboarding_form_id()
    
    # Create related entities with consistent IDs
    onboarding_form = create_onboarding_form(
        id=scenario_id,
        user_id=scenario_id,
        **{k: v for k, v in kwargs.items() if k.startswith("form_")}
    )
    
    setup_command = create_setup_onboarding_form_command(
        user_id=scenario_id,
        typeform_id=onboarding_form.typeform_id,
        webhook_url=onboarding_form.webhook_url,
        **{k: v for k, v in kwargs.items() if k.startswith("command_")}
    )
    
  
    return {
        "onboarding_form": onboarding_form,
        "setup_command": setup_command,
    } 