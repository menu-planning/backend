from __future__ import annotations

# Relocated content from services/typeform_client.py

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import boto3
from boto3.session import Session as Boto3Session
from botocore.config import Config as BotoConfig
from anyio import to_thread
from urllib.parse import urljoin
from collections import deque

import httpx
import anyio
from pydantic import BaseModel, ValidationError, ConfigDict

from src.contexts.client_onboarding.config import config
from src.logging.logger import correlation_id_ctx
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
    def __init__(self, requests_per_second: float):
        if requests_per_second <= 0:
            raise ValueError("Rate limit must be positive")
        if requests_per_second > 10:
            logger.warning("Rate limit of %s req/sec may exceed TypeForm API limits", requests_per_second)
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.request_timestamps: deque = deque(maxlen=100)
        self.lock = anyio.Lock()
        self.last_request_time = 0.0

    def validate_rate_limit_config(self) -> Dict[str, Any]:
        validation_result = {
            "is_valid": True,
            "rate_limit": self.requests_per_second,
            "min_interval_ms": self.min_interval * 1000,
            "warnings": [],
            "recommendations": [],
        }
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
        async with self.lock:
            current_time = time.time()
            recent_requests = [ts for ts in self.request_timestamps if current_time - ts <= 60]
            actual_rate = len(recent_requests) / 60.0
            compliance_percentage = (
                min(100, (self.requests_per_second / max(actual_rate, 0.001)) * 100) if actual_rate > 0 else 100
            )
            return {
                "configured_rate_limit": self.requests_per_second,
                "actual_rate_60s": round(actual_rate, 3),
                "total_requests_tracked": len(self.request_timestamps),
                "compliance_percentage": round(compliance_percentage, 1),
                "is_compliant": actual_rate <= self.requests_per_second,
                "time_to_next_request": max(0, self.min_interval - (current_time - self.last_request_time)),
                "last_request_time": self.last_request_time,
            }

    async def reset_rate_limit_tracking(self) -> None:
        async with self.lock:
            self.request_timestamps.clear()
            self.last_request_time = 0.0


class FormInfo(BaseModel):
    id: str
    title: str
    type: str
    workspace: Dict[str, Any]
    theme: Dict[str, Any]
    settings: Dict[str, Any]
    welcome_screens: List[Dict[str, Any]]
    thankyou_screens: List[Dict[str, Any]]
    fields: List[Dict[str, Any]]
    hidden: Optional[List[str]] = None
    variables: Optional[Dict[str, Any]] = None
    model_config = ConfigDict(extra="allow")


class WebhookInfo(BaseModel):
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
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or config.typeform_api_key
        self.base_url = base_url or config.typeform_api_base_url
        if not self.api_key:
            raise TypeFormAuthenticationError("TypeForm API key is required")
        # Proxy configuration
        self.use_proxy: bool = getattr(config, "typeform_via_proxy", False)
        self.proxy_function_name: Optional[str] = getattr(config, "typeform_proxy_function_name", "") or None
        if self.use_proxy and self.proxy_function_name:
            # Create a Lambda client with fast-fail timeouts to avoid hangs
            # - connect_timeout: quick network failure detection
            # - read_timeout: upper bound for Invoke
            # - retries: 1 attempt to avoid long backoffs
            session = Boto3Session()
            region_name = session.region_name or None
            boto_cfg = BotoConfig(connect_timeout=3, read_timeout=10, retries={"max_attempts": 1})
            self.lambda_client = boto3.client("lambda", region_name=region_name, config=boto_cfg)
        else:
            self.lambda_client = None
        self.rate_limit_validator = RateLimitValidator(config.typeform_rate_limit_requests_per_second)
        rate_limit_validation = self.rate_limit_validator.validate_rate_limit_config()
        if rate_limit_validation["warnings"]:
            for warning in rate_limit_validation["warnings"]:
                logger.warning("Rate limit validation: %s", warning)
        logger.info(
            "TypeFormClient initialized with rate limit: %s req/sec (min interval: %.3f ms)",
            self.rate_limit_validator.requests_per_second,
            self.rate_limit_validator.min_interval * 1000,
        )
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        timeout = httpx.Timeout(
            connect=5.0,
            read=config.typeform_timeout_seconds,
            write=10.0,
            pool=5.0,
        )
        limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=timeout,
            limits=limits,
            follow_redirects=True,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def close(self):
        await self.client.aclose()

    async def _enforce_rate_limit(self) -> None:
        await self.rate_limit_validator.enforce_rate_limit()

    async def get_rate_limit_status(self) -> Dict[str, Any]:
        return await self.rate_limit_validator.get_rate_limit_status()

    async def validate_rate_limit_compliance(self) -> bool:
        status = await self.get_rate_limit_status()
        return status["is_compliant"]

    async def reset_rate_limit_tracking(self) -> None:
        await self.rate_limit_validator.reset_rate_limit_tracking()
        logger.info("Rate limit tracking reset")

    def _build_url(self, endpoint: str) -> str:
        return urljoin(f"{self.base_url}/", endpoint.lstrip("/"))

    def _handle_response(self, response: Any) -> Dict[str, Any]:
        try:
            data = response.json()
        except Exception:
            data = {"message": response.text}
        if response.status_code == 200:
            return data
        elif response.status_code == 401:
            raise TypeFormAuthenticationError("Invalid API key or authentication failed", status_code=response.status_code, response_data=data)
        elif response.status_code == 403:
            raise TypeFormAuthenticationError("Access forbidden - insufficient permissions", status_code=response.status_code, response_data=data)
        elif response.status_code == 404:
            raise TypeFormFormNotFoundError("unknown", status_code=response.status_code, response_data=data)
        elif response.status_code == 422:
            raise FormValidationError("validation", data.get('message', 'Invalid request data'), f"Validation error: {data.get('message', 'Invalid request data')}", status_code=response.status_code, response_data=data)
        elif response.status_code == 429:
            retry_after = None
            retry_after_header = response.headers.get("Retry-After")
            if retry_after_header:
                try:
                    retry_after = int(retry_after_header)
                except ValueError:
                    logger.warning(f"Could not parse Retry-After header: {retry_after_header}")
            if retry_after:
                logger.warning(f"TypeForm API rate limit exceeded (429), retry after {retry_after} seconds")
            else:
                logger.warning("TypeForm API rate limit exceeded (429)")
            raise TypeFormAPIError(
                f"Rate limit exceeded: {data.get('message', 'Too many requests')}",
                status_code=response.status_code,
                response_data=data,
                retry_after=retry_after,
            )
        else:
            raise TypeFormAPIError(
                f"API request failed: {data.get('message', 'Unknown error')}",
                status_code=response.status_code,
                response_data=data,
            )

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        await self._enforce_rate_limit()
        if self.use_proxy and self.lambda_client and self.proxy_function_name:
            proxy_response = await self._invoke_proxy_raw(method=method, endpoint=endpoint, **kwargs)
            # Reuse existing response handling via a lightweight adapter
            class _ProxyResponseAdapter:
                def __init__(self, status_code: int, headers: Dict[str, Any], text: str):
                    self.status_code = status_code
                    self.headers = headers
                    self.text = text

                def json(self) -> Dict[str, Any]:
                    return json.loads(self.text)

            adapted = _ProxyResponseAdapter(
                status_code=proxy_response["status_code"],
                headers=proxy_response.get("headers", {}),
                text=proxy_response.get("text", ""),
            )
            logger.info(
                "HTTP %s %s (via proxy) -> %s",
                method,
                self._build_url(endpoint),
                adapted.status_code,
            )
            return self._handle_response(adapted)
        else:
            url = self._build_url(endpoint)
            logger.debug("Making %s request to %s", method, url)
            try:
                response = await self.client.request(method, url, **kwargs)
            except httpx.ConnectError as e:
                logger.error("Connect error during %s %s: %s", method, url, str(e))
                raise
            logger.info("HTTP %s %s -> %s", method, url, response.status_code)
            return self._handle_response(response)

    async def _invoke_proxy_raw(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        if not (self.lambda_client and self.proxy_function_name):
            raise TypeFormAPIError("Proxy not configured")
        # Extract body and params in a generic way
        body_text: Optional[str] = None
        if "json" in kwargs and kwargs["json"] is not None:
            body_text = json.dumps(kwargs["json"])  # type: ignore[no-any-return]
        elif "data" in kwargs and kwargs["data"] is not None:
            data_obj = kwargs["data"]
            if isinstance(data_obj, str):
                body_text = data_obj
            elif isinstance(data_obj, (bytes, bytearray, memoryview)):
                body_bytes = bytes(data_obj)
                body_text = body_bytes.decode("utf-8")
            else:
                body_text = json.dumps(data_obj)
        params = kwargs.get("params", {}) or {}
        hdrs = kwargs.get("headers", {}) or {}
        # Merge with default client headers
        outbound_headers = {**self.headers, **hdrs}
        # Pull correlation id from logging context
        try:
            correlation_id = correlation_id_ctx.get()
        except Exception:
            correlation_id = None
        event = {
            "method": method,
            "path": f"/{endpoint.lstrip('/')}",
            "query": params,
            "headers": outbound_headers,
            "body": body_text,
            "correlation_id": correlation_id,
        }

        def _invoke():
            client = self.lambda_client
            if client is None:
                raise TypeFormAPIError("Proxy not configured (no client)")
            response = client.invoke(
                FunctionName=self.proxy_function_name,  # type: ignore[arg-type]
                InvocationType="RequestResponse",
                Payload=json.dumps(event).encode("utf-8"),
            )
            payload_stream = response.get("Payload")
            raw = payload_stream.read().decode("utf-8") if payload_stream else "{}"
            try:
                result = json.loads(raw)
            except Exception:
                result = {"statusCode": 502, "headers": {"content-type": "application/json"}, "body": raw}
            status_code = int(result.get("statusCode", 502))
            headers = result.get("headers", {}) or {}
            text = result.get("body", "") or ""
            return {"status_code": status_code, "headers": headers, "text": text}

        try:
            # Enforce an overall timeout to prevent indefinite waits
            with anyio.fail_after(12.0):
                proxy_result = await to_thread.run_sync(_invoke)
        except TimeoutError:
            raise TypeFormAPIError(
                "Lambda Invoke timed out",
                status_code=503,
                response_data={"message": "proxy_invoke_timeout"},
            )
        return proxy_result

    async def validate_form_access(self, form_id: str) -> FormInfo:
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
        return await self.validate_form_access(form_id)

    async def get_form_with_retry(self, form_id: str, max_retries: int = 3) -> FormInfo:
        from src.contexts.client_onboarding.core.services.exceptions import TypeFormRateLimitError
        for attempt in range(max_retries + 1):
            try:
                return await self.get_form(form_id)
            except TypeFormAPIError as e:
                if e.status_code == 429 and attempt < max_retries:
                    wait_time = 2 ** attempt
                    await anyio.sleep(wait_time)
                    continue
                elif e.status_code == 429:
                    raise TypeFormRateLimitError(
                        "Rate limit exceeded",
                        status_code=429,
                        response_data=e.response_data,
                        retry_after=e.retry_after,
                    )
                else:
                    raise
        raise TypeFormRateLimitError("Max retries exceeded")

    async def get_form_with_exponential_backoff(self, form_id: str, max_retries: int = 3, base_delay: float = 0.1) -> FormInfo:
        from src.contexts.client_onboarding.core.services.exceptions import TypeFormRateLimitError
        for attempt in range(max_retries + 1):
            try:
                return await self.get_form(form_id)
            except TypeFormAPIError as e:
                if e.status_code == 429 and attempt < max_retries:
                    wait_time = base_delay * (2 ** attempt)
                    await anyio.sleep(wait_time)
                    continue
                elif e.status_code == 429:
                    raise TypeFormRateLimitError(
                        "Rate limit exceeded",
                        status_code=429,
                        response_data=e.response_data,
                        retry_after=e.retry_after,
                    )
                else:
                    raise
        raise TypeFormRateLimitError("Max retries exceeded")

    async def list_webhooks(self, form_id: str) -> List[WebhookInfo]:
        logger.info(f"Listing webhooks for form: {form_id}")
        data = await self._make_request("GET", f"forms/{form_id}/webhooks")
        webhooks: List[WebhookInfo] = []
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
        auto_cleanup_existing: bool = True,
    ) -> WebhookInfo:
        logger.info(f"Starting automated webhook creation for form {form_id}: {webhook_url}")
        if not form_id or not form_id.strip():
            raise FormValidationError("form_id", "", "form_id cannot be empty")
        if not webhook_url or not webhook_url.strip():
            raise FormValidationError("webhook_url", "", "webhook_url cannot be empty")
        if not webhook_url.startswith(('http://', 'https://')):
            raise FormValidationError("webhook_url", webhook_url, "webhook_url must be a valid HTTP/HTTPS URL")
        try:
            await self.get_form(form_id)
        except TypeFormFormNotFoundError:
            logger.error(f"Form {form_id} not found, cannot create webhook")
            raise TypeFormWebhookCreationError(webhook_url, f"Form {form_id} does not exist or is not accessible")
        if auto_cleanup_existing:
            try:
                existing_webhook = await self.get_webhook(form_id, tag)
                logger.info(f"Found existing webhook {existing_webhook.id} with tag {tag}, removing...")
                await self.delete_webhook(form_id, tag)
                logger.info(f"Successfully cleaned up existing webhook {existing_webhook.id}")
            except (TypeFormWebhookNotFoundError, TypeFormAPIError):
                logger.debug(f"No existing webhook found with tag {tag}, proceeding with creation")
        last_error = None
        for attempt in range(1, retry_attempts + 1):
            try:
                logger.info(f"Webhook creation attempt {attempt}/{retry_attempts}")
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
                        f"Webhook URL mismatch after creation: expected {webhook_url}, got {verification_webhook.url}"
                    )
                logger.info(f"Automated webhook creation successful: {webhook.id}")
                return webhook
            except Exception as e:
                last_error = e
                logger.warning(f"Webhook creation attempt {attempt} failed: {e}")
                if attempt < retry_attempts:
                    await anyio.sleep(2 ** attempt)
        error_msg = f"Failed to create webhook after {retry_attempts} attempts. Last error: {last_error}"
        logger.error(error_msg)
        raise TypeFormWebhookCreationError(webhook_url, error_msg)

    async def bulk_webhook_creation(self, webhook_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info(f"Starting bulk webhook creation for {len(webhook_configs)} webhooks")
        results = {"total_requested": len(webhook_configs), "successful_creations": [], "failed_creations": [], "skipped_existing": []}
        successful_webhooks: List[WebhookInfo] = []
        failed_webhooks: List[Dict[str, Any]] = []
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
                    verify_ssl=verify_ssl,
                )
                successful_webhooks.append(webhook)
                logger.info(f"Batch webhook {i+1}/{len(webhook_configs)} created successfully")
            except Exception as e:
                logger.error(f"Failed to create webhook {i+1}: {e}")
                failed_webhooks.append(webhook_config)
        results["successful_creations"] = successful_webhooks
        results["failed_creations"] = failed_webhooks
        if failed_webhooks:
            logger.warning(
                f"Batch creation completed with {len(failed_webhooks)} failures out of {len(webhook_configs)} total"
            )
        else:
            logger.info(
                f"Batch webhook creation completed successfully: {len(successful_webhooks)} webhooks created"
            )
        return results

    async def check_webhook_health(self, form_id: str, tag: str, include_delivery_stats: bool = True) -> Dict[str, Any]:
        logger.info(f"Checking health for webhook {tag} on form {form_id}")
        try:
            webhook = await self.get_webhook(form_id, tag)
            health_status: Dict[str, Any] = {
                "webhook_id": webhook.id,
                "tag": tag,
                "form_id": form_id,
                "status": "healthy" if webhook.enabled else "disabled",
                "url": webhook.url,
                "enabled": webhook.enabled,
                "verify_ssl": webhook.verify_ssl,
                "last_checked": datetime.now().isoformat(),
                "issues": [],
            }
            if not webhook.url:
                health_status["issues"].append("webhook_url_missing")
                health_status["status"] = "unhealthy"
            elif not webhook.url.startswith(('http://', 'https://')):
                health_status["issues"].append("invalid_webhook_url_scheme")
                health_status["status"] = "unhealthy"
            try:
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
                "issues": ["health_check_failed"],
            }

    async def monitor_webhooks_health(self, form_ids: List[str], tag_filter: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"Starting webhook health monitoring for {len(form_ids)} forms")
        health_reports: Dict[str, Any] = {}
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
                form_health_reports: List[Dict[str, Any]] = []
                for webhook in webhooks:
                    if tag_filter and webhook.tag != tag_filter:
                        continue
                    health_report = await self.check_webhook_health(form_id=form_id, tag=webhook.tag, include_delivery_stats=False)
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
                logger.error(f"Failed to monitor webhooks for form {form_id}: {e}")
                health_reports[form_id] = [{
                    "webhook_id": None,
                    "tag": "unknown",
                    "form_id": form_id,
                    "status": "error",
                    "error": str(e),
                    "issues": ["monitoring_failed"],
                }]
                overall_stats["error_webhooks"] += 1
        # Attach summary as a dedicated keys with proper types
        health_reports_summary: Dict[str, Any] = overall_stats
        health_reports["_summary"] = health_reports_summary
        health_reports["_monitoring_timestamp"] = datetime.now().isoformat()
        logger.info(f"Webhook health monitoring completed: {overall_stats}")
        return health_reports

    async def _get_webhook_delivery_stats(self, form_id: str, tag: str) -> Dict[str, Any]:
        return {
            "available": False,
            "reason": "TypeForm API does not currently provide webhook delivery statistics",
            "last_attempted": datetime.now().isoformat(),
        }

    async def create_webhook(self, form_id: str, webhook_url: str, tag: str, enabled: bool = True, verify_ssl: bool = True) -> WebhookInfo:
        logger.info(f"Creating webhook for form {form_id} with tag {tag}")
        webhook_data = {"url": webhook_url, "enabled": enabled, "verify_ssl": verify_ssl, "tag": tag}
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
        logger.info(f"Updating webhook {tag} for form {form_id} (using delete+create)")
        from src.contexts.client_onboarding.core.services.exceptions import FormValidationError as _FormValidationError
        if not any([webhook_url is not None, enabled is not None, verify_ssl is not None]):
            raise _FormValidationError("webhook_properties", "", "At least one webhook property must be provided for update")
        try:
            existing_webhook = await self.get_webhook(form_id, tag)
            final_url = webhook_url if webhook_url is not None else existing_webhook.url
            final_enabled = enabled if enabled is not None else existing_webhook.enabled
            final_verify_ssl = verify_ssl if verify_ssl is not None else existing_webhook.verify_ssl
            await self.delete_webhook(form_id, tag)
            webhook = await self.create_webhook(
                form_id=form_id,
                webhook_url=final_url,
                tag=tag,
                enabled=final_enabled,
                verify_ssl=final_verify_ssl,
            )
            logger.info(f"Successfully updated webhook via delete+create: {webhook.id}")
            return webhook
        except TypeFormWebhookNotFoundError:
            raise TypeFormFormNotFoundError(form_id)
        except ValidationError as e:
            raise _FormValidationError("webhook_data", str(e), f"Invalid webhook response data: {e}")

    async def delete_webhook(self, form_id: str, tag: str) -> bool:
        logger.info(f"Deleting webhook {tag} for form {form_id}")
        await self._enforce_rate_limit()
        path = f"forms/{form_id}/webhooks/{tag}"
        if self.use_proxy and self.lambda_client and self.proxy_function_name:
            proxy_response = await self._invoke_proxy_raw(method="DELETE", endpoint=path)
            if proxy_response["status_code"] == 204:
                logger.info(f"Successfully deleted webhook: {tag}")
                return True
            elif proxy_response["status_code"] == 404:
                raise TypeFormWebhookNotFoundError(tag)
            else:
                # let standard handler raise if needed
                class _ProxyResponseAdapter:
                    def __init__(self, status_code: int, headers: Dict[str, Any], text: str):
                        self.status_code = status_code
                        self.headers = headers
                        self.text = text

                    def json(self) -> Dict[str, Any]:
                        return json.loads(self.text)
                adapted = _ProxyResponseAdapter(
                    status_code=proxy_response["status_code"],
                    headers=proxy_response.get("headers", {}),
                    text=proxy_response.get("text", ""),
                )
                self._handle_response(adapted)
                return False
        else:
            url = self._build_url(path)
            logger.debug("Making DELETE request to %s", url)
            response = await self.client.delete(url)
            if response.status_code == 204:
                logger.info(f"Successfully deleted webhook: {tag}")
                return True
            elif response.status_code == 404:
                raise TypeFormWebhookNotFoundError(tag)
            else:
                self._handle_response(response)
                return False

    async def get_webhook(self, form_id: str, tag: str) -> WebhookInfo:
        logger.info(f"Retrieving webhook {tag} for form {form_id}")
        try:
            data = await self._make_request("GET", f"forms/{form_id}/webhooks/{tag}")
            webhook = WebhookInfo(**data)
            logger.info(f"Successfully retrieved webhook: {webhook.id}")
            return webhook
        except ValidationError as e:
            raise FormValidationError("webhook_data", str(e), f"Invalid webhook response data: {e}")


def create_typeform_client(api_key: Optional[str] = None) -> TypeFormClient:
    return TypeFormClient(api_key=api_key)


