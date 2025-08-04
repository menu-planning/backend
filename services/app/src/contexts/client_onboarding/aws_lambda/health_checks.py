"""
Client Onboarding System Health Check Lambda

Comprehensive health check Lambda for monitoring webhook health and processing status
for observability. Verifies container, database, TypeForm API, and service health.
"""

from typing import Any, Dict, List, Optional
import json
import anyio
from datetime import UTC, datetime
from dataclasses import dataclass, asdict, field

from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.client_onboarding.core.adapters.middleware.logging_middleware import (
    create_api_logging_middleware
)
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler
)
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id
from src.contexts.client_onboarding.config import config

from .CORS_headers import CORS_headers

# Initialize container and middleware
container = Container()
logging_middleware = create_api_logging_middleware()


@dataclass
class HealthCheckResult:
    """Result of a single health check component."""
    component: str
    status: str  # "healthy", "unhealthy", "warning"
    message: str
    response_time_ms: float
    details: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class SystemHealthCheck:
    """Overall system health check result."""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    version: str
    components: List[HealthCheckResult]
    overall_response_time_ms: float
    correlation_id: str


async def check_container_health() -> HealthCheckResult:
    """Check container bootstrap health."""
    start_time = datetime.now(UTC)
    
    try:
        # Test container bootstrap
        container.bootstrap()
        
        response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
        return HealthCheckResult(
            component="container_bootstrap",
            status="healthy",
            message="Container bootstrap successful",
            response_time_ms=response_time,
            details={"bootstrap_method": "dependency_injection"}
        )
    except Exception as e:
        response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
        return HealthCheckResult(
            component="container_bootstrap",
            status="unhealthy",
            message=f"Container bootstrap failed: {str(e)}",
            response_time_ms=response_time,
            details={"error_type": type(e).__name__}
        )


async def check_database_health() -> HealthCheckResult:
    """Check database connectivity and repository health."""
    start_time = datetime.now(UTC)
    
    try:
        async with container.get_uow() as uow:
            # Test database connection by attempting a simple query
            # This will test both connection and repository functionality
            await uow.onboarding_forms.count_by_user(user_id=None)  # Count query doesn't need user_id
            
        response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
        return HealthCheckResult(
            component="database",
            status="healthy",
            message="Database connection and repositories healthy",
            response_time_ms=response_time,
            details={"connection_type": "async_postgresql"}
        )
    except Exception as e:
        response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
        return HealthCheckResult(
            component="database",
            status="unhealthy",
            message=f"Database health check failed: {str(e)}",
            response_time_ms=response_time,
            details={"error_type": type(e).__name__}
        )


async def check_typeform_api_health() -> HealthCheckResult:
    """
    Check TypeForm API connectivity and rate limit status.
    
    Returns:
        HealthCheckResult with TypeForm API status
    """
    start_time = datetime.now(UTC)
    
    try:
        logger.info("Checking TypeForm API health")
        
        async with container.typeform_client() as typeform_client:
            # Check rate limit status first
            rate_limit_status = await typeform_client.get_rate_limit_status()
            
            # Verify rate limit compliance
            is_compliant = await typeform_client.validate_rate_limit_compliance()
            
            # Try to make a simple API call (using a test form ID if available)
            test_form_id = getattr(config, "test_form_id", None)  # Optional test form for health checks
            api_accessible = True
            api_error = None
            
            if test_form_id:
                try:
                    await typeform_client.validate_form_access(test_form_id)
                    logger.info(f"Successfully validated test form access: {test_form_id}")
                except Exception as e:
                    api_accessible = False
                    api_error = str(e)
                    logger.warning(f"Test form validation failed: {e}")
            
            # Determine overall health status
            if is_compliant and api_accessible:
                status = "healthy"
                message = "TypeForm API is healthy and rate limits compliant"
            elif is_compliant and not api_accessible and test_form_id:
                status = "degraded"  # Rate limits OK but API issues
                message = "TypeForm API rate limits OK but test form access failed"
            elif not is_compliant:
                status = "unhealthy"  # Rate limit issues
                message = "TypeForm API rate limit non-compliant"
            else:
                status = "healthy"  # No test form configured, but rate limits are good
                message = "TypeForm API rate limits compliant (no test form configured)"
            
            response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            return HealthCheckResult(
                component="typeform_api",
                status=status,
                message=message,
                response_time_ms=response_time,
                details={
                    "rate_limit_status": rate_limit_status,
                    "rate_limit_compliant": is_compliant,
                    "api_accessible": api_accessible,
                    "api_error": api_error,
                    "test_form_configured": test_form_id is not None
                }
            )
            
    except Exception as e:
        response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
        logger.error(f"TypeForm API health check failed: {e}")
        return HealthCheckResult(
            component="typeform_api",
            status="unhealthy",
            message=f"TypeForm API health check failed: {str(e)}",
            response_time_ms=response_time,
            details={"error": str(e)}
        )


async def check_webhook_processing_health() -> HealthCheckResult:
    """Check webhook processing service health."""
    start_time = datetime.now(UTC)
    
    try:
        # Test webhook processing services by verifying they can be instantiated
        from src.contexts.client_onboarding.core.services.response_parser import ResponseDataParser
        from src.contexts.client_onboarding.core.services.client_identifier_extractor import ClientIdentifierExtractor
        from src.contexts.client_onboarding.core.services.response_transformer import ResponseTransformer
        
        # Test service instantiation
        parser = ResponseDataParser()
        extractor = ClientIdentifierExtractor()
        transformer = ResponseTransformer()
        
        response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
        return HealthCheckResult(
            component="webhook_processing",
            status="healthy",
            message="Webhook processing services healthy",
            response_time_ms=response_time,
            details={
                "services_available": ["ResponseDataParser", "ClientIdentifierExtractor", "ResponseTransformer"]
            }
        )
    except Exception as e:
        response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
        return HealthCheckResult(
            component="webhook_processing",
            status="unhealthy",
            message=f"Webhook processing health check failed: {str(e)}",
            response_time_ms=response_time,
            details={"error_type": type(e).__name__}
        )


async def check_middleware_health() -> HealthCheckResult:
    """Check middleware layer health."""
    start_time = datetime.now(UTC)
    
    try:
        # Test middleware instantiation
        from src.contexts.client_onboarding.core.adapters.middleware.error_middleware import ClientOnboardingErrorMiddleware
        from src.contexts.client_onboarding.core.adapters.middleware.auth_middleware import ClientOnboardingAuthMiddleware
        
        # Test middleware can be created
        error_middleware = ClientOnboardingErrorMiddleware()
        auth_middleware = ClientOnboardingAuthMiddleware()
        
        response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
        return HealthCheckResult(
            component="middleware",
            status="healthy",
            message="Middleware layer healthy",
            response_time_ms=response_time,
            details={
                "middleware_available": ["ErrorMiddleware", "AuthMiddleware", "LoggingMiddleware"]
            }
        )
    except Exception as e:
        response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
        return HealthCheckResult(
            component="middleware",
            status="unhealthy",
            message=f"Middleware health check failed: {str(e)}",
            response_time_ms=response_time,
            details={"error_type": type(e).__name__}
        )


def determine_overall_status(components: List[HealthCheckResult]) -> str:
    """Determine overall system health status based on component results."""
    unhealthy_count = sum(1 for c in components if c.status == "unhealthy")
    warning_count = sum(1 for c in components if c.status == "warning")
    
    if unhealthy_count > 0:
        return "unhealthy"
    elif warning_count > 0:
        return "degraded"
    else:
        return "healthy"


@lambda_exception_handler(CORS_headers)
async def async_lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function handler for comprehensive client onboarding system health check.
    
    Monitors webhook health and processing status for observability.
    
    Args:
        event: Lambda event
        context: Lambda context object
        
    Returns:
        Dict containing statusCode, headers, and body for Lambda response
    """
    async with logging_middleware.log_request_response(event, context) as operation_context:
        correlation_id = generate_correlation_id()
        operation_context["correlation_id"] = correlation_id
        
        logger.info(f"Client onboarding system health check requested. {LambdaHelpers.extract_log_data(event)}")
        
        overall_start_time = datetime.now(UTC)
        
        # Run all health checks sequentially for simplicity
        try:
            health_checks = [
                await check_container_health(),
                await check_database_health(),
                await check_typeform_api_health(),
                await check_webhook_processing_health(),
                await check_middleware_health()
            ]
        except Exception as e:
            # If health check execution itself fails
            logger.error(f"Health check execution failed: {e}", exc_info=True)
            overall_response_time = (datetime.now(UTC) - overall_start_time).total_seconds() * 1000
            
            return {
                "statusCode": 500,
                "headers": CORS_headers,
                "body": json.dumps({
                    "status": "error",
                    "error": "Health check execution failed",
                    "timestamp": datetime.now(UTC).isoformat() + "Z",
                    "correlation_id": correlation_id,
                    "overall_response_time_ms": overall_response_time
                }),
            }
        
        overall_response_time = (datetime.now(UTC) - overall_start_time).total_seconds() * 1000
        overall_status = determine_overall_status(health_checks)
        
        # Create comprehensive health check result
        system_health = SystemHealthCheck(
            status=overall_status,
            timestamp=datetime.now(UTC).isoformat() + "Z",
            version="1.0.0",
            components=health_checks,
            overall_response_time_ms=overall_response_time,
            correlation_id=correlation_id
        )
        
        # Determine HTTP status code based on overall health
        if overall_status == "healthy":
            status_code = 200
        elif overall_status == "degraded":
            status_code = 200  # Still operational, but with warnings
        else:  # unhealthy
            status_code = 503
        
        logger.info(f"Health check completed. Status: {overall_status}, Response time: {overall_response_time:.2f}ms")
        
        return {
            "statusCode": status_code,
            "headers": CORS_headers,
            "body": json.dumps(asdict(system_health), indent=2),
        }


# Synchronous handler for Lambda runtime compatibility
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Synchronous wrapper for async health check handler."""
    return anyio.run(async_lambda_handler, event, context) 