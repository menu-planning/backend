from src.contexts.recipes_catalog.core.adapters.other_ctx_providers.iam.api_schemas.api_user import (
    ApiUser,
)
from src.contexts.seedwork.adapters.internal_providers.base_iam_provider import (
    BaseIAMProvider,
)


class IAMProvider(BaseIAMProvider[ApiUser]):
    """Recipes catalog specific IAM provider.

    Inherits from BaseIAMProvider and configures it with recipes_catalog
    specific ApiUser type and caller context for user authentication
    and authorization.

    Notes:
        Integrates with base IAM provider for user management.
        Uses recipes_catalog specific ApiUser schema.
    """

    def __init__(self):
        """Initialize IAM provider with recipes catalog configuration.

        Notes:
            Sets ApiUser as the user class and "recipes_catalog" as caller context.
        """
        super().__init__(api_user_class=ApiUser, caller_context="recipes_catalog")

    @staticmethod
    async def get(user_id: str) -> dict:
        """Retrieve user by ID using static method wrapper.

        Args:
            user_id: Unique identifier for the user.

        Returns:
            Dictionary containing user data or error information.

        Notes:
            Static method wrapper for backward compatibility.
            Creates provider instance and delegates to base class.
        """
        provider = IAMProvider()
        return await super(IAMProvider, provider).get(user_id)
