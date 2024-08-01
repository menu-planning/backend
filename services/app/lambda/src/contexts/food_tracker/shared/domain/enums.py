from enum import Enum, unique

from src.contexts.seedwork.shared.domain.enums import Permission as SeedPermission
from src.contexts.seedwork.shared.domain.enums import Role as SeedRole


@unique
class Permission(SeedPermission):
    MANAGE_USERS = "manage_users"
    MANAGE_HOUSES = "manage_houses"
    MANAGE_ITEMS = "manage_items"
    VIEW_AUDIT_LOG = "view_audit_log"
    ACCESS_DEVELOPER_TOOLS = "access_developer_tools"
    ACCESS_SUPPORT = "access_support"
    ACCESS_BASIC_FEATURES = "access_basic_features"


@unique
class Role(SeedRole):
    ADMINISTRATOR = {
        Permission.MANAGE_USERS,
        Permission.MANAGE_HOUSES,
        Permission.MANAGE_ITEMS,
        Permission.VIEW_AUDIT_LOG,
    }
    USER_MANAGER = {Permission.MANAGE_USERS}
    HOUSE_MANAGER = {Permission.MANAGE_HOUSES}
    ITEM_MANAGER = {Permission.MANAGE_ITEMS}
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
    ENERGY = "kcal"
    IU = "IU"

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Unit) and self.value == __o.value


@unique
class FoodGroup(Enum):
    ENERGY = "Energéticos"
    BUILDERS = "Construtores"
    REGULATORS = "Reguladores"

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, FoodGroup) and self.value == __o.value


@unique
class ProcessType(Enum):
    UNPROCESSED = "In natura"
    MIN_PROCCESSED = "Minimante processados"
    PROCESSED = "Processados"
    ULTRA_PROCESSED = "Ultra processados"
    OILS_FAT_SALT_SUGAR = "Óleos, gorduras, sal e açúcar"

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, ProcessType) and self.value == __o.value


@unique
class DietType(Enum):
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    LOWFODMAP = "lowfodmap"
    GLUTEN_FREE = "gluten_free"
    LACTOSE_FREE = "lactose_free"
    SUGAR_FREE = "sugar_free"
    LOW_SODIUM = "low_sodium"
    LOW_FAT = "low_fat"
    LOW_SUGAR = "low_sugar"
    LOW_CALORIES = "low_calories"
    LOW_CARB = "low_carb"
    HIGH_PROTEIN = "high_protein"
    HIGH_FIBER = "high_fiber"
    HIGH_CALCIUM = "high_calcium"
    HIGH_IRON = "high_iron"
    HIGH_POTASSIUM = "high_potassium"
    # TODO: add more diet types

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, DietType) and self.value == __o.value
