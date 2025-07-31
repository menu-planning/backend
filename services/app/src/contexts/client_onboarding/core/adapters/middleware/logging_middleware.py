"""
Logging middleware for client onboarding context with TypeForm-specific logging.

This middleware extends shared_kernel logging patterns with client_onboarding specific context:
- TypeForm webhook processing logs
- Form ownership context tracking
- Client identifier extraction logging
- Response processing pipeline monitoring
- Security event logging for form access
"""

import json
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from src.logging.logger import StructlogFactory
from src.contexts.shared_kernel.middleware.logging_middleware import LoggingMiddleware as BaseLoggingMiddleware


class ClientOnboardingLoggingMiddleware(BaseLoggingMiddleware):
    """
    Client onboarding specific logging middleware.
    
    Extends shared_kernel logging with:
    - TypeForm webhook processing context
    - Form ownership and permission tracking
    - Client identifier extraction monitoring
    - Response processing pipeline logging
    - Security event audit trail
    """
    
    def __init__(
        self,
        logger_name: str = "client_onboarding",
        log_request_body: bool = True,
        log_response_body: bool = True,
        max_body_size: int = 2000,  # Larger for TypeForm responses
        performance_warning_threshold: float = 8.0,  # Higher for webhook processing
        log_typeform_signatures: bool = False,  # Security: don't log signatures by default
        log_client_identifiers: bool = True,
        enable_audit_logging: bool = True
    ):
        """
        Initialize client onboarding logging middleware.
        
        Args:
            logger_name: Name for the logger instance
            log_request_body: Whether to log request body content
            log_response_body: Whether to log response body content
            max_body_size: Maximum body size to log (larger for TypeForm responses)
            performance_warning_threshold: Warn if execution time exceeds threshold
            log_typeform_signatures: Whether to log TypeForm signatures (security sensitive)
            log_client_identifiers: Whether to log extracted client identifiers
            enable_audit_logging: Whether to enable security audit logging
        """
        super().__init__(
            logger_name=logger_name,
            log_request_body=log_request_body,
            log_response_body=log_response_body,
            max_body_size=max_body_size,
            performance_warning_threshold=performance_warning_threshold
        )
        
        self.log_typeform_signatures = log_typeform_signatures
        self.log_client_identifiers = log_client_identifiers
        self.enable_audit_logging = enable_audit_logging
        
        # Client onboarding specific logger
        self.audit_logger = StructlogFactory.get_logger(f"{logger_name}_audit")
    
    def extract_typeform_context(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract TypeForm-specific context from event.
        
        Args:
            event: Lambda event dictionary
            
        Returns:
            TypeForm context information
        """
        typeform_context = {}
        
        # Extract from headers
        headers = event.get("headers", {})
        typeform_context.update({
            "typeform_signature": bool(headers.get("typeform-signature")) if not self.log_typeform_signatures else headers.get("typeform-signature"),
            "typeform_user_agent": headers.get("user-agent", "").startswith("Typeform"),
            "content_type": headers.get("content-type"),
            "content_length": headers.get("content-length")
        })
        
        # Extract from body if it's a webhook
        body = event.get("body")
        if body:
            try:
                payload = json.loads(body) if isinstance(body, str) else body
                typeform_context.update({
                    "event_id": payload.get("event_id"),
                    "event_type": payload.get("event_type"),
                    "form_response": {
                        "form_id": payload.get("form_response", {}).get("form_id"),
                        "response_id": payload.get("form_response", {}).get("token"),
                        "submitted_at": payload.get("form_response", {}).get("submitted_at"),
                        "landed_at": payload.get("form_response", {}).get("landed_at")
                    } if payload.get("form_response") else None
                })
            except (json.JSONDecodeError, TypeError, AttributeError):
                typeform_context["payload_parse_error"] = True
        
        # Extract from path parameters
        path_params = event.get("pathParameters", {}) or {}
        typeform_context.update({
            "form_id_param": path_params.get("form_id"),
            "response_id_param": path_params.get("response_id")
        })
        
        return typeform_context
    
    def extract_form_ownership_context(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract form ownership and permission context.
        
        Args:
            event: Lambda event dictionary
            
        Returns:
            Form ownership context
        """
        ownership_context = {}
        
        # User context from request context or headers
        request_context = event.get("requestContext", {})
        authorizer = request_context.get("authorizer", {})
        
        ownership_context.update({
            "user_id": authorizer.get("user_id") or authorizer.get("sub"),
            "account_id": authorizer.get("account_id"),
            "permissions": authorizer.get("permissions", []),
            "is_authenticated": bool(authorizer.get("user_id"))
        })
        
        # Extract form access patterns
        path = event.get("path", "")
        method = event.get("httpMethod", "")
        
        ownership_context.update({
            "access_pattern": self._determine_access_pattern(path, method),
            "requires_form_ownership": self._requires_form_ownership(path, method),
            "is_webhook_endpoint": "/webhook" in path
        })
        
        return ownership_context
    
    def _determine_access_pattern(self, path: str, method: str) -> str:
        """Determine the type of access pattern being attempted."""
        if "/webhook" in path:
            return "webhook_processing"
        elif "/forms/" in path and method == "GET":
            return "form_query"
        elif "/forms/" in path and method in ["POST", "PUT"]:
            return "form_management"
        elif "/responses/" in path:
            return "response_query"
        else:
            return "unknown"
    
    def _requires_form_ownership(self, path: str, method: str) -> bool:
        """Determine if the endpoint requires form ownership validation."""
        return (
            "/forms/" in path or 
            "/responses/" in path
        ) and "/webhook" not in path
    
    def log_client_identifier_extraction(
        self, 
        correlation_id: str,
        form_id: str,
        response_id: str,
        extracted_identifiers: Dict[str, Any],
        confidence_scores: Optional[Dict[str, float]] = None,
        extraction_method: str = "auto_detection"
    ) -> None:
        """
        Log client identifier extraction results.
        
        Args:
            correlation_id: Request correlation ID
            form_id: TypeForm form ID
            response_id: TypeForm response ID
            extracted_identifiers: Extracted client identifiers
            confidence_scores: Confidence scores for extraction
            extraction_method: Method used for extraction
        """
        if not self.log_client_identifiers:
            return
        
        # Sanitize identifiers for logging (hash emails/phones for privacy)
        sanitized_identifiers = {}
        for key, value in extracted_identifiers.items():
            if key in ["email", "phone"] and value:
                # Log only presence and partial info for privacy
                sanitized_identifiers[key] = {
                    "present": True,
                    "domain": value.split("@")[1] if "@" in value and key == "email" else None,
                    "length": len(str(value))
                }
            else:
                sanitized_identifiers[key] = value
        
        self.structured_logger.info(
            "Client identifier extraction completed",
            correlation_id=correlation_id,
            form_id=form_id,
            response_id=response_id,
            extraction_method=extraction_method,
            identifiers_extracted=sanitized_identifiers,
            confidence_scores=confidence_scores or {},
            extraction_success=bool(any(extracted_identifiers.values()))
        )
    
    def log_response_processing_pipeline(
        self,
        correlation_id: str,
        pipeline_stage: str,
        form_id: str,
        response_id: str,
        stage_result: str,
        processing_time: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log response processing pipeline stages.
        
        Args:
            correlation_id: Request correlation ID
            pipeline_stage: Current processing stage
            form_id: TypeForm form ID
            response_id: TypeForm response ID
            stage_result: Result of the stage (success/error/skipped)
            processing_time: Time taken for this stage
            metadata: Additional stage-specific metadata
        """
        self.structured_logger.info(
            "Response processing pipeline stage",
            correlation_id=correlation_id,
            pipeline_stage=pipeline_stage,
            form_id=form_id,
            response_id=response_id,
            stage_result=stage_result,
            processing_time=processing_time,
            metadata=metadata or {}
        )
    
    def log_security_event(
        self,
        correlation_id: str,
        event_type: str,
        user_id: Optional[str],
        form_id: Optional[str],
        security_result: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Enhanced security event logging with threat level classification and structured metadata.
        
        Args:
            correlation_id: Request correlation ID
            event_type: Type of security event (webhook_signature_verification_*, etc.)
            user_id: User involved in the event
            form_id: Form involved in the event  
            security_result: Result of security check (SUCCESS/FAILED/ERROR)
            details: Additional security event details
        """
        if not self.enable_audit_logging:
            return
        
        # Enhanced security event structure
        enhanced_details = details or {}
        
        # Determine threat level based on event type and result
        threat_level = self._determine_threat_level(event_type, security_result)
        
        # Add webhook-specific structured metadata
        webhook_metadata = self._extract_webhook_metadata(event_type, enhanced_details)
        
        # Track failure patterns for alerting
        failure_context = self._analyze_failure_patterns(
            event_type, security_result, enhanced_details
        )
        
        # Enhanced structured security log
        self.audit_logger.info(
            "Security audit event",
            correlation_id=correlation_id,
            event_type=event_type,
            event_category=self._categorize_security_event(event_type),
            user_id=user_id,
            form_id=form_id,
            security_result=security_result,
            threat_level=threat_level,
            timestamp=datetime.now(timezone.utc).isoformat(),
            webhook_metadata=webhook_metadata,
            failure_analysis=failure_context,
            raw_details=enhanced_details
        )
        
        # Alert on high-threat events or failure patterns
        if threat_level in ["HIGH", "CRITICAL"] or failure_context.get("alert_threshold_reached"):
            self._log_security_alert(
                correlation_id, event_type, threat_level, failure_context
            )
    
    def _determine_threat_level(self, event_type: str, security_result: str) -> str:
        """Determine threat level for security event classification."""
        if security_result == "SUCCESS":
            return "LOW"
        
        # High-risk event types
        high_risk_events = [
            "webhook_signature_verification_failed",
            "webhook_replay_attack_detected", 
            "webhook_malformed_signature",
            "webhook_missing_signature"
        ]
        
        # Critical event types
        critical_events = [
            "webhook_signature_bypass_attempt",
            "webhook_multiple_failures_same_source"
        ]
        
        if event_type in critical_events:
            return "CRITICAL"
        elif event_type in high_risk_events:
            return "HIGH"
        elif security_result == "FAILED":
            return "MEDIUM"
        else:
            return "LOW"
    
    def _categorize_security_event(self, event_type: str) -> str:
        """Categorize security events for better organization."""
        if "webhook_signature" in event_type:
            return "webhook_authentication"
        elif "webhook_replay" in event_type:
            return "replay_protection"
        elif "webhook_rate_limit" in event_type:
            return "rate_limiting"
        elif "webhook" in event_type:
            return "webhook_security"
        else:
            return "general_security"
    
    def _extract_webhook_metadata(self, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure webhook-specific metadata."""
        if not event_type.startswith("webhook_"):
            return {}
        
        webhook_meta = {}
        
        # Extract signature-related metadata
        if "signature" in event_type:
            webhook_meta.update({
                "signature_present": details.get("signature_headers", {}) != {},
                "signature_format_valid": not details.get("error", "").startswith("Invalid signature format"),
                "payload_hash_prefix": details.get("payload_hash", "")[:8],
                "verification_timestamp": details.get("verification_timestamp"),
                "timestamp_tolerance_used": details.get("timestamp_tolerance_minutes", 5)
            })
        
        # Extract network-related metadata
        if "source_ip" in details:
            webhook_meta["client_info"] = {
                "source_ip": details["source_ip"],
                "ip_hash": hash(details["source_ip"]) % 10000  # Anonymized tracking
            }
        
        # Extract payload metadata
        if "payload_hash" in details:
            webhook_meta["payload_info"] = {
                "hash_prefix": details["payload_hash"][:8],
                "size_category": self._categorize_payload_size(details.get("payload_size", 0))
            }
        
        return webhook_meta
    
    def _analyze_failure_patterns(self, event_type: str, security_result: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze failure patterns for alerting and threat detection."""
        if security_result == "SUCCESS":
            return {"pattern_risk": "none"}
        
        failure_analysis = {
            "failure_type": event_type,
            "error_category": self._categorize_error(details.get("error", "")),
            "repeated_failure_risk": False,
            "alert_threshold_reached": False
        }
        
        # Analyze source IP failure patterns (simplified tracking)
        source_ip = details.get("source_ip")
        if source_ip and source_ip != "unknown":
            # In production, this would use a proper cache/database for tracking
            # For now, we'll add metadata to support external failure tracking
            failure_analysis.update({
                "source_tracking": {
                    "ip_hash": hash(source_ip) % 10000,
                    "requires_external_tracking": True,
                    "tracking_key": f"failures_{hash(source_ip) % 10000}_{event_type}"
                }
            })
        
        # Detect potentially malicious patterns
        error_msg = details.get("error", "").lower()
        if any(keyword in error_msg for keyword in ["malformed", "invalid format", "missing"]):
            failure_analysis["pattern_risk"] = "potential_attack"
        elif "timeout" in error_msg or "network" in error_msg:
            failure_analysis["pattern_risk"] = "infrastructure"
        else:
            failure_analysis["pattern_risk"] = "authentication"
        
        return failure_analysis
    
    def _categorize_error(self, error_message: str) -> str:
        """Categorize error messages for pattern analysis."""
        error_lower = error_message.lower()
        
        if "signature" in error_lower and "mismatch" in error_lower:
            return "signature_mismatch"
        elif "malformed" in error_lower or "invalid format" in error_lower:
            return "malformed_request"
        elif "missing" in error_lower:
            return "missing_required_data"
        elif "timeout" in error_lower or "expired" in error_lower:
            return "timing_issue"
        else:
            return "unknown_error"
    
    def _categorize_payload_size(self, size: int) -> str:
        """Categorize payload size for anomaly detection."""
        if size == 0:
            return "empty"
        elif size < 1024:  # < 1KB
            return "small"
        elif size < 10240:  # < 10KB
            return "normal" 
        elif size < 102400:  # < 100KB
            return "large"
        else:
            return "very_large"
    
    def _log_security_alert(self, correlation_id: str, event_type: str, threat_level: str, failure_context: Dict[str, Any]) -> None:
        """Log high-priority security alerts for immediate attention."""
        self.audit_logger.warning(
            "SECURITY ALERT: High-priority security event detected",
            correlation_id=correlation_id,
            alert_type="webhook_security_alert",
            event_type=event_type,
            threat_level=threat_level,
            alert_timestamp=datetime.now(timezone.utc).isoformat(),
            failure_context=failure_context,
            requires_investigation=True
        )
    
    @asynccontextmanager
    async def log_request_response(
        self, 
        event: Dict[str, Any], 
        context: Any,
        correlation_id: Optional[str] = None
    ):
        """
        Enhanced context manager with client onboarding specific logging.
        
        Args:
            event: Lambda event dictionary
            context: Lambda context object
            correlation_id: Optional correlation ID
            
        Yields:
            Dictionary with operation context including client onboarding data
        """
        # Use parent context manager for basic functionality
        async with super().log_request_response(event, context, correlation_id) as operation_context:
            
            # Add client onboarding specific context
            typeform_context = self.extract_typeform_context(event)
            ownership_context = self.extract_form_ownership_context(event)
            
            # Enhanced operation context
            enhanced_context = {
                **operation_context,
                "typeform_context": typeform_context,
                "ownership_context": ownership_context,
                "client_onboarding_metadata": {
                    "is_webhook_request": typeform_context.get("typeform_user_agent", False),
                    "has_form_signature": bool(typeform_context.get("typeform_signature")),
                    "requires_ownership_check": ownership_context.get("requires_form_ownership", False),
                    "access_pattern": ownership_context.get("access_pattern", "unknown")
                }
            }
            
            # Log enhanced request start
            self.structured_logger.info(
                "Client onboarding request started",
                correlation_id=enhanced_context["correlation_id"],
                typeform_context=typeform_context,
                ownership_context=ownership_context,
                request_metadata=enhanced_context["request_metadata"]
            )
            
            yield enhanced_context


# Factory functions for different environments and use cases

def create_webhook_logging_middleware(
    performance_threshold: float = 10.0,
    enable_audit: bool = True
) -> ClientOnboardingLoggingMiddleware:
    """
    Create logging middleware optimized for webhook processing.
    
    Args:
        performance_threshold: Performance warning threshold for webhooks
        enable_audit: Whether to enable audit logging
        
    Returns:
        Configured logging middleware for webhooks
    """
    return ClientOnboardingLoggingMiddleware(
        logger_name="client_onboarding_webhook",
        log_request_body=True,
        log_response_body=False,  # Webhooks typically don't need response body logging
        max_body_size=5000,  # Larger for TypeForm webhook payloads
        performance_warning_threshold=performance_threshold,
        log_typeform_signatures=False,  # Security: never log signatures
        log_client_identifiers=True,
        enable_audit_logging=enable_audit
    )


def create_api_logging_middleware(
    include_response_body: bool = True,
    enable_audit: bool = True
) -> ClientOnboardingLoggingMiddleware:
    """
    Create logging middleware optimized for API endpoints.
    
    Args:
        include_response_body: Whether to log API response bodies
        enable_audit: Whether to enable audit logging
        
    Returns:
        Configured logging middleware for API endpoints
    """
    return ClientOnboardingLoggingMiddleware(
        logger_name="client_onboarding_api",
        log_request_body=True,
        log_response_body=include_response_body,
        max_body_size=2000,
        performance_warning_threshold=5.0,
        log_typeform_signatures=False,
        log_client_identifiers=False,  # API endpoints might not process identifiers
        enable_audit_logging=enable_audit
    )


def create_development_logging_middleware() -> ClientOnboardingLoggingMiddleware:
    """
    Create logging middleware optimized for development environment.
    
    Returns:
        Configured logging middleware for development
    """
    return ClientOnboardingLoggingMiddleware(
        logger_name="client_onboarding_dev",
        log_request_body=True,
        log_response_body=True,
        max_body_size=10000,  # Larger for debugging
        performance_warning_threshold=15.0,  # More lenient for dev
        log_typeform_signatures=False,  # Still secure in dev
        log_client_identifiers=True,
        enable_audit_logging=True
    ) 