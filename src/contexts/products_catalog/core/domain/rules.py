from src.contexts.products_catalog.core.domain.enums import Permission
from src.contexts.seedwork.shared.domain.rules import BusinessRule
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser


class OnlyAdminUserCanCreateClassification(BusinessRule):
    __message = "Only administrators can create classifications"

    def __init__(self, user: SeedUser):
        self.user = user

    def is_broken(self) -> bool:
        return not self.user.has_permission(Permission.MANAGE_PRODUCTS)

    def get_message(self) -> str:
        return self.__message
