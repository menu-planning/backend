"""
Configuration for Client Onboarding Context

Settings for TypeForm API integration, webhook security, and AWS Lambda deployment.
"""

import os
import sys
from typing import Any, ClassVar, Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.logging.logger import get_logger


class ClientOnboardingConfig(BaseSettings):
    """Configuration settings for client onboarding services."""

    # Constants for validation limits
    TYPEFORM_MAX_RATE_LIMIT: ClassVar[int] = 2
    TYPEFORM_MAX_TIMEOUT_SECONDS: ClassVar[int] = 300
    TYPEFORM_MIN_API_KEY_LENGTH: ClassVar[int] = 10
    TYPEFORM_MIN_WEBHOOK_SECRET_LENGTH: ClassVar[int] = 10
    TYPEFORM_PRODUCTION_WEBHOOK_SECRET_LENGTH: ClassVar[int] = 20
    TYPEFORM_STRONG_WEBHOOK_SECRET_LENGTH: ClassVar[int] = 32
    TYPEFORM_MAX_PAYLOAD_SIZE_MB: ClassVar[int] = 10
    TYPEFORM_MIN_RETRY_INTERVAL_MINUTES: ClassVar[int] = 1
    TYPEFORM_MAX_RETRY_INTERVAL_MINUTES: ClassVar[int] = 60
    TYPEFORM_MAX_RETRY_MAX_INTERVAL_MINUTES: ClassVar[int] = 120
    TYPEFORM_MAX_BACKOFF_MULTIPLIER: ClassVar[float] = 5.0
    TYPEFORM_MAX_JITTER_PERCENTAGE: ClassVar[float] = 50.0
    TYPEFORM_REQUIRED_RETRY_DURATION_HOURS: ClassVar[int] = 10
    TYPEFORM_MIN_RETRY_ATTEMPTS: ClassVar[int] = 3
    TYPEFORM_MAX_RETRY_ATTEMPTS: ClassVar[int] = 50
    TYPEFORM_MAX_FAILURE_RATE_PERCENTAGE: ClassVar[float] = 100.0
    TYPEFORM_MIN_TIMEOUT_SECONDS: ClassVar[int] = 30
    TYPEFORM_MIN_RETRY_JITTER_PERCENTAGE: ClassVar[float] = 10.0
    TYPEFORM_OPTIMAL_RETRY_JITTER_PERCENTAGE: ClassVar[float] = 25.0
    TYPEFORM_MIN_RATE_LIMIT_INTERVAL_SECONDS: ClassVar[float] = 0.5

    # TypeForm API Configuration
    typeform_api_key: str = os.getenv("TYPEFORM_API_KEY", "")
    typeform_api_base_url: str = "https://api.typeform.com"
    typeform_api_version: str = "v1"
    typeform_rate_limit_requests_per_second: int = (
        2  # Changed from 4 to 2 for TypeForm API compliance
    )
    typeform_timeout_seconds: int = 30

    # TypeForm Proxy (egress) Configuration
    typeform_via_proxy: bool = (
        os.getenv("TYPEFORM_VIA_PROXY", "false").lower() == "true"
    )
    typeform_proxy_function_name: str = os.getenv("TYPEFORM_PROXY_FUNCTION_NAME", "")

    # Webhook Configuration
    typeform_webhook_secret: str = os.getenv("TYPEFORM_WEBHOOK_SECRET", "")
    webhook_endpoint_url: str = os.getenv("TYPEFORM_WEBHOOK_URL", "")
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
    webhook_processing_enabled: bool = (
        os.getenv("WEBHOOK_PROCESSING_ENABLED", "true").lower() == "true"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",  # Allow extra env vars to be ignored
    )

    @field_validator("typeform_rate_limit_requests_per_second")
    @classmethod
    def validate_rate_limit_compliance(cls, v: int) -> int:
        """Validate rate limiting configuration for TypeForm API compliance."""
        if v > cls.TYPEFORM_MAX_RATE_LIMIT:
            error_msg = (
                f"TypeForm API rate limit must be {cls.TYPEFORM_MAX_RATE_LIMIT} "
                f"req/sec or lower for compliance, got {v}. "
                "See https://www.typeform.com/developers/responses/ for details."
            )
            raise ValueError(error_msg)
        if v <= 0:
            error_msg = f"Rate limit must be positive, got {v}"
            raise ValueError(error_msg)
        return v

    @field_validator("typeform_timeout_seconds")
    @classmethod
    def validate_timeout_reasonable(cls, v: int) -> int:
        """Validate timeout configuration is reasonable."""
        if v <= 0:
            error_msg = f"Timeout must be positive, got {v}"
            raise ValueError(error_msg)
        if v > cls.TYPEFORM_MAX_TIMEOUT_SECONDS:
            error_msg = (
                f"Timeout too high (max {cls.TYPEFORM_MAX_TIMEOUT_SECONDS}s), got {v}"
            )
            raise ValueError(error_msg)
        return v

    @field_validator("max_webhook_payload_size")
    @classmethod
    def validate_payload_size(cls, v: int) -> int:
        """Validate webhook payload size limits."""
        if v <= 0:
            error_msg = f"Payload size must be positive, got {v}"
            raise ValueError(error_msg)
        max_size = cls.TYPEFORM_MAX_PAYLOAD_SIZE_MB * 1024 * 1024
        if v > max_size:
            error_msg = (
                f"Payload size too large "
                f"(max {cls.TYPEFORM_MAX_PAYLOAD_SIZE_MB}MB), got {v}"
            )
            raise ValueError(error_msg)
        return v

    @field_validator("webhook_retry_initial_interval_minutes")
    @classmethod
    def validate_retry_initial_interval(cls, v: int) -> int:
        """Validate initial retry interval is reasonable."""
        if v <= 0:
            error_msg = f"Retry initial interval must be positive, got {v}"
            raise ValueError(error_msg)
        if v < cls.TYPEFORM_MIN_RETRY_INTERVAL_MINUTES:
            error_msg = (
                f"Retry initial interval too short "
                f"(min {cls.TYPEFORM_MIN_RETRY_INTERVAL_MINUTES} minute), got {v}"
            )
            raise ValueError(error_msg)
        if v > cls.TYPEFORM_MAX_RETRY_INTERVAL_MINUTES:
            error_msg = (
                f"Retry initial interval too long "
                f"(max {cls.TYPEFORM_MAX_RETRY_INTERVAL_MINUTES} minutes), got {v}"
            )
            raise ValueError(error_msg)
        return v

    @field_validator("webhook_retry_max_interval_minutes")
    @classmethod
    def validate_retry_max_interval(cls, v: int) -> int:
        """Validate maximum retry interval is reasonable."""
        if v <= 0:
            error_msg = f"Retry max interval must be positive, got {v}"
            raise ValueError(error_msg)
        if v > cls.TYPEFORM_MAX_RETRY_MAX_INTERVAL_MINUTES:
            error_msg = (
                f"Retry max interval too long "
                f"(max {cls.TYPEFORM_MAX_RETRY_MAX_INTERVAL_MINUTES} minutes), got {v}"
            )
            raise ValueError(error_msg)
        return v

    @field_validator("webhook_retry_exponential_backoff_multiplier")
    @classmethod
    def validate_retry_backoff_multiplier(cls, v: float) -> float:
        """Validate exponential backoff multiplier is reasonable."""
        if v <= 1.0:
            error_msg = f"Backoff multiplier must be > 1.0, got {v}"
            raise ValueError(error_msg)
        if v > cls.TYPEFORM_MAX_BACKOFF_MULTIPLIER:
            error_msg = (
                f"Backoff multiplier too high "
                f"(max {cls.TYPEFORM_MAX_BACKOFF_MULTIPLIER}), got {v}"
            )
            raise ValueError(error_msg)
        return v

    @field_validator("webhook_retry_jitter_percentage")
    @classmethod
    def validate_retry_jitter_percentage(cls, v: float) -> float:
        """Validate jitter percentage is reasonable."""
        if v < 0:
            error_msg = f"Jitter percentage must be non-negative, got {v}"
            raise ValueError(error_msg)
        if v > cls.TYPEFORM_MAX_JITTER_PERCENTAGE:
            error_msg = (
                f"Jitter percentage too high "
                f"(max {cls.TYPEFORM_MAX_JITTER_PERCENTAGE}%), got {v}"
            )
            raise ValueError(error_msg)
        return v

    @field_validator("webhook_retry_max_duration_hours")
    @classmethod
    def validate_retry_max_duration(cls, v: int) -> int:
        """Validate maximum retry duration matches TypeForm requirements."""
        if v <= 0:
            error_msg = f"Retry max duration must be positive, got {v}"
            raise ValueError(error_msg)
        if v != cls.TYPEFORM_REQUIRED_RETRY_DURATION_HOURS:
            error_msg = (
                f"Retry max duration must be "
                f"{cls.TYPEFORM_REQUIRED_RETRY_DURATION_HOURS} "
                f"hours per TypeForm requirements, got {v}"
            )
            raise ValueError(error_msg)
        return v

    @field_validator("webhook_retry_max_total_attempts")
    @classmethod
    def validate_retry_max_attempts(cls, v: int) -> int:
        """Validate maximum retry attempts is reasonable."""
        if v <= 0:
            error_msg = f"Retry max attempts must be positive, got {v}"
            raise ValueError(error_msg)
        if v < cls.TYPEFORM_MIN_RETRY_ATTEMPTS:
            error_msg = (
                f"Retry max attempts too low "
                f"(min {cls.TYPEFORM_MIN_RETRY_ATTEMPTS}), got {v}"
            )
            raise ValueError(error_msg)
        if v > cls.TYPEFORM_MAX_RETRY_ATTEMPTS:
            error_msg = (
                f"Retry max attempts too high "
                f"(max {cls.TYPEFORM_MAX_RETRY_ATTEMPTS}), got {v}"
            )
            raise ValueError(error_msg)
        return v

    @field_validator("webhook_retry_failure_rate_disable_threshold")
    @classmethod
    def validate_retry_failure_rate_threshold(cls, v: float) -> float:
        """Validate failure rate disable threshold."""
        if v < 0:
            error_msg = f"Failure rate threshold must be non-negative, got {v}"
            raise ValueError(error_msg)
        if v > cls.TYPEFORM_MAX_FAILURE_RATE_PERCENTAGE:
            error_msg = (
                f"Failure rate threshold cannot exceed "
                f"{cls.TYPEFORM_MAX_FAILURE_RATE_PERCENTAGE}%, got {v}"
            )
            raise ValueError(error_msg)
        return v

    @model_validator(mode="after")
    def validate_webhook_configuration(self) -> Self:
        """Validate webhook configuration completeness and security."""
        validation_errors = []

        # Skip validation in testing environments
        is_testing = (
            os.getenv("TESTING", "false").lower() == "true"
            or os.getenv("PYTEST_CURRENT_TEST") is not None
            or "pytest" in sys.modules
        )
        if is_testing:
            return self

        # Check required environment variables for production
        if not self.typeform_api_key:
            validation_errors.append(
                "TYPEFORM_API_KEY environment variable is required"
            )
        elif len(self.typeform_api_key) < self.TYPEFORM_MIN_API_KEY_LENGTH:
            validation_errors.append(
                "TYPEFORM_API_KEY appears to be invalid (too short)"
            )

        if not self.typeform_webhook_secret:
            validation_errors.append(
                "TYPEFORM_WEBHOOK_SECRET environment variable is required "
                "for webhook security"
            )
        elif (
            len(self.typeform_webhook_secret) < self.TYPEFORM_MIN_WEBHOOK_SECRET_LENGTH
        ):
            validation_errors.append(
                "TYPEFORM_WEBHOOK_SECRET appears to be too weak (minimum 10 characters)"
            )

        if not self.webhook_endpoint_url:
            validation_errors.append(
                "TYPEFORM_WEBHOOK_URL environment variable is required"
            )
        elif not self.webhook_endpoint_url.startswith(("https://", "http://")):
            validation_errors.append("TYPEFORM_WEBHOOK_URL must be a valid HTTP(S) URL")

        # Validate security settings
        if self.webhook_timeout_seconds > self.typeform_timeout_seconds:
            validation_errors.append(
                f"Webhook timeout ({self.webhook_timeout_seconds}s) should not exceed "
                f"API timeout ({self.typeform_timeout_seconds}s)"
            )

        # Validate retry configuration relationships
        if (
            self.webhook_retry_initial_interval_minutes
            >= self.webhook_retry_max_interval_minutes
        ):
            error_msg = (
                f"Retry initial interval "
                f"({self.webhook_retry_initial_interval_minutes}min) "
                f"must be less than max interval "
                f"({self.webhook_retry_max_interval_minutes}min)"
            )
            validation_errors.append(error_msg)

        if validation_errors:
            error_message = "Configuration validation failed:\n" + "\n".join(
                f"  - {error}" for error in validation_errors
            )
            raise ValueError(error_message)

        return self

    def validate_production_environment(self) -> dict[str, Any]:
        """Validate production environment configuration."""
        status = {
            "environment": self.environment,
            "webhook_processing_enabled": self.webhook_processing_enabled,
            "rate_limit_compliance": (
                self.typeform_rate_limit_requests_per_second
                <= self.TYPEFORM_MAX_RATE_LIMIT
            ),
            "configuration_valid": True,
            "issues": [],
        }

        if self.environment == "production":
            required_fields = [
                ("typeform_api_key", self.typeform_api_key),
                ("typeform_webhook_secret", self.typeform_webhook_secret),
                ("webhook_endpoint_url", self.webhook_endpoint_url),
            ]

            missing_fields = [name for name, value in required_fields if not value]
            if missing_fields:
                status["issues"].extend(
                    [f"Missing required field: {field}" for field in missing_fields]
                )
                status["configuration_valid"] = False

            # Validate webhook secret strength
            if (
                self.typeform_webhook_secret
                and len(self.typeform_webhook_secret)
                < self.TYPEFORM_PRODUCTION_WEBHOOK_SECRET_LENGTH
            ):
                status["issues"].append(
                    "Webhook secret must be at least 20 characters for production"
                )
                status["configuration_valid"] = False

        return status

    def health_check(self) -> dict[str, Any]:
        """Perform configuration health check."""
        production_status = self.validate_production_environment()
        startup_status = self.validate_startup_configuration()

        return {
            "environment_status": production_status,
            "configuration_status": startup_status,
            "overall_healthy": production_status["configuration_valid"]
            and startup_status["valid"],
        }

    def _validate_rate_limiting(self, validation_results: dict[str, Any]) -> None:
        """Validate rate limiting configuration."""
        if self.typeform_rate_limit_requests_per_second == self.TYPEFORM_MAX_RATE_LIMIT:
            validation_results["recommendations"].append(
                "Rate limiting correctly configured at 2 req/sec "
                "for TypeForm compliance"
            )

    def _validate_webhook_security(self, validation_results: dict[str, Any]) -> None:
        """Validate webhook security configuration."""
        if (
            len(self.typeform_webhook_secret)
            >= self.TYPEFORM_STRONG_WEBHOOK_SECRET_LENGTH
        ):
            validation_results["recommendations"].append(
                "Webhook secret has strong length (32+ characters)"
            )
        elif (
            len(self.typeform_webhook_secret) >= self.TYPEFORM_MIN_WEBHOOK_SECRET_LENGTH
        ):
            validation_results["warnings"].append(
                "Consider using a longer webhook secret "
                "(32+ characters) for enhanced security"
            )

    def _validate_url_security(self, validation_results: dict[str, Any]) -> None:
        """Validate URL security configuration."""
        if self.webhook_endpoint_url.startswith("https://"):
            validation_results["recommendations"].append(
                "Webhook endpoint uses HTTPS for secure communication"
            )
        elif self.webhook_endpoint_url.startswith("http://"):
            validation_results["warnings"].append(
                "Webhook endpoint uses HTTP - consider HTTPS for production"
            )

    def _validate_timeout_configuration(
        self, validation_results: dict[str, Any]
    ) -> None:
        """Validate timeout configuration."""
        if self.typeform_timeout_seconds >= self.TYPEFORM_MIN_TIMEOUT_SECONDS:
            validation_results["recommendations"].append(
                f"API timeout configured appropriately at "
                f"{self.typeform_timeout_seconds}s"
            )
        else:
            validation_results["warnings"].append(
                f"API timeout may be too low "
                f"({self.typeform_timeout_seconds}s) - consider 30s+"
            )

    def _validate_performance_recommendations(
        self, validation_results: dict[str, Any]
    ) -> None:
        """Validate performance recommendations."""
        rate_limit_interval = 1.0 / self.typeform_rate_limit_requests_per_second
        if rate_limit_interval >= self.TYPEFORM_MIN_RATE_LIMIT_INTERVAL_SECONDS:
            validation_results["recommendations"].append(
                f"Rate limiting provides good API stability with "
                f"{rate_limit_interval:.2f}s intervals"
            )

    def _validate_retry_configuration(self, validation_results: dict[str, Any]) -> None:
        """Validate retry configuration."""
        if self.webhook_retry_initial_interval_minutes == self.TYPEFORM_MAX_RATE_LIMIT:
            validation_results["recommendations"].append(
                "Retry initial interval correctly configured at "
                "2 minutes per TypeForm requirements"
            )

        if (
            self.webhook_retry_max_duration_hours
            == self.TYPEFORM_REQUIRED_RETRY_DURATION_HOURS
        ):
            validation_results["recommendations"].append(
                "Retry max duration correctly configured at "
                "10 hours per TypeForm requirements"
            )

        if (
            self.webhook_retry_jitter_percentage
            == self.TYPEFORM_OPTIMAL_RETRY_JITTER_PERCENTAGE
        ):
            validation_results["recommendations"].append(
                "Retry jitter configured at optimal 25% to prevent thundering herd"
            )
        elif (
            self.webhook_retry_jitter_percentage
            < self.TYPEFORM_MIN_RETRY_JITTER_PERCENTAGE
        ):
            validation_results["warnings"].append(
                f"Retry jitter may be too low "
                f"({self.webhook_retry_jitter_percentage}%) - consider 20-30%"
            )

    def validate_startup_configuration(self) -> dict[str, Any]:
        """
        Perform comprehensive startup configuration validation.

        Returns:
            Dict with validation results and recommendations
        """
        logger = get_logger("validate_startup_configuration")
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": [],
        }

        # Break down validation into smaller methods to reduce complexity
        self._validate_rate_limiting(validation_results)
        self._validate_webhook_security(validation_results)
        self._validate_url_security(validation_results)
        self._validate_timeout_configuration(validation_results)
        self._validate_performance_recommendations(validation_results)
        self._validate_retry_configuration(validation_results)

        # Log validation results
        if validation_results["errors"]:
            validation_results["valid"] = False
            logger.error("Configuration validation failed:")
            for error in validation_results["errors"]:
                logger.error("Configuration validation error", error=error)

        if validation_results["warnings"]:
            logger.warning("Configuration warnings detected:")
            for warning in validation_results["warnings"]:
                logger.warning("Configuration validation warning", warning=warning)

        if validation_results["recommendations"]:
            logger.info("Configuration recommendations:")
            for rec in validation_results["recommendations"]:
                logger.info("Configuration recommendation", recommendation=rec)

        return validation_results


# Global configuration instance with startup validation
config = ClientOnboardingConfig()

# Perform startup validation and log results (skip during testing)
is_testing = (
    os.getenv("TESTING", "false").lower() == "true"
    or os.getenv("PYTEST_CURRENT_TEST") is not None
    or "pytest" in sys.modules
)
if not is_testing:
    startup_validation = config.validate_startup_configuration()
    if not startup_validation["valid"]:
        error_msg = "Configuration validation failed - check logs for details"
        raise RuntimeError(error_msg)
