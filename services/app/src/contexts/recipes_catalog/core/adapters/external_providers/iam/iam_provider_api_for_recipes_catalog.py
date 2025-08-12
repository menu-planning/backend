from src.contexts.seedwork.shared.adapters.internal_providers.base_iam_provider import BaseIAMProvider
from src.contexts.recipes_catalog.core.adapters.external_providers.iam.api_schemas.api_user import ApiUser


class IAMProvider(BaseIAMProvider[ApiUser]):
    """
    Recipes catalog specific IAM provider.
    
    Inherits from BaseIAMProvider and configures it with recipes_catalog
    specific ApiUser type and caller context.
    """
    
    def __init__(self):
        super().__init__(
            api_user_class=ApiUser,
            caller_context="recipes_catalog"
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
