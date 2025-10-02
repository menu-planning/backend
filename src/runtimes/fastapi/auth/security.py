"""
FastAPI security dependencies for JWT authentication with Cognito.

This module provides FastAPI security dependencies that follow the FastAPI pattern
while integrating with the existing authentication infrastructure including cache,
token refresh, and revocation.
"""

from typing import Any
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from src.runtimes.fastapi.auth.jwt_validator import CognitoJWTValidator, JWTValidationError, CognitoJWTClaims
from src.runtimes.fastapi.auth.cache import RequestScopedAuthCache
from src.runtimes.fastapi.auth.token_revocation import CognitoTokenRevoker

from src.logging.logger import get_logger

logger = get_logger(__name__)

class JWTAuthorizationCredentials(BaseModel):
    """JWT authorization credentials with parsed claims."""
    
    jwt_token: str
    header: dict[str, Any]
    claims: CognitoJWTClaims
    signature: str
    message: str


class JWTBearer(HTTPBearer):
    """
    FastAPI JWT Bearer authentication following the FastAPI pattern.
    
    This class integrates with the existing authentication infrastructure
    including JWT validation, caching, and token revocation checking.
    """
    
    def __init__(
        self, 
        jwt_validator: CognitoJWTValidator | None = None,
        cache: RequestScopedAuthCache | None = None,
        token_revoker: CognitoTokenRevoker | None = None,
        auto_error: bool = True
    ):
        """
        Initialize JWT Bearer authentication.
        
        Args:
            jwt_validator: JWT validator instance (creates default if None)
            cache: Request-scoped cache instance (creates default if None)
            token_revoker: Token revoker instance (creates default if None)
            auto_error: Whether to automatically raise HTTP exceptions on auth failure
        """
        super().__init__(auto_error=auto_error)
        self.jwt_validator = jwt_validator or CognitoJWTValidator()
        self.cache = cache or RequestScopedAuthCache()
        self.token_revoker = token_revoker or CognitoTokenRevoker()
    
    async def __call__(self, request: Request) -> JWTAuthorizationCredentials | None:
        """
        Extract and validate JWT credentials from request.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            JWTAuthorizationCredentials if valid, None if auto_error=False
            
        Raises:
            HTTPException: If authentication fails and auto_error=True
        """
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return None
            
        credentials: HTTPAuthorizationCredentials | None = await super().__call__(request)

        if not credentials:
            if self.auto_error:
                logger.error("Authentication required", request_url=str(request.url), request_method=request.method)
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        if credentials.scheme != "Bearer":
            if self.auto_error:
                logger.error("Invalid authentication scheme", request_url=str(request.url), request_method=request.method)
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        jwt_token = credentials.credentials
        
        try:
            # Check cache first
            cache_key = f"jwt_credentials:{jwt_token}"
            cached_credentials = self.cache.get(cache_key)
            if cached_credentials:
                return cached_credentials
            
            # Validate JWT token
            claims = await self.jwt_validator.validate_token(jwt_token)
            
            # Check if token is revoked
            if self.token_revoker.is_token_revoked(jwt_token):
                logger.error("Token has been revoked", request_url=str(request.url), request_method=request.method)
                raise HTTPException(
                    status_code=401,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Parse JWT components
            message, signature = jwt_token.rsplit(".", 1)
            
            # Get unverified header using jwt library
            import jwt as pyjwt
            header = pyjwt.get_unverified_header(jwt_token)
            
            # Create credentials object
            jwt_credentials = JWTAuthorizationCredentials(
                jwt_token=jwt_token,
                header=header,
                claims=claims,
                signature=signature,
                message=message,
            )
            
            # Cache the validated credentials
            self.cache.set(cache_key, jwt_credentials)
            
            return jwt_credentials
            
        except JWTValidationError as e:
            if self.auto_error:
                logger.error("Invalid token", request_url=str(request.url), request_method=request.method)
                raise HTTPException(
                    status_code=401,
                    detail=f"Invalid token: {e.error_code}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        except HTTPException:
            logger.error("HTTP exception occurred", request_url=str(request.url), request_method=request.method)
            # Re-raise HTTP exceptions
            raise
        
        except Exception as e:
            if self.auto_error:
                logger.error("Authentication failed", request_url=str(request.url), request_method=request.method)
                raise HTTPException(
                    status_code=401,
                    detail="Authentication failed",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None


# Create default JWT Bearer instance
jwt_bearer = JWTBearer(auto_error=False)  # Don't auto-raise for Swagger UI integration


