"""Shared dependencies for FastAPI routers."""

from fastapi import Depends, HTTPException, Request
from typing import Annotated, Optional

from src.contexts.client_onboarding.core.domain.shared.value_objects.user import User as ClientOnboardingUser
from src.contexts.products_catalog.core.domain.value_objects.user import User as ProductsUser
from src.contexts.recipes_catalog.core.domain.shared.value_objects.user import User as RecipesUser
from src.contexts.iam.core.domain.root_aggregate.user import User as IAMUser
from src.contexts.shared_kernel.middleware.auth.authentication import AuthContext, UnifiedIAMProvider
from src.runtimes.fastapi.auth.security import (
    jwt_bearer,
    JWTAuthorizationCredentials
)
from src.runtimes.fastapi.auth.jwt_validator import CognitoJWTValidator


async def get_auth_context_with_iam(
    request: Request,
    jwt_credentials: Optional[JWTAuthorizationCredentials] = Depends(jwt_bearer),
    caller_context: str = "default"
) -> AuthContext:
    """
    Get full authentication context with IAM integration (MUST HAVE).
    
    This is the comprehensive dependency that replaces the middleware functionality:
    - JWT validation and caching (via JWTBearer)
    - User role extraction from JWT
    - Full user object fetching via UnifiedIAMProvider
    - Request metadata collection
    
    Args:
        jwt_credentials: Validated JWT credentials from JWTBearer
        request: FastAPI Request object
        caller_context: The IAM context to fetch user data from
        
    Returns:
        Complete AuthContext with user object from IAM
        
    Raises:
        HTTPException: If authentication fails
    """
    if not jwt_credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user ID and roles from JWT (MUST HAVE)
    user_id = jwt_credentials.claims.sub
    jwt_validator = CognitoJWTValidator()
    user_roles = jwt_validator.extract_user_roles(jwt_credentials.claims)
    
    # Fetch full user object from IAM (MUST HAVE)
    user_object = None
    if user_id and caller_context:
        try:
            iam_provider = UnifiedIAMProvider(
                logger_name=f"fastapi_iam_{caller_context}",
                cache_strategy="request"
            )
            response = await iam_provider.get_user(user_id, caller_context)
            if response.get("statusCode") == 200:
                user_object = response["body"]
        except Exception as e:
            # Log warning but continue with basic auth context
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                "Failed to fetch user from IAM",
                extra={
                    "user_id": user_id,
                    "caller_context": caller_context,
                    "error": str(e),
                }
            )
    
    # Add FastAPI request information to metadata (MUST HAVE)
    metadata = {
        "request_url": str(request.url),
        "request_method": request.method,
        "user_agent": request.headers.get("user-agent"),
        "client_ip": request.client.host if request.client else None,
    }
    
    # Create complete auth context
    auth_context = AuthContext(
        user_id_from_jwt=user_id,
        user_roles_from_jwt=user_roles,
        is_authenticated=True,
        metadata=metadata,
        user_domain_obj=user_object,
        caller_context=caller_context,
    )
    
    # Store in request state for compatibility with existing code
    request.state.auth_context = auth_context
    
    return auth_context






# Context-specific auth context dependencies
async def get_client_onboarding_auth_context(
    request: Request,
    jwt_credentials: Optional[JWTAuthorizationCredentials] = Depends(jwt_bearer)
) -> AuthContext:
    """Get auth context for client onboarding with IAM integration."""
    return await get_auth_context_with_iam(request, jwt_credentials, "client_onboarding")


async def get_products_auth_context(
    request: Request,
    jwt_credentials: Optional[JWTAuthorizationCredentials] = Depends(jwt_bearer)
) -> AuthContext:
    """Get auth context for products catalog with IAM integration."""
    return await get_auth_context_with_iam(request, jwt_credentials, "products_catalog")


async def get_recipes_auth_context(
    request: Request,
    jwt_credentials: Optional[JWTAuthorizationCredentials] = Depends(jwt_bearer)
) -> AuthContext:
    """Get auth context for recipes catalog with IAM integration."""
    return await get_auth_context_with_iam(request, jwt_credentials, "recipes_catalog")


async def get_iam_auth_context(
    request: Request,
    jwt_credentials: Optional[JWTAuthorizationCredentials] = Depends(jwt_bearer)
) -> AuthContext:
    """Get auth context for IAM with IAM integration."""
    return await get_auth_context_with_iam(request, jwt_credentials, "iam")


# Context-specific user dependencies with comprehensive IAM integration
async def get_client_onboarding_user(
    auth_context: Annotated[AuthContext, Depends(get_client_onboarding_auth_context)]
) -> ClientOnboardingUser:
    """Get current user for client onboarding context with full IAM integration."""
    if not auth_context.user_domain_obj:
        raise HTTPException(
            status_code=401,
            detail="Client onboarding user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_context.user_domain_obj


async def get_products_user(
    auth_context: Annotated[AuthContext, Depends(get_products_auth_context)]
) -> ProductsUser:
    """Get current user for products catalog context with full IAM integration."""
    if not auth_context.user_domain_obj:
        raise HTTPException(
            status_code=401,
            detail="Products user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_context.user_domain_obj


async def get_recipes_user(
    auth_context: Annotated[AuthContext, Depends(get_recipes_auth_context)]
) -> RecipesUser:
    """Get current user for recipes catalog context with full IAM integration."""
    if not auth_context.user_domain_obj:
        raise HTTPException(
            status_code=401,
            detail="Recipes user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_context.user_domain_obj


async def get_iam_user(
    auth_context: Annotated[AuthContext, Depends(get_iam_auth_context)]
) -> IAMUser:
    """Get current user for IAM context with full IAM integration."""
    if not auth_context.user_domain_obj:
        raise HTTPException(
            status_code=401,
            detail="IAM user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_context.user_domain_obj
