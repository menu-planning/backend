from __future__ import annotations

from enum import Enum, unique

from src.contexts.seedwork.shared.domain.enums import Permission as SeedPermission
from src.contexts.seedwork.shared.domain.enums import Role as SeedRole


@unique
class Permission(SeedPermission):
    MANAGE_USERS = "manage_users"
    MANAGE_CLIENTS = "manage_clients"
    VIEW_AUDIT_LOG = "view_audit_log"
    ACCESS_DEVELOPER_TOOLS = "access_developer_tools"
    ACCESS_SUPPORT = "access_support"
    ACCESS_BASIC_FEATURES = "access_basic_features"


@unique
class Role(SeedRole):
    ADMINISTRATOR = {
        Permission.MANAGE_USERS,
        Permission.MANAGE_CLIENTS,
        Permission.VIEW_AUDIT_LOG,
    }
    USER_MANAGER = {Permission.MANAGE_USERS}
    CLIENT_MANAGER = {Permission.MANAGE_CLIENTS}
    AUDITOR = {Permission.VIEW_AUDIT_LOG}
    USER = {Permission.ACCESS_BASIC_FEATURES}
    DEVELOPER = {Permission.ACCESS_DEVELOPER_TOOLS}
    SUPPORT_STAFF = {Permission.ACCESS_SUPPORT, Permission.ACCESS_BASIC_FEATURES}

    @property
    def permissions(self) -> list[str]:
        return [i.value for i in list(self.value)]


@unique
class Privacy(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"


class State(Enum):
    AC = "AC"
    AL = "AL"
    AP = "AP"
    AM = "AM"
    BA = "BA"
    CE = "CE"
    DF = "DF"
    ES = "ES"
    GO = "GO"
    MA = "MA"
    MT = "MT"
    MS = "MS"
    MG = "MG"
    PA = "PA"
    PB = "PB"
    PR = "PR"
    PE = "PE"
    PI = "PI"
    RJ = "RJ"
    RN = "RN"
    RS = "RS"
    RO = "RO"
    RR = "RR"
    SC = "SC"
    SP = "SP"
    SE = "SE"
    TO = "TO"

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, State) and self.value == __o.value
