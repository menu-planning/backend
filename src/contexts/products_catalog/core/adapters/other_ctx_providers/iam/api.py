from src.contexts.products_catalog.core.adapters.other_ctx_providers.iam.api_schemas.api_user import (
    ApiUser,
)
from src.contexts.seedwork.adapters.internal_providers.base_iam_provider import (
    BaseIAMProvider,
)


class IAMProvider(BaseIAMProvider[ApiUser]):
    """
    Products catalog specific IAM provider.

    Inherits from BaseIAMProvider and configures it with products_catalog
    specific ApiUser type and caller context.
    """

    def __init__(self):
        super().__init__(
            api_user_class=ApiUser,
            caller_context="products_catalog"
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
