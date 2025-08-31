import os
from functools import lru_cache
from typing import Any, Dict

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SchemaStandardizationFeatureFlags(BaseSettings):
    """
    Feature flags for API Schema Standardization rollout.
    
    Controls context-by-context rollout of schema pattern standardization
    across all 5 contexts. Each context can be independently enabled/disabled
    for safe incremental deployment.
    
    Environment Variables:
    - SCHEMA_STANDARDIZATION_ENABLED: Master toggle for all schema standardization
    - SCHEMA_SEEDWORK_ENABLED: Enable standardization for Seedwork context
    - SCHEMA_SHARED_KERNEL_ENABLED: Enable standardization for Shared Kernel context
    - SCHEMA_IAM_ENABLED: Enable standardization for IAM context
    - SCHEMA_PRODUCTS_CATALOG_ENABLED: Enable standardization for Products Catalog context
    - SCHEMA_RECIPES_CATALOG_ENABLED: Enable standardization for Recipes Catalog context
    - SCHEMA_VALIDATION_MODE: Validation strictness (strict/lenient/disabled)
    - SCHEMA_ROLLBACK_MODE: Enable automatic rollback on errors
    """

    model_config = SettingsConfigDict(env_prefix="SCHEMA_STANDARDIZATION_")

    # Master feature flag - must be True for any context to use standardization
    enabled: bool = Field(
        default=False,
        description="Master toggle for schema standardization across all contexts"
    )

    # Context-specific feature flags for incremental rollout
    seedwork_enabled: bool = Field(
        default=False,
        description="Enable schema standardization for Seedwork context (foundation layer)"
    )

    shared_kernel_enabled: bool = Field(
        default=False,
        description="Enable schema standardization for Shared Kernel context"
    )

    iam_enabled: bool = Field(
        default=False,
        description="Enable schema standardization for IAM context (authentication/authorization)"
    )

    products_catalog_enabled: bool = Field(
        default=False,
        description="Enable schema standardization for Products Catalog context"
    )

    recipes_catalog_enabled: bool = Field(
        default=False,
        description="Enable schema standardization for Recipes Catalog context"
    )

    # Validation and safety settings
    validation_mode: str = Field(
        default="strict",
        description="Validation strictness: strict/lenient/disabled"
    )

    rollback_mode: bool = Field(
        default=True,
        description="Enable automatic rollback on schema validation errors"
    )

    # Performance and monitoring settings
    performance_monitoring_enabled: bool = Field(
        default=True,
        description="Enable detailed performance monitoring for schema operations"
    )

    compliance_logging_enabled: bool = Field(
        default=True,
        description="Enable detailed compliance logging for audit purposes"
    )

    # Testing and debugging
    debug_mode: bool = Field(
        default=False,
        description="Enable debug mode for schema standardization (development only)"
    )

    @field_validator("validation_mode")
    @classmethod
    def validate_validation_mode(cls, v: str) -> str:
        allowed_modes = {"strict", "lenient", "disabled"}
        if v not in allowed_modes:
            raise ValueError(f"validation_mode must be one of {allowed_modes}")
        return v

    def is_context_enabled(self, context_name: str) -> bool:
        """
        Check if schema standardization is enabled for a specific context.
        
        Args:
            context_name: Name of the context (seedwork, shared_kernel, iam, 
                         products_catalog, recipes_catalog)
        
        Returns:
            bool: True if both master flag and context flag are enabled
        """
        if not self.enabled:
            return False

        context_flag_map = {
            "seedwork": self.seedwork_enabled,
            "shared_kernel": self.shared_kernel_enabled,
            "iam": self.iam_enabled,
            "products_catalog": self.products_catalog_enabled,
            "recipes_catalog": self.recipes_catalog_enabled
        }

        return context_flag_map.get(context_name, False)

    def get_enabled_contexts(self) -> list[str]:
        """
        Get list of all currently enabled contexts.
        
        Returns:
            list[str]: List of enabled context names
        """
        if not self.enabled:
            return []

        enabled_contexts = []
        context_checks = [
            ("seedwork", self.seedwork_enabled),
            ("shared_kernel", self.shared_kernel_enabled),
            ("iam", self.iam_enabled),
            ("products_catalog", self.products_catalog_enabled),
            ("recipes_catalog", self.recipes_catalog_enabled)
        ]

        for context_name, is_enabled in context_checks:
            if is_enabled:
                enabled_contexts.append(context_name)

        return enabled_contexts

    def get_rollout_status(self) -> dict[str, Any]:
        """
        Get comprehensive rollout status for monitoring and reporting.
        
        Returns:
            Dict[str, Any]: Status information including enabled contexts,
                           configuration settings, and rollout progress
        """
        return {
            "master_enabled": self.enabled,
            "enabled_contexts": self.get_enabled_contexts(),
            "total_contexts": 5,
            "rollout_percentage": len(self.get_enabled_contexts()) / 5 * 100,
            "validation_mode": self.validation_mode,
            "rollback_mode": self.rollback_mode,
            "performance_monitoring": self.performance_monitoring_enabled,
            "compliance_logging": self.compliance_logging_enabled,
            "debug_mode": self.debug_mode
        }


@lru_cache
def get_schema_standardization_flags() -> SchemaStandardizationFeatureFlags:
    """Get cached feature flags instance."""
    return SchemaStandardizationFeatureFlags()


# Global instance for easy access throughout the application
schema_flags = get_schema_standardization_flags()
