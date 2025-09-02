"""Business rules for Products Catalog domain.

Contains domain-specific business rules that enforce constraints
and policies within the product catalog system.
"""

from src.contexts.products_catalog.core.domain.enums import Permission
from src.contexts.seedwork.domain.rules import BusinessRule
from src.contexts.seedwork.domain.value_objects.user import SeedUser


class OnlyAdminUserCanCreateClassification(BusinessRule):
    """Business rule enforcing that only administrators can create classifications.
    
    Ensures that classification entities (brands, categories, food groups, etc.)
    can only be created by users with the MANAGE_PRODUCTS permission.
    """
    __message = "Only administrators can create classifications"

    def __init__(self, user: SeedUser):
        """Initialize the rule with a user to validate.
        
        Args:
            user: The user attempting to create a classification.
        """
        self.user = user

    def is_broken(self) -> bool:
        """Check if the user lacks permission to create classifications.
        
        Returns:
            True if the user does not have MANAGE_PRODUCTS permission.
        """
        return not self.user.has_permission(Permission.MANAGE_PRODUCTS)

    def get_message(self) -> str:
        """Return the error message when this rule is broken.
        
        Returns:
            Human-readable error message.
        """
        return self.__message
