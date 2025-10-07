"""
FastAPI JWT token validator for Cognito authentication.

This module provides JWT token validation for FastAPI applications using
Cognito User Pool tokens. It validates token signatures, expiration,
and extracts user claims.
"""

import logging
from datetime import datetime, timezone
from typing import Any

import httpx
import jwt
from jwt import PyJWKClient
from pydantic import BaseModel, Field

from src.config.app_config import get_app_settings
from src.contexts.shared_kernel.middleware.auth.authentication import AuthenticationError
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class JWTValidationError(AuthenticationError):
    """Exception raised when JWT validation fails."""
    
    def __init__(self, message: str, error_code: str = "INVALID_TOKEN"):
        super().__init__(message)
        self.error_code = error_code


class CognitoJWTClaims(BaseModel):
    """Cognito JWT token claims structure.
    
    Based on AWS Cognito documentation:
    - https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-id-token.html
    - https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html
    """
    
    # Standard JWT claims
    sub: str = Field(..., description="User ID (subject) - unique identifier for authenticated user")
    iss: str = Field(..., description="Token issuer - Cognito User Pool URL")
    aud: str = Field(..., description="Token audience - App Client ID")
    exp: int = Field(..., description="Expiration time (Unix timestamp)")
    iat: int = Field(..., description="Issued at time (Unix timestamp)")
    nbf: int | None = Field(None, description="Not before time (Unix timestamp)")
    token_use: str = Field(..., description="Token use (access, id, refresh)")
    scope: str | None = Field(None, description="Token scope - OAuth 2.0 scopes")
    auth_time: int | None = Field(None, description="Authentication time (Unix timestamp)")
    jti: str | None = Field(None, description="JWT ID - unique identifier for the JWT")
    
    # Cognito-specific claims for ID tokens
    cognito_username: str | None = Field(None, alias="cognito:username")
    cognito_groups: list[str] | None = Field(None, alias="cognito:groups")
    cognito_roles: list[str] | None = Field(None, alias="cognito:roles")
    cognito_preferred_role: str | None = Field(None, alias="cognito:preferred_role")
    
    # Cognito-specific claims for access tokens
    client_id: str | None = Field(None, description="App Client ID (access token only)")
    username: str | None = Field(None, description="Username (access token only)")
    
    # Token revocation claims (when token revocation is enabled)
    origin_jti: str | None = Field(None, description="Token revocation identifier associated with refresh token")
    
    # Identity provider claims
    identities: list[dict[str, Any]] | None = Field(None, description="Third-party identity provider information")
    
    # Additional OIDC claims
    nonce: str | None = Field(None, description="Nonce for replay attack protection")
    event_id: str | None = Field(None, description="Event identifier")
    
    # Custom claims
    custom_roles: str | None = Field(None, alias="custom:roles")
    
    class Config:
        populate_by_name = True


class CognitoJWTValidator:
    """
    JWT token validator for Cognito User Pool tokens.
    
    This validator:
    - Validates JWT token signature using Cognito's public keys
    - Checks token expiration and not-before times
    - Validates issuer and audience
    - Extracts and validates user claims
    - Caches JWKS (JSON Web Key Set) for performance
    
    Attributes:
        jwks_client: PyJWKClient for fetching and caching JWKS
        cognito_region: AWS region where Cognito User Pool is located
        user_pool_id: Cognito User Pool ID
        client_id: Cognito App Client ID
        _jwks_cache: Cache for JWKS to avoid repeated HTTP calls
    """
    
    def __init__(
        self,
        cognito_region:str | None = None,
        user_pool_id:str | None = None,
        client_id:str | None = None,
        check_revocation: bool = True,
    ):
        """
        Initialize Cognito JWT validator.
        
        Args:
            cognito_region: AWS region for Cognito User Pool
            user_pool_id: Cognito User Pool ID
            client_id: Cognito App Client ID
            check_revocation: Whether to check token revocation status
            
        Notes:
            If parameters are not provided, they will be loaded from app configuration.
        """
        config = get_app_settings()
        
        self.cognito_region = cognito_region or config.cognito_region
        self.user_pool_id = user_pool_id or config.cognito_user_pool_id
        self.client_id = client_id or config.cognito_client_id
        self.check_revocation = check_revocation
        
        if not all([self.cognito_region, self.user_pool_id, self.client_id]):
            raise ValueError(
                "Cognito configuration missing. Please provide cognito_region, "
                "user_pool_id, and client_id or configure them in app settings."
            )
        
        # Construct JWKS URL
        self.jwks_url = (
            f"https://cognito-idp.{self.cognito_region}.amazonaws.com/"
            f"{self.user_pool_id}/.well-known/jwks.json"
        )
        
        # Initialize JWKS client with caching
        # Based on PyJWT documentation: https://pyjwt.readthedocs.io/en/stable/usage.html
        self.jwks_client = PyJWKClient(
            uri=self.jwks_url,
            cache_keys=True,           # Cache signing keys for performance
            max_cached_keys=16,        # Default max cached keys
            cache_jwk_set=True,        # Cache the JWK set
            lifespan=3600,             # Cache for 1 hour (3600 seconds)
            timeout=30,                # HTTP timeout
        )
        
        # Initialize token revoker if revocation checking is enabled
        self.token_revoker = None
        if self.check_revocation:
            try:
                from src.runtimes.fastapi.auth.token_revocation import get_token_revoker
                self.token_revoker = get_token_revoker()
            except ImportError:
                logger.warning("Token revocation module not available, revocation checking disabled")
                self.check_revocation = False
        
        logger.info(
            "CognitoJWTValidator initialized",
            extra={
                "cognito_region": self.cognito_region,
                "user_pool_id": self.user_pool_id,
                "jwks_url": self.jwks_url,
            }
        )
    
    async def validate_token(self, token: str) -> CognitoJWTClaims:
        """
        Validate Cognito JWT token and extract claims.
        
        Args:
            token: JWT token string (without 'Bearer ' prefix)
            
        Returns:
            CognitoJWTClaims: Validated and parsed token claims
            
        Raises:
            JWTValidationError: When token validation fails
            
        Notes:
            This method validates:
            - Token signature using Cognito's public keys
            - Token expiration (exp claim)
            - Token not-before time (nbf claim)
            - Token issuer (iss claim)
            - Token audience (aud claim)
        """
        try:
            # Get signing key from JWKS using the token directly
            # Based on PyJWT documentation: https://pyjwt.readthedocs.io/en/stable/usage.html
            signing_key = self.jwks_client.get_signing_key_from_jwt(token).key
            # Decode and validate token
            # Based on PyJWT documentation patterns for Cognito validation
            decoded_token = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=f"https://cognito-idp.{self.cognito_region}.amazonaws.com/{self.user_pool_id}",
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )
            
            # Validate token use
            token_use = decoded_token.get("token_use")
            if token_use not in ["access", "id"]:
                raise JWTValidationError(
                    f"Invalid token_use: {token_use}. Expected 'access' or 'id'"
                )
            
            # Check token revocation if enabled
            if self.check_revocation and self.token_revoker:
                if self.token_revoker.is_token_revoked(token):
                    raise JWTValidationError(
                        "Token has been revoked",
                        "TOKEN_REVOKED"
                    )
            
            # Parse claims using Pydantic model
            claims = CognitoJWTClaims(**decoded_token)
            
            logger.debug(
                "JWT token validated successfully",
                extra={
                    "user_id": claims.sub,
                    "token_use": claims.token_use,
                    "expires_at": datetime.fromtimestamp(claims.exp, tz=timezone.utc).isoformat(),
                }
            )
            
            return claims
            
        except jwt.ExpiredSignatureError as e:
            logger.warning("JWT token expired", extra={"error": str(e)})
            raise JWTValidationError("Token has expired", "TOKEN_EXPIRED") from e
            
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid JWT token", extra={"error": str(e)})
            raise JWTValidationError("Invalid token", "INVALID_TOKEN") from e
            
        except Exception as e:
            logger.error("JWT validation failed", extra={"error": str(e)})
            raise JWTValidationError("Token validation failed", "VALIDATION_ERROR") from e
    
    def extract_user_roles(self, claims: CognitoJWTClaims) -> list[str]:
        """
        Extract user roles from Cognito JWT claims.
        
        Args:
            claims: Validated Cognito JWT claims
            
        Returns:
            List of user roles extracted from claims
        """
        roles = []
        
        # Extract roles from custom:roles claim
        if claims.custom_roles:
            roles.extend([role.strip() for role in claims.custom_roles.split(",")])
        
        # Extract roles from cognito:groups claim
        if claims.cognito_groups:
            roles.extend(claims.cognito_groups)
        
        # Remove duplicates and empty roles
        roles = list(set([role for role in roles if role.strip()]))
        
        logger.debug(
            "User roles extracted",
            extra={
                "user_id": claims.sub,
                "roles": roles,
                "custom_roles": claims.custom_roles,
                "cognito_groups": claims.cognito_groups,
            }
        )
        
        return roles
    
    async def get_user_pool_info(self) -> dict[str, Any]:
        """
        Get Cognito User Pool information for debugging/validation.
        
        Returns:
            Dictionary containing User Pool information
            
        Notes:
            This method fetches User Pool metadata from Cognito's
            well-known configuration endpoint.
        """
        try:
            config_url = (
                f"https://cognito-idp.{self.cognito_region}.amazonaws.com/"
                f"{self.user_pool_id}/.well-known/openid_configuration"
            )
            
            async with httpx.AsyncClient() as client:
                response = await client.get(config_url)
                response.raise_for_status()
                
                config = response.json()
                
                logger.debug(
                    "Cognito User Pool configuration retrieved",
                    extra={
                        "issuer": config.get("issuer"),
                        "jwks_uri": config.get("jwks_uri"),
                        "supported_scopes": config.get("scopes_supported", []),
                    }
                )
                
                return config
                
        except Exception as e:
            logger.error(
                "Failed to retrieve Cognito User Pool configuration",
                extra={"error": str(e)}
            )
            raise JWTValidationError("Failed to retrieve User Pool configuration") from e


# Global validator instance (singleton pattern)
_validator_instance: CognitoJWTValidator | None = None


class DevJWTValidator:
    """
    Development mode JWT validator that generates valid JWTs with fixed claims.
    
    This validator creates properly signed JWT tokens with fixed dev user data,
    eliminating the need for Cognito during development while maintaining
    the same JWT structure and validation flow.
    """
    
    def __init__(self):
        """Initialize Dev JWT validator with configuration."""
        self.config = get_app_settings()
        self.secret_key = self.config.token_secret_key.get_secret_value()
        self.algorithm = self.config.algorithm
        self.check_revocation = False  # Dev mode doesn't check revocation
    
    async def validate_token(self, token: str) -> CognitoJWTClaims:
        """
        Validate a development JWT token or generate a new one.
        
        In dev mode, we accept any token and return fixed dev claims.
        For security, we could validate the token format if needed.
        
        Args:
            token: JWT token string (can be any value in dev mode)
            
        Returns:
            CognitoJWTClaims: Fixed dev user claims
        """
        # Parse dev user roles from config
        dev_roles = [role.strip() for role in self.config.dev_user_roles.split(",") if role.strip()]
        
        # Create fixed dev claims that match CognitoJWTClaims structure
        dev_claims = CognitoJWTClaims(
            sub=self.config.dev_user_id,
            iss="dev-mode",
            aud="dev-client", 
            exp=int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
            iat=int(datetime.now(timezone.utc).timestamp()),
            token_use="access",
            **{"cognito:username": self.config.dev_user_email},
            **{"cognito:groups": dev_roles},
            **{"custom:roles": self.config.dev_user_roles},
            client_id="dev-client",
            nbf=None,
            scope=None,
            auth_time=None,
            jti=None,
            **{"cognito:roles": None},
            **{"cognito:preferred_role": None},
            username=None,
            origin_jti=None,
            identities=None,
            nonce=None,
            event_id=None,
        )
        
        logger.debug(
            "Dev mode JWT validation successful",
            extra={
                "user_id": dev_claims.sub,
                "user_email": dev_claims.cognito_username,
                "user_roles": dev_roles,
            }
        )
        
        return dev_claims
    
    def extract_user_roles(self, claims: CognitoJWTClaims) -> list[str]:
        """
        Extract user roles from dev JWT claims.
        
        Args:
            claims: Dev JWT claims
            
        Returns:
            List of user roles
        """
        roles = []
        
        # Extract roles from custom:roles claim
        if claims.custom_roles:
            roles.extend([role.strip() for role in claims.custom_roles.split(",")])
        
        # Extract roles from cognito:groups claim
        if claims.cognito_groups:
            roles.extend(claims.cognito_groups)
        
        # Remove duplicates and empty roles
        roles = list(set([role for role in roles if role.strip()]))
        
        logger.debug(
            "Dev user roles extracted",
            extra={
                "user_id": claims.sub,
                "roles": roles,
                "custom_roles": claims.custom_roles,
                "cognito_groups": claims.cognito_groups,
            }
        )
        
        return roles


def get_jwt_validator() -> CognitoJWTValidator | DevJWTValidator:
    """
    Get the appropriate JWT validator instance based on environment configuration.
    
    Returns:
        DevJWTValidator for development mode, CognitoJWTValidator for production
    """
    config = get_app_settings()
    
    if config.dev_mode_auth_bypass:
        logger.info("Using DevJWTValidator for authentication (dev mode enabled)")
        return DevJWTValidator()
    else:
        logger.info("Using CognitoJWTValidator for authentication (Cognito mode)")
        # Use singleton pattern for Cognito validator
        global _validator_instance
        if _validator_instance is None:
            _validator_instance = CognitoJWTValidator()
        return _validator_instance
