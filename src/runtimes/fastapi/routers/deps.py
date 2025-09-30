"""Shared dependencies for FastAPI routers."""

from fastapi import Depends, HTTPException, Request
from typing import Annotated

from src.contexts.client_onboarding.core.domain.shared.value_objects.user import User as ClientOnboardingUser
from src.contexts.products_catalog.core.domain.value_objects.user import User as ProductsUser
from src.contexts.recipes_catalog.core.domain.shared.value_objects.user import User as RecipesUser
from src.contexts.shared_kernel.middleware.auth.authentication import AuthContext


def get_current_user(request: Request) -> ClientOnboardingUser:
    """Get current authenticated user from request state.
    
    This is a generic user extractor that works across all contexts.
    The actual user type will be determined by the context-specific dependencies.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not hasattr(request.state, "auth_context"):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    auth_context: AuthContext = request.state.auth_context
    if not auth_context.is_authenticated or not auth_context.user_object:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return auth_context.user_object


# Context-specific user dependencies
def get_client_onboarding_user(
    user: Annotated[ClientOnboardingUser, Depends(get_current_user)]
) -> ClientOnboardingUser:
    """Get current user for client onboarding context."""
    return user


def get_products_user(
    user: Annotated[ProductsUser, Depends(get_current_user)]
) -> ProductsUser:
    """Get current user for products catalog context."""
    return user


def get_recipes_user(
    user: Annotated[RecipesUser, Depends(get_current_user)]
) -> RecipesUser:
    """Get current user for recipes catalog context."""
    return user
