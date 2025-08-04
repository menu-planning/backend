"""
Fallback data handlers for Client Onboarding Context.

Handles partial data, missing fields, and service unavailability gracefully to ensure
the onboarding process continues even when some data is missing or services are temporarily unavailable.

Features:
- Graceful degradation for TypeForm API failures
- Partial response processing with missing field handling
- Client identifier extraction fallbacks
- Service unavailability recovery strategies
- Integration with retry handler and error middleware
- Structured logging for fallback events
"""

import asyncio
from typing import Any, Dict, List, Optional, TypeVar
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.logging.logger import StructlogFactory, correlation_id_ctx
from src.contexts.client_onboarding.core.adapters.mappers.field_mapping_config import (
    FallbackStrategy,
    ClientIdentifierType,
    FieldMappingConfig
)
from src.contexts.client_onboarding.core.services.exceptions import (
    TypeFormRateLimitError,
    WebhookPayloadError
)

# Type variables
T = TypeVar('T')

# Configure structured logging
logger = StructlogFactory.get_logger("client_onboarding_fallback_handlers")


class FallbackReason(Enum):
    """Reasons why fallback handling was triggered."""
    SERVICE_UNAVAILABLE = "service_unavailable"
    PARTIAL_DATA = "partial_data"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_DATA_FORMAT = "invalid_data_format"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    TIMEOUT_ERROR = "timeout_error"
    AUTHENTICATION_FAILURE = "authentication_failure"
    VALIDATION_ERROR = "validation_error"


class FallbackAction(Enum):
    """Actions taken during fallback handling."""
    USE_PLACEHOLDER = "use_placeholder"
    SKIP_FIELD = "skip_field"
    USE_DEFAULT_VALUE = "use_default_value"
    QUEUE_FOR_RETRY = "queue_for_retry"
    REQUIRE_MANUAL_REVIEW = "require_manual_review"
    CONTINUE_WITH_PARTIAL = "continue_with_partial"
    ABORT_PROCESSING = "abort_processing"


@dataclass
class FallbackResult:
    """Result of fallback handling operation."""
    success: bool
    action_taken: FallbackAction
    fallback_reason: FallbackReason
    fallback_data: Optional[Dict[str, Any]] = None
    requires_review: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class PartialProcessingResult:
    """Result of partial data processing."""
    processed_data: Dict[str, Any]
    missing_fields: List[str]
    failed_fields: List[str]
    fallback_fields: List[str]
    success_rate: float
    requires_manual_review: bool
    processing_warnings: List[str] = field(default_factory=list)


class ClientOnboardingFallbackHandlers:
    """
    Fallback handlers for client onboarding data processing.
    
    Provides graceful degradation strategies for various failure scenarios
    including partial data, service unavailability, and missing fields.
    """
    
    def __init__(
        self,
        field_mapping_config: Optional[FieldMappingConfig] = None,
        default_timeout: float = 30.0,
        enable_partial_processing: bool = True,
        min_success_threshold: float = 0.5
    ):
        """
        Initialize fallback handlers.
        
        Args:
            field_mapping_config: Configuration for field mapping fallbacks
            default_timeout: Default timeout for fallback operations
            enable_partial_processing: Whether to enable partial data processing
            min_success_threshold: Minimum success rate to continue processing
        """
        self.field_mapping_config = field_mapping_config
        self.default_timeout = default_timeout
        self.enable_partial_processing = enable_partial_processing
        self.min_success_threshold = min_success_threshold
        
        # Initialize default fallback strategies if not provided
        if not self.field_mapping_config:
            self._initialize_default_fallbacks()
    
    def _initialize_default_fallbacks(self) -> None:
        """Initialize default fallback strategies."""
        default_strategies = [
            FallbackStrategy(
                identifier_type=ClientIdentifierType.EMAIL,
                use_placeholder=False,
                require_manual_review=True,
                confidence_threshold=0.8
            ),
            FallbackStrategy(
                identifier_type=ClientIdentifierType.NAME,
                use_placeholder=True,
                placeholder_pattern="Guest_{timestamp}",
                require_manual_review=False,
                confidence_threshold=0.6
            ),
            FallbackStrategy(
                identifier_type=ClientIdentifierType.PHONE,
                use_placeholder=False,
                require_manual_review=False,
                confidence_threshold=0.9
            )
        ]
        
        self.field_mapping_config = FieldMappingConfig(
            rules=[],  # Will be provided by actual configuration
            fallback_strategies=default_strategies
        )
    
    async def handle_webhook_payload_fallback(
        self,
        payload: Dict[str, Any],
        original_error: Exception,
        correlation_id: Optional[str] = None
    ) -> FallbackResult:
        """
        Handle webhook payload processing fallbacks.
        
        Args:
            payload: Original webhook payload
            original_error: The original error that triggered fallback
            correlation_id: Request correlation ID
            
        Returns:
            Fallback result with processed data or error handling strategy
        """
        correlation_id = correlation_id or correlation_id_ctx.get(None) or "unknown"
        
        logger.info(
            "Webhook payload fallback triggered",
            correlation_id=correlation_id,
            error_type=type(original_error).__name__,
            error_message=str(original_error),
            payload_keys=list(payload.keys()) if payload else []
        )
        
        # Determine fallback reason based on error type
        fallback_reason = self._determine_fallback_reason(original_error)
        
        try:
            if isinstance(original_error, TypeFormRateLimitError):
                return await self._handle_rate_limit_fallback(payload, correlation_id)
            
            elif isinstance(original_error, WebhookPayloadError):
                return await self._handle_payload_validation_fallback(payload, correlation_id)
            
            elif isinstance(original_error, asyncio.TimeoutError):
                return await self._handle_timeout_fallback(payload, correlation_id)
            
            else:
                return await self._handle_generic_fallback(payload, fallback_reason, correlation_id)
                
        except Exception as e:
            logger.error(
                "Fallback handling failed",
                correlation_id=correlation_id,
                original_error=str(original_error),
                fallback_error=str(e)
            )
            
            return FallbackResult(
                success=False,
                action_taken=FallbackAction.ABORT_PROCESSING,
                fallback_reason=fallback_reason,
                requires_review=True,
                warnings=[f"Fallback handling failed: {str(e)}"]
            )
    
    async def handle_partial_response_processing(
        self,
        response_data: Dict[str, Any],
        required_fields: List[str],
        correlation_id: Optional[str] = None
    ) -> PartialProcessingResult:
        """
        Handle partial response data processing.
        
        Args:
            response_data: TypeForm response data (potentially incomplete)
            required_fields: List of required field names
            correlation_id: Request correlation ID
            
        Returns:
            Partial processing result with success metrics
        """
        correlation_id = correlation_id or correlation_id_ctx.get(None) or "unknown"
        
        processed_data = {}
        missing_fields = []
        failed_fields = []
        fallback_fields = []
        warnings = []
        
        logger.info(
            "Starting partial response processing",
            correlation_id=correlation_id,
            total_fields=len(required_fields),
            available_fields=len(response_data.keys()) if response_data else 0
        )
        
        # Process each required field
        for field_name in required_fields:
            try:
                if field_name in response_data:
                    # Field is present, validate and process
                    field_value = response_data[field_name]
                    if self._is_valid_field_value(field_value):
                        processed_data[field_name] = field_value
                    else:
                        # Field present but invalid, try fallback
                        fallback_result = await self._apply_field_fallback(
                            field_name, field_value, correlation_id
                        )
                        if fallback_result.success:
                            processed_data[field_name] = fallback_result.fallback_data
                            fallback_fields.append(field_name)
                            if fallback_result.warnings:
                                warnings.extend(fallback_result.warnings)
                        else:
                            failed_fields.append(field_name)
                else:
                    # Field is missing, apply fallback strategy
                    missing_fields.append(field_name)
                    fallback_result = await self._apply_missing_field_fallback(
                        field_name, correlation_id
                    )
                    if fallback_result.success and fallback_result.fallback_data:
                        processed_data[field_name] = fallback_result.fallback_data
                        fallback_fields.append(field_name)
                    if fallback_result.warnings:
                        warnings.extend(fallback_result.warnings)
                        
            except Exception as e:
                logger.warning(
                    "Field processing failed",
                    correlation_id=correlation_id,
                    field_name=field_name,
                    error=str(e)
                )
                failed_fields.append(field_name)
                warnings.append(f"Field {field_name} processing failed: {str(e)}")
        
        # Calculate success metrics
        total_fields = len(required_fields)
        successful_fields = len(processed_data)
        success_rate = successful_fields / total_fields if total_fields > 0 else 0.0
        
        # Determine if manual review is required
        requires_review = (
            success_rate < self.min_success_threshold or
            len(failed_fields) > 0 or
            any(self._field_requires_review(field) for field in fallback_fields)
        )
        
        logger.info(
            "Partial response processing completed",
            correlation_id=correlation_id,
            success_rate=success_rate,
            processed_fields=successful_fields,
            missing_fields=len(missing_fields),
            failed_fields=len(failed_fields),
            fallback_fields=len(fallback_fields),
            requires_review=requires_review
        )
        
        return PartialProcessingResult(
            processed_data=processed_data,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            fallback_fields=fallback_fields,
            success_rate=success_rate,
            requires_manual_review=requires_review,
            processing_warnings=warnings
        )
    
    async def handle_client_identifier_fallback(
        self,
        extracted_identifiers: Dict[str, Any],
        confidence_scores: Dict[str, float],
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle client identifier extraction fallbacks.
        
        Args:
            extracted_identifiers: Originally extracted identifiers
            confidence_scores: Confidence scores for each identifier
            correlation_id: Request correlation ID
            
        Returns:
            Enhanced identifiers with fallback values
        """
        correlation_id = correlation_id or correlation_id_ctx.get(None) or "unknown"
        
        enhanced_identifiers = extracted_identifiers.copy()
        
        logger.info(
            "Client identifier fallback processing",
            correlation_id=correlation_id,
            original_identifiers=list(extracted_identifiers.keys()),
            confidence_scores=confidence_scores
        )
        
        # Process each identifier type with fallback strategies
        if self.field_mapping_config and self.field_mapping_config.fallback_strategies:
            for strategy in self.field_mapping_config.fallback_strategies:
                identifier_type = strategy.identifier_type
                type_key = identifier_type.value
                
                current_value = enhanced_identifiers.get(type_key)
                confidence = confidence_scores.get(type_key, 0.0)
                
                # Apply fallback if confidence is below threshold or value is missing
                if confidence < strategy.confidence_threshold or not current_value:
                    fallback_value = await self._generate_identifier_fallback(
                        strategy, current_value, correlation_id
                    )
                    
                    if fallback_value:
                        enhanced_identifiers[type_key] = fallback_value
                        enhanced_identifiers[f"{type_key}_fallback"] = True
                        enhanced_identifiers[f"{type_key}_original_confidence"] = confidence
                        
                        logger.info(
                            "Applied identifier fallback",
                            correlation_id=correlation_id,
                            identifier_type=type_key,
                            original_confidence=confidence,
                            fallback_applied=True
                        )
        
        return enhanced_identifiers
    
    async def handle_service_unavailability(
        self,
        service_name: str,
        operation: str,
        fallback_data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> FallbackResult:
        """
        Handle service unavailability scenarios.
        
        Args:
            service_name: Name of the unavailable service
            operation: Operation that failed
            fallback_data: Optional fallback data to use
            correlation_id: Request correlation ID
            
        Returns:
            Fallback result with service degradation strategy
        """
        correlation_id = correlation_id or correlation_id_ctx.get(None) or "unknown"
        
        logger.warning(
            "Service unavailability detected",
            correlation_id=correlation_id,
            service_name=service_name,
            operation=operation,
            has_fallback_data=bool(fallback_data)
        )
        
        # Determine degradation strategy based on service and operation
        if service_name == "typeform_api":
            return await self._handle_typeform_service_fallback(operation, fallback_data, correlation_id)
        elif service_name == "database":
            return await self._handle_database_service_fallback(operation, fallback_data, correlation_id)
        else:
            return await self._handle_generic_service_fallback(service_name, operation, fallback_data, correlation_id)
    
    # Private helper methods
    
    def _determine_fallback_reason(self, error: Exception) -> FallbackReason:
        """Determine fallback reason based on error type."""
        if isinstance(error, TypeFormRateLimitError):
            return FallbackReason.RATE_LIMIT_EXCEEDED
        elif isinstance(error, asyncio.TimeoutError):
            return FallbackReason.TIMEOUT_ERROR
        elif isinstance(error, WebhookPayloadError):
            return FallbackReason.INVALID_DATA_FORMAT
        elif "authentication" in str(error).lower():
            return FallbackReason.AUTHENTICATION_FAILURE
        else:
            return FallbackReason.SERVICE_UNAVAILABLE
    
    async def _handle_rate_limit_fallback(
        self, 
        payload: Dict[str, Any], 
        correlation_id: str
    ) -> FallbackResult:
        """Handle TypeForm rate limit fallbacks."""
        logger.info(
            "Applying rate limit fallback",
            correlation_id=correlation_id,
            strategy="queue_for_retry"
        )
        
        return FallbackResult(
            success=True,
            action_taken=FallbackAction.QUEUE_FOR_RETRY,
            fallback_reason=FallbackReason.RATE_LIMIT_EXCEEDED,
            metadata={
                "retry_after": 60,  # seconds
                "priority": "high",
                "original_payload": payload
            }
        )
    
    async def _handle_payload_validation_fallback(
        self, 
        payload: Dict[str, Any], 
        correlation_id: str
    ) -> FallbackResult:
        """Handle webhook payload validation fallbacks."""
        # Extract whatever valid data we can from the payload
        if not self.enable_partial_processing:
            return FallbackResult(
                success=False,
                action_taken=FallbackAction.ABORT_PROCESSING,
                fallback_reason=FallbackReason.INVALID_DATA_FORMAT,
                requires_review=True
            )
        
        # Try to salvage partial data
        salvaged_data = await self._salvage_payload_data(payload)
        
        if salvaged_data:
            return FallbackResult(
                success=True,
                action_taken=FallbackAction.CONTINUE_WITH_PARTIAL,
                fallback_reason=FallbackReason.PARTIAL_DATA,
                fallback_data=salvaged_data,
                requires_review=True,
                warnings=["Payload validation failed, using partial data"]
            )
        else:
            return FallbackResult(
                success=False,
                action_taken=FallbackAction.REQUIRE_MANUAL_REVIEW,
                fallback_reason=FallbackReason.INVALID_DATA_FORMAT,
                requires_review=True
            )
    
    async def _handle_timeout_fallback(
        self, 
        payload: Dict[str, Any], 
        correlation_id: str
    ) -> FallbackResult:
        """Handle timeout fallbacks."""
        return FallbackResult(
            success=True,
            action_taken=FallbackAction.QUEUE_FOR_RETRY,
            fallback_reason=FallbackReason.TIMEOUT_ERROR,
            fallback_data=payload,
            metadata={"retry_delay": 30}
        )
    
    async def _handle_generic_fallback(
        self, 
        payload: Dict[str, Any], 
        reason: FallbackReason, 
        correlation_id: str
    ) -> FallbackResult:
        """Handle generic fallback scenarios."""
        return FallbackResult(
            success=True,
            action_taken=FallbackAction.REQUIRE_MANUAL_REVIEW,
            fallback_reason=reason,
            requires_review=True,
            warnings=["Generic fallback applied, manual review required"]
        )
    
    def _is_valid_field_value(self, value: Any) -> bool:
        """Check if a field value is valid."""
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        if isinstance(value, (list, dict)) and not value:
            return False
        return True
    
    async def _apply_field_fallback(
        self, 
        field_name: str, 
        field_value: Any, 
        correlation_id: str
    ) -> FallbackResult:
        """Apply fallback for invalid field value."""
        # For now, simple fallback - could be enhanced with field-specific logic
        return FallbackResult(
            success=False,
            action_taken=FallbackAction.SKIP_FIELD,
            fallback_reason=FallbackReason.INVALID_DATA_FORMAT,
            warnings=[f"Invalid value for field {field_name}: {field_value}"]
        )
    
    async def _apply_missing_field_fallback(
        self, 
        field_name: str, 
        correlation_id: str
    ) -> FallbackResult:
        """Apply fallback for missing field."""
        # Check if we have a default value for this field
        default_value = self._get_default_value_for_field(field_name)
        
        if default_value is not None:
            return FallbackResult(
                success=True,
                action_taken=FallbackAction.USE_DEFAULT_VALUE,
                fallback_reason=FallbackReason.MISSING_REQUIRED_FIELD,
                fallback_data=default_value,
                warnings=[f"Used default value for missing field {field_name}"]
            )
        else:
            return FallbackResult(
                success=False,
                action_taken=FallbackAction.SKIP_FIELD,
                fallback_reason=FallbackReason.MISSING_REQUIRED_FIELD,
                warnings=[f"No fallback available for missing field {field_name}"]
            )
    
    def _get_default_value_for_field(self, field_name: str) -> Any:
        """Get default value for a field if available."""
        # Field-specific default values
        defaults = {
            "submission_id": lambda: f"missing_{datetime.now(timezone.utc).timestamp()}",
            "submitted_at": lambda: datetime.now(timezone.utc).isoformat(),
            "status": "incomplete"
        }
        
        default = defaults.get(field_name)
        if callable(default):
            return default()
        return default
    
    def _field_requires_review(self, field_name: str) -> bool:
        """Check if a field requires manual review when fallback is applied."""
        critical_fields = ["email", "client_name", "phone", "form_id"]
        return field_name in critical_fields
    
    async def _generate_identifier_fallback(
        self, 
        strategy: FallbackStrategy, 
        original_value: Any, 
        correlation_id: str
    ) -> Optional[str]:
        """Generate fallback value for client identifier."""
        if not strategy.use_placeholder:
            return None
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        if strategy.placeholder_pattern:
            return strategy.placeholder_pattern.replace("{timestamp}", timestamp)
        
        # Default placeholders by type
        defaults = {
            ClientIdentifierType.EMAIL: f"unknown_{timestamp}@placeholder.local",
            ClientIdentifierType.NAME: f"Guest_{timestamp}",
            ClientIdentifierType.PHONE: None  # No default for phone
        }
        
        return defaults.get(strategy.identifier_type)
    
    async def _handle_typeform_service_fallback(
        self, 
        operation: str, 
        fallback_data: Optional[Dict[str, Any]], 
        correlation_id: str
    ) -> FallbackResult:
        """Handle TypeForm API service fallbacks."""
        if operation in ["form_validation", "webhook_setup"]:
            # Critical operations - require retry
            return FallbackResult(
                success=True,
                action_taken=FallbackAction.QUEUE_FOR_RETRY,
                fallback_reason=FallbackReason.SERVICE_UNAVAILABLE,
                metadata={"retry_delay": 60, "max_retries": 3}
            )
        else:
            # Non-critical operations - continue with degraded functionality
            return FallbackResult(
                success=True,
                action_taken=FallbackAction.CONTINUE_WITH_PARTIAL,
                fallback_reason=FallbackReason.SERVICE_UNAVAILABLE,
                fallback_data=fallback_data or {},
                requires_review=True
            )
    
    async def _handle_database_service_fallback(
        self, 
        operation: str, 
        fallback_data: Optional[Dict[str, Any]], 
        correlation_id: str
    ) -> FallbackResult:
        """Handle database service fallbacks."""
        # Database unavailability is critical - always retry
        return FallbackResult(
            success=True,
            action_taken=FallbackAction.QUEUE_FOR_RETRY,
            fallback_reason=FallbackReason.SERVICE_UNAVAILABLE,
            metadata={"retry_delay": 30, "max_retries": 5, "exponential_backoff": True}
        )
    
    async def _handle_generic_service_fallback(
        self, 
        service_name: str, 
        operation: str, 
        fallback_data: Optional[Dict[str, Any]], 
        correlation_id: str
    ) -> FallbackResult:
        """Handle generic service fallbacks."""
        return FallbackResult(
            success=True,
            action_taken=FallbackAction.REQUIRE_MANUAL_REVIEW,
            fallback_reason=FallbackReason.SERVICE_UNAVAILABLE,
            requires_review=True,
            warnings=[f"Service {service_name} unavailable for operation {operation}"]
        )
    
    async def _salvage_payload_data(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Attempt to salvage valid data from invalid payload."""
        if not payload:
            return None
        
        salvaged = {}
        
        # Try to extract basic required fields
        safe_fields = ["event_id", "event_type", "form_response"]
        for field_name in safe_fields:
            if field_name in payload and payload[field_name] is not None:
                try:
                    # Basic validation - ensure it's serializable
                    import json
                    json.dumps(payload[field_name])
                    salvaged[field_name] = payload[field_name]
                except (TypeError, ValueError):
                    continue
        
        return salvaged if salvaged else None


# Factory functions for different use cases

def create_webhook_fallback_handler(
    enable_partial_processing: bool = True,
    min_success_threshold: float = 0.7
) -> ClientOnboardingFallbackHandlers:
    """
    Create fallback handler optimized for webhook processing.
    
    Args:
        enable_partial_processing: Whether to enable partial data processing
        min_success_threshold: Minimum success rate for processing
        
    Returns:
        Configured fallback handler for webhooks
    """
    return ClientOnboardingFallbackHandlers(
        default_timeout=45.0,  # Longer timeout for webhooks
        enable_partial_processing=enable_partial_processing,
        min_success_threshold=min_success_threshold
    )


def create_api_fallback_handler(
    min_success_threshold: float = 0.8
) -> ClientOnboardingFallbackHandlers:
    """
    Create fallback handler optimized for API endpoints.
    
    Args:
        min_success_threshold: Minimum success rate for API operations
        
    Returns:
        Configured fallback handler for API endpoints
    """
    return ClientOnboardingFallbackHandlers(
        default_timeout=30.0,
        enable_partial_processing=False,  # APIs typically need complete data
        min_success_threshold=min_success_threshold
    )


def create_development_fallback_handler() -> ClientOnboardingFallbackHandlers:
    """
    Create fallback handler optimized for development environment.
    
    Returns:
        Configured fallback handler for development
    """
    return ClientOnboardingFallbackHandlers(
        default_timeout=60.0,  # More lenient for dev
        enable_partial_processing=True,
        min_success_threshold=0.5  # More forgiving for testing
    ) 