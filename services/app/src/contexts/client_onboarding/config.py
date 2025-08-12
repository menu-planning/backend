"""
Configuration for Client Onboarding Context

Settings for TypeForm API integration, webhook security, and AWS Lambda deployment.
"""

import os
import sys
import logging
from typing import List, Dict, Any, Self
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator


class ClientOnboardingConfig(BaseSettings):
    """Configuration settings for client onboarding services."""
    
    # TypeForm API Configuration
    typeform_api_key: str = os.getenv("TYPEFORM_API_KEY", "")
    typeform_api_base_url: str = "https://api.typeform.com"
    typeform_api_version: str = "v1"
    typeform_rate_limit_requests_per_second: int = 2  # Changed from 4 to 2 for TypeForm API compliance
    typeform_timeout_seconds: int = 30

    # TypeForm Proxy (egress) Configuration
    typeform_via_proxy: bool = os.getenv("TYPEFORM_VIA_PROXY", "false").lower() == "true"
    typeform_proxy_function_name: str = os.getenv("TYPEFORM_PROXY_FUNCTION_NAME", "")
    
    # Webhook Configuration
    typeform_webhook_secret: str = os.getenv("TYPEFORM_WEBHOOK_SECRET", "")
    webhook_endpoint_url: str = os.getenv("WEBHOOK_ENDPOINT_URL", "")
    webhook_timeout_seconds: int = 30
    
    # Security Settings
    webhook_signature_header: str = "Typeform-Signature"
    max_webhook_payload_size: int = 1024 * 1024  # 1MB
    
    # Webhook Retry Configuration
    webhook_retry_initial_interval_minutes: int = 2
    webhook_retry_max_interval_minutes: int = 60
    webhook_retry_exponential_backoff_multiplier: float = 2.0
    webhook_retry_jitter_percentage: float = 25.0
    webhook_retry_max_duration_hours: int = 10
    webhook_retry_max_total_attempts: int = 20
    webhook_retry_failure_rate_disable_threshold: float = 100.0
    webhook_retry_failure_rate_evaluation_window_hours: int = 24
    
    # Database Settings
    enable_response_encryption: bool = True
    response_retention_days: int = 365
    
    # Production Environment Validation
    environment: str = os.getenv("ENVIRONMENT", "development")
    webhook_processing_enabled: bool = os.getenv("WEBHOOK_PROCESSING_ENABLED", "true").lower() == "true"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Allow extra env vars to be ignored
    )
    
    @field_validator('typeform_rate_limit_requests_per_second')
    @classmethod
    def validate_rate_limit_compliance(cls, v: int) -> int:
        """Validate rate limiting configuration for TypeForm API compliance."""
        if v > 2:
            raise ValueError(
                f"TypeForm API rate limit must be 2 req/sec or lower for compliance, got {v}. "
                "See https://www.typeform.com/developers/responses/ for rate limit details."
            )
        if v <= 0:
            raise ValueError(f"Rate limit must be positive, got {v}")
        return v
    
    @field_validator('typeform_timeout_seconds')
    @classmethod
    def validate_timeout_reasonable(cls, v: int) -> int:
        """Validate timeout configuration is reasonable."""
        if v <= 0:
            raise ValueError(f"Timeout must be positive, got {v}")
        if v > 300:  # 5 minutes max
            raise ValueError(f"Timeout too high (max 300s), got {v}")
        return v
    
    @field_validator('max_webhook_payload_size')
    @classmethod
    def validate_payload_size(cls, v: int) -> int:
        """Validate webhook payload size limits."""
        if v <= 0:
            raise ValueError(f"Payload size must be positive, got {v}")
        if v > 10 * 1024 * 1024:  # 10MB max
            raise ValueError(f"Payload size too large (max 10MB), got {v}")
        return v
    
    @field_validator('webhook_retry_initial_interval_minutes')
    @classmethod
    def validate_retry_initial_interval(cls, v: int) -> int:
        """Validate initial retry interval is reasonable."""
        if v <= 0:
            raise ValueError(f"Retry initial interval must be positive, got {v}")
        if v < 1:
            raise ValueError(f"Retry initial interval too short (min 1 minute), got {v}")
        if v > 60:
            raise ValueError(f"Retry initial interval too long (max 60 minutes), got {v}")
        return v
    
    @field_validator('webhook_retry_max_interval_minutes')
    @classmethod
    def validate_retry_max_interval(cls, v: int) -> int:
        """Validate maximum retry interval is reasonable."""
        if v <= 0:
            raise ValueError(f"Retry max interval must be positive, got {v}")
        if v > 120:  # 2 hours max
            raise ValueError(f"Retry max interval too long (max 120 minutes), got {v}")
        return v
    
    @field_validator('webhook_retry_exponential_backoff_multiplier')
    @classmethod
    def validate_retry_backoff_multiplier(cls, v: float) -> float:
        """Validate exponential backoff multiplier is reasonable."""
        if v <= 1.0:
            raise ValueError(f"Backoff multiplier must be > 1.0, got {v}")
        if v > 5.0:
            raise ValueError(f"Backoff multiplier too high (max 5.0), got {v}")
        return v
    
    @field_validator('webhook_retry_jitter_percentage')
    @classmethod
    def validate_retry_jitter_percentage(cls, v: float) -> float:
        """Validate jitter percentage is reasonable."""
        if v < 0:
            raise ValueError(f"Jitter percentage must be non-negative, got {v}")
        if v > 50.0:
            raise ValueError(f"Jitter percentage too high (max 50%), got {v}")
        return v
    
    @field_validator('webhook_retry_max_duration_hours')
    @classmethod
    def validate_retry_max_duration(cls, v: int) -> int:
        """Validate maximum retry duration matches TypeForm requirements."""
        if v <= 0:
            raise ValueError(f"Retry max duration must be positive, got {v}")
        if v != 10:
            raise ValueError(f"Retry max duration must be 10 hours per TypeForm requirements, got {v}")
        return v
    
    @field_validator('webhook_retry_max_total_attempts')
    @classmethod
    def validate_retry_max_attempts(cls, v: int) -> int:
        """Validate maximum retry attempts is reasonable."""
        if v <= 0:
            raise ValueError(f"Retry max attempts must be positive, got {v}")
        if v < 3:
            raise ValueError(f"Retry max attempts too low (min 3), got {v}")
        if v > 50:
            raise ValueError(f"Retry max attempts too high (max 50), got {v}")
        return v
    
    @field_validator('webhook_retry_failure_rate_disable_threshold')
    @classmethod
    def validate_retry_failure_rate_threshold(cls, v: float) -> float:
        """Validate failure rate disable threshold."""
        if v < 0:
            raise ValueError(f"Failure rate threshold must be non-negative, got {v}")
        if v > 100.0:
            raise ValueError(f"Failure rate threshold cannot exceed 100%, got {v}")
        return v
    
    @model_validator(mode='after')
    def validate_webhook_configuration(self) -> Self:
        """Validate webhook configuration completeness and security."""
        validation_errors = []
        
        # Skip validation in testing environments
        is_testing = (os.getenv("TESTING", "false").lower() == "true" or 
                     os.getenv("PYTEST_CURRENT_TEST") is not None or
                     'pytest' in sys.modules)
        if is_testing:
            return self
        
        # Check required environment variables for production
        if not self.typeform_api_key:
            validation_errors.append("TYPEFORM_API_KEY environment variable is required")
        elif len(self.typeform_api_key) < 10:
            validation_errors.append("TYPEFORM_API_KEY appears to be invalid (too short)")
        
        if not self.typeform_webhook_secret:
            validation_errors.append("TYPEFORM_WEBHOOK_SECRET environment variable is required for webhook security")
        elif len(self.typeform_webhook_secret) < 10:
            validation_errors.append("TYPEFORM_WEBHOOK_SECRET appears to be too weak (minimum 10 characters)")
        
        if not self.webhook_endpoint_url:
            validation_errors.append("WEBHOOK_ENDPOINT_URL environment variable is required")
        elif not self.webhook_endpoint_url.startswith(('https://', 'http://')):
            validation_errors.append("WEBHOOK_ENDPOINT_URL must be a valid HTTP(S) URL")
        
        # Validate security settings
        if self.webhook_timeout_seconds > self.typeform_timeout_seconds:
            validation_errors.append(
                f"Webhook timeout ({self.webhook_timeout_seconds}s) should not exceed "
                f"API timeout ({self.typeform_timeout_seconds}s)"
            )
        
        # Validate retry configuration relationships
        if self.webhook_retry_initial_interval_minutes >= self.webhook_retry_max_interval_minutes:
            validation_errors.append(
                f"Retry initial interval ({self.webhook_retry_initial_interval_minutes}min) must be less than "
                f"max interval ({self.webhook_retry_max_interval_minutes}min)"
            )
        
        if validation_errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in validation_errors)
            raise ValueError(error_message)
        
        return self
    
    def validate_production_environment(self) -> Dict[str, Any]:
        """Validate production environment configuration."""
        status = {
            "environment": self.environment,
            "webhook_processing_enabled": self.webhook_processing_enabled,
            "rate_limit_compliance": self.typeform_rate_limit_requests_per_second <= 2,
            "configuration_valid": True,
            "issues": []
        }
        
        if self.environment == "production":
            required_fields = [
                ("typeform_api_key", self.typeform_api_key),
                ("typeform_webhook_secret", self.typeform_webhook_secret),
                ("webhook_endpoint_url", self.webhook_endpoint_url)
            ]
            
            missing_fields = [name for name, value in required_fields if not value]
            if missing_fields:
                status["issues"].extend([f"Missing required field: {field}" for field in missing_fields])
                status["configuration_valid"] = False
                
            # Validate webhook secret strength
            if self.typeform_webhook_secret and len(self.typeform_webhook_secret) < 20:
                status["issues"].append("Webhook secret must be at least 20 characters for production")
                status["configuration_valid"] = False
                
        return status
    
    def health_check(self) -> Dict[str, Any]:
        """Perform configuration health check."""
        production_status = self.validate_production_environment()
        startup_status = self.validate_startup_configuration()
        
        return {
            "environment_status": production_status,
            "configuration_status": startup_status,
            "overall_healthy": production_status["configuration_valid"] and startup_status["valid"]
        }
    
    def validate_startup_configuration(self) -> Dict[str, Any]:
        """
        Perform comprehensive startup configuration validation.
        
        Returns:
            Dict with validation results and recommendations
        """
        logger = logging.getLogger(__name__)
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Rate limiting validation
        if self.typeform_rate_limit_requests_per_second == 2:
            validation_results["recommendations"].append(
                "Rate limiting correctly configured at 2 req/sec for TypeForm compliance"
            )
        
        # Webhook security validation
        if len(self.typeform_webhook_secret) >= 32:
            validation_results["recommendations"].append(
                "Webhook secret has strong length (32+ characters)"
            )
        elif len(self.typeform_webhook_secret) >= 10:
            validation_results["warnings"].append(
                "Consider using a longer webhook secret (32+ characters) for enhanced security"
            )
        
        # URL validation
        if self.webhook_endpoint_url.startswith('https://'):
            validation_results["recommendations"].append(
                "Webhook endpoint uses HTTPS for secure communication"
            )
        elif self.webhook_endpoint_url.startswith('http://'):
            validation_results["warnings"].append(
                "Webhook endpoint uses HTTP - consider HTTPS for production"
            )
        
        # Timeout configuration validation
        if self.typeform_timeout_seconds >= 30:
            validation_results["recommendations"].append(
                f"API timeout configured appropriately at {self.typeform_timeout_seconds}s"
            )
        else:
            validation_results["warnings"].append(
                f"API timeout may be too low ({self.typeform_timeout_seconds}s) - consider 30s+"
            )
        
        # Performance recommendations
        rate_limit_interval = 1.0 / self.typeform_rate_limit_requests_per_second
        if rate_limit_interval >= 0.5:  # 500ms between requests
            validation_results["recommendations"].append(
                f"Rate limiting provides good API stability with {rate_limit_interval:.2f}s intervals"
            )
        
        # Retry configuration validation
        if self.webhook_retry_initial_interval_minutes == 2:
            validation_results["recommendations"].append(
                "Retry initial interval correctly configured at 2 minutes per TypeForm requirements"
            )
        
        if self.webhook_retry_max_duration_hours == 10:
            validation_results["recommendations"].append(
                "Retry max duration correctly configured at 10 hours per TypeForm requirements"
            )
        
        if self.webhook_retry_jitter_percentage == 25.0:
            validation_results["recommendations"].append(
                "Retry jitter configured at optimal 25% to prevent thundering herd"
            )
        elif self.webhook_retry_jitter_percentage < 10.0:
            validation_results["warnings"].append(
                f"Retry jitter may be too low ({self.webhook_retry_jitter_percentage}%) - consider 20-30%"
            )
        
        # Log validation results
        if validation_results["errors"]:
            validation_results["valid"] = False
            logger.error("Configuration validation failed:")
            for error in validation_results["errors"]:
                logger.error(f"  ERROR: {error}")
        
        if validation_results["warnings"]:
            logger.warning("Configuration warnings detected:")
            for warning in validation_results["warnings"]:
                logger.warning(f"  WARNING: {warning}")
        
        if validation_results["recommendations"]:
            logger.info("Configuration recommendations:")
            for rec in validation_results["recommendations"]:
                logger.info(f"  INFO: {rec}")
        
        return validation_results


# Global configuration instance with startup validation
config = ClientOnboardingConfig()

# Perform startup validation and log results (skip during testing)
is_testing = (os.getenv("TESTING", "false").lower() == "true" or 
             os.getenv("PYTEST_CURRENT_TEST") is not None or
             'pytest' in sys.modules)
if not is_testing:
    startup_validation = config.validate_startup_configuration()
    if not startup_validation["valid"]:
        raise RuntimeError("Configuration validation failed - check logs for details") 