"""
Test data factories for client_onboarding context

Centralized imports for all data factory functions following
the recipes_catalog pattern.
"""

# Import factories as they are created
from .client_factories import (
    create_setup_onboarding_form_command_kwargs,
    create_setup_onboarding_form_command,
    create_update_webhook_url_command_kwargs,
    create_update_webhook_url_command,
    create_form_response_received_event_kwargs,
    create_form_response_received_event,
    create_client_data_extracted_event_kwargs,
    create_client_data_extracted_event,
    create_onboarding_form_webhook_setup_event_kwargs,
    create_onboarding_form_webhook_setup_event,
    create_onboarding_form_kwargs,
    create_onboarding_form,
    create_restaurant_onboarding_form,
    create_catering_onboarding_form,
    create_complete_onboarding_scenario,
)

from .domain_factories import (
    get_default_form_response_data,
    get_default_client_data,
)

from .typeform_factories import (
    create_typeform_webhook_payload,
)

# Explicitly declare what should be exported
__all__ = [
    # Command factories
    "create_setup_onboarding_form_command_kwargs",
    "create_setup_onboarding_form_command",
    "create_update_webhook_url_command_kwargs",
    "create_update_webhook_url_command",
    
    # Event factories
    "create_form_response_received_event_kwargs",
    "create_form_response_received_event",
    "create_client_data_extracted_event_kwargs",
    "create_client_data_extracted_event",
    "create_onboarding_form_webhook_setup_event_kwargs",
    "create_onboarding_form_webhook_setup_event",
    
    # Form factories
    "create_onboarding_form_kwargs",
    "create_onboarding_form",
    "create_restaurant_onboarding_form",
    "create_catering_onboarding_form",
    
    # Scenario factories
    "create_complete_onboarding_scenario",
    
    # Default data utilities
    "get_default_form_response_data",
    "get_default_client_data",
    
    # Webhook factories
    "create_typeform_webhook_payload",
] 