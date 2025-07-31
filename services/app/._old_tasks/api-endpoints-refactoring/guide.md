# Implementation Guide: API Endpoints Standardization & Refactoring

---
feature: api-endpoints-refactoring
complexity: standard
risk_level: low
estimated_time: 80-100 hours
phases: 3
---

## Overview
Standardize AWS Lambda endpoints across contexts (recipes_catalog, products_catalog, iam) through lightweight utilities and consistent patterns that work alongside existing proven infrastructure (@lambda_exception_handler, MessageBus) rather than replacing it.

## Architecture

### Target Structure
```
src/
└── contexts/
    ├── shared_kernel/
    │   └── endpoints/
    │       └── base_endpoint_handler.py   - LambdaHelpers utilities
    ├── products_catalog/aws_lambda/       - Products Lambda endpoints
    ├── recipes_catalog/aws_lambda/        - Recipes Lambda endpoints
    └── iam/aws_lambda/                    - IAM Lambda endpoints
    └── existing patterns maintained:
        ├── @lambda_exception_handler      - Exception handling (KEEP)
        ├── MessageBus                     - Business logic + timeouts (KEEP)
        ├── IAMProvider.get()              - Simple auth pattern (KEEP)
        └── Direct event parsing           - Clear and debuggable (IMPROVE)
```

### Integration Points
- **IAMProvider**: User authentication and authorization (existing pattern)
- **MessageBus**: Command/query handling (existing pattern)
- **UnitOfWork**: Database operations (existing pattern)
- **@lambda_exception_handler**: Exception handling (existing pattern)
- **CORS_headers**: Cross-origin resource sharing (existing pattern)

## Files to Modify/Create

### Core Files
- `src/contexts/shared_kernel/endpoints/base_endpoint_handler.py` - LambdaHelpers utility class (SIMPLIFIED)

### Context Endpoints (UPDATED)
- `src/contexts/products_catalog/aws_lambda/*.py` - Update to use LambdaHelpers
- `src/contexts/recipes_catalog/aws_lambda/*.py` - Update to use LambdaHelpers
- `src/contexts/iam/aws_lambda/*.py` - Update to use LambdaHelpers

## Current Working Pattern (TO MAINTAIN)
```python
@lambda_exception_handler  # Handles all exceptions ✅
async def async_handler(event, context):
    # Simple auth check
    response = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response
    
    # Direct event parsing (clear and simple)
    recipe_id = event.get("pathParameters", {}).get("id")
    
    # Business logic with MessageBus (timeout handled here)
    bus: MessageBus = container.bootstrap()
    async with bus.uow as uow:
        recipe = await uow.recipes.get(recipe_id)
    
    # Simple response formatting
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": ApiRecipe.from_domain(recipe).model_dump_json()
    }
```

## Improved Pattern (WITH UTILITIES)
```python
@lambda_exception_handler  # Keep existing exception handling
async def async_handler(event, context):
    # Use utilities for consistency
    user_id = LambdaHelpers.extract_user_id(event)
    recipe_id = LambdaHelpers.extract_path_parameter(event, "id")
    
    # Keep existing auth pattern
    response = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response
    
    # Keep existing business logic pattern
    bus: MessageBus = container.bootstrap()
    async with bus.uow as uow:
        recipe = await uow.recipes.get(recipe_id)
    
    # Use utilities for consistent response formatting
    return LambdaHelpers.format_success_response(
        ApiRecipe.from_domain(recipe), 
        cors_headers=CORS_headers
    )
``` 