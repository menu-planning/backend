"""Domain roles and permissions for recipes catalog."""
from enum import unique

from src.contexts.seedwork.domain.enums import Permission as SeedPermission
from src.contexts.seedwork.domain.enums import Role as SeedRole


@unique
class Permission(SeedPermission):
    """Domain-specific permissions for recipes catalog operations.

    Extends base permissions with catalog-specific capabilities.
    """
    MANAGE_USERS = "manage_users"
    MANAGE_RECIPES = "manage_recipes"
    MANAGE_MEALS = "manage_meals"
    MANAGE_MENUS = "manage_menus"
    MANAGE_CLIENTS = "manage_clients"
    VIEW_AUDIT_LOG = "view_audit_log"
    ACCESS_DEVELOPER_TOOLS = "access_developer_tools"
    ACCESS_SUPPORT = "access_support"
    ACCESS_BASIC_FEATURES = "access_basic_features"


@unique
class Role(SeedRole):
    """Domain-specific roles with predefined permission sets.

    Each role provides a curated set of permissions for different user types.
    """
    ADMINISTRATOR = frozenset({
        Permission.MANAGE_USERS,
        Permission.MANAGE_RECIPES,
        Permission.MANAGE_MEALS,
        Permission.MANAGE_MENUS,
        Permission.MANAGE_CLIENTS,
        Permission.VIEW_AUDIT_LOG,
    })
    USER_MANAGER = frozenset({Permission.MANAGE_USERS})
    RECIPE_MANAGER = frozenset({Permission.MANAGE_RECIPES})
    MEAL_MANAGER = frozenset({Permission.MANAGE_MEALS})
    MENU_MANAGER = frozenset({Permission.MANAGE_MENUS})
    CLIENT_MANAGER = frozenset({Permission.MANAGE_CLIENTS})
    AUDITOR = frozenset({Permission.VIEW_AUDIT_LOG})
    USER = frozenset({Permission.ACCESS_BASIC_FEATURES})
    DEVELOPER = frozenset({Permission.ACCESS_DEVELOPER_TOOLS})
    SUPPORT_STAFF = frozenset({Permission.ACCESS_SUPPORT, Permission.ACCESS_BASIC_FEATURES})

    @property
    def permissions(self) -> list[str]:
        """Return list of permission values for this role.

        Returns:
            List of permission string values.
        """
        return [i.value for i in list(self.value)]
