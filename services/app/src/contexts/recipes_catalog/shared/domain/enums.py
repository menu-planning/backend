from __future__ import annotations

from enum import Enum, unique

from src.contexts.seedwork.shared.domain.enums import Permission as SeedPermission
from src.contexts.seedwork.shared.domain.enums import Role as SeedRole


@unique
class Permission(SeedPermission):
    MANAGE_USERS = "manage_users"
    MANAGE_RECIPES = "manage_recipes"
    VIEW_AUDIT_LOG = "view_audit_log"
    ACCESS_DEVELOPER_TOOLS = "access_developer_tools"
    ACCESS_SUPPORT = "access_support"
    ACCESS_BASIC_FEATURES = "access_basic_features"


@unique
class Role(SeedRole):
    ADMINISTRATOR = {
        Permission.MANAGE_USERS,
        Permission.MANAGE_RECIPES,
        Permission.VIEW_AUDIT_LOG,
    }
    USER_MANAGER = {Permission.MANAGE_USERS}
    RECIPE_MANAGER = {Permission.MANAGE_RECIPES}
    AUDITOR = {Permission.VIEW_AUDIT_LOG}
    USER = {Permission.ACCESS_BASIC_FEATURES}
    DEVELOPER = {Permission.ACCESS_DEVELOPER_TOOLS}
    SUPPORT_STAFF = {Permission.ACCESS_SUPPORT, Permission.ACCESS_BASIC_FEATURES}

    @property
    def permissions(self) -> list[str]:
        return [i.value for i in list(self.value)]


@unique
class MealType(str, Enum):
    PRE_WORKOUT = "pré treino"
    POST_WORKOUT = "pós treino"
    BREAKFAST = "breakfast"
    MORNING_SNACK = "lanche da manhã"
    LUNCH = "almoço"
    AFTERNOON_SNACK = "lanche da tarde"
    DINNER = "jantar"
    SUPPER = "ceia"
    DESSERT = "sobremesa"
    DRINK = "bebida"
    OTHER = "outro"
