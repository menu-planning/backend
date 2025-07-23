# LambdaHelpers Usage Guide

## Overview

`LambdaHelpers` is a utility class that provides simple, static methods for standardizing AWS Lambda event parsing and response formatting across all contexts (recipes, products, IAM). It works **alongside** existing proven patterns rather than replacing them.

## Key Benefits

- ✅ **No Breaking Changes**: Works with existing `@lambda_exception_handler`, `MessageBus`, `IAMProvider` patterns
- ✅ **Simple Static Methods**: No complex inheritance or configuration
- ✅ **Consistent Parsing**: Standardized event parameter extraction
- ✅ **CORS Integration**: Built-in CORS header management
- ✅ **Type Safety**: Full TypeScript-style typing for better IDE support

## Quick Start

### Import
```python
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
```

### Basic Usage Pattern
```python
@lambda_exception_handler  # Keep existing exception handling
async def async_handler(event, context):
    # Extract parameters using LambdaHelpers
    user_id = LambdaHelpers.extract_user_id(event)
    recipe_id = LambdaHelpers.extract_path_parameter(event, "id")
    query_params = LambdaHelpers.extract_query_parameters(event)
    
    # Keep existing auth pattern
    response = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response
    
    # Keep existing business logic pattern
    bus: MessageBus = container.bootstrap()
    async with bus.uow as uow:
        recipe = await uow.recipes.get(recipe_id)
    
    # Use LambdaHelpers for consistent response formatting
    return LambdaHelpers.format_success_response(
        data=ApiRecipe.from_domain(recipe),
        cors_headers=CORS_headers
    )
```

## Method Reference

### Event Parsing Methods

#### `extract_path_parameter(event, param_name, default=None)`
Extract a single path parameter from the Lambda event.

```python
# For route: /recipes/{id}
recipe_id = LambdaHelpers.extract_path_parameter(event, "id")
# Returns: string value or None

# With default value
recipe_id = LambdaHelpers.extract_path_parameter(event, "id", "default_id")
```

#### `extract_query_parameters(event)`
Extract all query string parameters as a dictionary.

```python
query_params = LambdaHelpers.extract_query_parameters(event)
# Returns: {"page": "1", "limit": "50", "search": "chicken"} or {}

# Use with pagination utilities
page, page_size = extract_pagination_from_query(query_params)
```

#### `extract_multi_value_query_parameters(event)`
Extract multi-value query parameters (e.g., `?tags=vegan&tags=healthy`).

```python
multi_params = LambdaHelpers.extract_multi_value_query_parameters(event)
# Returns: {"tags": ["vegan", "healthy"]} or {}

tags = multi_params.get("tags", [])
```

#### `extract_request_body(event, as_dict=False)`
Extract and parse the request body.

```python
# As JSON string (default)
body_str = LambdaHelpers.extract_request_body(event)

# As dictionary
body_dict = LambdaHelpers.extract_request_body(event, as_dict=True)
# Returns: parsed JSON as dict or None

# Use with Pydantic models
if body_dict:
    recipe_data = ApiRecipe(**body_dict)
```

#### `extract_user_id(event)`
Extract user ID from authorizer context.

```python
user_id = LambdaHelpers.extract_user_id(event)
# Returns: user ID string or None

# Works with existing IAM patterns
if user_id:
    response = await IAMProvider.get(user_id)
```

### Response Formatting Methods

#### `format_success_response(data, status_code=200, cors_headers=None, custom_serializer=None)`
Create standardized success responses.

```python
# Single entity response
recipe = ApiRecipe.from_domain(domain_recipe)
return LambdaHelpers.format_success_response(
    data=recipe,
    cors_headers=CORS_headers
)

# Collection response (works with TypeAdapter)
recipes = [ApiRecipe.from_domain(r) for r in domain_recipes]
return LambdaHelpers.format_success_response(
    data=recipes,
    cors_headers=CORS_headers
)

# Custom status code
return LambdaHelpers.format_success_response(
    data={"message": "Recipe created"},
    status_code=201,
    cors_headers=CORS_headers
)

# With custom serializer (existing pattern)
return LambdaHelpers.format_success_response(
    data=complex_data,
    cors_headers=CORS_headers,
    custom_serializer=custom_serializer
)
```

#### `format_error_response(message, status_code=400, error_code=None, cors_headers=None)`
Create standardized error responses.

```python
# Basic error response
return LambdaHelpers.format_error_response(
    message="Recipe not found",
    status_code=404,
    cors_headers=CORS_headers
)

# With error code
return LambdaHelpers.format_error_response(
    message="Invalid recipe data",
    status_code=400,
    error_code="VALIDATION_ERROR",
    cors_headers=CORS_headers
)
```

### Utility Methods

#### `get_default_cors_headers()`
Get standardized CORS headers.

```python
cors_headers = LambdaHelpers.get_default_cors_headers()
# Returns: {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type,Authorization"}

# Use when you need CORS headers programmatically
if some_condition:
    headers = LambdaHelpers.get_default_cors_headers()
    headers["Custom-Header"] = "value"
```

#### `is_localstack_environment()`
Check if running in LocalStack (development) environment.

```python
if LambdaHelpers.is_localstack_environment():
    # Skip auth in development
    print("Running in LocalStack - auth bypassed")
else:
    # Production auth required
    response = await IAMProvider.get(user_id)
```

## Collection Response Integration

For endpoints returning collections, integrate with TypeAdapter utilities:

```python
from pydantic import TypeAdapter
from src.contexts.shared_kernel.schemas.collection_response import (
    create_paginated_response, 
    extract_pagination_from_query
)

# Create TypeAdapter at module level (once per cold start)
recipe_list_adapter = TypeAdapter(list[ApiRecipe])

@lambda_exception_handler
async def fetch_recipes_handler(event, context):
    # Extract pagination using LambdaHelpers
    query_params = LambdaHelpers.extract_query_parameters(event)
    page, page_size = extract_pagination_from_query(query_params)
    
    # Business logic
    bus: MessageBus = container.bootstrap()
    async with bus.uow as uow:
        recipes = await uow.recipes.query(limit=page_size, offset=(page-1)*page_size)
        total_count = await uow.recipes.count()
    
    # Convert to API objects
    api_recipes = [ApiRecipe.from_domain(r) for r in recipes]
    
    # Create paginated response
    collection = create_paginated_response(
        items=api_recipes,
        total_count=total_count,
        page_size=page_size,
        current_page=page
    )
    
    # Format response with TypeAdapter
    return {
        "statusCode": 200,
        "headers": LambdaHelpers.get_default_cors_headers(),
        "body": recipe_collection_adapter.dump_json(collection).decode('utf-8')
    }
```

## Error Handling Patterns

LambdaHelpers works seamlessly with existing error handling:

```python
@lambda_exception_handler  # Handles all exceptions
async def async_handler(event, context):
    try:
        # Extract parameters - safe, returns None if missing
        recipe_id = LambdaHelpers.extract_path_parameter(event, "id")
        if not recipe_id:
            return LambdaHelpers.format_error_response(
                message="Recipe ID is required",
                status_code=400,
                cors_headers=CORS_headers
            )
        
        # Business logic
        bus: MessageBus = container.bootstrap()
        async with bus.uow as uow:
            recipe = await uow.recipes.get(recipe_id)
            if not recipe:
                return LambdaHelpers.format_error_response(
                    message="Recipe not found",
                    status_code=404,
                    cors_headers=CORS_headers
                )
        
        # Success response
        return LambdaHelpers.format_success_response(
            data=ApiRecipe.from_domain(recipe),
            cors_headers=CORS_headers
        )
        
    except ValidationError as e:
        # Custom error handling
        return LambdaHelpers.format_error_response(
            message=f"Validation error: {str(e)}",
            status_code=400,
            cors_headers=CORS_headers
        )
    # @lambda_exception_handler catches all other exceptions
```

## Environment Detection

Use `is_localstack_environment()` for development vs production logic:

```python
@lambda_exception_handler
async def async_handler(event, context):
    user_id = LambdaHelpers.extract_user_id(event)
    
    # Skip auth in LocalStack for easier development
    if not LambdaHelpers.is_localstack_environment():
        response = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
    else:
        # Development mode - create mock user
        current_user = SeedUser(id=user_id or "dev_user")
    
    # Rest of handler logic...
```

## Best Practices

### 1. **Module-Level TypeAdapters**
Create TypeAdapters at module level for best performance:

```python
from pydantic import TypeAdapter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe

# Once per cold start
recipe_list_adapter = TypeAdapter(list[ApiRecipe])
recipe_collection_adapter = TypeAdapter(CollectionResponse[ApiRecipe])

def lambda_handler(event, context):
    # Use pre-created adapters
    pass
```

### 2. **Consistent Error Responses**
Always include CORS headers in error responses:

```python
return LambdaHelpers.format_error_response(
    message="Error message",
    status_code=400,
    cors_headers=CORS_headers  # Don't forget this!
)
```

### 3. **Safe Parameter Extraction**
Always check for None when extracting parameters:

```python
recipe_id = LambdaHelpers.extract_path_parameter(event, "id")
if not recipe_id:
    return LambdaHelpers.format_error_response(
        message="ID parameter is required",
        status_code=400,
        cors_headers=CORS_headers
    )
```

### 4. **Preserve Existing Patterns**
Don't replace working patterns - enhance them:

```python
# GOOD: Enhance existing pattern
@lambda_exception_handler  # Keep this
async def handler(event, context):
    user_id = LambdaHelpers.extract_user_id(event)  # Add this
    response = await IAMProvider.get(user_id)       # Keep this
    # ... business logic with MessageBus             # Keep this
    return LambdaHelpers.format_success_response(data, CORS_headers)  # Add this

# BAD: Don't replace everything with a new framework
```

## Migration Checklist

When updating an existing Lambda handler:

1. ✅ **Import LambdaHelpers**
2. ✅ **Replace manual event parsing** with `extract_*` methods
3. ✅ **Replace manual response building** with `format_*_response` methods  
4. ✅ **Keep existing error handling** (`@lambda_exception_handler`)
5. ✅ **Keep existing auth patterns** (`IAMProvider.get()`)
6. ✅ **Keep existing business logic** (`MessageBus`, `UnitOfWork`)
7. ✅ **Add TypeAdapter** for collection endpoints (module level)
8. ✅ **Test thoroughly** to ensure no breaking changes

This ensures a smooth migration with improved consistency and no disruption to working functionality. 