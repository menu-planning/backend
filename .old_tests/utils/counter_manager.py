"""
Centralized counter management for all test data factories.

This module provides a single source of truth for all deterministic counters
used across the test suite, ensuring consistent IDs and proper test isolation.

Benefits:
- Single reset function for all counters
- No ID collisions between different factory files
- Easy maintenance and extensibility
- Guaranteed test isolation
"""

# =============================================================================
# CENTRALIZED COUNTERS
# =============================================================================

# Domain entity counters
_MEAL_COUNTER = 1
_RECIPE_COUNTER = 1
_CLIENT_COUNTER = 1
_MENU_COUNTER = 1
_USER_COUNTER = 1
_PRODUCT_COUNTER = 1
_SUPPLIER_COUNTER = 1
_CUSTOMER_COUNTER = 1
_ORDER_COUNTER = 1

# Value object counters
_TAG_COUNTER = 1
_INGREDIENT_COUNTER = 1
_RATING_COUNTER = 1
_MENU_MEAL_COUNTER = 1

# API schema counters
_API_MEAL_COUNTER = 1
_API_RECIPE_COUNTER = 1
_API_INGREDIENT_COUNTER = 1
_API_RATING_COUNTER = 1
_API_ROLE_COUNTER = 1
_API_USER_COUNTER = 1

# Update operation counters
_UPDATE_COUNTER = 1

# General purpose counters
_GENERAL_COUNTER = 1
_SOURCE_COUNTER = 1
_BRAND_COUNTER = 1
_CATEGORY_COUNTER = 1
_ROLE_COUNTER = 1

# ORM-specific counters (separate from domain model counters)
_ORM_PRODUCT_COUNTER = 1
_ORM_SOURCE_COUNTER = 1
_ORM_BRAND_COUNTER = 1
_ORM_CATEGORY_COUNTER = 1

# Client onboarding context counters
_ONBOARDING_FORM_COUNTER = 1
_WEBHOOK_COUNTER = 1
_FORM_RESPONSE_COUNTER = 1
_TYPEFORM_API_COUNTER = 1


def get_next_meal_id() -> str:
    """Get next meal counter value."""
    global _MEAL_COUNTER
    current = _MEAL_COUNTER
    _MEAL_COUNTER += 1
    return str(current)


def get_next_recipe_id() -> str:
    """Get next recipe counter value."""
    global _RECIPE_COUNTER
    current = _RECIPE_COUNTER
    _RECIPE_COUNTER += 1
    return str(current)


def get_next_client_id() -> str:
    """Get next client counter value."""
    global _CLIENT_COUNTER
    current = _CLIENT_COUNTER
    _CLIENT_COUNTER += 1
    return str(current)


def get_next_menu_id() -> str:
    """Get next menu counter value."""
    global _MENU_COUNTER
    current = _MENU_COUNTER
    _MENU_COUNTER += 1
    return str(current)


def get_next_tag_id() -> str:
    """Get next tag counter value."""
    global _TAG_COUNTER
    current = _TAG_COUNTER
    _TAG_COUNTER += 1
    return str(current)


def get_next_ingredient_id() -> str:
    """Get next ingredient counter value."""
    global _INGREDIENT_COUNTER
    current = _INGREDIENT_COUNTER
    _INGREDIENT_COUNTER += 1
    return str(current)


def get_next_rating_id() -> str:
    """Get next rating counter value."""
    global _RATING_COUNTER
    current = _RATING_COUNTER
    _RATING_COUNTER += 1
    return str(current)


def get_next_menu_meal_id() -> str:
    """Get next menu meal counter value."""
    global _MENU_MEAL_COUNTER
    current = _MENU_MEAL_COUNTER
    _MENU_MEAL_COUNTER += 1
    return str(current)


def get_next_api_meal_id() -> str:
    """Get next API meal counter value."""
    global _API_MEAL_COUNTER
    current = _API_MEAL_COUNTER
    _API_MEAL_COUNTER += 1
    return str(current)


def get_next_api_recipe_id() -> str:
    """Get next API recipe counter value."""
    global _API_RECIPE_COUNTER
    current = _API_RECIPE_COUNTER
    _API_RECIPE_COUNTER += 1
    return str(current)


def get_next_api_ingredient_id() -> str:
    """Get next API ingredient counter value."""
    global _API_INGREDIENT_COUNTER
    current = _API_INGREDIENT_COUNTER
    _API_INGREDIENT_COUNTER += 1
    return str(current)


def get_next_api_rating_id() -> str:
    """Get next API rating counter value."""
    global _API_RATING_COUNTER
    current = _API_RATING_COUNTER
    _API_RATING_COUNTER += 1
    return str(current)


def get_next_user_id() -> str:
    """Get next user counter value."""
    global _USER_COUNTER
    current = _USER_COUNTER
    _USER_COUNTER += 1
    return str(current)


def get_next_product_id() -> str:
    """Get next product counter value."""
    global _PRODUCT_COUNTER
    current = _PRODUCT_COUNTER
    _PRODUCT_COUNTER += 1
    return str(current)


def get_next_supplier_id() -> str:
    """Get next supplier counter value."""
    global _SUPPLIER_COUNTER
    current = _SUPPLIER_COUNTER
    _SUPPLIER_COUNTER += 1
    return str(current)


def get_next_customer_id() -> str:
    """Get next customer counter value."""
    global _CUSTOMER_COUNTER
    current = _CUSTOMER_COUNTER
    _CUSTOMER_COUNTER += 1
    return str(current)


def get_next_order_id() -> str:
    """Get next order counter value."""
    global _ORDER_COUNTER
    current = _ORDER_COUNTER
    _ORDER_COUNTER += 1
    return str(current)


def get_next_general_id() -> str:
    """Get next general counter value."""
    global _GENERAL_COUNTER
    current = _GENERAL_COUNTER
    _GENERAL_COUNTER += 1
    return str(current)


def get_next_source_id() -> str:
    """Get next source counter value."""
    global _SOURCE_COUNTER
    current = _SOURCE_COUNTER
    _SOURCE_COUNTER += 1
    return str(current)


def get_next_brand_id() -> str:
    """Get next brand counter value."""
    global _BRAND_COUNTER
    current = _BRAND_COUNTER
    _BRAND_COUNTER += 1
    return str(current)


def get_next_category_id() -> str:
    """Get next category counter value."""
    global _CATEGORY_COUNTER
    current = _CATEGORY_COUNTER
    _CATEGORY_COUNTER += 1
    return str(current)


def get_next_role_id() -> str:
    """Get next role counter value."""
    global _ROLE_COUNTER
    current = _ROLE_COUNTER
    _ROLE_COUNTER += 1
    return str(current)


def get_next_api_role_id() -> str:
    """Get next API role counter value."""
    global _API_ROLE_COUNTER
    current = _API_ROLE_COUNTER
    _API_ROLE_COUNTER += 1
    return str(current)


def get_next_api_user_id() -> str:
    """Get next API user counter value."""
    global _API_USER_COUNTER
    current = _API_USER_COUNTER
    _API_USER_COUNTER += 1
    return str(current)


def get_next_update_id() -> str:
    """Get next update counter value."""
    global _UPDATE_COUNTER
    current = _UPDATE_COUNTER
    _UPDATE_COUNTER += 1
    return str(current)


def get_next_orm_product_id() -> str:
    """Get next ORM product counter value."""
    global _ORM_PRODUCT_COUNTER
    current = _ORM_PRODUCT_COUNTER
    _ORM_PRODUCT_COUNTER += 1
    return str(current)


def get_next_orm_source_id() -> str:
    """Get next ORM source counter value."""
    global _ORM_SOURCE_COUNTER
    current = _ORM_SOURCE_COUNTER
    _ORM_SOURCE_COUNTER += 1
    return str(current)


def get_next_orm_brand_id() -> str:
    """Get next ORM brand counter value."""
    global _ORM_BRAND_COUNTER
    current = _ORM_BRAND_COUNTER
    _ORM_BRAND_COUNTER += 1
    return str(current)


def get_next_orm_category_id() -> str:
    """Get next ORM category counter value."""
    global _ORM_CATEGORY_COUNTER
    current = _ORM_CATEGORY_COUNTER
    _ORM_CATEGORY_COUNTER += 1
    return str(current)


def get_next_onboarding_form_id() -> str:
    """Get next onboarding form counter value."""
    global _ONBOARDING_FORM_COUNTER
    current = _ONBOARDING_FORM_COUNTER
    _ONBOARDING_FORM_COUNTER += 1
    return str(current)


def get_next_webhook_id() -> str:
    """Get next webhook counter value."""
    global _WEBHOOK_COUNTER
    current = _WEBHOOK_COUNTER
    _WEBHOOK_COUNTER += 1
    return str(current)


def get_next_form_response_id() -> str:
    """Get next form response counter value."""
    global _FORM_RESPONSE_COUNTER
    current = _FORM_RESPONSE_COUNTER
    _FORM_RESPONSE_COUNTER += 1
    return str(current)


def get_next_typeform_api_id() -> str:
    """Get next TypeForm API counter value."""
    global _TYPEFORM_API_COUNTER
    current = _TYPEFORM_API_COUNTER
    _TYPEFORM_API_COUNTER += 1
    return str(current)


def get_next_typeform_api_counter() -> str:
    """Get next TypeForm API counter value (alias for consistency)."""
    return get_next_typeform_api_id()


def get_next_webhook_counter() -> str:
    """Get next webhook counter value (alias for consistency)."""
    return get_next_webhook_id()


def get_next_form_response_counter() -> str:
    """Get next form response counter value (alias for consistency)."""
    return get_next_form_response_id()


def get_next_client_counter() -> str:
    """Get next client counter value (alias for consistency)."""
    return get_next_client_id()


def reset_all_counters() -> None:
    """
    Reset all counters to 1 for complete test isolation.

    This function should be called before each test to ensure
    deterministic and isolated test behavior across the entire suite.
    """
    global _MEAL_COUNTER, _RECIPE_COUNTER, _CLIENT_COUNTER, _MENU_COUNTER
    global _USER_COUNTER, _PRODUCT_COUNTER, _SUPPLIER_COUNTER, _CUSTOMER_COUNTER, _ORDER_COUNTER
    global _TAG_COUNTER, _INGREDIENT_COUNTER
    global _RATING_COUNTER, _MENU_MEAL_COUNTER, _API_MEAL_COUNTER, _API_RECIPE_COUNTER
    global _API_INGREDIENT_COUNTER, _API_RATING_COUNTER, _GENERAL_COUNTER
    global _SOURCE_COUNTER, _BRAND_COUNTER, _CATEGORY_COUNTER, _ROLE_COUNTER
    global _API_ROLE_COUNTER, _API_USER_COUNTER, _UPDATE_COUNTER
    global _ORM_PRODUCT_COUNTER, _ORM_SOURCE_COUNTER, _ORM_BRAND_COUNTER, _ORM_CATEGORY_COUNTER
    global _ONBOARDING_FORM_COUNTER, _WEBHOOK_COUNTER, _FORM_RESPONSE_COUNTER, _TYPEFORM_API_COUNTER

    # Reset all counters to 1
    _MEAL_COUNTER = 1
    _RECIPE_COUNTER = 1
    _CLIENT_COUNTER = 1
    _MENU_COUNTER = 1
    _USER_COUNTER = 1
    _PRODUCT_COUNTER = 1
    _SUPPLIER_COUNTER = 1
    _CUSTOMER_COUNTER = 1
    _ORDER_COUNTER = 1
    _TAG_COUNTER = 1
    _INGREDIENT_COUNTER = 1
    _RATING_COUNTER = 1
    _MENU_MEAL_COUNTER = 1
    _API_MEAL_COUNTER = 1
    _API_RECIPE_COUNTER = 1
    _API_INGREDIENT_COUNTER = 1
    _API_RATING_COUNTER = 1
    _GENERAL_COUNTER = 1
    _SOURCE_COUNTER = 1
    _BRAND_COUNTER = 1
    _CATEGORY_COUNTER = 1
    _ROLE_COUNTER = 1
    _API_ROLE_COUNTER = 1
    _API_USER_COUNTER = 1
    _UPDATE_COUNTER = 1
    _ORM_PRODUCT_COUNTER = 1
    _ORM_SOURCE_COUNTER = 1
    _ORM_BRAND_COUNTER = 1
    _ORM_CATEGORY_COUNTER = 1
    _ONBOARDING_FORM_COUNTER = 1
    _WEBHOOK_COUNTER = 1
    _FORM_RESPONSE_COUNTER = 1
    _TYPEFORM_API_COUNTER = 1
