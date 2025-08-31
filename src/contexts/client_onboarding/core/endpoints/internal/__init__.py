"""
Internal Provider Endpoints

HTTP endpoints that expose client_onboarding data to other contexts.
These endpoints follow the same pattern as IAM internal providers.
"""

from .get_form_response import get_form_response
from .get_form_responses import get_form_responses

__all__ = [
    "get_form_response",
    "get_form_responses",
]
