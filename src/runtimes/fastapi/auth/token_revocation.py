"""
FastAPI token revocation support for Cognito authentication.

This module provides token revocation functionality for Cognito User Pool tokens,
handling revoked token tracking and validation according to AWS Cognito best practices.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

import httpx
from pydantic import BaseModel, Field

from src.config.app_config import get_app_settings
from src.contexts.shared_kernel.middleware.auth.authentication import AuthenticationError

logger = logging.getLogger(__name__)


class TokenRevocationError(AuthenticationError):
    """Exception raised when token revocation operations fail."""
    
    def __init__(self, message: str, error_code: str = "REVOCATION_FAILED"):
        super().__init__(message)
        self.error_code = error_code


class RevokeTokenRequest(BaseModel):
    """Request model for token revocation."""
    
    token: str = Field(..., description="Token to revoke (access, ID, or refresh token)")
    client_id: Optional[str] = Field(None, description="Cognito App Client ID")


class CognitoTokenRevoker:
    """
    Token revoker for Cognito User Pool tokens.
    
    This class handles:
    - Token revocation via Cognito RevokeToken endpoint
    - Revoked token tracking using origin_jti
    - Token revocation validation
    - Cache management for revoked tokens
    
    Based on AWS Cognito documentation:
    https://docs.aws.amazon.com/cognito/latest/developerguide/token-revocation.html
    
    Attributes:
        cognito_region: AWS region where Cognito User Pool is located
        user_pool_id: Cognito User Pool ID
        client_id: Cognito App Client ID
        client_secret: Cognito App Client Secret (if configured)
        revoke_endpoint: Cognito OAuth2 revoke endpoint URL
        _revoked_tokens: Cache for revoked token origin_jti values
    """
    
    def __init__(
        self,
        cognito_region: Optional[str] = None,
        user_pool_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """
        Initialize Cognito token revoker.
        
        Args:
            cognito_region: AWS region for Cognito User Pool
            user_pool_id: Cognito User Pool ID
            client_id: Cognito App Client ID
            client_secret: Cognito App Client Secret (if configured)
            
        Notes:
            If parameters are not provided, they will be loaded from app configuration.
        """
        config = get_app_settings()
        
        self.cognito_region = cognito_region or config.cognito_region
        self.user_pool_id = user_pool_id or config.cognito_user_pool_id
        self.client_id = client_id or config.cognito_client_id
        self.client_secret = client_secret or getattr(config, 'cognito_client_secret', None)
        
        if not all([self.cognito_region, self.user_pool_id, self.client_id]):
            raise ValueError(
                "Cognito configuration missing. Please provide cognito_region, "
                "user_pool_id, and client_id or configure them in app settings."
            )
        
        # Construct revoke endpoint URL
        self.revoke_endpoint = (
            f"https://{self.user_pool_id}.auth.{self.cognito_region}.amazoncognito.com/oauth2/revoke"
        )
        
        # Cache for revoked tokens (origin_jti -> revocation_time)
        self._revoked_tokens: dict[str, datetime] = {}
        
        logger.info(
            "CognitoTokenRevoker initialized",
            extra={
                "cognito_region": self.cognito_region,
                "user_pool_id": self.user_pool_id,
                "revoke_endpoint": self.revoke_endpoint,
                "has_client_secret": bool(self.client_secret),
            }
        )
    
    async def revoke_token(self, token: str) -> bool:
        """
        Revoke a Cognito token.
        
        Args:
            token: Token to revoke (access, ID, or refresh token)
            
        Returns:
            bool: True if token was successfully revoked
            
        Raises:
            TokenRevocationError: When token revocation fails
            
        Notes:
            This method calls Cognito's RevokeToken endpoint to revoke the token.
            After successful revocation, the token's origin_jti is cached locally
            to prevent future validation of revoked tokens.
        """
        try:
            # Prepare request data
            data = {
                "token": token,
                "client_id": self.client_id,
            }
            
            # Add client secret if configured (for confidential clients)
            if self.client_secret:
                data["client_secret"] = self.client_secret
            
            # Prepare headers
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            logger.debug(
                "Revoking token",
                extra={
                    "client_id": self.client_id,
                    "has_client_secret": bool(self.client_secret),
                    "revoke_endpoint": self.revoke_endpoint,
                }
            )
            
            # Make request to Cognito revoke endpoint
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.revoke_endpoint,
                    data=data,
                    headers=headers,
                )
                
                response.raise_for_status()
                
                logger.info(
                    "Token revoked successfully",
                    extra={
                        "status_code": response.status_code,
                    }
                )
                
                # Extract origin_jti from token and cache it
                try:
                    import jwt
                    decoded = jwt.decode(
                        token,
                        options={"verify_signature": False, "verify_exp": False}
                    )
                    origin_jti = decoded.get("origin_jti")
                    if origin_jti:
                        self._revoked_tokens[origin_jti] = datetime.now(tz=timezone.utc)
                        logger.debug(
                            "Cached revoked token origin_jti",
                            extra={"origin_jti": origin_jti}
                        )
                except Exception as e:
                    logger.warning(
                        "Failed to extract origin_jti from revoked token",
                        extra={"error": str(e)}
                    )
                
                return True
                
        except httpx.HTTPStatusError as e:
            error_message = "Token revocation failed"
            error_code = "REVOCATION_FAILED"
            
            try:
                error_data = e.response.json()
                error_message = error_data.get("error_description", error_message)
                error_code = error_data.get("error", error_code)
            except Exception:
                error_message = f"HTTP {e.response.status_code}: {e.response.text}"
            
            logger.warning(
                "Token revocation failed with HTTP error",
                extra={
                    "status_code": e.response.status_code,
                    "error_message": error_message,
                    "error_code": error_code,
                }
            )
            
            raise TokenRevocationError(error_message, error_code) from e
            
        except httpx.RequestError as e:
            error_message = f"Network error during token revocation: {str(e)}"
            logger.error("Token revocation network error", extra={"error": str(e)})
            raise TokenRevocationError(error_message, "NETWORK_ERROR") from e
            
        except Exception as e:
            error_message = f"Unexpected error during token revocation: {str(e)}"
            logger.error("Token revocation unexpected error", extra={"error": str(e)})
            raise TokenRevocationError(error_message, "UNEXPECTED_ERROR") from e
    
    def is_token_revoked(self, token: str) -> bool:
        """
        Check if a token has been revoked.
        
        Args:
            token: JWT token string to check
            
        Returns:
            bool: True if token is revoked
            
        Notes:
            This method checks if the token's origin_jti is in the revoked tokens cache.
            It also cleans up expired entries from the cache.
        """
        try:
            import jwt
            
            # Decode token without verification (just to get claims)
            decoded = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False}
            )
            
            origin_jti = decoded.get("origin_jti")
            if not origin_jti:
                # No origin_jti means token revocation is not enabled
                return False
            
            # Clean up expired cache entries (older than 24 hours)
            self._cleanup_revoked_tokens_cache()
            
            # Check if token is in revoked cache
            is_revoked = origin_jti in self._revoked_tokens
            
            if is_revoked:
                revocation_time = self._revoked_tokens[origin_jti]
                logger.debug(
                    "Token is revoked",
                    extra={
                        "origin_jti": origin_jti,
                        "revocation_time": revocation_time.isoformat(),
                    }
                )
            
            return is_revoked
            
        except Exception as e:
            logger.warning(
                "Failed to check token revocation status",
                extra={"error": str(e)}
            )
            # If we can't decode the token, assume it's not revoked for safety
            return False
    
    def _cleanup_revoked_tokens_cache(self) -> None:
        """Clean up expired entries from the revoked tokens cache."""
        cutoff_time = datetime.now(tz=timezone.utc) - timedelta(hours=24)
        expired_entries = [
            origin_jti for origin_jti, revocation_time 
            in self._revoked_tokens.items()
            if revocation_time < cutoff_time
        ]
        
        for origin_jti in expired_entries:
            del self._revoked_tokens[origin_jti]
        
        if expired_entries:
            logger.debug(
                "Cleaned up expired revoked token entries",
                extra={
                    "expired_count": len(expired_entries),
                    "remaining_count": len(self._revoked_tokens),
                }
            )
    
    def get_revoked_tokens_count(self) -> int:
        """
        Get the number of cached revoked tokens.
        
        Returns:
            int: Number of revoked tokens in cache
        """
        return len(self._revoked_tokens)


# Global revoker instance (singleton pattern)
_revoker_instance: Optional[CognitoTokenRevoker] = None


def get_token_revoker() -> CognitoTokenRevoker:
    """
    Get or create the global token revoker instance.
    
    Returns:
        CognitoTokenRevoker: Global revoker instance
        
    Notes:
        Uses singleton pattern to avoid recreating HTTP clients
        and maintain efficient configuration across requests.
    """
    global _revoker_instance
    
    if _revoker_instance is None:
        _revoker_instance = CognitoTokenRevoker()
    
    return _revoker_instance
