"""
TypeForm API Client

HTTP client for TypeForm API operations including form validation,
webhook CRUD operations, and API error handling.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
from collections import deque

import httpx
import anyio
from pydantic import BaseModel, ValidationError, ConfigDict

from src.contexts.client_onboarding.config import config
from src.contexts.client_onboarding.core.services.exceptions import (
    TypeFormAPIError,
    TypeFormAuthenticationError, 
    TypeFormFormNotFoundError,
    TypeFormWebhookCreationError,
    TypeFormWebhookNotFoundError,
    FormValidationError,
)


logger = logging.getLogger(__name__)


class RateLimitValidator:
    """
    Rate limit validation and enforcement for TypeForm API client.
    
    Provides request rate validation, monitoring, and compliance checking
    to ensure TypeForm API rate limits are respected.
    
    Uses anyio.Lock for proper async synchronization instead of threading.Lock.
    """
    
    def __init__(self, requests_per_second: float):
        """
        Initialize rate limit validator.
        
        Args:
            requests_per_second: Maximum requests allowed per second
        """
        if requests_per_second <= 0:
            raise ValueError("Rate limit must be positive")
        if requests_per_second > 10:
            logger.warning("Rate limit of %s req/sec may exceed TypeForm API limits", requests_per_second)
            
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.request_timestamps: deque = deque(maxlen=100)  # Track last 100 requests
        self.lock = anyio.Lock()  # Use anyio.Lock for async synchronization
        self.last_request_time = 0.0
        
    def validate_rate_limit_config(self) -> Dict[str, Any]:
        """
        Validate rate limit configuration against TypeForm API requirements.
        
        Returns:
            Dict with validation results and recommendations
        """
        validation_result = {
            "is_valid": True,
            "rate_limit": self.requests_per_second,
            "min_interval_ms": self.min_interval * 1000,
            "warnings": [],
            "recommendations": []
        }
        
        # TypeForm API officially supports 2 req/sec for most endpoints
        if self.requests_per_second > 2:
            validation_result["warnings"].append(
                f"Rate limit {self.requests_per_second} req/sec exceeds TypeForm recommended 2 req/sec"
            )
            validation_result["recommendations"].append("Consider reducing to 2 req/sec for compliance")
            
        if self.requests_per_second < 0.5:
            validation_result["warnings"].append("Very conservative rate limit may impact performance")
            
        if self.min_interval < 0.1:
            validation_result["warnings"].append("Request interval below 100ms may trigger rate limiting")
            
        return validation_result
        
    async def enforce_rate_limit(self) -> None:
        """
        Enforce rate limit by blocking if necessary.
        
        This method ensures that requests don't exceed the configured rate limit
        by introducing delays when needed.
        
        Now properly async using anyio.Lock and anyio.sleep.
        """
        async with self.lock:
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            
            if time_since_last_request < self.min_interval:
                sleep_time = self.min_interval - time_since_last_request
                logger.debug("Rate limit enforced: sleeping %.3f seconds", sleep_time)
                await anyio.sleep(sleep_time)
                current_time = time.time()
                
            self.last_request_time = current_time
            self.request_timestamps.append(current_time)
            
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status and metrics.
        
        Returns:
            Dict with rate limit metrics and compliance status
        """
        async with self.lock:
            current_time = time.time()
            
            # Calculate actual request rate over last 60 seconds
            recent_requests = [
                ts for ts in self.request_timestamps 
                if current_time - ts <= 60
            ]
            
            actual_rate = len(recent_requests) / 60.0
            compliance_percentage = (
                min(100, (self.requests_per_second / max(actual_rate, 0.001)) * 100)
                if actual_rate > 0 else 100
            )
            
            return {
                "configured_rate_limit": self.requests_per_second,
                "actual_rate_60s": round(actual_rate, 3),
                "total_requests_tracked": len(self.request_timestamps),
                "compliance_percentage": round(compliance_percentage, 1),
                "is_compliant": actual_rate <= self.requests_per_second,
                "time_to_next_request": max(0, self.min_interval - (current_time - self.last_request_time)),
                "last_request_time": self.last_request_time
            }
            
    async def reset_rate_limit_tracking(self) -> None:
        """Reset rate limit tracking data."""
        async with self.lock:
            self.request_timestamps.clear()
            self.last_request_time = 0.0


class FormInfo(BaseModel):
    """TypeForm form information model."""
    id: str
    title: str
    type: str
    workspace: Dict[str, Any]
    theme: Dict[str, Any]
    settings: Dict[str, Any]
    welcome_screens: List[Dict[str, Any]]
    thankyou_screens: List[Dict[str, Any]]
    fields: List[Dict[str, Any]]
    hidden: Optional[List[str]] = None  # Optional - not always present in API response
    variables: Optional[Dict[str, Any]] = None  # Optional - not always present in API response
    
    model_config = ConfigDict(extra="allow")


class WebhookInfo(BaseModel):
    """TypeForm webhook information model."""
    id: str
    form_id: str
    tag: str
    url: str
    enabled: bool
    created_at: str
    updated_at: str
    verify_ssl: bool
    
    model_config = ConfigDict(extra="allow")


class TypeFormClient:
    """
    TypeForm API client for form validation and webhook management.
    
    Provides methods to:
    - Validate form access and retrieve form details
    - Create, update, delete, and list webhooks
    - Handle API authentication and errors
    - Enforce rate limiting compliance
    
    Now fully async-compatible with anyio synchronization.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize TypeForm API client.
        
        Args:
            api_key: TypeForm API key (defaults to config value)
            base_url: TypeForm API base URL (defaults to config value)
        """
        self.api_key = api_key or config.typeform_api_key
        self.base_url = base_url or config.typeform_api_base_url
        
        if not self.api_key:
            raise TypeFormAuthenticationError("TypeForm API key is required")
        
        # Initialize rate limit validator
        self.rate_limit_validator = RateLimitValidator(
            config.typeform_rate_limit_requests_per_second
        )
        
        # Validate rate limit configuration
        rate_limit_validation = self.rate_limit_validator.validate_rate_limit_config()
        if rate_limit_validation["warnings"]:
            for warning in rate_limit_validation["warnings"]:
                logger.warning("Rate limit validation: %s", warning)
        
        logger.info(
            "TypeFormClient initialized with rate limit: %s req/sec (min interval: %.3f ms)",
            self.rate_limit_validator.requests_per_second,
            self.rate_limit_validator.min_interval * 1000
        )
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Configure HTTP client with timeouts and retries
        self.client = httpx.AsyncClient(  # Use AsyncClient for async operations
            headers=self.headers,
            timeout=config.typeform_timeout_seconds,
            follow_redirects=True
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def _enforce_rate_limit(self) -> None:
        """Enforce rate limit before making API requests."""
        await self.rate_limit_validator.enforce_rate_limit()
    
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status and compliance metrics.
        
        Returns:
            Dict with rate limit metrics
        """
        return await self.rate_limit_validator.get_rate_limit_status()
    
    async def validate_rate_limit_compliance(self) -> bool:
        """
        Validate that the client is operating within rate limit bounds.
        
        Returns:
            True if client is compliant with rate limits
        """
        status = await self.get_rate_limit_status()
        return status["is_compliant"]
    
    async def reset_rate_limit_tracking(self) -> None:
        """Reset rate limit tracking metrics."""
        await self.rate_limit_validator.reset_rate_limit_tracking()
        logger.info("Rate limit tracking reset")

    def _build_url(self, endpoint: str) -> str:
        """Build complete API URL from endpoint."""
        return urljoin(f"{self.base_url}/", endpoint.lstrip("/"))
    
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions for errors.
        
        Args:
            response: HTTP response object
            
        Returns:
            Parsed response data
            
        Raises:
            TypeFormAPIError: For various API error conditions
        """
        try:
            data = response.json()
        except Exception:
            data = {"message": response.text}
        
        if response.status_code == 200:
            return data
        elif response.status_code == 401:
            raise TypeFormAuthenticationError(
                "Invalid API key or authentication failed",
                status_code=response.status_code,
                response_data=data
            )
        elif response.status_code == 403:
            raise TypeFormAuthenticationError(
                "Access forbidden - insufficient permissions",
                status_code=response.status_code,
                response_data=data
            )
        elif response.status_code == 404:
            raise TypeFormFormNotFoundError(
                "unknown",  # form_id will be unknown here
                status_code=response.status_code,
                response_data=data
            )
        elif response.status_code == 422:
            raise FormValidationError(
                "validation",  # field name
                data.get('message', 'Invalid request data'),  # value 
                f"Validation error: {data.get('message', 'Invalid request data')}",  # reason
                status_code=response.status_code,
                response_data=data
            )
        elif response.status_code == 429:
            # Extract retry-after header for intelligent retry handling
            retry_after = None
            retry_after_header = response.headers.get("Retry-After")
            if retry_after_header:
                try:
                    # Try to parse as integer seconds first (most common)
                    retry_after = int(retry_after_header)
                except ValueError:
                    # Could be HTTP date format, but we'll keep it simple for now
                    logger.warning(f"Could not parse Retry-After header: {retry_after_header}")
            
            # Log rate limit hit for monitoring
            if retry_after:
                logger.warning(f"TypeForm API rate limit exceeded (429), retry after {retry_after} seconds")
            else:
                logger.warning("TypeForm API rate limit exceeded (429)")
            raise TypeFormAPIError(
                f"Rate limit exceeded: {data.get('message', 'Too many requests')}",
                status_code=response.status_code,
                response_data=data,
                retry_after=retry_after
            )
        else:
            raise TypeFormAPIError(
                f"API request failed: {data.get('message', 'Unknown error')}",
                status_code=response.status_code,
                response_data=data
            )

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request with rate limiting enforcement.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Parsed response data
        """
        # Enforce rate limit before making request
        await self._enforce_rate_limit()
        
        url = self._build_url(endpoint)
        logger.debug("Making %s request to %s", method, url)
        
        response = await self.client.request(method, url, **kwargs)
        return self._handle_response(response)
    
    async def validate_form_access(self, form_id: str) -> FormInfo:
        """
        Validate access to TypeForm form and retrieve form details.
        
        Args:
            form_id: TypeForm form ID to validate
            
        Returns:
            Form information if accessible
            
        Raises:
            TypeFormAPIError: If form is not accessible or invalid
        """
        logger.info(f"Validating access to form: {form_id}")
        
        try:
            data = await self._make_request("GET", f"forms/{form_id}")
            
            form_info = FormInfo(**data)
            logger.info(f"Successfully validated form: {form_info.title}")
            return form_info
            
        except ValidationError as e:
            raise FormValidationError("form_data", str(e), f"Invalid form data structure: {e}")
        except Exception as e:
            logger.error(f"Form validation failed: {e}")
            raise
    
    async def get_form(self, form_id: str) -> FormInfo:
        """
        Retrieve detailed form information.
        
        Args:
            form_id: TypeForm form ID
            
        Returns:
            Complete form information
        """
        return await self.validate_form_access(form_id)
    
    async def get_form_with_retry(self, form_id: str, max_retries: int = 3) -> FormInfo:
        """
        Get form with retry logic for rate limiting.
        
        Args:
            form_id: TypeForm form ID
            max_retries: Maximum number of retry attempts
            
        Returns:
            Form information
            
        Raises:
            TypeFormRateLimitError: If max retries exceeded
        """
        from .exceptions import TypeFormRateLimitError
        
        for attempt in range(max_retries + 1):
            try:
                return await self.get_form(form_id)
            except TypeFormAPIError as e:
                if e.status_code == 429 and attempt < max_retries:
                    # Rate limited, wait and retry
                    wait_time = 2 ** attempt  # Exponential backoff
                    await anyio.sleep(wait_time)
                    continue
                elif e.status_code == 429:
                    raise TypeFormRateLimitError(
                        "Rate limit exceeded",
                        status_code=429,
                        response_data=e.response_data,
                        retry_after=e.retry_after
                    )
                else:
                    raise
        
        # This shouldn't be reached, but for safety
        raise TypeFormRateLimitError("Max retries exceeded")
    
    async def get_form_with_exponential_backoff(
        self, 
        form_id: str, 
        max_retries: int = 3, 
        base_delay: float = 0.1
    ) -> FormInfo:
        """
        Get form with exponential backoff retry logic.
        
        Args:
            form_id: TypeForm form ID
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds
            
        Returns:
            Form information
        """
        from .exceptions import TypeFormRateLimitError
        
        for attempt in range(max_retries + 1):
            try:
                return await self.get_form(form_id)
            except TypeFormAPIError as e:
                if e.status_code == 429 and attempt < max_retries:
                    # Rate limited, wait with exponential backoff
                    wait_time = base_delay * (2 ** attempt)
                    await anyio.sleep(wait_time)
                    continue
                elif e.status_code == 429:
                    raise TypeFormRateLimitError(
                        "Rate limit exceeded",
                        status_code=429,
                        response_data=e.response_data,
                        retry_after=e.retry_after
                    )
                else:
                    raise
        
        # This shouldn't be reached, but for safety
        raise TypeFormRateLimitError("Max retries exceeded")
    
    async def list_webhooks(self, form_id: str) -> List[WebhookInfo]:
        """
        List all webhooks for a TypeForm form.
        
        Args:
            form_id: TypeForm form ID
            
        Returns:
            List of webhook information objects
        """
        logger.info(f"Listing webhooks for form: {form_id}")
        
        data = await self._make_request("GET", f"forms/{form_id}/webhooks")
        
        webhooks = []
        for webhook_data in data.get("items", []):
            try:
                webhook = WebhookInfo(**webhook_data)
                webhooks.append(webhook)
            except ValidationError as e:
                logger.warning(f"Skipping invalid webhook data: {e}")
        
        logger.info(f"Found {len(webhooks)} webhooks for form {form_id}")
        return webhooks
    
    async def create_webhook_with_automation(
        self,
        form_id: str,
        webhook_url: str,
        tag: str = "client_onboarding",
        enabled: bool = True,
        verify_ssl: bool = True,
        retry_attempts: int = 3,
        auto_cleanup_existing: bool = True
    ) -> WebhookInfo:
        """
        Create a new webhook with automated setup and validation.
        
        Args:
            form_id: TypeForm form ID
            webhook_url: URL to receive webhook notifications
            tag: Webhook tag for identification
            enabled: Whether webhook is enabled
            verify_ssl: Whether to verify SSL certificates
            retry_attempts: Number of retry attempts on failure
            auto_cleanup_existing: Whether to automatically remove existing webhooks with same tag
            
        Returns:
            Created webhook information
            
        Raises:
            TypeFormWebhookCreationError: If webhook creation fails after retries
            FormValidationError: If parameters are invalid
        """
        logger.info(f"Starting automated webhook creation for form {form_id}: {webhook_url}")
        
        # Validate inputs
        if not form_id or not form_id.strip():
            raise FormValidationError("form_id", "", "form_id cannot be empty")
        if not webhook_url or not webhook_url.strip():
            raise FormValidationError("webhook_url", "", "webhook_url cannot be empty")
        if not webhook_url.startswith(('http://', 'https://')):
            raise FormValidationError("webhook_url", webhook_url, "webhook_url must be a valid HTTP/HTTPS URL")
        
        # Check if form exists before creating webhook
        try:
            await self.get_form(form_id)
        except TypeFormFormNotFoundError:
            logger.error(f"Form {form_id} not found, cannot create webhook")
            raise TypeFormWebhookCreationError(
                webhook_url, 
                f"Form {form_id} does not exist or is not accessible"
            )
        
        # Auto-cleanup existing webhook with same tag if requested
        if auto_cleanup_existing:
            try:
                existing_webhook = await self.get_webhook(form_id, tag)
                logger.info(f"Found existing webhook {existing_webhook.id} with tag {tag}, removing...")
                await self.delete_webhook(form_id, tag)
                logger.info(f"Successfully cleaned up existing webhook {existing_webhook.id}")
            except (TypeFormWebhookNotFoundError, TypeFormAPIError):
                # No existing webhook or other error - continue with creation
                logger.debug(f"No existing webhook found with tag {tag}, proceeding with creation")
        
        # Attempt webhook creation with retries
        last_error = None
        for attempt in range(1, retry_attempts + 1):
            try:
                logger.info(f"Webhook creation attempt {attempt}/{retry_attempts}")
                webhook = await self.create_webhook(
                    form_id=form_id,
                    webhook_url=webhook_url,
                    tag=tag,
                    enabled=enabled,
                    verify_ssl=verify_ssl
                )
                
                # Verify webhook was created successfully
                verification_webhook = await self.get_webhook(form_id, tag)
                if verification_webhook.url != webhook_url:
                    logger.warning(f"Webhook URL mismatch after creation: expected {webhook_url}, got {verification_webhook.url}")
                
                logger.info(f"Automated webhook creation successful: {webhook.id}")
                return webhook
                
            except Exception as e:
                last_error = e
                logger.warning(f"Webhook creation attempt {attempt} failed: {e}")
                if attempt < retry_attempts:
                    await anyio.sleep(2 ** attempt)  # Exponential backoff
                
        # All attempts failed
        error_msg = f"Failed to create webhook after {retry_attempts} attempts. Last error: {last_error}"
        logger.error(error_msg)
        raise TypeFormWebhookCreationError(webhook_url, error_msg)

    async def bulk_webhook_creation(self, webhook_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple webhooks in batch with comprehensive error handling.
        
        Args:
            webhook_configs: List of webhook configuration dictionaries
            
        Returns:
            Dictionary with creation results, successes, and failures
        """
        logger.info(f"Starting bulk webhook creation for {len(webhook_configs)} webhooks")
        
        results = {
            "total_requested": len(webhook_configs),
            "successful_creations": [],
            "failed_creations": [],
            "skipped_existing": []
        }
        
        successful_webhooks = []
        failed_webhooks = []
        
        for i, webhook_config in enumerate(webhook_configs):
            try:
                form_id = webhook_config.get('form_id')
                webhook_url = webhook_config.get('webhook_url')
                tag = webhook_config.get('tag', f'bulk_webhook_{i}')
                enabled = webhook_config.get('enabled', True)
                verify_ssl = webhook_config.get('verify_ssl', True)

                if not form_id or not webhook_url:
                    logger.error(f"Webhook config {i} missing required fields: {webhook_config}")
                    failed_webhooks.append(webhook_config)
                    continue
                
                webhook = await self.create_webhook_with_automation(
                    form_id=form_id,
                    webhook_url=webhook_url,
                    tag=tag,
                    enabled=enabled,
                    verify_ssl=verify_ssl
                )
                successful_webhooks.append(webhook)
                logger.info(f"Batch webhook {i+1}/{len(webhook_configs)} created successfully")
                
            except Exception as e:
                logger.error(f"Failed to create webhook {i+1}: {e}")
                failed_webhooks.append(webhook_config)
        
        results["successful_creations"] = successful_webhooks
        results["failed_creations"] = failed_webhooks
        
        if failed_webhooks:
            logger.warning(f"Batch creation completed with {len(failed_webhooks)} failures out of {len(webhook_configs)} total")
        else:
            logger.info(f"Batch webhook creation completed successfully: {len(successful_webhooks)} webhooks created")
        
        return results

    async def check_webhook_health(
        self,
        form_id: str,
        tag: str,
        include_delivery_stats: bool = True
    ) -> Dict[str, Any]:
        """
        Check the health status of a webhook.
        
        Args:
            form_id: TypeForm form ID
            tag: Webhook tag to check
            include_delivery_stats: Whether to include delivery statistics
            
        Returns:
            Dictionary containing webhook health information
        """
        logger.info(f"Checking health for webhook {tag} on form {form_id}")
        
        try:
            # Get webhook information
            webhook = await self.get_webhook(form_id, tag)
            
            health_status = {
                "webhook_id": webhook.id,
                "tag": tag,
                "form_id": form_id,
                "status": "healthy" if webhook.enabled else "disabled",
                "url": webhook.url,
                "enabled": webhook.enabled,
                "verify_ssl": webhook.verify_ssl,
                "last_checked": datetime.now().isoformat(),
                "issues": []
            }
            
            # Basic webhook validation
            if not webhook.url:
                health_status["issues"].append("webhook_url_missing")
                health_status["status"] = "unhealthy"
            elif not webhook.url.startswith(('http://', 'https://')):
                health_status["issues"].append("invalid_webhook_url_scheme")
                health_status["status"] = "unhealthy"
            
            if not webhook.enabled:
                health_status["issues"].append("webhook_disabled")
            
            # Check webhook endpoint reachability
            try:
                # Simple HEAD request to check if endpoint is reachable
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.head(webhook.url)
                    health_status["endpoint_reachable"] = True
                    health_status["endpoint_status_code"] = response.status_code
                    if response.status_code >= 400:
                        health_status["issues"].append(f"endpoint_error_{response.status_code}")
                        health_status["status"] = "degraded"
            except Exception as e:
                health_status["endpoint_reachable"] = False
                health_status["endpoint_error"] = str(e)
                health_status["issues"].append("endpoint_unreachable")
                health_status["status"] = "unhealthy"
            
            # Include delivery statistics if requested
            if include_delivery_stats:
                try:
                    delivery_stats = await self._get_webhook_delivery_stats(form_id, tag)
                    health_status["delivery_stats"] = delivery_stats
                except Exception as e:
                    logger.warning(f"Could not retrieve delivery stats for webhook {tag}: {e}")
                    health_status["delivery_stats_error"] = str(e)
            
            logger.info(f"Webhook health check completed: {health_status['status']}")
            return health_status
            
        except Exception as e:
            logger.error(f"Failed to check webhook health for {tag}: {e}")
            return {
                "webhook_id": None,
                "tag": tag,
                "form_id": form_id,
                "status": "error",
                "last_checked": datetime.now().isoformat(),
                "error": str(e),
                "issues": ["health_check_failed"]
            }
    
    async def monitor_webhooks_health(
        self,
        form_ids: List[str],
        tag_filter: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Monitor health of multiple webhooks across forms.
        
        Args:
            form_ids: List of form IDs to monitor
            tag_filter: Optional tag filter (if None, monitors all webhooks)
            
        Returns:
            Dictionary mapping form IDs to their webhook health reports
        """
        logger.info(f"Starting webhook health monitoring for {len(form_ids)} forms")
        
        health_reports = {}
        overall_stats = {
            "total_webhooks": 0,
            "healthy_webhooks": 0,
            "degraded_webhooks": 0,
            "unhealthy_webhooks": 0,
            "error_webhooks": 0
        }
        
        for form_id in form_ids:
            try:
                # Get all webhooks for this form
                webhooks = await self.list_webhooks(form_id)
                form_health_reports = []
                
                for webhook in webhooks:
                    # Apply tag filter if specified
                    if tag_filter and webhook.tag != tag_filter:
                        continue
                    
                    health_report = await self.check_webhook_health(
                        form_id=form_id,
                        tag=webhook.tag,
                        include_delivery_stats=False  # Skip detailed stats for bulk monitoring
                    )
                    form_health_reports.append(health_report)
                    
                    # Update overall statistics
                    overall_stats["total_webhooks"] += 1
                    status = health_report.get("status", "error")
                    if status == "healthy":
                        overall_stats["healthy_webhooks"] += 1
                    elif status == "degraded":
                        overall_stats["degraded_webhooks"] += 1
                    elif status == "unhealthy":
                        overall_stats["unhealthy_webhooks"] += 1
                    else:
                        overall_stats["error_webhooks"] += 1
                
                health_reports[form_id] = form_health_reports
                
            except Exception as e:
                logger.error(f"Failed to monitor webhooks for form {form_id}: {e}")
                health_reports[form_id] = [{
                    "webhook_id": None,
                    "tag": "unknown",
                    "form_id": form_id,
                    "status": "error",
                    "error": str(e),
                    "issues": ["monitoring_failed"]
                }]
                overall_stats["error_webhooks"] += 1
        
        # Add summary statistics
        health_reports["_summary"] = overall_stats
        health_reports["_monitoring_timestamp"] = datetime.now().isoformat()
        
        logger.info(f"Webhook health monitoring completed: {overall_stats}")
        return health_reports
    
    async def _get_webhook_delivery_stats(self, form_id: str, tag: str) -> Dict[str, Any]:
        """
        Get delivery statistics for a webhook (if available via TypeForm API).
        
        Note: This is a placeholder for future TypeForm API webhook analytics.
        TypeForm may not provide detailed delivery stats via API.
        """
        # This would be implemented when TypeForm provides webhook analytics API
        return {
            "available": False,
            "reason": "TypeForm API does not currently provide webhook delivery statistics",
            "last_attempted": datetime.now().isoformat()
        }

    async def create_webhook(self, form_id: str, webhook_url: str, tag: str, enabled: bool = True, verify_ssl: bool = True) -> WebhookInfo:
        """
        Create a new webhook for a TypeForm form.
        
        Args:
            form_id: TypeForm form ID
            webhook_url: URL to receive webhook notifications
            tag: Unique tag to identify the webhook
            enabled: Whether webhook should be enabled
            verify_ssl: Whether to verify SSL certificates
            
        Returns:
            Created webhook information
            
        Raises:
            TypeFormWebhookCreationError: If webhook creation fails
        """
        logger.info(f"Creating webhook for form {form_id} with tag {tag}")
        
        webhook_data = {
            "url": webhook_url,
            "enabled": enabled,
            "verify_ssl": verify_ssl,
            "tag": tag
        }
        
        try:
            data = await self._make_request("PUT", f"forms/{form_id}/webhooks/{tag}", json=webhook_data)
            
            webhook = WebhookInfo(**data)
            logger.info(f"Successfully created webhook: {webhook.id}")
            return webhook
            
        except ValidationError as e:
            raise TypeFormWebhookCreationError(webhook_url, f"Invalid webhook response data: {e}")
        except TypeFormAPIError as e:
            raise TypeFormWebhookCreationError(webhook_url, f"Failed to create webhook: {e.message}")
    
    async def update_webhook(self, form_id: str, tag: str, webhook_url: Optional[str] = None, enabled: Optional[bool] = None, verify_ssl: Optional[bool] = None) -> WebhookInfo:
        """
        Update an existing webhook for a TypeForm form.
        
        NOTE: TypeForm API doesn't support PATCH for webhooks, so this method
        implements updates via DELETE + CREATE pattern.
        
        Args:
            form_id: TypeForm form ID
            tag: Webhook tag to update
            webhook_url: New webhook URL (optional)
            enabled: New enabled status (optional)
            verify_ssl: New SSL verification setting (optional)
            
        Returns:
            Updated webhook information
        """
        logger.info(f"Updating webhook {tag} for form {form_id} (using delete+create)")
        
        if not any([webhook_url is not None, enabled is not None, verify_ssl is not None]):
            raise FormValidationError("webhook_properties", "", "At least one webhook property must be provided for update")
        
        try:
            # Get current webhook to preserve existing values
            existing_webhook = await self.get_webhook(form_id, tag)
            
            # Use provided values or fall back to existing ones
            final_url = webhook_url if webhook_url is not None else existing_webhook.url
            final_enabled = enabled if enabled is not None else existing_webhook.enabled
            final_verify_ssl = verify_ssl if verify_ssl is not None else existing_webhook.verify_ssl
            
            # Delete existing webhook
            await self.delete_webhook(form_id, tag)
            
            # Create new webhook with updated values
            webhook = await self.create_webhook(
                form_id=form_id,
                webhook_url=final_url,
                tag=tag,
                enabled=final_enabled,
                verify_ssl=final_verify_ssl
            )
            
            logger.info(f"Successfully updated webhook via delete+create: {webhook.id}")
            return webhook
            
        except TypeFormWebhookNotFoundError:
            raise TypeFormFormNotFoundError(form_id)
        except ValidationError as e:
            raise FormValidationError("webhook_data", str(e), f"Invalid webhook response data: {e}")

    async def delete_webhook(self, form_id: str, tag: str) -> bool:
        """
        Delete a webhook from a TypeForm form.
        
        Args:
            form_id: TypeForm form ID
            tag: Webhook tag to delete
            
        Returns:
            True if deletion was successful
        """
        logger.info(f"Deleting webhook {tag} for form {form_id}")
        
        # Enforce rate limit before making request
        await self._enforce_rate_limit()
        
        url = self._build_url(f"forms/{form_id}/webhooks/{tag}")
        logger.debug("Making DELETE request to %s", url)
        
        response = await self.client.delete(url)
        
        if response.status_code == 204:
            logger.info(f"Successfully deleted webhook: {tag}")
            return True
        elif response.status_code == 404:
            raise TypeFormWebhookNotFoundError(tag)
        else:
            # Use standard error handling for other status codes
            self._handle_response(response)
            return False
    
    async def get_webhook(self, form_id: str, tag: str) -> WebhookInfo:
        """
        Get details of a specific webhook.
        
        Args:
            form_id: TypeForm form ID
            tag: Webhook tag
            
        Returns:
            Webhook information
        """
        logger.info(f"Retrieving webhook {tag} for form {form_id}")
        
        try:
            data = await self._make_request("GET", f"forms/{form_id}/webhooks/{tag}")
            
            webhook = WebhookInfo(**data)
            logger.info(f"Successfully retrieved webhook: {webhook.id}")
            return webhook
            
        except ValidationError as e:
            raise FormValidationError("webhook_data", str(e), f"Invalid webhook response data: {e}")


# Convenience function for creating client instances
def create_typeform_client(api_key: Optional[str] = None) -> TypeFormClient:
    """
    Create a TypeForm client instance.
    
    Args:
        api_key: Optional API key (uses config default if not provided)
        
    Returns:
        Configured TypeForm client
    """
    return TypeFormClient(api_key=api_key) 