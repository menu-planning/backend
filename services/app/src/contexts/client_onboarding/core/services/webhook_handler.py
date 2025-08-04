"""
Generic webhook handler for TypeForm webhook processing.

This module provides a deployment-agnostic webhook handler that can be used
in various contexts (FastAPI, AWS Lambda, etc.) to process incoming TypeForm webhooks.
"""

import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import UTC, datetime, timedelta
from collections import defaultdict

from src.contexts.client_onboarding.core.services.exceptions import (
    WebhookSecurityError,
    WebhookPayloadError,
    OnboardingFormNotFoundError,
    DatabaseOperationError,
    FormResponseProcessingError,
    WebhookSignatureError
)
from src.contexts.client_onboarding.core.services.webhook_security import WebhookSecurityVerifier
from src.contexts.client_onboarding.core.services.webhook_retry import WebhookRetryManager
from src.contexts.client_onboarding.core.adapters.middleware.logging_middleware import ClientOnboardingLoggingMiddleware


logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Generic webhook handler for processing TypeForm webhook events.
    
    This handler is deployment-agnostic and can be integrated into various
    web frameworks or serverless functions.
    """
    
    def __init__(
        self, 
        uow_factory, 
        logging_middleware: Optional[ClientOnboardingLoggingMiddleware] = None,
        retry_manager: Optional[WebhookRetryManager] = None
    ):
        """
        Initialize webhook handler with unit of work factory and optional retry integration.
        
        Args:
            uow_factory: Factory function that returns UnitOfWork instances
            logging_middleware: Optional logging middleware for structured security logging
            retry_manager: Optional retry manager for webhook delivery failures
        """
        self.uow_factory = uow_factory
        self.logging_middleware = logging_middleware
        self.retry_manager = retry_manager
        
        # Security alert configuration for failed verifications
        self.security_alert_config = {
            "failure_threshold": 5,  # Alert after 5 failures from same source
            "time_window_minutes": 15,  # Within 15 minute window
            "critical_failure_threshold": 10,  # Critical alert threshold
            "alert_cooldown_minutes": 30  # Minimum time between alerts for same source
        }
        
        # In-memory failure tracking (production should use Redis/cache)
        self._failure_tracker = defaultdict(list)
        self._alert_tracker = {}  # Track last alert time per source
    
    async def handle_webhook(
        self,
        payload: str,
        headers: Dict[str, str],
        webhook_secret: Optional[str] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Handle incoming TypeForm webhook request.
        
        Args:
            payload: Raw webhook payload as string
            headers: HTTP headers from the webhook request
            webhook_secret: Optional webhook secret for signature verification
            
        Returns:
            Tuple of (status_code, response_data)
        """
        try:
            # Log webhook reception
            logger.info(f"Received TypeForm webhook at {datetime.now(UTC)}")
            
            # Parse payload
            webhook_data = await self._parse_payload(payload)
            
            # Verify webhook if secret provided
            if webhook_secret:
                await self._verify_signature(payload, headers, webhook_secret, webhook_data)
            
            # Process the webhook event
            result = await self._process_webhook_event(webhook_data)
            
            logger.info(f"Webhook processed successfully: {result.get('form_response_id')}")
            
            return 200, {
                "status": "success",
                "message": "Webhook processed successfully",
                "data": result
            }
            
        except WebhookSecurityError as e:
            logger.warning(f"Webhook security validation failed: {e.message}")
            return 401, {
                "status": "error",
                "error": "security_validation_failed",
                "message": e.message
            }
            
        except WebhookPayloadError as e:
            logger.error(f"Webhook payload processing failed: {e.message}")
            return 400, {
                "status": "error",
                "error": "invalid_payload",
                "message": e.message
            }
            
        except OnboardingFormNotFoundError as e:
            logger.error(f"Onboarding form not found: {e.message}")
            return 404, {
                "status": "error",
                "error": "form_not_found",
                "message": e.message
            }
            
        except DatabaseOperationError as e:
            logger.error(f"Database operation failed: {e.message}")
            # Schedule for retry if retry manager available
            await self._schedule_webhook_retry_on_failure(
                headers=headers,
                failure_reason=f"Database operation failed: {e.message}",
                status_code=500
            )
            return 500, {
                "status": "error",
                "error": "database_error",
                "message": "Internal server error"
            }
            
        except Exception as e:
            logger.exception(f"Unexpected error processing webhook: {str(e)}")
            # Schedule for retry if retry manager available
            await self._schedule_webhook_retry_on_failure(
                headers=headers,
                failure_reason=f"Unexpected error: {str(e)}",
                status_code=500
            )
            return 500, {
                "status": "error",
                "error": "internal_error",
                "message": "Internal server error"
            }
    
    async def _parse_payload(self, payload: str) -> Dict[str, Any]:
        """
        Parse and validate the webhook payload.
        
        Args:
            payload: Raw payload string
            
        Returns:
            Parsed webhook data
            
        Raises:
            WebhookPayloadError: If payload is invalid
        """
        try:
            data = json.loads(payload)
            
            # Basic TypeForm webhook structure validation
            required_fields = ["event_id", "event_type", "form_response"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise WebhookPayloadError(
                    f"Missing required fields: {', '.join(missing_fields)}",
                    payload_data=data
                )
            
            # Validate event type
            if data["event_type"] != "form_response":
                raise WebhookPayloadError(
                    f"Unsupported event type: {data['event_type']}",
                    payload_data=data
                )
            
            return data
            
        except json.JSONDecodeError as e:
            raise WebhookPayloadError(
                f"Invalid JSON payload: {str(e)}",
                payload_data={"raw_payload": payload}
            )
    
    async def _verify_signature(
        self, 
        payload: str, 
        headers: Dict[str, str], 
        webhook_secret: str,
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Verify webhook signature using HMAC-SHA256.
        
        Args:
            payload: Raw webhook payload
            headers: HTTP headers containing signature
            webhook_secret: Secret for HMAC verification
            webhook_data: Parsed webhook data for enhanced logging context
            
        Raises:
            WebhookSecurityError: If signature verification fails
        """
        # Extract context for security logging
        correlation_id = headers.get('x-request-id', f"webhook_{datetime.now(UTC).timestamp()}")
        form_id = webhook_data.get('form_id') if webhook_data else None
        user_id = None
        if webhook_data and 'form_response' in webhook_data:
            user_id = webhook_data['form_response'].get('hidden', {}).get('user_id')
        
        # Validate signature header presence and format
        await self._validate_signature_header(headers)
        
        # Use the production HMAC-SHA256 verification
        verifier = WebhookSecurityVerifier(webhook_secret)
        
        try:
            verification_result = await verifier.verify_webhook_request(
                payload=payload,
                headers=headers,
                timestamp_tolerance_minutes=5
            )
            
            is_valid, error_message = verification_result
            
            if not is_valid:
                # Handle verification failure with enhanced security logging
                
                # Track failures for alerting
                source_ip = headers.get('x-forwarded-for', 'unknown')
                alert_triggered = self._track_security_failure(source_ip, error_message or "Unknown error")
                
                # Log security failure event for audit trail using structured logging
                if self.logging_middleware:
                    self.logging_middleware.log_security_event(
                        correlation_id=correlation_id,
                        event_type="webhook_signature_verification_failed",
                        user_id=user_id,
                        form_id=form_id,
                        security_result="FAILED",
                        details={
                            "error": error_message,
                            "signature_headers": {k: v for k, v in headers.items() if 'signature' in k.lower()},
                            "payload_hash": verifier._get_payload_hash(payload)[:8],
                            "verification_timestamp": datetime.now(UTC).isoformat(),
                            "source_ip": source_ip,
                            "failure_count": len(self._failure_tracker.get(source_ip, [])),
                            "alert_triggered": alert_triggered
                        }
                    )
                else:
                    # Fallback to basic logging if middleware not available
                    logger.warning(
                        "Webhook signature verification failed",
                        extra={
                            "event_type": "webhook_signature_failure",
                            "error": error_message,
                            "headers": {k: v for k, v in headers.items() if 'signature' in k.lower()},
                            "payload_hash": verifier._get_payload_hash(payload)[:8],
                            "failure_count": len(self._failure_tracker.get(source_ip, []))
                        }
                    )
                raise WebhookSignatureError(
                    reason=error_message or "Signature verification failed",
                    source_ip=source_ip,
                    payload_hash=verifier._get_payload_hash(payload)[:8]
                )
            else:
                # Log successful verification for audit trail
                if self.logging_middleware:
                    self.logging_middleware.log_security_event(
                        correlation_id=correlation_id,
                        event_type="webhook_signature_verification_success",
                        user_id=user_id,
                        form_id=form_id,
                        security_result="SUCCESS",
                        details={
                            "verification_timestamp": datetime.now(UTC).isoformat(),
                            "payload_hash": verifier._get_payload_hash(payload)[:8],
                            "source_ip": headers.get('x-forwarded-for', 'unknown')
                        }
                    )
                
        except WebhookSignatureError:
            # Re-raise signature errors without additional logging (already logged above)
            raise
        except WebhookSecurityError:
            # Re-raise other security errors without additional logging
            raise
        except Exception as e:
            # Log unexpected errors for audit trail
            if self.logging_middleware:
                self.logging_middleware.log_security_event(
                    correlation_id=correlation_id,
                    event_type="webhook_signature_verification_error",
                    user_id=user_id,
                    form_id=form_id,
                    security_result="ERROR",
                    details={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "verification_timestamp": datetime.now(UTC).isoformat()
                    }
                )
            logger.error(f"Unexpected error during signature verification: {e}", exc_info=True)
            raise WebhookSignatureError(
                reason=f"Signature verification error: {str(e)}",
                source_ip=headers.get('x-forwarded-for', 'unknown')
            )

    async def _validate_signature_header(self, headers: Dict[str, str]) -> None:
        """
        Validate the presence and format of TypeForm signature header.
        
        Args:
            headers: HTTP headers from the request
            
        Raises:
            WebhookSecurityError: If header is missing or malformed
        """
        # Check for signature header (case-insensitive)
        signature_header = None
        signature_value = None
        
        # Try standard TypeForm header names
        for header_name in ["Typeform-Signature", "typeform-signature", "X-Typeform-Signature"]:
            if header_name in headers:
                signature_header = header_name
                signature_value = headers[header_name]
                break
        
        if not signature_header or not signature_value:
            raise WebhookSecurityError(
                "Missing required TypeForm signature header. Expected 'Typeform-Signature' header."
            )
        
        # Validate signature format (should be sha256=<base64>)
        if not signature_value.startswith('sha256='):
            raise WebhookSecurityError(
                f"Invalid signature format in header '{signature_header}'. "
                "Expected format: 'sha256=<base64-encoded-signature>'"
            )
        
        # Validate signature length (basic check)
        signature_part = signature_value[7:]  # Remove 'sha256=' prefix
        if len(signature_part) < 40:  # Basic length check for base64-encoded SHA256
            raise WebhookSecurityError(
                f"Invalid signature length in header '{signature_header}'. "
                "Signature appears to be too short."
            )
        
        logger.debug(f"Signature header validation passed for '{signature_header}'")
    
    async def _process_webhook_event(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the webhook event and store the form response.
        
        Args:
            webhook_data: Parsed webhook data
            
        Returns:
            Processing result data
            
        Raises:
            OnboardingFormNotFoundError: If form not found
            DatabaseOperationError: If database operation fails
            FormResponseProcessingError: If response processing fails
        """
        form_response = webhook_data["form_response"]
        form_id = form_response.get("form_id")
        response_id = form_response.get("token")  # TypeForm uses 'token' as response ID
        
        if not form_id:
            raise FormResponseProcessingError(
                response_id or "unknown",
                "validation",
                "Missing form_id in webhook data"
            )
        
        if not response_id:
            raise FormResponseProcessingError(
                "unknown",
                "validation", 
                "Missing response token in webhook data"
            )
        
        async with self.uow_factory() as uow:
            try:
                # Find the onboarding form by TypeForm ID
                onboarding_form = await uow.onboarding_forms.get_by_typeform_id(form_id)
                
                if not onboarding_form:
                    raise OnboardingFormNotFoundError(
                        form_id,
                        identifier_type="typeform_id"
                    )
                
                # Create form response record
                form_response_data = {
                    "form_id": onboarding_form.id,
                    "response_id": response_id,
                    "response_data": form_response,
                    "submitted_at": datetime.now(UTC),
                    "webhook_event_id": webhook_data.get("event_id"),
                }
                
                # Extract client identifiers if available
                answers = form_response.get("answers", [])
                client_identifiers = await self._extract_client_identifiers(answers)
                if client_identifiers:
                    form_response_data["client_identifiers"] = client_identifiers
                
                # Store the response
                db_response = await uow.form_responses.create(form_response_data)
                await uow.commit()
                
                logger.info(f"Stored form response {response_id} for form {onboarding_form.id}")
                
                return {
                    "form_response_id": db_response.id,
                    "onboarding_form_id": onboarding_form.id,
                    "typeform_response_id": response_id,
                    "client_identifiers": client_identifiers,
                    "processed_at": datetime.now(UTC).isoformat()
                }
                
            except Exception as e:
                await uow.rollback()
                if isinstance(e, (OnboardingFormNotFoundError, FormResponseProcessingError)):
                    raise
                raise DatabaseOperationError(
                    "create",
                    "form_response",
                    str(e)
                )
    
    async def _extract_client_identifiers(self, answers: list) -> Dict[str, Any]:
        """
        Extract client identification information from form answers.
        
        Args:
            answers: List of form answers from TypeForm
            
        Returns:
            Dictionary of client identifiers
        """
        identifiers = {}
        
        # Common identifier fields to look for
        identifier_fields = {
            "email": ["email", "email_address", "contact_email"],
            "name": ["name", "full_name", "company_name", "client_name"],
            "phone": ["phone", "phone_number", "contact_phone"],
            "company": ["company", "company_name", "organization"],
        }
        
        for answer in answers:
            field = answer.get("field", {})
            field_ref = field.get("ref", "").lower()
            field_type = field.get("type", "")
            
            # Extract value based on field type
            value = None
            if field_type == "email":
                value = answer.get("email")
            elif field_type in ["short_text", "long_text"]:
                value = answer.get("text")
            elif field_type == "phone_number":
                value = answer.get("phone_number")
            
            if value:
                # Match field reference to identifier types
                for identifier_type, field_refs in identifier_fields.items():
                    if any(ref in field_ref for ref in field_refs):
                        identifiers[identifier_type] = value
                        break
        
        return identifiers

    def _track_security_failure(self, source_ip: str, error_message: str) -> bool:
        """
        Track security failures for alerting and return whether an alert was triggered.
        
        Args:
            source_ip: Source IP address of the failed request
            error_message: Error message from the failure
            
        Returns:
            bool: True if an alert was triggered, False otherwise
        """
        if source_ip == "unknown":
            return False
        
        current_time = datetime.now(UTC)
        
        # Clean old failures outside the time window
        self._clean_old_failures(source_ip, current_time)
        
        # Record this failure
        self._failure_tracker[source_ip].append({
            "timestamp": current_time,
            "error": error_message
        })
        
        failure_count = len(self._failure_tracker[source_ip])
        
        # Check if we should trigger an alert
        should_alert = self._should_trigger_alert(source_ip, failure_count, current_time)
        
        if should_alert:
            self._trigger_security_alert(source_ip, failure_count, error_message)
            self._alert_tracker[source_ip] = current_time
            return True
        
        return False
    
    def _clean_old_failures(self, source_ip: str, current_time: datetime) -> None:
        """Remove failures outside the configured time window."""
        if source_ip not in self._failure_tracker:
            return
        
        time_threshold = current_time - timedelta(
            minutes=self.security_alert_config["time_window_minutes"]
        )
        
        self._failure_tracker[source_ip] = [
            failure for failure in self._failure_tracker[source_ip]
            if failure["timestamp"] > time_threshold
        ]
        
        # Clean up empty entries
        if not self._failure_tracker[source_ip]:
            del self._failure_tracker[source_ip]
    
    def _should_trigger_alert(self, source_ip: str, failure_count: int, current_time: datetime) -> bool:
        """Determine if an alert should be triggered based on failure patterns."""
        # Check if we've exceeded the failure threshold
        if failure_count < self.security_alert_config["failure_threshold"]:
            return False
        
        # Check cooldown period to avoid spam
        if source_ip in self._alert_tracker:
            last_alert = self._alert_tracker[source_ip]
            cooldown_threshold = current_time - timedelta(
                minutes=self.security_alert_config["alert_cooldown_minutes"]
            )
            if last_alert > cooldown_threshold:
                return False  # Still in cooldown period
        
        return True
    
    def _trigger_security_alert(self, source_ip: str, failure_count: int, error_message: str) -> None:
        """Trigger a security alert for repeated failures."""
        alert_level = "HIGH" if failure_count >= self.security_alert_config["critical_failure_threshold"] else "MEDIUM"
        
        # Use enhanced logging middleware for alerts if available
        if self.logging_middleware:
            self.logging_middleware.log_security_event(
                correlation_id=f"alert_{datetime.now(UTC).timestamp()}",
                event_type="webhook_multiple_failures_same_source",
                user_id=None,
                form_id=None,
                security_result="ALERT",
                details={
                    "source_ip": source_ip,
                    "failure_count": failure_count,
                    "recent_error": error_message,
                    "alert_level": alert_level,
                    "time_window_minutes": self.security_alert_config["time_window_minutes"],
                    "alert_triggered_at": datetime.now(UTC).isoformat()
                }
            )
        
        # Also log to standard logger for immediate visibility
        logger.warning(
            f"SECURITY ALERT: {failure_count} webhook signature failures from {source_ip} "
            f"within {self.security_alert_config['time_window_minutes']} minutes. "
            f"Alert level: {alert_level}",
            extra={
                "alert_type": "repeated_webhook_failures",
                "source_ip": source_ip,
                "failure_count": failure_count,
                "alert_level": alert_level
            }
        )
    
    async def _schedule_webhook_retry_on_failure(
        self,
        headers: Dict[str, str],
        failure_reason: str,
        status_code: int
    ) -> None:
        """
        Schedule webhook for retry when processing fails.
        
        Args:
            headers: HTTP headers from the webhook request
            failure_reason: Reason for the failure
            status_code: HTTP status code that will be returned
        """
        if not self.retry_manager:
            logger.debug("No retry manager configured - webhook retry not scheduled")
            return
        
        try:
            # Extract webhook and form identifiers from headers
            webhook_id = headers.get('x-webhook-id', f'unknown-{datetime.now(UTC).timestamp()}')
            form_id = headers.get('x-typeform-form-id', 'unknown')
            webhook_url = headers.get('x-webhook-url', headers.get('origin', 'unknown'))
            
            # Log retry scheduling
            logger.info(
                f"Scheduling webhook retry for webhook_id={webhook_id}, "
                f"form_id={form_id}, reason={failure_reason}, status_code={status_code}"
            )
            
            # Schedule the retry
            retry_record = await self.retry_manager.schedule_webhook_retry(
                webhook_id=webhook_id,
                form_id=form_id,
                webhook_url=webhook_url,
                initial_failure_reason=failure_reason,
                initial_status_code=status_code
            )
            
            logger.info(
                f"Webhook retry scheduled successfully: webhook_id={webhook_id}, "
                f"next_retry_time={retry_record.next_retry_time}, "
                f"retry_status={retry_record.retry_status.value}"
            )
            
        except Exception as e:
            # Don't let retry scheduling failures affect webhook response
            logger.error(
                f"Failed to schedule webhook retry: {str(e)}. "
                f"Original failure: {failure_reason}",
                exc_info=True
            )


# Factory function for FastAPI or other web framework integration
def create_webhook_handler(uow_factory) -> WebhookHandler:
    """
    Factory function to create a webhook handler instance.
    
    Args:
        uow_factory: Unit of work factory function
        
    Returns:
        Configured WebhookHandler instance
    """
    return WebhookHandler(uow_factory)


# Lambda-specific wrapper (can be in separate deployment package)
async def lambda_handler_wrapper(event, context, uow_factory):
    """
    AWS Lambda wrapper for the webhook handler.
    
    This function can be used in a separate Lambda deployment package
    that imports this core webhook handling logic.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        uow_factory: Unit of work factory function
        
    Returns:
        Lambda response object
    """
    handler = WebhookHandler(uow_factory)
    
    # Extract data from Lambda event
    body = event.get("body", "{}")
    headers = event.get("headers", {})
    webhook_secret = None  # Would be loaded from environment/config
    
    status_code, response_data = await handler.handle_webhook(
        payload=body,
        headers=headers,
        webhook_secret=webhook_secret
    )
    
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(response_data)
    } 