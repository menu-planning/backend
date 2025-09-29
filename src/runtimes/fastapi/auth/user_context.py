"""
FastAPI user context extraction for authentication.

This module provides utilities for extracting user data from validated JWT tokens
and creating user context objects for FastAPI applications.
"""

import logging
from typing import Any
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from src.runtimes.fastapi.auth.jwt_validator import CognitoJWTClaims

logger = logging.getLogger(__name__)


class UserContext(BaseModel):
    """
    User context extracted from JWT token claims.
    
    This model represents the authenticated user's context with all relevant
    information extracted from Cognito JWT claims.
    """
    
    # Core user identification
    user_id: str = Field(..., description="Unique user identifier (subject claim)")
    username: str | None = Field(None, description="Cognito username")
    cognito_username: str | None = Field(None, description="Cognito username from claims")
    
    # Authentication information
    token_use: str = Field(..., description="Token use (access, id, refresh)")
    issuer: str = Field(..., description="Token issuer")
    audience: str = Field(..., description="Token audience")
    expires_at: datetime = Field(..., description="Token expiration time")
    issued_at: datetime = Field(..., description="Token issued time")
    auth_time: datetime | None = Field(None, description="Authentication time")
    
    # User roles and permissions
    roles: list[str] = Field(default_factory=list, description="User roles")
    groups: list[str] = Field(default_factory=list, description="Cognito groups")
    preferred_role: str | None = Field(None, description="Preferred role")
    
    # Token metadata
    client_id: str | None = Field(None, description="App client ID")
    jti: str | None = Field(None, description="JWT ID")
    origin_jti: str | None = Field(None, description="Token revocation identifier")
    
    # Identity provider information
    identities: list[dict[str, Any]] | None = Field(None, description="Identity provider info")
    
    # Custom attributes
    custom_roles: str | None = Field(None, description="Custom roles from claims")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserContextExtractor:
    """
    Extractor for user context from Cognito JWT claims.
    
    This class provides methods to extract and transform Cognito JWT claims
    into structured user context objects for FastAPI applications.
    """
    
    def extract_user_context(self, claims: CognitoJWTClaims) -> UserContext:
        """
        Extract user context from Cognito JWT claims.
        
        Args:
            claims: Validated Cognito JWT claims
            
        Returns:
            UserContext: Structured user context object
            
        Notes:
            This method transforms JWT claims into a structured user context
            with proper type conversion and role extraction.
        """
        try:
            # Extract roles from multiple sources
            roles = self._extract_user_roles(claims)
            groups = self._extract_user_groups(claims)
            
            # Convert timestamps to datetime objects
            expires_at = datetime.fromtimestamp(claims.exp, tz=timezone.utc)
            issued_at = datetime.fromtimestamp(claims.iat, tz=timezone.utc)
            auth_time = None
            if claims.auth_time:
                auth_time = datetime.fromtimestamp(claims.auth_time, tz=timezone.utc)
            
            user_context = UserContext(
                # Core identification
                user_id=claims.sub,
                username=claims.username,
                cognito_username=claims.cognito_username,
                
                # Authentication info
                token_use=claims.token_use,
                issuer=claims.iss,
                audience=claims.aud,
                expires_at=expires_at,
                issued_at=issued_at,
                auth_time=auth_time,
                
                # Roles and permissions
                roles=roles,
                groups=groups,
                preferred_role=claims.cognito_preferred_role,
                
                # Token metadata
                client_id=claims.client_id,
                jti=claims.jti,
                origin_jti=claims.origin_jti,
                
                # Identity provider info
                identities=claims.identities,
                
                # Custom attributes
                custom_roles=claims.custom_roles,
            )
            
            logger.debug(
                "User context extracted",
                extra={
                    "user_id": user_context.user_id,
                    "username": user_context.username,
                    "roles": user_context.roles,
                    "groups": user_context.groups,
                    "token_use": user_context.token_use,
                    "expires_at": user_context.expires_at.isoformat(),
                }
            )
            
            return user_context
            
        except Exception as e:
            logger.error(
                "Failed to extract user context",
                extra={
                    "user_id": getattr(claims, 'sub', None),
                    "error": str(e),
                }
            )
            raise ValueError(f"Failed to extract user context: {str(e)}") from e
    
    def _extract_user_roles(self, claims: CognitoJWTClaims) -> list[str]:
        """
        Extract user roles from JWT claims.
        
        Args:
            claims: Cognito JWT claims
            
        Returns:
            List of user roles
        """
        roles = []
        
        # Extract from custom:roles claim
        if claims.custom_roles:
            roles.extend([role.strip() for role in claims.custom_roles.split(",")])
        
        # Extract from cognito:roles claim
        if claims.cognito_roles:
            roles.extend(claims.cognito_roles)
        
        # Remove duplicates and empty roles
        roles = list(set([role for role in roles if role.strip()]))
        
        return roles
    
    def _extract_user_groups(self, claims: CognitoJWTClaims) -> list[str]:
        """
        Extract user groups from JWT claims.
        
        Args:
            claims: Cognito JWT claims
            
        Returns:
            List of user groups
        """
        groups = []
        
        # Extract from cognito:groups claim
        if claims.cognito_groups:
            groups.extend(claims.cognito_groups)
        
        # Remove duplicates and empty groups
        groups = list(set([group for group in groups if group.strip()]))
        
        return groups
    
    def is_token_valid(self, user_context: UserContext) -> bool:
        """
        Check if the token in user context is still valid.
        
        Args:
            user_context: User context with token information
            
        Returns:
            bool: True if token is valid (not expired)
        """
        now = datetime.now(tz=timezone.utc)
        return user_context.expires_at > now
    
    def get_token_remaining_lifetime(self, user_context: UserContext) -> float | None:
        """
        Get remaining token lifetime in seconds.
        
        Args:
            user_context: User context with token information
            
        Returns:
            Optional[float]: Remaining lifetime in seconds, or None if expired
        """
        now = datetime.now(tz=timezone.utc)
        if user_context.expires_at <= now:
            return None
        
        delta = user_context.expires_at - now
        return delta.total_seconds()
    
    # Note: Role checking methods have been removed to avoid duplication
    # with AuthContext. Use AuthContext.has_role(), AuthContext.has_any_role()
    # for role checking functionality.
    
    def get_user_summary(self, user_context: UserContext) -> dict[str, Any]:
        """
        Get a summary of user context for logging/debugging.
        
        Args:
            user_context: User context to summarize
            
        Returns:
            Dictionary with user summary information
        """
        return {
            "user_id": user_context.user_id,
            "username": user_context.username,
            "roles": user_context.roles,
            "groups": user_context.groups,
            "token_use": user_context.token_use,
            "expires_at": user_context.expires_at.isoformat(),
            "is_valid": self.is_token_valid(user_context),
            "remaining_lifetime": self.get_token_remaining_lifetime(user_context),
        }


# Global extractor instance (singleton pattern)
_extractor_instance: UserContextExtractor | None = None


def get_user_context_extractor() -> UserContextExtractor:
    """
    Get or create the global user context extractor instance.
    
    Returns:
        UserContextExtractor: Global extractor instance
        
    Notes:
        Uses singleton pattern to avoid recreating extractor instances
        across requests.
    """
    global _extractor_instance
    
    if _extractor_instance is None:
        _extractor_instance = UserContextExtractor()
    
    return _extractor_instance
