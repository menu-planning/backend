"""
TypeForm API Response Factories

Generates realistic TypeForm API responses for testing purposes.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- TypeForm form response factories
- Webhook payload factories  
- API response data factories
- Validation and error scenario factories

All data follows the exact structure of TypeForm API responses.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from tests.utils.counter_manager import (
    get_next_typeform_api_counter,
    get_next_webhook_counter,
    get_next_form_response_counter,
    get_next_client_counter
)

# =============================================================================
# FORM RESPONSE FACTORIES
# =============================================================================

def create_form_info_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create TypeForm FormInfo response kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required FormInfo parameters
    """
    counter = get_next_typeform_api_counter()
    
    final_kwargs = {
        "id": kwargs.get("id", f"test_form_{counter:03d}"),
        "title": kwargs.get("title", f"Test Onboarding Form {counter}"),
        "type": kwargs.get("type", "quiz"),  # Required field
        "description": kwargs.get("description", f"Test form description for testing - Form {counter}"),
        "created_at": kwargs.get("created_at", "2024-01-01T00:00:00Z"),
        "updated_at": kwargs.get("updated_at", "2024-01-01T00:00:00Z"),
        "published": kwargs.get("published", True),
        "public_url": kwargs.get("public_url", f"https://test-form.typeform.com/to/test_form_{counter:03d}"),
        "workspace": kwargs.get("workspace", {
            "href": f"https://api.typeform.com/workspaces/test_workspace_{counter}"
        }),
        "theme": kwargs.get("theme", {
            "href": f"https://api.typeform.com/themes/test_theme_{counter}"
        }),
        "settings": kwargs.get("settings", {
            "is_public": True,
            "progress_bar": "percentage",
            "show_progress_bar": True,
            "show_typeform_branding": True,
            "meta": {
                "allow_indexing": False
            }
        }),
        # Required fields for FormInfo model
        "welcome_screens": kwargs.get("welcome_screens", [
            {
                "id": f"welcome_{counter}",
                "title": f"Welcome to Form {counter}",
                "properties": {}
            }
        ]),
        "thankyou_screens": kwargs.get("thankyou_screens", [
            {
                "id": f"thankyou_{counter}",
                "title": "Thank you!",
                "properties": {}
            }
        ]),
        "fields": kwargs.get("fields", [
            {
                "id": f"field_{counter}_1",
                "title": "What is your name?",
                "type": "short_text",
                "ref": f"name_ref_{counter}",
                "properties": {}
            },
            {
                "id": f"field_{counter}_2", 
                "title": "What is your email?",
                "type": "email",
                "ref": f"email_ref_{counter}",
                "properties": {}
            }
        ]),
        "hidden": kwargs.get("hidden", []),
        "variables": kwargs.get("variables", {}),
        "_links": kwargs.get("_links", {
            "display": f"https://test-form.typeform.com/to/test_form_{counter:03d}",
            "responses": f"https://api.typeform.com/forms/test_form_{counter:03d}/responses"
        }),
    }
    
    return final_kwargs


def create_webhook_info_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create TypeForm WebhookInfo response kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required WebhookInfo parameters
    """
    webhook_counter = get_next_webhook_counter()
    form_counter = get_next_typeform_api_counter()
    
    final_kwargs = {
        "id": kwargs.get("id", f"test_webhook_{webhook_counter:03d}"),
        "form_id": kwargs.get("form_id", f"test_form_{form_counter:03d}"),
        "tag": kwargs.get("tag", "default"),
        "url": kwargs.get("url", f"https://test-webhook.example.com/hook/{webhook_counter}"),
        "enabled": kwargs.get("enabled", True),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc).isoformat()),
        "updated_at": kwargs.get("updated_at", datetime.now(timezone.utc).isoformat()),
        "verify_ssl": kwargs.get("verify_ssl", True),
        "secret": kwargs.get("secret", f"test_secret_{webhook_counter}"),
        "_links": kwargs.get("_links", {
            "self": f"https://api.typeform.com/forms/test_form_{form_counter:03d}/webhooks/test_webhook_{webhook_counter:03d}"
        }),
    }
    
    return final_kwargs


def create_webhooks_list_response_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create TypeForm webhooks list response with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with webhooks list response structure
    """
    webhook_count = kwargs.get("webhook_count", 2)
    form_id = kwargs.get("form_id", f"test_form_{get_next_typeform_api_counter():03d}")
    
    webhooks = []
    for i in range(webhook_count):
        webhook_kwargs = create_webhook_info_kwargs(form_id=form_id)
        webhooks.append(webhook_kwargs)
    
    final_kwargs = {
        "items": kwargs.get("items", webhooks),
        "page_count": kwargs.get("page_count", 1),
        "total_items": kwargs.get("total_items", webhook_count),
    }
    
    return final_kwargs


# =============================================================================
# FORM RESPONSE FACTORIES
# =============================================================================

def create_form_field_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create TypeForm field definition with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with field definition structure
    """
    counter = get_next_typeform_api_counter()
    
    final_kwargs = {
        "id": kwargs.get("id", f"field_{counter}"),
        "title": kwargs.get("title", f"Test Question {counter}"),
        "type": kwargs.get("type", "short_text"),
        "ref": kwargs.get("ref", f"question_ref_{counter}"),
        "properties": kwargs.get("properties", {}),
    }
    
    return final_kwargs


def create_form_answer_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create TypeForm answer with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with answer structure
    """
    counter = get_next_form_response_counter()
    
    final_kwargs = {
        "field": kwargs.get("field", {
            "id": f"field_{counter}",
            "type": "short_text", 
            "ref": f"question_ref_{counter}"
        }),
        "type": kwargs.get("type", "text"),
        "text": kwargs.get("text", f"Test Answer {counter}"),
    }
    
    return final_kwargs


def create_client_onboarding_form_response_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create realistic client onboarding form response with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with complete form response structure
    """
    counter = get_next_form_response_counter()
    client_counter = get_next_client_counter()
    
    # Create default definition structure
    default_definition = {
        "id": f"onboarding_form_{counter:03d}",
        "title": f"Client Onboarding Form {counter}",
        "fields": [
            create_form_field_kwargs(
                id=f"company_name_{counter}",
                title="What is your company name?",
                type="short_text",
                ref="company_name"
            ),
            create_form_field_kwargs(
                id=f"contact_email_{counter}",
                title="What is your primary contact email?",
                type="email",
                ref="contact_email"
            ),
            create_form_field_kwargs(
                id=f"contact_name_{counter}",
                title="What is your contact person's name?",
                type="short_text", 
                ref="contact_name"
            ),
            create_form_field_kwargs(
                id=f"business_type_{counter}",
                title="What type of business are you?",
                type="multiple_choice",
                ref="business_type"
            ),
            create_form_field_kwargs(
                id=f"monthly_budget_{counter}",
                title="What is your approximate monthly budget?",
                type="number",
                ref="monthly_budget"
            )
        ]
    }
    
    # Create default answers structure
    default_answers = [
        create_form_answer_kwargs(
            field={
                "id": f"company_name_{counter}",
                "type": "short_text",
                "ref": "company_name"
            },
            type="text",
            text=f"Test Company {client_counter}"
        ),
        create_form_answer_kwargs(
            field={
                "id": f"contact_email_{counter}",
                "type": "email",
                "ref": "contact_email"
            },
            type="email",
            email=f"contact.{client_counter}@testcompany{client_counter}.com"
        ),
        create_form_answer_kwargs(
            field={
                "id": f"contact_name_{counter}",
                "type": "short_text",
                "ref": "contact_name"
            },
            type="text",
            text=f"Contact Person {client_counter}"
        ),
        create_form_answer_kwargs(
            field={
                "id": f"business_type_{counter}",
                "type": "multiple_choice",
                "ref": "business_type"
            },
            type="choice",
            choice={
                "label": "Restaurant",
                "other": None
            }
        ),
        create_form_answer_kwargs(
            field={
                "id": f"monthly_budget_{counter}",
                "type": "number",
                "ref": "monthly_budget"
            },
            type="number",
            number=1000 + (client_counter * 500)
        )
    ]
    
    final_kwargs = {
        "form_id": kwargs.get("form_id", default_definition["id"]),  # Add direct form_id field
        "landing_id": kwargs.get("landing_id", f"landing_{counter:08d}"),
        "token": kwargs.get("token", f"token_{counter:08d}"),
        "response_id": kwargs.get("response_id", f"response_{counter:08d}"),
        "landed_at": kwargs.get("landed_at", (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()),
        "submitted_at": kwargs.get("submitted_at", datetime.now(timezone.utc).isoformat()),
        "definition": kwargs.get("definition", default_definition),
        "answers": kwargs.get("answers", default_answers),
    }
    
    return final_kwargs


# =============================================================================
# WEBHOOK PAYLOAD FACTORIES
# =============================================================================

def create_webhook_payload_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create TypeForm webhook payload with deterministic values.
    
    This represents the exact structure TypeForm sends to webhook endpoints.
    Follows the established pattern from data_factories.py.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with webhook payload structure
    """
    counter = get_next_form_response_counter()
    
    # Create default form_response and merge with provided overrides to ensure required fields exist
    provided_form_response = kwargs.get("form_response", {})
    default_form_response = create_client_onboarding_form_response_kwargs(**(provided_form_response or {}))

    # If caller passed a dict as form_response, merge it over defaults; otherwise use default
    if isinstance(provided_form_response, dict) and provided_form_response:
        merged_form_response = {**default_form_response, **provided_form_response}
    else:
        merged_form_response = default_form_response

    final_kwargs = {
        "event_id": kwargs.get("event_id", f"webhook_event_{counter:08d}"),
        "event_type": kwargs.get("event_type", "form_response"),
        "form_response": merged_form_response,
    }

    # Allow override of any top-level attribute (following data_factories.py pattern)
    # but preserve our merged form_response unless explicitly replaced again
    for k, v in kwargs.items():
        if k == "form_response":
            continue
        final_kwargs[k] = v

    return final_kwargs


def create_typeform_signature_headers(**kwargs) -> Dict[str, str]:
    """
    Create TypeForm webhook signature headers for testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with signature headers
    """
    counter = get_next_webhook_counter()
    
    final_kwargs = {
        "Typeform-Signature": kwargs.get("Typeform-Signature", f"sha256=test_signature_{counter}"),
        "Content-Type": kwargs.get("Content-Type", "application/json"),
        "User-Agent": kwargs.get("User-Agent", "Typeform-Webhooks/1.0"),
    }
    
    return final_kwargs


# =============================================================================
# ERROR SCENARIO FACTORIES
# =============================================================================

def create_api_error_response_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create TypeForm API error response with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with error response structure
    """
    counter = get_next_typeform_api_counter()
    
    default_details = [
        {
            "code": "FIELD_REQUIRED",
            "message": f"Field validation error {counter}",
            "field": f"test_field_{counter}"
        }
    ]
    
    final_kwargs = {
        "code": kwargs.get("code", "BAD_REQUEST"),
        "message": kwargs.get("message", f"Test error message {counter}"),
        "details": kwargs.get("details", default_details),
    }
    
    return final_kwargs


def create_authentication_error_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create TypeForm authentication error response.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with auth error structure
    """
    counter = get_next_typeform_api_counter()
    
    final_kwargs = {
        "code": kwargs.get("code", "FORBIDDEN"),
        "message": kwargs.get("message", f"Authentication failed {counter}"),
        "description": kwargs.get("description", "Invalid API key or insufficient permissions"),
    }
    
    return final_kwargs


def create_not_found_error_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create TypeForm not found error response.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with not found error structure
    """
    counter = get_next_typeform_api_counter()
    
    final_kwargs = {
        "code": kwargs.get("code", "NOT_FOUND"), 
        "message": kwargs.get("message", f"Resource not found {counter}"),
        "description": kwargs.get("description", "The requested form or webhook does not exist"),
    }
    
    return final_kwargs


# =============================================================================
# BULK DATA FACTORIES
# =============================================================================

def create_multiple_form_responses(count: int = 3, **kwargs) -> List[Dict[str, Any]]:
    """
    Create multiple form responses for testing pagination and bulk operations.
    
    Args:
        count: Number of responses to create
        **kwargs: Common overrides for all responses
        
    Returns:
        List of form response dictionaries
    """
    responses = []
    for i in range(count):
        response_kwargs = create_client_onboarding_form_response_kwargs(**kwargs)
        responses.append(response_kwargs)
    
    return responses


def create_multiple_webhook_payloads(count: int = 3, **kwargs) -> List[Dict[str, Any]]:
    """
    Create multiple webhook payloads for testing bulk processing.
    
    Args:
        count: Number of payloads to create
        **kwargs: Common overrides for all payloads
        
    Returns:
        List of webhook payload dictionaries
    """
    payloads = []
    for i in range(count):
        payload_kwargs = create_webhook_payload_kwargs(**kwargs)
        payloads.append(payload_kwargs)
    
    return payloads


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def validate_form_response_structure(response: Dict[str, Any]) -> bool:
    """
    Validate that a form response has the expected structure.
    
    Args:
        response: Form response dictionary to validate
        
    Returns:
        True if structure is valid
    """
    required_fields = ["landing_id", "token", "response_id", "landed_at", "submitted_at", "definition", "answers"]
    
    for field in required_fields:
        if field not in response:
            return False
    
    # Validate definition structure
    definition = response["definition"]
    if not all(key in definition for key in ["id", "title", "fields"]):
        return False
    
    # Validate answers structure
    answers = response["answers"]
    if not isinstance(answers, list):
        return False
    
    for answer in answers:
        if not all(key in answer for key in ["field", "type"]):
            return False
    
    return True


def validate_webhook_payload_structure(payload: Dict[str, Any]) -> bool:
    """
    Validate that a webhook payload has the expected structure.
    
    Args:
        payload: Webhook payload dictionary to validate
        
    Returns:
        True if structure is valid
    """
    required_fields = ["event_id", "event_type", "form_response"]
    
    for field in required_fields:
        if field not in payload:
            return False
    
    # Validate form_response structure
    return validate_form_response_structure(payload["form_response"])


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_typeform_webhook_payload(**kwargs) -> Dict[str, Any]:
    """
    Alias for create_webhook_payload_kwargs for e2e test compatibility.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with webhook payload structure (same as create_webhook_payload_kwargs)
    """
    return create_webhook_payload_kwargs(**kwargs)

def create_realistic_onboarding_scenario(**kwargs) -> Dict[str, Any]:
    """
    Create a realistic client onboarding scenario with all related data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with complete scenario data
    """
    # Extract form_id and response_id to pass to nested factories
    form_id = kwargs.get("form_id")
    response_id = kwargs.get("response_id")
    
    # Prepare form_response kwargs with necessary overrides
    form_response_kwargs = kwargs.get("form_response", {})
    if form_id:
        form_response_kwargs["form_id"] = form_id
    if response_id:
        form_response_kwargs["response_id"] = response_id
    
    # Prepare kwargs for webhook payload WITHOUT form_response (let factory generate it)
    webhook_payload_kwargs = kwargs.get("webhook_payload", {})
    # Don't override form_response here - let the webhook factory use the complete structure
    # webhook_payload_kwargs["form_response"] = form_response_kwargs
    
    # Create default values for each component
    default_form_info = create_form_info_kwargs(**kwargs.get("form_info", {}))
    default_webhook_info = create_webhook_info_kwargs(**kwargs.get("webhook_info", {}))
    default_form_response = create_client_onboarding_form_response_kwargs(**form_response_kwargs)
    
    # Pass the complete form response to the webhook payload factory
    webhook_payload_kwargs["form_response"] = default_form_response
    default_webhook_payload = create_webhook_payload_kwargs(**webhook_payload_kwargs)
    default_signature_headers = create_typeform_signature_headers(**kwargs.get("signature_headers", {}))
    
    scenario = {
        "form_info": kwargs.get("form_info", default_form_info),
        "webhook_info": kwargs.get("webhook_info", default_webhook_info),
        "form_response": kwargs.get("form_response", default_form_response),
        "webhook_payload": kwargs.get("webhook_payload", default_webhook_payload),
        "signature_headers": kwargs.get("signature_headers", default_signature_headers),
    }
    
    # Add any additional kwargs that aren't component-specific
    for key, value in kwargs.items():
        if key not in ['form_response', 'webhook_payload', 'form_info', 'webhook_info', 'signature_headers', 'form_id', 'response_id']:
            scenario[key] = value
    
    return scenario 