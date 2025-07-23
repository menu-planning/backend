# Lambda Migration Examples

This document shows concrete before/after examples of migrating existing Lambda handlers to use LambdaHelpers while preserving all working patterns.

## Example 1: Simple Recipe Fetch Handler

### Before (Original Pattern)
```python
import os
from typing import Any

import anyio
from pydantic import TypeAdapter

from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import IAMProvider
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import lambda_exception_handler
from src.contexts.shared_kernel.services.messagebus import MessageBus
from ..CORS_headers import CORS_headers

container = Container()

@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # Manual event parsing
    authorizer_context = event["requestContext"]["authorizer"]
    user_id = authorizer_context.get("claims").get("sub")
    recipe_id = event.get("pathParameters", {}).get("id")
    
    # Existing auth pattern (KEEP)
    response: dict = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response
    
    # Existing business logic (KEEP)
    bus: MessageBus = container.bootstrap()
    async with bus.uow as uow:
        recipe = await uow.recipes.get(recipe_id)
    
    # Manual response formatting
    if not recipe:
        return {
            "statusCode": 404,
            "headers": CORS_headers,
            "body": json.dumps({"detail": "Recipe not found"})
        }
    
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": ApiRecipe.from_domain(recipe).model_dump_json()
    }
```

### After (With LambdaHelpers)
```python
import os
from typing import Any

import anyio
from pydantic import TypeAdapter

from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import IAMProvider
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import lambda_exception_handler
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from ..CORS_headers import CORS_headers

container = Container()

@lambda_exception_handler  # UNCHANGED
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # LambdaHelpers event parsing (IMPROVED)
    user_id = LambdaHelpers.extract_user_id(event)
    recipe_id = LambdaHelpers.extract_path_parameter(event, "id")
    
    # Existing auth pattern (UNCHANGED)
    response: dict = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response
    
    # Existing business logic (UNCHANGED)
    bus: MessageBus = container.bootstrap()
    async with bus.uow as uow:
        recipe = await uow.recipes.get(recipe_id)
    
    # LambdaHelpers response formatting (IMPROVED)
    if not recipe:
        return LambdaHelpers.format_error_response(
            message="Recipe not found",
            status_code=404,
            cors_headers=CORS_headers
        )
    
    return LambdaHelpers.format_success_response(
        data=ApiRecipe.from_domain(recipe),
        cors_headers=CORS_headers
    )
```

### Changes Made:
- ✅ **Added LambdaHelpers import**
- ✅ **Replaced manual event parsing** with `extract_user_id()` and `extract_path_parameter()`
- ✅ **Replaced manual response formatting** with `format_error_response()` and `format_success_response()`
- ✅ **Preserved `@lambda_exception_handler`** - no changes
- ✅ **Preserved IAM auth pattern** - no changes  
- ✅ **Preserved MessageBus business logic** - no changes
- ✅ **Preserved CORS headers** - now passed as parameter

## Example 2: Collection Endpoint with Query Parameters

### Before (Original Pattern)
```python
@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # Manual event parsing
    authorizer_context = event["requestContext"]["authorizer"]
    user_id = authorizer_context.get("claims").get("sub")
    
    query_params: Any | dict[str, Any] = (
        event.get("multiValueQueryStringParameters") 
        if event.get("multiValueQueryStringParameters") 
        else {}
    )
    filters: dict[str,Any] = {k.replace("-", "_"): v for k, v in query_params.items()}
    filters["limit"] = int(query_params.get("limit", 50))
    filters["sort"] = query_params.get("sort", "-updated_at")
    
    # Clean up filters
    for k, v in filters.items():
        if isinstance(v, list) and len(v) == 1:
            filters[k] = v[0]

    # Existing auth and business logic
    response: dict = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response
    
    bus: MessageBus = Container().bootstrap()
    async with bus.uow as uow:
        result = await uow.recipes.query(filter=filters)
    
    # Manual response formatting with TypeAdapter
    try:
        return {
            "statusCode": 200,
            "headers": CORS_headers,
            "body": json.dumps(
                [ApiRecipe.from_domain(r).model_dump() for r in result] if result else [],
                default=custom_serializer,
            )
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"detail": str(e)})
        }
```

### After (With LambdaHelpers + TypeAdapter)
```python
from pydantic import TypeAdapter
from src.contexts.shared_kernel.schemas.collection_response import (
    extract_pagination_from_query,
    create_paginated_response
)

# TypeAdapter at module level (once per cold start)
recipe_list_adapter = TypeAdapter(list[ApiRecipe])

@lambda_exception_handler  # UNCHANGED
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # LambdaHelpers event parsing (IMPROVED)
    user_id = LambdaHelpers.extract_user_id(event)
    query_params = LambdaHelpers.extract_query_parameters(event)
    multi_params = LambdaHelpers.extract_multi_value_query_parameters(event)
    
    # Simplified filter processing (IMPROVED)
    filters = {k.replace("-", "_"): v for k, v in multi_params.items()}
    page, page_size = extract_pagination_from_query(query_params, default_page_size=50)
    
    # Existing auth pattern (UNCHANGED)
    response: dict = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response
    
    # Existing business logic with pagination (ENHANCED)
    bus: MessageBus = Container().bootstrap()
    async with bus.uow as uow:
        result = await uow.recipes.query(
            filter=filters,
            limit=page_size,
            offset=(page - 1) * page_size
        )
        total_count = await uow.recipes.count(filter=filters)
    
    # LambdaHelpers + TypeAdapter response (IMPROVED)
    api_recipes = [ApiRecipe.from_domain(r) for r in result] if result else []
    
    # Simple list response
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": recipe_list_adapter.dump_json(api_recipes).decode('utf-8')
    }
    
    # OR paginated response
    # collection = create_paginated_response(
    #     items=api_recipes,
    #     total_count=total_count,
    #     page_size=page_size,
    #     current_page=page
    # )
    # return LambdaHelpers.format_success_response(collection, cors_headers=CORS_headers)
```

### Changes Made:
- ✅ **Added TypeAdapter at module level** for performance
- ✅ **Simplified query parameter extraction** with LambdaHelpers methods
- ✅ **Added pagination utilities** for consistent pagination handling
- ✅ **Removed manual JSON serialization** - TypeAdapter handles it
- ✅ **Preserved all business logic** - just enhanced with pagination
- ✅ **Exception handling** still handled by `@lambda_exception_handler`

## Example 3: POST Endpoint with Request Body

### Before (Original Pattern)
```python
@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # Manual event parsing
    authorizer_context = event["requestContext"]["authorizer"]
    user_id = authorizer_context.get("claims").get("sub")
    
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"detail": "Invalid JSON in request body"})
        }
    
    # Manual validation
    try:
        recipe_data = ApiRecipe(**body)
    except ValidationError as e:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"detail": f"Validation error: {str(e)}"})
        }
    
    # Existing patterns
    response: dict = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response
    
    bus: MessageBus = Container().bootstrap()
    async with bus.uow as uow:
        domain_recipe = recipe_data.to_domain()
        await uow.recipes.save(domain_recipe)
        await uow.commit()
    
    return {
        "statusCode": 201,
        "headers": CORS_headers,
        "body": recipe_data.model_dump_json()
    }
```

### After (With LambdaHelpers)
```python
@lambda_exception_handler  # UNCHANGED
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # LambdaHelpers event parsing (IMPROVED)
    user_id = LambdaHelpers.extract_user_id(event)
    body_dict = LambdaHelpers.extract_request_body(event, as_dict=True)
    
    # Simplified validation (IMPROVED)
    if not body_dict:
        return LambdaHelpers.format_error_response(
            message="Request body is required",
            status_code=400,
            cors_headers=CORS_headers
        )
    
    try:
        recipe_data = ApiRecipe(**body_dict)
    except ValidationError as e:
        return LambdaHelpers.format_error_response(
            message=f"Validation error: {str(e)}",
            status_code=400,
            cors_headers=CORS_headers
        )
    
    # Existing patterns (UNCHANGED)
    response: dict = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response
    
    bus: MessageBus = Container().bootstrap()
    async with bus.uow as uow:
        domain_recipe = recipe_data.to_domain()
        await uow.recipes.save(domain_recipe)
        await uow.commit()
    
    # LambdaHelpers response (IMPROVED)
    return LambdaHelpers.format_success_response(
        data=recipe_data,
        status_code=201,
        cors_headers=CORS_headers
    )
```

### Changes Made:
- ✅ **Simplified request body parsing** with `extract_request_body(as_dict=True)`
- ✅ **Standardized error responses** with `format_error_response()`
- ✅ **Cleaner success response** with `format_success_response()` and custom status code
- ✅ **Preserved validation logic** - just cleaner error handling
- ✅ **All business logic unchanged**

## Example 4: IAM Context Endpoint

### Before (Original Pattern)
```python
@lambda_exception_handler
async def async_handler(event, context):
    # Manual event parsing
    authorizer_context = event["requestContext"]["authorizer"]
    caller_user_id = authorizer_context.get("claims").get("sub")
    
    try:
        body = json.loads(event.get("body", ""))
    except:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid JSON"})
        }
    
    # IAM specific auth pattern (different from recipes)
    response = await internal.get(caller_user_id, "iam")
    if response.get("statusCode") != 200:
        return response
    current_user: SeedUser = response["body"]
    
    # Business logic
    command = CreateUserCommand(**body, author_id=current_user.id)
    bus: MessageBus = Container().bootstrap()
    async with bus.uow as uow:
        result = await bus.handle(command, uow)
    
    # Manual response
    return {
        "statusCode": 201,
        "body": json.dumps({"message": "User created", "id": str(result.id)})
    }
```

### After (With LambdaHelpers)
```python
@lambda_exception_handler  # UNCHANGED
async def async_handler(event, context):
    # LambdaHelpers event parsing (IMPROVED)
    caller_user_id = LambdaHelpers.extract_user_id(event)
    body_dict = LambdaHelpers.extract_request_body(event, as_dict=True)
    
    if not body_dict:
        return LambdaHelpers.format_error_response(
            message="Request body is required",
            status_code=400
        )
    
    # IAM specific auth pattern (UNCHANGED)
    response = await internal.get(caller_user_id, "iam")
    if response.get("statusCode") != 200:
        return response
    current_user: SeedUser = response["body"]
    
    # Business logic (UNCHANGED)
    command = CreateUserCommand(**body_dict, author_id=current_user.id)
    bus: MessageBus = Container().bootstrap()
    async with bus.uow as uow:
        result = await bus.handle(command, uow)
    
    # LambdaHelpers response (IMPROVED)
    return LambdaHelpers.format_success_response(
        data={"message": "User created", "id": str(result.id)},
        status_code=201
    )
```

### Changes Made:
- ✅ **Preserved IAM-specific auth pattern** - `internal.get()` instead of `IAMProvider.get()`
- ✅ **Improved event parsing** with LambdaHelpers
- ✅ **Standardized response format** while maintaining IAM message structure
- ✅ **All business logic unchanged**

## Example 5: LocalStack Development Support

### Before (Manual Environment Detection)
```python
@lambda_exception_handler
async def async_handler(event, context):
    user_id = event["requestContext"]["authorizer"].get("claims").get("sub")
    
    # Manual LocalStack detection
    if os.getenv("AWS_ENDPOINT_URL") or os.getenv("LOCALSTACK_HOSTNAME"):
        # Skip auth in development
        current_user = SeedUser(id=user_id or "dev_user")
    else:
        # Production auth
        response = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
        current_user = response["body"]
    
    # Rest of handler...
```

### After (With LambdaHelpers)
```python
@lambda_exception_handler  # UNCHANGED
async def async_handler(event, context):
    user_id = LambdaHelpers.extract_user_id(event)
    
    # LambdaHelpers environment detection (IMPROVED)
    if LambdaHelpers.is_localstack_environment():
        # Development mode
        current_user = SeedUser(id=user_id or "dev_user")
    else:
        # Production auth (UNCHANGED)
        response = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
        current_user = response["body"]
    
    # Rest of handler...
```

### Changes Made:
- ✅ **Simplified environment detection** with `is_localstack_environment()`
- ✅ **Cleaner development/production branching**
- ✅ **Preserved auth logic for both environments**

## Migration Checklist

For each Lambda handler migration:

### Pre-Migration
- [ ] **Identify current patterns** (auth method, business logic, response format)
- [ ] **Note any custom serialization** (custom_serializer usage)
- [ ] **Check error handling** (custom vs standard patterns)
- [ ] **Identify query parameter usage** (simple vs multi-value)

### During Migration
- [ ] **Add LambdaHelpers import**
- [ ] **Replace event parsing** with `extract_*` methods
- [ ] **Replace response building** with `format_*_response` methods
- [ ] **Add TypeAdapter** for collection endpoints (module level)
- [ ] **Preserve existing decorators** (`@lambda_exception_handler`)
- [ ] **Preserve auth patterns** (IAMProvider, internal.get, etc.)
- [ ] **Preserve business logic** (MessageBus, UnitOfWork, commands)

### Post-Migration
- [ ] **Test all endpoints** thoroughly
- [ ] **Verify CORS headers** in all responses
- [ ] **Check error response format** consistency
- [ ] **Validate pagination** (if applicable)
- [ ] **Test in LocalStack** and production environments

### Performance Considerations
- [ ] **Create TypeAdapters at module level** (not in function)
- [ ] **Use TypeAdapters for collections** instead of manual JSON serialization
- [ ] **Preserve existing custom_serializer** patterns where needed
- [ ] **Keep successful patterns** (caching, connection pooling, etc.)

## Common Pitfalls to Avoid

1. **Don't replace working auth patterns**
   ```python
   # WRONG: Trying to standardize different auth patterns
   response = await IAMProvider.get(user_id)  # Always use this
   
   # CORRECT: Preserve context-specific auth
   if context == "iam":
       response = await internal.get(user_id, "iam")
   else:
       response = await IAMProvider.get(user_id)
   ```

2. **Don't forget CORS headers in errors**
   ```python
   # WRONG: Missing CORS in error responses
   return LambdaHelpers.format_error_response("Error", 400)
   
   # CORRECT: Include CORS headers
   return LambdaHelpers.format_error_response("Error", 400, cors_headers=CORS_headers)
   ```

3. **Don't create TypeAdapters in functions**
   ```python
   # WRONG: Creates adapter on every invocation
   def handler(event, context):
       adapter = TypeAdapter(list[ApiRecipe])  # Expensive!
       return adapter.dump_json(recipes)
   
   # CORRECT: Create at module level
   recipe_adapter = TypeAdapter(list[ApiRecipe])  # Once per cold start
   
   def handler(event, context):
       return recipe_adapter.dump_json(recipes)
   ```

4. **Don't break existing exception handling**
   ```python
   # WRONG: Adding try/catch when @lambda_exception_handler exists
   @lambda_exception_handler
   def handler(event, context):
       try:
           # Business logic
       except Exception as e:
           return {"statusCode": 500, "body": str(e)}  # Duplicates decorator
   
   # CORRECT: Let decorator handle exceptions
   @lambda_exception_handler
   def handler(event, context):
       # Business logic - exceptions handled by decorator
   ```

This migration approach ensures **zero breaking changes** while improving consistency and maintainability. 