"""Enumerations for product permissions, roles, units, and UI filter types."""

from enum import Enum, unique

from src.contexts.seedwork.domain.enums import Permission as SeedPermission
from src.contexts.seedwork.domain.enums import Role as SeedRole


@unique
class Permission(SeedPermission):
    """Permissions specific to Products Catalog context.
    
    Extends the base permission system with catalog-specific permissions
    for managing products, users, and system access.
    """
    MANAGE_USERS = "manage_users"
    MANAGE_PRODUCTS = "manage_products"
    VIEW_AUDIT_LOG = "view_audit_log"
    ACCESS_DEVELOPER_TOOLS = "access_developer_tools"
    ACCESS_SUPPORT = "access_support"
    ACCESS_BASIC_FEATURES = "access_basic_features"


@unique
class Role(SeedRole):
    """Role definitions for Products Catalog with associated permissions.
    
    Each role contains a frozenset of permissions that define what actions
    users with that role can perform within the catalog system.
    """
    ADMINISTRATOR = frozenset({
        Permission.MANAGE_USERS,
        Permission.MANAGE_PRODUCTS,
        Permission.VIEW_AUDIT_LOG,
    })
    USER_MANAGER = frozenset({Permission.MANAGE_USERS})
    PRODUCT_MANAGER = frozenset({Permission.MANAGE_PRODUCTS})
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


@unique
class Unit(str, Enum):
    """Units used across the catalog domain and nutrition facts.
    
    Standardized unit definitions for measurements, weights, volumes,
    and nutritional values throughout the product catalog.
    """
    UNIT = "un"
    KILOGRAM = "kg"
    GRAM = "g"
    MILLIGRAM = "mg"
    MICROGRAM = "mcg"
    LITER = "l"
    MILLILITER = "ml"
    PERCENT = "percent"
    ENERGY = "kcal"
    IU = "IU"


@unique
class FrontendFilterTypes(Enum):
    """Filter control types used by the frontend when querying products.
    
    Defines the UI component types available for filtering product
    search results in the frontend application.
    """
    SINGLE_SELECTION = "single_selection"
    MULTI_SELECTION = "multi_selection"
    SORT = "sort"
    SWITCH = "switch"
    EXPANDABLE_SWITCH = "expandable_switch"
    DATE_SELECTION = "date_selection"


class ProductClassificationType(str, Enum):
    """Classification enum to reference taxonomy groups in the catalog.
    
    Identifies the different types of classification entities used
    to categorize and organize products in the catalog system.
    """
    CATEGORIES = "categories"
    BRANDS = "brands"
    FOOD_GROUPS = "food-groups"
    PARENT_CATEGORIES = "parent-categories"
    PROCESS_TYPES = "process-types"
    SOURCES = "sources"
