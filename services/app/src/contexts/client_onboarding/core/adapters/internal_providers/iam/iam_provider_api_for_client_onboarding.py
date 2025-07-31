from src.contexts.seedwork.shared.adapters.internal_providers.base_iam_provider import BaseIAMProvider
from src.contexts.client_onboarding.core.adapters.internal_providers.iam.api_schemas.api_user import ApiUser


class IAMProvider(BaseIAMProvider[ApiUser]):
    """
    Client onboarding specific IAM provider.
    
    Inherits from BaseIAMProvider and configures it with client_onboarding
    specific ApiUser type and caller context.
    """
    
    def __init__(self):
        super().__init__(
            api_user_class=ApiUser,
            caller_context="client_onboarding"
        )
    
    @staticmethod
    async def get(id: str) -> dict:
        """
        Static method wrapper for backward compatibility.
        
        Args:
            id: The user ID to retrieve
            
        Returns:
            Dict containing user data or error information
        """
        provider = IAMProvider()
        return await super(IAMProvider, provider).get(id) 