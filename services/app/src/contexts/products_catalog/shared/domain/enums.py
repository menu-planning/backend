from enum import Enum, unique

from src.contexts.seedwork.shared.domain.enums import Permission as SeedPermission
from src.contexts.seedwork.shared.domain.enums import Role as SeedRole


@unique
class Permission(SeedPermission):
    MANAGE_USERS = "manage_users"
    MANAGE_PRODUCTS = "manage_products"
    VIEW_AUDIT_LOG = "view_audit_log"
    ACCESS_DEVELOPER_TOOLS = "access_developer_tools"
    ACCESS_SUPPORT = "access_support"
    ACCESS_BASIC_FEATURES = "access_basic_features"


@unique
class Role(SeedRole):
    ADMINISTRATOR = {
        Permission.MANAGE_USERS,
        Permission.MANAGE_PRODUCTS,
        Permission.VIEW_AUDIT_LOG,
    }
    USER_MANAGER = {Permission.MANAGE_USERS}
    PRODUCT_MANAGER = {Permission.MANAGE_PRODUCTS}
    AUDITOR = {Permission.VIEW_AUDIT_LOG}
    USER = {Permission.ACCESS_BASIC_FEATURES}
    DEVELOPER = {Permission.ACCESS_DEVELOPER_TOOLS}
    SUPPORT_STAFF = {Permission.ACCESS_SUPPORT, Permission.ACCESS_BASIC_FEATURES}

    @property
    def permissions(self) -> list[str]:
        return [i.value for i in list(self.value)]


@unique
class Unit(str, Enum):
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
    SINGLE_SELECTION = "single_selection"
    MULTI_SELECTION = "multi_selection"
    # DATE_RANGE = "date_range"
    SORT = "sort"
    SWITCH = "switch"
    EXPANDABLE_SWITCH = "expandable_switch"
    DATE_SELECTION = "date_selection"

    # def __hash__(self) -> int:
    #     return hash(self.value)

    # def __eq__(self, __o: object) -> bool:
    #     return isinstance(__o, FoodGroup) and self.value == __o.value


class ProductClassificationType(str, Enum):
    CATEGORIES = "categories"
    BRANDS = "brands"
    FOOD_GROUPS = "food-groups"
    PARENT_CATEGORIES = "parent-categories"
    PROCESS_TYPES = "process-types"
    SOURCES = "sources"
