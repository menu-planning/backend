from src.contexts.recipes_catalog.shared.domain.enums import Role as EnumRoles
from src.contexts.seedwork.shared.domain.rules import BusinessRule
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.shared_kernel.domain.enums import Privacy


class OnlyAdminUserCanCreatePublicTag(BusinessRule):
    __message = "Only administrators can create public tags"

    def __init__(self, user: SeedUser, privacy: Privacy):
        self.user = user
        self.privacy = privacy

    def is_broken(self) -> bool:
        return self.privacy == Privacy.PUBLIC and not self.user.has_role(
            EnumRoles.ADMINISTRATOR
        )

    def get_message(self) -> str:
        return self.__message
