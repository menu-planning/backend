from src.contexts.iam.core.adapters.api_schemas.entities.user import ApiUser
from src.contexts.iam.core.domain.entities.user import User
from src.contexts.iam.core.domain.value_objects.role import Role


def _deep_dict_equal(dict1, dict2):
    """
    Recursively checks if two dictionaries are equal, accounting for nested dictionaries
    and lists containing dictionaries as their items.
    """
    if isinstance(dict1, dict) and isinstance(dict2, dict):
        if dict1.keys() != dict2.keys():
            return False
        for key in dict1:
            if not _deep_dict_equal(dict1[key], dict2[key]):
                return False
        return True
    elif isinstance(dict1, list) and isinstance(dict2, list):
        # Ensure both lists contain the same dictionaries, regardless of order
        if len(dict1) != len(dict2):
            return False
        for item in dict1:
            # Check each item in dict1 to see if there is an equivalent in dict2
            if isinstance(item, dict):
                if not any(_deep_dict_equal(item, d2_item) for d2_item in dict2):
                    return False
            else:
                # For non-dict items, just ensure the item is present in dict2
                if item not in dict2:
                    return False
        return True
    else:
        return dict1 == dict2


def test_api_user_base_from_domain() -> None:
    user_in_db = {
        "id": "1",
        "roles": [
            {
                "name": "administrator",
                "context": "IAM",
                "permissions": ["manage_roles", "manage_users", "view_audit_log"],
            }
        ],
        "discarded": False,
        "version": "1",
    }
    user_kwargs = user_in_db | {"roles": [Role.administrator()]}
    assert _deep_dict_equal(
        ApiUser(**user_in_db).model_dump(),
        ApiUser.from_domain(User(**user_kwargs)).model_dump(),
    )
