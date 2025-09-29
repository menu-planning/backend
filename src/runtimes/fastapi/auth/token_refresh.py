"""
FastAPI token refresh mechanism for Cognito authentication.

This module provides token refresh functionality for Cognito User Pool tokens,
handling refresh token exchange and automatic token renewal.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel, Field

from src.config.app_config import get_app_settings
from src.contexts.shared_kernel.middleware.auth.authentication import AuthenticationError

logger = logging.getLogger(__name__)


class TokenRefreshError(AuthenticationError):
    """Exception raised when token refresh fails."""
    
    def __init__(self, message: str, error_code: str = "REFRESH_FAILED"):
        super().__init__(message)
        self.error_code = error_code


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""
    
    refresh_token: str = Field(..., description="Cognito refresh token")
    client_id: Optional[str] = Field(None, description="Cognito App Client ID")


class TokenResponse(BaseModel):
    """Response model for token refresh."""
    
    access_token: str = Field(..., description="New access token")
    id_token: Optional[str] = Field(None, description="New ID token")
    refresh_token: Optional[str] = Field(None, description="New refresh token")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    token_type: str = Field(default="Bearer", description="Token type")


class CognitoTokenRefresher:
    """
    Token refresher for Cognito User Pool tokens.
    
    This class handles:
    - Refresh token exchange with Cognito
    - Token expiration tracking
    - Automatic token renewal
    - Error handling and retry logic
    
    Attributes:
        cognito_region: AWS region where Cognito User Pool is located
        user_pool_id: Cognito User Pool ID
        client_id: Cognito App Client ID
        client_secret: Cognito App Client Secret (if configured)
        token_endpoint: Cognito OAuth2 token endpoint URL
    """
    
    def __init__(
        self,
        cognito_region: Optional[str] = None,
        user_pool_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """
        Initialize Cognito token refresher.
        
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
        
        # Construct token endpoint URL
        self.token_endpoint = (
            f"https://{self.user_pool_id}.auth.{self.cognito_region}.amazoncognito.com/oauth2/token"
        )
        
        logger.info(
            "CognitoTokenRefresher initialized",
            extra={
                "cognito_region": self.cognito_region,
                "user_pool_id": self.user_pool_id,
                "token_endpoint": self.token_endpoint,
                "has_client_secret": bool(self.client_secret),
            }
        )
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh Cognito access token using refresh token.
        
        Args:
            refresh_token: Cognito refresh token
            
        Returns:
            TokenResponse: New tokens and expiration information
            
        Raises:
            TokenRefreshError: When token refresh fails
            
        Notes:
            This method exchanges a refresh token for new access and ID tokens.
            It handles Cognito's OAuth2 token endpoint with proper error handling.
        """
        try:
            # Prepare request data
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
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
                "Refreshing token",
                extra={
                    "client_id": self.client_id,
                    "has_client_secret": bool(self.client_secret),
                    "token_endpoint": self.token_endpoint,
                }
            )
            
            # Make request to Cognito token endpoint
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.token_endpoint,
                    data=data,
                    headers=headers,
                )
                
                response.raise_for_status()
                token_data = response.json()
                
                logger.debug(
                    "Token refresh successful",
                    extra={
                        "expires_in": token_data.get("expires_in"),
                        "token_type": token_data.get("token_type"),
                        "has_id_token": "id_token" in token_data,
                        "has_new_refresh_token": "refresh_token" in token_data,
                    }
                )
                
                # Parse and validate response
                return TokenResponse(
                    access_token=token_data["access_token"],
                    id_token=token_data.get("id_token"),
                    refresh_token=token_data.get("refresh_token"),
                    expires_in=token_data["expires_in"],
                    token_type=token_data.get("token_type", "Bearer"),
                )
                
        except httpx.HTTPStatusError as e:
            error_message = "Token refresh failed"
            error_code = "REFRESH_FAILED"
            
            try:
                error_data = e.response.json()
                error_message = error_data.get("error_description", error_message)
                error_code = error_data.get("error", error_code)
            except (json.JSONDecodeError, KeyError):
                error_message = f"HTTP {e.response.status_code}: {e.response.text}"
            
            logger.warning(
                "Token refresh failed with HTTP error",
                extra={
                    "status_code": e.response.status_code,
                    "error_message": error_message,
                    "error_code": error_code,
                }
            )
            
            raise TokenRefreshError(error_message, error_code) from e
            
        except httpx.RequestError as e:
            error_message = f"Network error during token refresh: {str(e)}"
            logger.error("Token refresh network error", extra={"error": str(e)})
            raise TokenRefreshError(error_message, "NETWORK_ERROR") from e
            
        except Exception as e:
            error_message = f"Unexpected error during token refresh: {str(e)}"
            logger.error("Token refresh unexpected error", extra={"error": str(e)})
            raise TokenRefreshError(error_message, "UNEXPECTED_ERROR") from e
    
    def is_token_expired(self, token: str, buffer_percentage: float = 0.25) -> bool:
        """
        Check if a JWT token is expired or will expire soon.
        
        Args:
            token: JWT token string
            buffer_percentage: Percentage of token lifespan to use before considering it expired (default 0.25 = 75% usage)
            
        Returns:
            bool: True if token is expired or has used more than (1 - buffer_percentage) of its lifespan
            
        Notes:
            This method follows AWS Cognito best practices by using tokens for approximately 75% of their lifespan.
            Based on: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-caching-tokens.html
        """
        try:
            import jwt
            
            # Decode token without verification (just to get claims)
            decoded = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False}
            )
            
            exp_timestamp = decoded.get("exp")
            if not exp_timestamp:
                # No expiration claim - assume expired for safety
                return True
            
            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            now = datetime.now(tz=timezone.utc)
            
            # Calculate token lifespan and buffer time based on percentage
            issued_at = decoded.get("iat", exp_timestamp)
            issued_datetime = datetime.fromtimestamp(issued_at, tz=timezone.utc)
            total_lifespan = exp_datetime - issued_datetime
            buffer_time = total_lifespan * buffer_percentage
            
            is_expired = (exp_datetime - buffer_time) <= now
            
            logger.debug(
                "Token expiration check",
                extra={
                    "expires_at": exp_datetime.isoformat(),
                    "current_time": now.isoformat(),
                    "total_lifespan_seconds": total_lifespan.total_seconds(),
                    "buffer_percentage": buffer_percentage,
                    "buffer_seconds": buffer_time.total_seconds(),
                    "is_expired": is_expired,
                }
            )
            
            return is_expired
            
        except Exception as e:
            logger.warning(
                "Failed to check token expiration",
                extra={"error": str(e)}
            )
            # If we can't decode the token, assume it's expired for safety
            return True
    
    async def refresh_token_if_needed(
        self,
        access_token: str,
        refresh_token: str,
        buffer_percentage: float = 0.25
    ) -> tuple[str, Optional[str]]:
        """
        Refresh token if it's expired or will expire soon.
        
        Args:
            access_token: Current access token
            refresh_token: Refresh token for renewal
            buffer_percentage: Percentage of token lifespan to use before refreshing (default 0.25 = 75% usage)
            
        Returns:
            Tuple of (access_token, new_refresh_token)
            - If token is still valid, returns original tokens
            - If token is expired, returns new tokens from refresh
            
        Notes:
            This method follows AWS Cognito best practices by using tokens for approximately 75% of their lifespan.
            Based on: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-caching-tokens.html
        """
        if not self.is_token_expired(access_token, buffer_percentage):
            logger.debug("Token is still valid, no refresh needed")
            return access_token, None
        
        logger.info("Token is expired or expiring soon, refreshing")
        
        try:
            token_response = await self.refresh_token(refresh_token)
            
            logger.info(
                "Token refreshed successfully",
                extra={
                    "expires_in": token_response.expires_in,
                    "has_new_refresh_token": bool(token_response.refresh_token),
                }
            )
            
            new_refresh_token = token_response.refresh_token or refresh_token
            return token_response.access_token, new_refresh_token
            
        except TokenRefreshError as e:
            logger.error(
                "Token refresh failed",
                extra={
                    "error_message": str(e),
                    "error_code": e.error_code,
                }
            )
            raise


# Global refresher instance (singleton pattern)
_refresher_instance: Optional[CognitoTokenRefresher] = None


def get_token_refresher() -> CognitoTokenRefresher:
    """
    Get or create the global token refresher instance.
    
    Returns:
        CognitoTokenRefresher: Global refresher instance
        
    Notes:
        Uses singleton pattern to avoid recreating HTTP clients
        and maintain efficient configuration across requests.
    """
    global _refresher_instance
    
    if _refresher_instance is None:
        _refresher_instance = CognitoTokenRefresher()
    
    return _refresher_instance
