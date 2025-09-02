from enum import unique

from src.contexts.seedwork.domain.enums import Permission as SeedPermission
from src.contexts.seedwork.domain.enums import Role as SeedRole


@unique
class Permission(SeedPermission):
    """Client onboarding specific permissions.

    Extends the base permission system with onboarding form management,
    webhook configuration, and client data access permissions.
    """

    MANAGE_ONBOARDING_FORMS = "manage_onboarding_forms"
    VIEW_ONBOARDING_RESPONSES = "view_onboarding_responses"
    CONFIGURE_TYPEFORM_WEBHOOKS = "configure_typeform_webhooks"
    ACCESS_CLIENT_DATA = "access_client_data"
    MANAGE_FIELD_MAPPINGS = "manage_field_mappings"
    ACCESS_BASIC_FEATURES = "access_basic_features"
    VIEW_AUDIT_LOG = "view_audit_log"
    ACCESS_DEVELOPER_TOOLS = "access_developer_tools"
    ACCESS_SUPPORT = "access_support"


@unique
class Role(SeedRole):
    """Client onboarding specific roles with predefined permission sets.

    Defines hierarchical roles for onboarding form management with varying
    levels of access to forms, responses, and configuration.
    """

    FORM_ADMINISTRATOR = frozenset({
        Permission.MANAGE_ONBOARDING_FORMS,
        Permission.VIEW_ONBOARDING_RESPONSES,
        Permission.CONFIGURE_TYPEFORM_WEBHOOKS,
        Permission.ACCESS_CLIENT_DATA,
        Permission.MANAGE_FIELD_MAPPINGS,
        Permission.VIEW_AUDIT_LOG,
    })
    FORM_MANAGER = frozenset({
        Permission.MANAGE_ONBOARDING_FORMS,
        Permission.VIEW_ONBOARDING_RESPONSES,
        Permission.CONFIGURE_TYPEFORM_WEBHOOKS,
        Permission.ACCESS_CLIENT_DATA,
    })
    FORM_VIEWER = frozenset({
        Permission.VIEW_ONBOARDING_RESPONSES,
        Permission.ACCESS_CLIENT_DATA,
    })
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
