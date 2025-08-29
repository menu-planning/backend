# Middleware Usage Examples

This document provides examples of how to use the unified middleware system with its new timeout and cancel scope capabilities, and how to properly use the refactored `LambdaHelpers` for event parsing and query processing.

## Basic Usage

### Simple Middleware Composition
```python
from src.contexts.shared_kernel.middleware.core.middleware_composer import MiddlewareComposer
from src.contexts.shared_kernel.middleware.core.base_middleware import BaseMiddleware

# Create middleware instances
logging_middleware = LoggingMiddleware()
auth_middleware = AuthMiddleware()
error_middleware = ErrorHandlingMiddleware()

# Compose with default timeout
composer = MiddlewareComposer(
    middleware=[logging_middleware, auth_middleware, error_middleware],
    default_timeout=30.0  # 30 second timeout
)

# Compose the handler
final_handler = composer.compose(original_handler)
```

### Per-Request Timeout Override
```python
# Override timeout for specific requests
final_handler = composer.compose(original_handler, timeout=60.0)  # 60 second timeout
```

## Complete Lambda Handler Example

### ✅ CORRECT: Using Unified Middleware + LambdaHelpers
```python
from src.contexts.shared_kernel.middleware.decorators.lambda_handler import async_endpoint_handler
from src.contexts.shared_kernel.middleware.logging.structured_logger import aws_lambda_logging_middleware
from src.contexts.shared_kernel.middleware.auth.authentication import recipes_aws_auth_middleware
from src.contexts.shared_kernel.middleware.error_handling.exception_handler import aws_lambda_exception_handler_middleware
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers

@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.fetch_recipe",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="fetch_recipe_exception_handler",
        logger_name="recipes_catalog.fetch_recipe.errors",
    ),
    timeout=30.0,
    name="fetch_recipe_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for recipes.
    
    This handler focuses purely on business logic. All cross-cutting concerns
    are handled by the unified middleware:
    - Authentication: AuthenticationMiddleware provides event["_auth_context"]
    - Logging: StructuredLoggingMiddleware handles request/response logging
    - Error Handling: ExceptionHandlerMiddleware catches and formats all errors
    - CORS: Handled automatically by the middleware system
    """
    # ✅ Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    # ✅ Use LambdaHelpers for event parsing and query processing
    filters = LambdaHelpers.process_query_filters_from_aws_event(
        event=event,
        filter_schema_class=ApiRecipeFilter,
        use_multi_value=True,
        default_limit=50,
        default_sort="-updated_at",
    )

    # Apply user-specific tag filtering for recipes
    if current_user:
        if filters.get("tags"):
            filters["tags"] = [(i, current_user.id) for i in filters["tags"]]
        if filters.get("tags_not_exists"):
            filters["tags_not_exists"] = [
                (i, current_user.id) for i in filters["tags_not_exists"]
            ]

    # Business logic only - no manual logging, auth, or error handling
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        result = await uow.recipes.query(filters=filters)

    # Convert domain recipes to API recipes
    api_recipes = []
    for recipe in result:
        api_recipe = ApiRecipe.from_domain(recipe)
        api_recipes.append(api_recipe)

    # Serialize API recipes
    response_body = RecipeListAdapter.dump_json(api_recipes)

    # ✅ Use LambdaHelpers for CORS headers
    return {
        "statusCode": 200,
        "headers": LambdaHelpers.get_default_cors_headers(),
        "body": response_body,
    }
```

### ❌ WRONG: Manual Implementation (Redundant with Middleware)
```python
# ❌ DON'T DO THIS - Middleware already handles these concerns
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    # ❌ Manual logging (redundant with middleware)
    logger.debug("Event received", event_data=...)
    
    # ❌ Manual auth (redundant with middleware)
    auth_result = await LambdaHelpers.validate_user_authentication(...)
    
    # ❌ Manual error handling (redundant with middleware)
    try:
        # business logic
    except Exception as e:
        logger.exception(...)
        return error_response
```

## LambdaHelpers Usage Patterns

### 1. Event Parameter Extraction
```python
# Extract path parameters
recipe_id = LambdaHelpers.extract_path_parameter(event, "id")
product_id = LambdaHelpers.extract_path_parameter(event, "product_id")

# Extract query parameters
query_params = LambdaHelpers.extract_query_parameters(event)
multi_value_params = LambdaHelpers.extract_multi_value_query_parameters(event)

# Extract request body
body = LambdaHelpers.extract_request_body(event, parse_json=True)
raw_body = LambdaHelpers.extract_request_body(event, parse_json=False)
```

### 2. Query Filter Processing
```python
# Complete query processing pipeline
filters = LambdaHelpers.process_query_filters_from_aws_event(
    event=event,
    filter_schema_class=ApiProductFilter,
    use_multi_value=True,
    default_limit=25,
    default_sort="name"
)

# Manual filter processing (if needed)
raw_params = LambdaHelpers.extract_query_parameters(event)
normalized_params = LambdaHelpers.normalize_kebab_case_keys(raw_params)
flattened_params = LambdaHelpers.flatten_single_item_lists(normalized_params)
pagination_params = LambdaHelpers.extract_pagination_params(
    flattened_params, 
    default_limit=50, 
    default_sort="-created_at"
)
```

### 3. Response Formatting
```python
# Get CORS headers
cors_headers = LambdaHelpers.get_default_cors_headers()

# Build response
return {
    "statusCode": 200,
    "headers": cors_headers,
    "body": json.dumps(result)
}
```

## Middleware with Individual Timeouts

### Custom Middleware with Timeout
```python
class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, name: str | None = None, timeout: float | None = None):
        super().__init__(name=name, timeout=timeout)
    
    async def __call__(self, handler: Handler, event: dict[str, Any], context: Any) -> dict[str, Any]:
        # Use middleware-specific timeout for database operations
        if self.timeout:
            with anyio.move_on_after(self.timeout) as scope:
                # Database operations here
                result = await self._execute_db_operation(event)
                if scope.cancel_called:
                    return {"error": "Database operation timeout", "statusCode": 408}
                return await handler(event, context)
        
        # No timeout specified
        return await handler(event, context)

# Usage with individual timeout
db_middleware = DatabaseMiddleware(timeout=10.0)  # 10 second DB timeout
```

## Exception Handling with Cancel Scopes

### Error Middleware Example
```python
class ErrorHandlingMiddleware(BaseMiddleware):
    async def __call__(self, handler: Handler, event: dict[str, Any], context: Any) -> dict[str, Any]:
        try:
            return await handler(event, context)
        except anyio.get_cancelled_exc_class():
            # Handle cancellation gracefully
            return {"error": "Request cancelled", "statusCode": 499}
        except TimeoutError:
            # Handle timeout errors
            return {"error": "Request timeout", "statusCode": 408}
        except Exception as e:
            # Handle other application errors
            logger.exception(f"Unhandled exception: {e}")
            return {"error": "Internal server error", "statusCode": 500}
```

## FastAPI Integration

### FastAPI Middleware Wrapper
```python
from fastapi import Request, Response
from fastapi.responses import StreamingResponse

class FastAPIMiddlewareComposer(MiddlewareComposer):
    def compose_for_fastapi(self, handler: Callable, timeout: float | None = None):
        """Compose middleware specifically for FastAPI endpoints."""
        async def fastapi_handler(request: Request) -> Response:
            # Convert FastAPI request to event format
            event = self._request_to_event(request)
            
            # Use the composed handler with timeout
            composed = self.compose(handler, timeout)
            result = await composed(event, request)  # request as context
            
            # Convert result back to FastAPI response
            return self._result_to_response(result)
        
        return fastapi_handler

# Usage in FastAPI
app = FastAPI()

@app.get("/api/endpoint")
@fastapi_composer.compose_for_fastapi(original_handler, timeout=30.0)
async def endpoint():
    pass
```

## Timeout Configuration Examples

### Environment-Based Configuration
```python
import os
from src.contexts.shared_kernel.middleware.core.middleware_composer import MiddlewareComposer

# Get timeout from environment
default_timeout = float(os.getenv("MIDDLEWARE_TIMEOUT", "30.0"))
auth_timeout = float(os.getenv("AUTH_TIMEOUT", "5.0"))

# Create composer with environment-based timeout
composer = MiddlewareComposer(
    middleware=[auth_middleware, logging_middleware],
    default_timeout=default_timeout
)

# Create auth middleware with specific timeout
auth_middleware = AuthMiddleware(timeout=auth_timeout)
```

### Context-Specific Timeouts
```python
# Different timeouts for different contexts
client_onboarding_composer = MiddlewareComposer(
    middleware=[auth_middleware, logging_middleware],
    default_timeout=60.0  # Longer timeout for onboarding
)

products_catalog_composer = MiddlewareComposer(
    middleware=[auth_middleware, logging_middleware],
    default_timeout=15.0  # Shorter timeout for catalog operations
)
```

## Testing Timeout Behavior

### Test Timeout Scenarios
```python
import pytest
import anyio

@pytest.mark.asyncio
async def test_middleware_timeout():
    # Create middleware that takes longer than timeout
    slow_middleware = SlowMiddleware()
    composer = MiddlewareComposer([slow_middleware], default_timeout=0.1)
    
    # Compose handler
    composed_handler = composer.compose(original_handler)
    
    # Execute with timeout (include context)
    test_context = {"request_id": "test-123"}
    result = await composed_handler(test_event, test_context)
    
    # Verify timeout response
    assert result["statusCode"] == 408
    assert "timeout" in result["error"].lower()

class SlowMiddleware(BaseMiddleware):
    async def __call__(self, handler: Handler, event: dict[str, Any], context: Any) -> dict[str, Any]:
        # Simulate slow operation
        await anyio.sleep(1.0)  # Longer than timeout
        return await handler(event, context)
```

## Handler Function Signatures

### AWS Lambda Handler
```python
# Your business logic handler must accept both event and context
async def business_logic_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # Access context information
    request_id = getattr(context, 'request_id', 'unknown')
    function_name = getattr(context, 'function_name', 'unknown')
    
    # Your business logic here
    return {
        "statusCode": 200,
        "body": f"Hello from {function_name}",
        "requestId": request_id
    }
```

### FastAPI Handler
```python
# For FastAPI, context is typically the Request object
async def fastapi_handler(event: dict[str, Any], context: Request) -> dict[str, Any]:
    # Access FastAPI request information
    user_agent = context.headers.get("user-agent", "unknown")
    client_ip = context.client.host if context.client else "unknown"
    
    return {
        "statusCode": 200,
        "body": "Hello from FastAPI",
        "userAgent": user_agent,
        "clientIP": client_ip
    }
```

## Context Usage Examples

### Accessing Context in Middleware
```python
class ContextAwareMiddleware(BaseMiddleware):
    async def __call__(self, handler: Handler, event: dict[str, Any], context: Any) -> dict[str, Any]:
        # Extract useful information from context
        if hasattr(context, 'request_id'):
            request_id = context.request_id
        elif hasattr(context, 'headers') and 'x-request-id' in context.headers:
            request_id = context.headers['x-request-id']
        else:
            request_id = 'unknown'
        
        # Add to event for downstream handlers
        event['request_id'] = request_id
        
        # Call next handler with both event and context
        return await handler(event, context)
```

### Testing with Mock Context
```python
@pytest.mark.asyncio
async def test_middleware_with_context():
    # Create mock context
    mock_context = type('MockContext', (), {
        'request_id': 'test-123',
        'function_name': 'test-function',
        'memory_limit_in_mb': 128
    })()
    
    # Test middleware with context
    result = await middleware(handler, test_event, mock_context)
    
    # Verify context was properly handled
    assert result['requestId'] == 'test-123'
```

## Best Practices

### ✅ DO: Use Unified Middleware + LambdaHelpers
1. **Use @async_endpoint_handler decorator** for all Lambda handlers
2. **Let middleware handle cross-cutting concerns** (auth, logging, error handling)
3. **Use LambdaHelpers for event parsing** (path params, query params, body)
4. **Use LambdaHelpers for query processing** (filters, pagination, validation)
5. **Use LambdaHelpers for CORS headers** in responses
6. **Focus handler code on business logic only**

### ❌ DON'T: Manual Implementation
1. **Don't implement manual authentication** - use auth middleware
2. **Don't implement manual logging** - use logging middleware  
3. **Don't implement manual error handling** - use exception handler middleware
4. **Don't duplicate event parsing logic** - use LambdaHelpers
5. **Don't ignore middleware timeout configuration**

### Middleware Configuration
1. **Always Accept Context**: Every handler and middleware must accept both `event` and `context` parameters
2. **Pass Context Through**: Always call `await handler(event, context)` to pass context downstream
3. **Set Appropriate Timeouts**: Different operations need different timeouts
4. **Handle Cancellation Gracefully**: Always provide meaningful responses
5. **Use Environment Configuration**: Make timeouts configurable per environment
6. **Monitor Performance**: Track middleware overhead with timeout handling
7. **Context Validation**: Validate context attributes before using them

### LambdaHelpers Usage
1. **Event Extraction**: Use for path params, query params, request body
2. **Query Processing**: Use for filter validation, pagination, normalization
3. **Response Formatting**: Use for CORS headers and response structure
4. **Error Handling**: Let middleware handle errors, just raise exceptions
5. **Validation**: Use Pydantic schemas through LambdaHelpers for consistency 