"""
External Provider: IAM Provider for Client Onboarding

IAM provider adapter for client onboarding context.
Provides user and role management integration with IAM context.
"""

from src.contexts.client_onboarding.core.adapters.external_providers.iam.api_schemas.api_user import (
    ApiUser,
)
from src.contexts.seedwork.adapters.internal_providers.base_iam_provider import (
    BaseIAMProvider,
)


class IAMProvider(BaseIAMProvider[ApiUser]):
    """IAM provider adapter for client onboarding context.

    Extends BaseIAMProvider with client onboarding specific configuration.
    Provides user and role management integration with IAM context.

    Notes:
        Adapter pattern implementation for cross-context communication.
        Configures ApiUser type and caller context for client onboarding.
    """

    def __init__(self):
        """Initialize IAM provider with client onboarding configuration."""
        super().__init__(api_user_class=ApiUser, caller_context="client_onboarding")

    @staticmethod
    async def get(user_id: str) -> dict:
        """Retrieve user data by ID.

        Static method wrapper for backward compatibility with existing code.

        Args:
            user_id: The user ID to retrieve

        Returns:
            Dictionary containing user data or error information
        """
        provider = IAMProvider()
        return await super(IAMProvider, provider).get(user_id)
