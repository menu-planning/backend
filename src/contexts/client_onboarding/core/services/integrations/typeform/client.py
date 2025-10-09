from __future__ import annotations

import json
import time
from collections import deque
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

import anyio
import httpx
import logfire
from anyio import to_thread
from src.contexts.shared_kernel.adapters.optimized_http_client import (
    create_optimized_http_client,
)
from pydantic import BaseModel, ConfigDict, ValidationError
from src.contexts.client_onboarding.config import config
from src.contexts.client_onboarding.core.services.exceptions import (
    FormValidationError,
    TypeFormAPIError,
    TypeFormAuthenticationError,
    TypeFormFormNotFoundError,
    TypeFormRateLimitError,
    TypeFormWebhookCreationError,
    TypeFormWebhookNotFoundError,
)

# Relocated content from services/typeform_client.py
from src.logging.logger import get_logger

logger = get_logger(__name__)

# Constants for HTTP status codes
HTTP_STATUS_OK = 200
HTTP_STATUS_CREATED = 201
HTTP_STATUS_NO_CONTENT = 204
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_UNPROCESSABLE_ENTITY = 422
HTTP_STATUS_TOO_MANY_REQUESTS = 429
HTTP_STATUS_SERVICE_UNAVAILABLE = 503

# Constants for error messages
ERROR_MSG_PROXY_NOT_CONFIGURED = "Proxy not configured (no client)"
ERROR_MSG_LAMBDA_INVOKE_TIMEOUT = "Lambda Invoke timed out"
ERROR_MSG_RATE_LIMIT_EXCEEDED = "Rate limit exceeded"
ERROR_MSG_MAX_RETRIES_EXCEEDED = "Max retries exceeded"
ERROR_MSG_FORM_ID_EMPTY = "form_id cannot be empty"
ERROR_MSG_WEBHOOK_URL_EMPTY = "webhook_url cannot be empty"
ERROR_MSG_WEBHOOK_URL_INVALID = "webhook_url must be a valid HTTP/HTTPS URL"
ERROR_MSG_WEBHOOK_PROPERTIES_REQUIRED = (
    "At least one webhook property must be provided for update"
)
ERROR_MSG_INVALID_WEBHOOK_DATA = "Invalid webhook response data: {}"
ERROR_MSG_WEBHOOK_CREATION_FAILED = "Failed to create webhook: {}"
ERROR_MSG_WEBHOOK_DELIVERY_STATS_UNAVAILABLE = (
    "TypeForm API does not currently provide webhook delivery statistics"
)

# Constants for rate limiting
MAX_RATE_LIMIT_WARNING = 10
RECOMMENDED_RATE_LIMIT = 2
MIN_RATE_LIMIT_WARNING = 0.5
MIN_INTERVAL_WARNING = 0.1
RATE_LIMIT_WINDOW_SECONDS = 60

# Constants for validation
ERROR_MSG_API_KEY_REQUIRED = "TypeForm API key is required"
ERROR_MSG_PROXY_NOT_CONFIGURED_GENERIC = "Proxy not configured"
ERROR_MSG_INVALID_API_KEY = "Invalid API key or authentication failed"
ERROR_MSG_ACCESS_FORBIDDEN = "Access forbidden - insufficient permissions"
ERROR_MSG_VALIDATION_ERROR = "validation"
ERROR_MSG_UNKNOWN_ERROR = "unknown"
ERROR_MSG_RATE_LIMIT_EXCEEDED_429 = "Rate limit exceeded: {}"
ERROR_MSG_API_REQUEST_FAILED = "API request failed: {}"


class RateLimitValidator:
    """Rate limit validator for TypeForm API requests.

    Enforces rate limiting to prevent exceeding TypeForm API limits and
    provides validation and monitoring capabilities for request rates.
    """

    RATE_LIMIT_POSITIVE_ERROR = "Rate limit must be positive"

    def __init__(self, requests_per_second: float):
        if requests_per_second <= 0:
            raise ValueError(self.RATE_LIMIT_POSITIVE_ERROR)
        if requests_per_second > MAX_RATE_LIMIT_WARNING:
            logger.warning(
                "Rate limit may exceed TypeForm API limits",
                rate_limit=requests_per_second,
                unit="req/sec",
                action="rate_limit_warning"
            )
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.request_timestamps: deque = deque(maxlen=100)
        self.lock = anyio.Lock()
        self.last_request_time = 0.0

    def validate_rate_limit_config(self) -> dict[str, Any]:
        """Validate rate limit configuration and return validation results.

        Returns:
            Dictionary containing validation results, warnings, and recommendations.
        """
        validation_result = {
            "is_valid": True,
            "rate_limit": self.requests_per_second,
            "min_interval_ms": self.min_interval * 1000,
            "warnings": [],
            "recommendations": [],
        }
        if self.requests_per_second > RECOMMENDED_RATE_LIMIT:
            validation_result["warnings"].append(
                f"Rate limit {self.requests_per_second} req/sec exceeds "
                f"TypeForm recommended {RECOMMENDED_RATE_LIMIT} req/sec"
            )
            validation_result["recommendations"].append(
                f"Consider reducing to {RECOMMENDED_RATE_LIMIT} req/sec for compliance"
            )
        if self.requests_per_second < MIN_RATE_LIMIT_WARNING:
            validation_result["warnings"].append(
                "Very conservative rate limit may impact performance"
            )
        if self.min_interval < MIN_INTERVAL_WARNING:
            validation_result["warnings"].append(
                "Request interval below 100ms may trigger rate limiting"
            )
        return validation_result

    async def enforce_rate_limit(self) -> None:
        """Enforce rate limiting by sleeping if necessary."""
        async with self.lock:
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.min_interval:
                sleep_time = self.min_interval - time_since_last_request
                logger.debug("Rate limit enforced", sleep_time=f"{sleep_time:.3f}", action="rate_limit_sleep")
                await anyio.sleep(sleep_time)
                current_time = time.time()
            self.last_request_time = current_time
            self.request_timestamps.append(current_time)

    async def get_rate_limit_status(self) -> dict[str, Any]:
        """Get current rate limit status and compliance information.

        Returns:
            Dictionary containing rate limit status, compliance metrics, and timing information.
        """
        async with self.lock:
            current_time = time.time()
            recent_requests = [
                ts
                for ts in self.request_timestamps
                if current_time - ts <= RATE_LIMIT_WINDOW_SECONDS
            ]
            actual_rate = len(recent_requests) / float(RATE_LIMIT_WINDOW_SECONDS)
            compliance_percentage = (
                min(100, (self.requests_per_second / max(actual_rate, 0.001)) * 100)
                if actual_rate > 0
                else 100
            )
            return {
                "configured_rate_limit": self.requests_per_second,
                "actual_rate_60s": round(actual_rate, 3),
                "total_requests_tracked": len(self.request_timestamps),
                "compliance_percentage": round(compliance_percentage, 1),
                "is_compliant": actual_rate <= self.requests_per_second,
                "time_to_next_request": max(
                    0, self.min_interval - (current_time - self.last_request_time)
                ),
                "last_request_time": self.last_request_time,
            }

    async def reset_rate_limit_tracking(self) -> None:
        """Reset rate limit tracking data."""
        async with self.lock:
            self.request_timestamps.clear()
            self.last_request_time = 0.0


class FormInfo(BaseModel):
    """TypeForm form information model.

    Attributes:
        id: TypeForm form identifier.
        title: Form title.
        type: Form type.
        workspace: Workspace information.
        theme: Form theme configuration.
        settings: Form settings.
        welcome_screens: Welcome screen configurations.
        thankyou_screens: Thank you screen configurations.
        fields: Form field definitions.
        hidden: Hidden field identifiers.
        variables: Form variables.
    """
    id: str
    title: str
    type: str
    workspace: dict[str, Any]
    theme: dict[str, Any]
    settings: dict[str, Any]
    welcome_screens: list[dict[str, Any]]
    thankyou_screens: list[dict[str, Any]]
    fields: list[dict[str, Any]]
    hidden: list[str] | None = None
    variables: dict[str, Any] | None = None
    model_config = ConfigDict(extra="allow")


class WebhookInfo(BaseModel):
    """TypeForm webhook information model.

    Attributes:
        id: Webhook identifier.
        form_id: Associated form identifier.
        tag: Webhook tag.
        url: Webhook URL.
        enabled: Whether the webhook is enabled.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        verify_ssl: Whether SSL verification is enabled.
    """
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
    """TypeForm API client with rate limiting and proxy support.

    Provides comprehensive access to TypeForm API endpoints with built-in
    rate limiting, retry mechanisms, and optional proxy support for
    webhook management and form operations.
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or config.typeform_api_key
        self.base_url = base_url or config.typeform_api_base_url
        if not self.api_key:
            raise TypeFormAuthenticationError(ERROR_MSG_API_KEY_REQUIRED)

        self.rate_limit_validator = RateLimitValidator(
            config.typeform_rate_limit_requests_per_second
        )
        rate_limit_validation = self.rate_limit_validator.validate_rate_limit_config()
        if rate_limit_validation["warnings"]:
            for warning in rate_limit_validation["warnings"]:
                logger.warning("Rate limit validation warning", warning=warning, action="rate_limit_validation")
        logger.info(
            "Rate limit validator configured",
            rate_limit=self.rate_limit_validator.requests_per_second,
            unit="req/sec",
            min_interval_ms=round(self.rate_limit_validator.min_interval * 1000, 3),
            action="rate_limit_config"
        )
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Use optimized HTTP client with TypeForm-specific configuration
        self.client = create_optimized_http_client(
            base_url=self.base_url,
            headers=self.headers,
            # Override timeout for TypeForm-specific needs
            timeout=httpx.Timeout(
                connect=5.0,
                read=config.typeform_timeout_seconds,
                write=10.0,
                pool=5.0,
            ),
            # Use TypeForm-specific connection limits (more conservative than defaults)
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
        logfire.instrument_httpx(self.client.client)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.client.close()

    async def close(self):
        """Close the HTTP client connection."""
        await self.client.close()

    async def _enforce_rate_limit(self) -> None:
        await self.rate_limit_validator.enforce_rate_limit()

    async def get_rate_limit_status(self) -> dict[str, Any]:
        """Get current rate limit status and compliance information.

        Returns:
            Dictionary containing rate limit status and compliance metrics.
        """
        return await self.rate_limit_validator.get_rate_limit_status()

    async def validate_rate_limit_compliance(self) -> bool:
        """Validate current rate limit compliance.

        Returns:
            True if currently compliant with rate limits.
        """
        status = await self.get_rate_limit_status()
        return status["is_compliant"]

    async def reset_rate_limit_tracking(self) -> None:
        """Reset rate limit tracking data."""
        await self.rate_limit_validator.reset_rate_limit_tracking()
        logger.info("Rate limit tracking reset", action="rate_limit_reset")

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint path."""
        return urljoin(f"{self.base_url}/", endpoint.lstrip("/"))

    def _handle_response(self, response: Any) -> dict[str, Any]:
        """Handle HTTP response and raise appropriate exceptions for errors.

        Args:
            response: HTTP response object.

        Returns:
            Response data dictionary.

        Raises:
            TypeFormAuthenticationError: For authentication failures.
            TypeFormFormNotFoundError: For form not found errors.
            FormValidationError: For validation errors.
            TypeFormAPIError: For other API errors.
        """
        try:
            data = response.json()
        except Exception:
            data = {"message": response.text}
        if response.status_code == HTTP_STATUS_OK:
            return data
        if response.status_code == HTTP_STATUS_UNAUTHORIZED:
            logger.warning(
                "TypeForm API authentication failed - invalid API key",
                security_event="typeform_auth_failure",
                security_level="high",
                status_code=response.status_code,
                security_risk="invalid_api_key",
                business_impact="external_api_access_denied",
                action="typeform_api_authentication"
            )
            raise TypeFormAuthenticationError(
                ERROR_MSG_INVALID_API_KEY,
                status_code=response.status_code,
                response_data=data,
            )
        if response.status_code == HTTP_STATUS_FORBIDDEN:
            logger.warning(
                "TypeForm API access forbidden - insufficient permissions",
                security_event="typeform_access_forbidden",
                security_level="high",
                status_code=response.status_code,
                security_risk="insufficient_permissions",
                business_impact="external_api_access_denied",
                action="typeform_api_authorization"
            )
            raise TypeFormAuthenticationError(
                ERROR_MSG_ACCESS_FORBIDDEN,
                status_code=response.status_code,
                response_data=data,
            )
        if response.status_code == HTTP_STATUS_NOT_FOUND:
            raise TypeFormFormNotFoundError(
                ERROR_MSG_UNKNOWN_ERROR,
                status_code=response.status_code,
                response_data=data,
            )
        if response.status_code == HTTP_STATUS_UNPROCESSABLE_ENTITY:
            raise FormValidationError(
                ERROR_MSG_VALIDATION_ERROR,
                data.get("message", "Invalid request data"),
                f"Validation error: {data.get('message', 'Invalid request data')}",
                status_code=response.status_code,
                response_data=data,
            )
        if response.status_code == HTTP_STATUS_TOO_MANY_REQUESTS:
            retry_after = None
            retry_after_header = response.headers.get("Retry-After")
            if retry_after_header:
                try:
                    retry_after = int(retry_after_header)
                except ValueError:
                    logger.warning(
                        "Could not parse Retry-After header",
                        retry_after_header=retry_after_header,
                        action="retry_after_parse_error"
                    )
            if retry_after:
                logger.warning(
                    "TypeForm API rate limit exceeded",
                    status_code=429,
                    retry_after_seconds=retry_after,
                    action="rate_limit_exceeded"
                )
            else:
                logger.warning(
                    "TypeForm API rate limit exceeded",
                    status_code=429,
                    action="rate_limit_exceeded"
                )

            rate_limit_msg = (
                f"Rate limit exceeded: {data.get('message', 'Too many requests')}"
            )
            raise TypeFormAPIError(
                rate_limit_msg,
                status_code=response.status_code,
                response_data=data,
                retry_after=retry_after,
            )

        api_error_msg = f"API request failed: {data.get('message', 'Unknown error')}"
        raise TypeFormAPIError(
            api_error_msg,
            status_code=response.status_code,
            response_data=data,
        )

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> dict[str, Any]:
        await self._enforce_rate_limit()

        url = self._build_url(endpoint)
        logger.debug(
            "Making HTTP request",
            method=method,
            url=url,
            action="http_request",
            service="typeform_api",
            request_type="external_api_call",
            endpoint=endpoint,
        )
        try:
            response = await self.client.request(method, url, **kwargs)
        except httpx.ConnectError:
            logger.error(
                "Connect error during HTTP request",
                method=method,
                url=url,
                action="http_connect_error",
                service="typeform_api",
                request_type="external_api_call",
                endpoint=endpoint,
                error_type="ConnectError",
                business_impact="typeform_api_unavailable",
                exc_info=True,
            )
            raise
        logger.info(
            "HTTP request completed",
            method=method,
            url=url,
            status_code=response.status_code,
            action="http_response",
            service="typeform_api",
            request_type="external_api_call",
            endpoint=endpoint,
            response_success=200 <= response.status_code < 300,
        )
        return self._handle_response(response)

    async def validate_form_access(self, form_id: str) -> FormInfo:
        """Validate access to a TypeForm form and return form information.

        Args:
            form_id: TypeForm form identifier.

        Returns:
            FormInfo object containing form details.

        Raises:
            TypeFormFormNotFoundError: If form not found or inaccessible.
            TypeFormAuthenticationError: For authentication failures.
            FormValidationError: For invalid form data structure.
        """
        logger.info("Validating form access", form_id=form_id, action="form_validation_start")
        try:
            data = await self._make_request("GET", f"forms/{form_id}")
            form_info = FormInfo(**data)
            logger.info("Form validation successful", form_title=form_info.title, action="form_validation_success")
        except ValidationError as e:
            error_msg = f"Invalid form data structure: {e}"
            field_name = "form_data"
            raise FormValidationError(field_name, str(e), error_msg) from e
        except Exception:
            logger.error("Form validation failed", exc_info=True)
            raise
        else:
            return form_info

    async def get_form(self, form_id: str) -> FormInfo:
        """Get TypeForm form information.

        Args:
            form_id: TypeForm form identifier.

        Returns:
            FormInfo object containing form details.
        """
        return await self.validate_form_access(form_id)

    async def get_form_with_retry(self, form_id: str, max_retries: int = 3) -> FormInfo:
        """Get TypeForm form information with retry logic for rate limits.

        Args:
            form_id: TypeForm form identifier.
            max_retries: Maximum number of retry attempts.

        Returns:
            FormInfo object containing form details.

        Raises:
            TypeFormRateLimitError: If rate limit exceeded after all retries.
            TypeFormAPIError: For other API errors.
        """

        for attempt in range(max_retries + 1):
            try:
                return await self.get_form(form_id)
            except TypeFormAPIError as e:
                if (
                    e.status_code == HTTP_STATUS_TOO_MANY_REQUESTS
                    and attempt < max_retries
                ):
                    wait_time = 2**attempt
                    await anyio.sleep(wait_time)
                    continue
                if e.status_code == HTTP_STATUS_TOO_MANY_REQUESTS:
                    raise TypeFormRateLimitError(
                        ERROR_MSG_RATE_LIMIT_EXCEEDED,
                        status_code=HTTP_STATUS_TOO_MANY_REQUESTS,
                        response_data=e.response_data,
                        retry_after=e.retry_after,
                    ) from e
                raise
        raise TypeFormRateLimitError(ERROR_MSG_MAX_RETRIES_EXCEEDED)

    async def get_form_with_exponential_backoff(
        self, form_id: str, max_retries: int = 3, base_delay: float = 0.1
    ) -> FormInfo:
        """Get TypeForm form information with exponential backoff retry logic.

        Args:
            form_id: TypeForm form identifier.
            max_retries: Maximum number of retry attempts.
            base_delay: Base delay in seconds for exponential backoff.

        Returns:
            FormInfo object containing form details.

        Raises:
            TypeFormRateLimitError: If rate limit exceeded after all retries.
            TypeFormAPIError: For other API errors.
        """

        for attempt in range(max_retries + 1):
            try:
                return await self.get_form(form_id)
            except TypeFormAPIError as e:
                if (
                    e.status_code == HTTP_STATUS_TOO_MANY_REQUESTS
                    and attempt < max_retries
                ):
                    wait_time = base_delay * (2**attempt)
                    await anyio.sleep(wait_time)
                    continue
                if e.status_code == HTTP_STATUS_TOO_MANY_REQUESTS:
                    raise TypeFormRateLimitError(
                        ERROR_MSG_RATE_LIMIT_EXCEEDED,
                        status_code=HTTP_STATUS_TOO_MANY_REQUESTS,
                        response_data=e.response_data,
                        retry_after=e.retry_after,
                    ) from e
                raise
        raise TypeFormRateLimitError(ERROR_MSG_MAX_RETRIES_EXCEEDED)

    async def list_webhooks(self, form_id: str) -> list[WebhookInfo]:
        """List all webhooks for a TypeForm form.

        Args:
            form_id: TypeForm form identifier.

        Returns:
            List of WebhookInfo objects for the form.
        """
        logger.info("Listing form webhooks", form_id=form_id, action="webhook_list_start")
        data = await self._make_request("GET", f"forms/{form_id}/webhooks")
        webhooks: list[WebhookInfo] = []
        for webhook_data in data.get("items", []):
            try:
                webhook = WebhookInfo(**webhook_data)
                webhooks.append(webhook)
            except ValidationError as e:
                logger.warning("Skipping invalid webhook data", error=str(e), action="webhook_validation_skip")
        logger.info("Webhooks retrieved", webhook_count=len(webhooks), form_id=form_id, action="webhook_list_complete")
        return webhooks

    async def create_webhook_with_automation(
        self,
        *,
        form_id: str,
        webhook_url: str,
        tag: str = "client_onboarding",
        enabled: bool = True,
        verify_ssl: bool = True,
        retry_attempts: int = 3,
        auto_cleanup_existing: bool = True,
    ) -> WebhookInfo:
        """Create webhook with automated retry and cleanup logic.

        Args:
            form_id: TypeForm form identifier.
            webhook_url: Webhook endpoint URL.
            tag: Webhook tag identifier.
            enabled: Whether to enable the webhook.
            verify_ssl: Whether to verify SSL certificates.
            retry_attempts: Number of retry attempts for creation.
            auto_cleanup_existing: Whether to clean up existing webhooks.

        Returns:
            WebhookInfo object for the created webhook.

        Raises:
            FormValidationError: For invalid form_id or webhook_url.
            TypeFormWebhookCreationError: For webhook creation failures.
            TypeFormFormNotFoundError: If form not found.
        """
        logger.info(
            "Creating webhook with automation",
            form_id=form_id,
            webhook_url=webhook_url,
            tag=tag,
            action="webhook_automation_start"
        )
        if not form_id or not form_id.strip():
            form_id_error = ERROR_MSG_FORM_ID_EMPTY
            field_name = "form_id"
            raise FormValidationError(field_name, "", form_id_error)
        if not webhook_url or not webhook_url.strip():
            webhook_url_error = ERROR_MSG_WEBHOOK_URL_EMPTY
            field_name = "webhook_url"
            raise FormValidationError(field_name, "", webhook_url_error)
        if not webhook_url.startswith(("http://", "https://")):
            webhook_url_invalid = ERROR_MSG_WEBHOOK_URL_INVALID
            field_name = "webhook_url"
            raise FormValidationError(field_name, webhook_url, webhook_url_invalid)
        try:
            await self.get_form(form_id)
        except TypeFormFormNotFoundError:
            logger.error(
                "Form not found, cannot create webhook",
                form_id=form_id,
                action="webhook_form_not_found",
                exc_info=True
            )
            raise TypeFormWebhookCreationError(
                webhook_url, f"Form {form_id} does not exist or is not accessible"
            ) from None
        if auto_cleanup_existing:
            try:
                existing_webhook = await self.get_webhook(form_id, tag)
                logger.info(
                    "Found existing webhook, removing",
                    webhook_id=existing_webhook.id,
                    tag=tag,
                    action="webhook_cleanup_start"
                )
                await self.delete_webhook(form_id, tag)
                logger.info(
                    "Successfully cleaned up existing webhook",
                    webhook_id=existing_webhook.id,
                    action="webhook_cleanup_success"
                )
            except (TypeFormWebhookNotFoundError, TypeFormAPIError):
                logger.debug(
                    "No existing webhook found, proceeding with creation",
                    tag=tag,
                    action="webhook_cleanup_skip"
                )
        last_error = None
        for attempt in range(1, retry_attempts + 1):
            try:
                logger.info("Webhook creation attempt", attempt=attempt, max_attempts=retry_attempts, action="webhook_create_retry")
                webhook = await self.create_webhook(
                    form_id=form_id,
                    webhook_url=webhook_url,
                    tag=tag,
                    enabled=enabled,
                    verify_ssl=verify_ssl,
                )
                verification_webhook = await self.get_webhook(form_id, tag)
                if verification_webhook.url != webhook_url:
                    logger.warning(
                        "Webhook URL mismatch after creation",
                        expected_url=webhook_url,
                        actual_url=verification_webhook.url,
                        action="webhook_url_mismatch"
                    )
                logger.info("Automated webhook creation successful", webhook_id=webhook.id, action="webhook_create_success")
                return webhook
            except Exception as e:
                last_error = e
                if attempt < retry_attempts:
                    await anyio.sleep(2**attempt)
                continue
            else:
                return webhook
        error_msg = (
            f"Failed to create webhook after {retry_attempts} attempts. "
            f"Last error: {last_error}"
        )
        logger.error(
            "Failed to create webhook after retries",
            retry_attempts=retry_attempts,
            last_error=str(last_error),
            action="webhook_create_failed"
        )
        raise TypeFormWebhookCreationError(webhook_url, error_msg)

    async def bulk_webhook_creation(
        self, webhook_configs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        logger.info(
            "Starting bulk webhook creation",
            webhook_count=len(webhook_configs),
            action="bulk_webhook_start"
        )
        results = {
            "total_requested": len(webhook_configs),
            "successful_creations": [],
            "failed_creations": [],
            "skipped_existing": [],
        }
        successful_webhooks: list[WebhookInfo] = []
        failed_webhooks: list[dict[str, Any]] = []
        for i, webhook_config in enumerate(webhook_configs):
            try:
                form_id = webhook_config.get("form_id")
                webhook_url = webhook_config.get("webhook_url")
                tag = webhook_config.get("tag", f"bulk_webhook_{i}")
                enabled = webhook_config.get("enabled", True)
                verify_ssl = webhook_config.get("verify_ssl", True)
                if not form_id or not webhook_url:
                    logger.error(
                        "Webhook config missing required fields",
                        config_index=i,
                        webhook_config=webhook_config,
                        action="bulk_webhook_config_error"
                    )
                    failed_webhooks.append(webhook_config)
                    continue
                webhook = await self.create_webhook_with_automation(
                    form_id=form_id,
                    webhook_url=webhook_url,
                    tag=tag,
                    enabled=enabled,
                    verify_ssl=verify_ssl,
                )
                successful_webhooks.append(webhook)
                logger.info(
                    "Batch webhook created successfully",
                    current=i+1,
                    total=len(webhook_configs),
                    action="bulk_webhook_progress"
                )
            except Exception:
                logger.error(
                    "Failed to create webhook in batch",
                    webhook_index=i+1,
                    action="bulk_webhook_error",
                    exc_info=True
                )
                failed_webhooks.append(webhook_config)
        results["successful_creations"] = successful_webhooks
        results["failed_creations"] = failed_webhooks
        if failed_webhooks:
            logger.warning(
                "Batch creation completed with failures",
                failed_count=len(failed_webhooks),
                total_count=len(webhook_configs),
                action="bulk_webhook_partial_success"
            )
        else:
            logger.info(
                "Batch webhook creation completed successfully",
                created_count=len(successful_webhooks),
                action="bulk_webhook_complete_success"
            )
        return results

    async def check_webhook_health(
        self, form_id: str, tag: str, *, include_delivery_stats: bool = True
    ) -> dict[str, Any]:
        logger.info("Checking webhook health", webhook_tag=tag, form_id=form_id, action="webhook_health_check")
        health_status: dict[str, Any] = {
            "webhook_id": None,
            "tag": tag,
            "form_id": form_id,
            "status": "unknown",
            "url": None,
            "enabled": False,
            "verify_ssl": False,
            "last_checked": datetime.now(UTC).isoformat(),
            "issues": [],
        }
        try:
            webhook = await self.get_webhook(form_id, tag)
            health_status["webhook_id"] = webhook.id
            health_status["tag"] = tag
            health_status["form_id"] = form_id
            health_status["status"] = "healthy" if webhook.enabled else "disabled"
            health_status["url"] = webhook.url
            health_status["enabled"] = webhook.enabled
            health_status["verify_ssl"] = webhook.verify_ssl
            health_status["last_checked"] = datetime.now(UTC).isoformat()
            health_status["issues"] = []

            try:
                # Test endpoint reachability
                try:
                    response = await self._test_webhook_endpoint(webhook.url)
                    health_status["endpoint_reachable"] = True
                    health_status["endpoint_status_code"] = response.status_code
                    if response.status_code >= HTTP_STATUS_BAD_REQUEST:
                        health_status["issues"].append(
                            f"endpoint_error_{response.status_code}"
                        )
                        health_status["endpoint_reachable"] = False
                    else:
                        health_status["endpoint_reachable"] = True
                except Exception as e:
                    health_status["endpoint_reachable"] = False
                    health_status["endpoint_error"] = str(e)

                # Get delivery statistics if requested
                if include_delivery_stats:
                    try:
                        delivery_stats = await self._get_webhook_delivery_stats(
                            form_id, tag
                        )
                        health_status["delivery_stats"] = delivery_stats
                    except Exception as e:
                        health_status["delivery_stats_error"] = str(e)
                logger.info(
                    "Webhook health check completed",
                    status=health_status['status'],
                    action="webhook_health_complete"
                )
            except Exception:
                logger.error(
                    "Failed to check webhook health",
                    tag=tag,
                    action="webhook_health_error",
                    exc_info=True
                )
                raise
            else:
                return health_status
        except Exception as e:
            logger.error(
                "Failed to check webhook health",
                tag=tag,
                action="webhook_health_error",
                exc_info=True
            )
            return {
                "webhook_id": None,
                "tag": tag,
                "form_id": form_id,
                "status": "error",
                "last_checked": datetime.now(UTC).isoformat(),
                "error": str(e),
                "issues": ["health_check_failed"],
            }

    async def monitor_webhooks_health(
        self, form_ids: list[str], tag_filter: str | None = None
    ) -> dict[str, Any]:
        logger.info("Starting webhook health monitoring", form_count=len(form_ids), action="health_monitoring_start")
        health_reports: dict[str, Any] = {}
        overall_stats = {
            "total_webhooks": 0,
            "healthy_webhooks": 0,
            "degraded_webhooks": 0,
            "unhealthy_webhooks": 0,
            "error_webhooks": 0,
        }
        for form_id in form_ids:
            try:
                webhooks = await self.list_webhooks(form_id)
                form_health_reports: list[dict[str, Any]] = []
                for webhook in webhooks:
                    if tag_filter and webhook.tag != tag_filter:
                        continue
                    health_report = await self.check_webhook_health(
                        form_id=form_id, tag=webhook.tag, include_delivery_stats=False
                    )
                    form_health_reports.append(health_report)
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
                logger.error(
                    "Failed to monitor webhooks for form",
                    form_id=form_id,
                    action="webhook_monitoring_error",
                    exc_info=True
                )
                health_reports[form_id] = [
                    {
                        "webhook_id": None,
                        "tag": "unknown",
                        "form_id": form_id,
                        "status": "error",
                        "error": str(e),
                        "issues": ["monitoring_failed"],
                    }
                ]
                overall_stats["error_webhooks"] += 1
        # Attach summary as a dedicated keys with proper types
        health_reports_summary: dict[str, Any] = overall_stats
        health_reports["_summary"] = health_reports_summary
        health_reports["_monitoring_timestamp"] = datetime.now(UTC).isoformat()
        logger.info("Webhook health monitoring completed", overall_stats=overall_stats, action="health_monitoring_complete")
        return health_reports

    async def _get_webhook_delivery_stats(
        self, _form_id: str, _tag: str
    ) -> dict[str, Any]:
        return {
            "available": False,
            "reason": ERROR_MSG_WEBHOOK_DELIVERY_STATS_UNAVAILABLE,
            "last_attempted": datetime.now(UTC).isoformat(),
        }

    async def create_webhook(
        self,
        form_id: str,
        webhook_url: str,
        tag: str,
        *,
        enabled: bool = True,
        verify_ssl: bool = True,
    ) -> WebhookInfo:
        """Create a new webhook for a TypeForm form.

        Args:
            form_id: TypeForm form identifier.
            webhook_url: Webhook endpoint URL.
            tag: Webhook tag identifier.
            enabled: Whether to enable the webhook.
            verify_ssl: Whether to verify SSL certificates.

        Returns:
            WebhookInfo object for the created webhook.

        Raises:
            FormValidationError: For invalid webhook response data.
            TypeFormWebhookCreationError: For webhook creation failures.
        """
        logger.info("Creating webhook", form_id=form_id, webhook_tag=tag, action="webhook_create_start")
        webhook_data = {
            "url": webhook_url,
            "enabled": enabled,
            "verify_ssl": verify_ssl,
            "tag": tag,
        }
        try:
            data = await self._make_request(
                "PUT", f"forms/{form_id}/webhooks/{tag}", json=webhook_data
            )
            webhook = WebhookInfo(**data)
            logger.info("Webhook created successfully", webhook_id=webhook.id, action="webhook_create_success")
        except ValidationError as e:
            webhook_data_error = f"Invalid webhook response data: {e}"
            field_name = "webhook_data"
            raise FormValidationError(field_name, str(e), webhook_data_error) from e
        except TypeFormAPIError as e:
            webhook_creation_error = f"Failed to create webhook: {e.message}"
            raise TypeFormWebhookCreationError(
                webhook_url, webhook_creation_error
            ) from e
        else:
            return webhook

    async def update_webhook(
        self,
        form_id: str,
        tag: str,
        webhook_url: str | None = None,
        *,
        enabled: bool | None = None,
        verify_ssl: bool | None = None,
    ) -> WebhookInfo:
        """Update webhook configuration using delete+create strategy.

        Args:
            form_id: TypeForm form identifier.
            tag: Webhook tag identifier.
            webhook_url: New webhook URL (optional).
            enabled: New enabled status (optional).
            verify_ssl: New SSL verification status (optional).

        Returns:
            WebhookInfo object for the updated webhook.

        Raises:
            FormValidationError: For invalid webhook properties or response data.
            TypeFormWebhookNotFoundError: If webhook not found.
            TypeFormFormNotFoundError: If form not found.
        """
        logger.info("Updating webhook via delete+create", webhook_tag=tag, form_id=form_id, action="webhook_update_start")

        if not any([webhook_url, enabled is not None, verify_ssl is not None]):
            webhook_props_error = ERROR_MSG_WEBHOOK_PROPERTIES_REQUIRED
            field_name = "webhook_properties"
            raise FormValidationError(
                field_name,
                "",
                webhook_props_error,
            )
        try:
            existing_webhook = await self.get_webhook(form_id, tag)
            final_url = webhook_url if webhook_url is not None else existing_webhook.url
            final_enabled = enabled if enabled is not None else existing_webhook.enabled
            final_verify_ssl = (
                verify_ssl if verify_ssl is not None else existing_webhook.verify_ssl
            )
            await self.delete_webhook(form_id, tag)
            webhook = await self.create_webhook(
                form_id=form_id,
                webhook_url=final_url,
                tag=tag,
                enabled=final_enabled,
                verify_ssl=final_verify_ssl,
            )
            logger.info("Webhook update successful", webhook_id=webhook.id, method="delete_create", action="webhook_update_success")
        except TypeFormWebhookNotFoundError:
            raise TypeFormFormNotFoundError(form_id) from None
        except ValidationError as e:
            webhook_data_error = f"Invalid webhook response data: {e}"
            field_name = "webhook_data"
            raise FormValidationError(field_name, str(e), webhook_data_error) from e
        else:
            return webhook

    async def delete_webhook(self, form_id: str, tag: str) -> bool:
        """Delete a webhook from a TypeForm form.

        Args:
            form_id: TypeForm form identifier.
            tag: Webhook tag identifier.

        Returns:
            True if webhook was deleted successfully.

        Raises:
            TypeFormWebhookNotFoundError: If webhook not found.
        """
        logger.info(
            "Deleting webhook",
            webhook_tag=tag,
            form_id=form_id,
            action="webhook_delete_start",
        )
        await self._enforce_rate_limit()
        path = f"forms/{form_id}/webhooks/{tag}"

        url = self._build_url(path)
        logger.debug("Making DELETE request", url=url, action="http_delete")
        response = await self.client.delete(url)
        if response.status_code == HTTP_STATUS_NO_CONTENT:
            logger.info(
                "Webhook deleted successfully",
                webhook_tag=tag,
                action="webhook_delete_success",
            )
            return True
        if response.status_code == HTTP_STATUS_NOT_FOUND:
            raise TypeFormWebhookNotFoundError(tag)
        self._handle_response(response)
        return False

    async def get_webhook(self, form_id: str, tag: str) -> WebhookInfo:
        """Get webhook information for a TypeForm form.

        Args:
            form_id: TypeForm form identifier.
            tag: Webhook tag identifier.

        Returns:
            WebhookInfo object containing webhook details.

        Raises:
            FormValidationError: For invalid webhook response data.
        """
        logger.info("Retrieving webhook", webhook_tag=tag, form_id=form_id, action="webhook_get_start")
        try:
            data = await self._make_request("GET", f"forms/{form_id}/webhooks/{tag}")
            webhook = WebhookInfo(**data)
            logger.info("Webhook retrieved successfully", webhook_id=webhook.id, action="webhook_get_success")
        except ValidationError as e:
            webhook_data_error = f"Invalid webhook response data: {e}"
            field_name = "webhook_data"
            raise FormValidationError(field_name, str(e), webhook_data_error) from e
        else:
            return webhook

    async def _test_webhook_endpoint(self, url: str) -> httpx.Response:
        """Test if a webhook endpoint is reachable and return the response.

        Args:
            url: Webhook endpoint URL to test.

        Returns:
            HTTP response from the endpoint.

        Raises:
            httpx.ConnectError: For connection errors.
            httpx.RequestError: For request errors.
        """
        try:
            response = await self.client.request("HEAD", url, timeout=10.0)
        except httpx.ConnectError:
            logger.error(
                "Connect error during webhook endpoint test",
                url=url,
                action="webhook_endpoint_connect_error",
                exc_info=True
            )
            raise
        except httpx.RequestError:
            logger.error(
                "Request error during webhook endpoint test",
                url=url,
                action="webhook_endpoint_request_error",
                exc_info=True
            )
            raise
        else:
            return response


def create_typeform_client(api_key: str | None = None) -> TypeFormClient:
    """Create a new TypeForm client instance.

    Args:
        api_key: Optional API key override. Uses config default if not provided.

    Returns:
        Configured TypeFormClient instance.
    """
    return TypeFormClient(api_key=api_key)
