# FastAPI Router Pattern - Established

## Overview
This document establishes the pattern for creating FastAPI routers that are compatible with both FastAPI and AWS Lambda implementations, following the same business logic patterns.

## Key Principles

### 1. Use Structured Filtering with Pydantic Models
Instead of individual query parameters, use Pydantic filter models with `Depends()`:

```python
@router.get("/query")
async def query_products(
    filters: ApiProductFilter = Depends(),  # FastAPI auto-converts query params
    bus: MessageBus = Depends(get_context_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
```

**Benefits:**
- Type safety and validation
- Automatic OpenAPI documentation
- Consistency with Lambda implementation
- Maintainable (add new filters in model, not function signature)

### 2. Use Bus/UoW Pattern (Not Internal Endpoints)
Follow the same pattern as Lambda implementation:

```python
# ✅ CORRECT - Use bus/UoW pattern
from src.contexts.products_catalog.core.services.uow import UnitOfWork
uow: UnitOfWork
async with bus.uow_factory() as uow:
    result: list = await uow.products.query(filters=filter_dict)

# ❌ INCORRECT - Don't use internal endpoints
from src.contexts.products_catalog.core.internal_endpoints.products.fetch import get_products
products_json = await get_products(filter_dict)
```

### 3. Use Correct JSON/Dict Conversion
**IMPORTANT**: Don't double-convert JSON!

```python
from pydantic import TypeAdapter

# Type adapter for JSON serialization (same as Lambda implementation)
ProductListTypeAdapter = TypeAdapter(list[ApiProduct])

# In endpoint:
api_products = []
for product in result:
    try:
        api_product = ApiProduct.from_domain(product)
        api_products.append(api_product)
    except Exception as e:
        conversion_errors += 1
        continue

# ✅ CORRECT - Convert to dict format for FastAPI response
products_data = [product.model_dump() for product in api_products]

# ❌ WRONG - Don't serialize to JSON then parse back to dict
# products_json = ProductListTypeAdapter.dump_json(api_products)
# products_data = json.loads(products_json)
```

**For single items:**
```python
# ✅ CORRECT
api_product = ApiProduct.from_domain(product)
product_data = api_product.model_dump()
return create_success_response(product_data)

# ❌ WRONG
# product_json = api_product.model_dump_json()
# product_data = json.loads(product_json)
```

### 4. Authentication Pattern
Use dependency injection for current user:

```python
def get_current_user(request: Request) -> User:
    """Get current authenticated user from request state."""
    if not hasattr(request.state, "auth_context"):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    auth_context: AuthContext = request.state.auth_context
    if not auth_context.is_authenticated or not auth_context.user_object:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return auth_context.user_object
```

### 5. Error Handling Pattern
Use consistent error handling with proper HTTP status codes:

```python
try:
    # Business logic here
    result = await business_operation()
    return create_success_response(result)
except HTTPException:
    raise  # Re-raise HTTP exceptions
except Exception as e:
    raise HTTPException(status_code=400, detail=f"Operation failed: {str(e)}")
```

### 6. Response Helper Functions
Use standardized response helpers:

```python
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_paginated_response,
    create_router,
)

# For single items
return create_success_response(data)

# For paginated lists
return create_paginated_response(
    data=items,
    total=total_count,
    page=page,
    limit=limit
)
```

## Complete Router Template

```python
"""FastAPI router for [context] endpoints."""

from fastapi import Depends, HTTPException, Query
from typing import Any
from pydantic import TypeAdapter

from src.contexts.[context].core.adapters.api_schemas.root_aggregate.api_[entity] import (
    Api[Entity],
)
from src.contexts.[context].core.adapters.api_schemas.root_aggregate.api_[entity]_filter import (
    Api[Entity]Filter,
)
from src.contexts.[context].core.services.uow import UnitOfWork
from src.contexts.[context].fastapi.dependencies import get_[context]_bus
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.[context].core.domain.value_objects.user import User
from src.contexts.shared_kernel.middleware.auth.authentication import AuthContext
from fastapi import Request
from src.runtimes.fastapi.routers.helpers import (
    create_success_response,
    create_paginated_response,
    create_router,
)

router = create_router(prefix="/[entities]", tags=["[entities]"])

# Type adapter for JSON serialization (same as Lambda implementation)
[Entity]ListTypeAdapter = TypeAdapter(list[Api[Entity]])


def get_current_user(request: Request) -> User:
    """Get current authenticated user from request state."""
    if not hasattr(request.state, "auth_context"):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    auth_context: AuthContext = request.state.auth_context
    if not auth_context.is_authenticated or not auth_context.user_object:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return auth_context.user_object


@router.get("/query")
async def query_[entities](
    filters: Api[Entity]Filter = Depends(),
    bus: MessageBus = Depends(get_[context]_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Query [entities] with pagination and filtering."""
    try:
        # Convert filters to dict for business logic compatibility
        filter_dict = filters.model_dump(exclude_none=True)
        
        # Query using bus/UoW pattern (same as Lambda implementation)
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            result: list = await uow.[entities].query(filters=filter_dict)
        
        # Convert domain entities to API format
        api_[entities] = []
        conversion_errors = 0
        
        for [entity] in result:
            try:
                api_[entity] = Api[Entity].from_domain([entity])
                api_[entities].append(api_[entity])
            except Exception as e:
                conversion_errors += 1
                continue
        
        # Convert to dict format for response
        [entities]_data = [entity.model_dump() for entity in api_[entities]]
        
        # Calculate pagination info
        page = (filter_dict.get("skip", 0) // filter_dict.get("limit", 50)) + 1
        limit = filter_dict.get("limit", 50)
        total = len([entities]_data)
        
        return create_paginated_response(
            data=[entities]_data,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to query [entities]: {str(e)}")


@router.get("/{[entity]_id}")
async def get_[entity](
    [entity]_id: str,
    bus: MessageBus = Depends(get_[context]_bus),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get a single [entity] by ID."""
    try:
        # Get using bus/UoW pattern (same as Lambda implementation)
        uow: UnitOfWork
        async with bus.uow_factory() as uow:
            [entity] = await uow.[entities].get([entity]_id)
        
        # Convert domain entity to API format
        api_[entity] = Api[Entity].from_domain([entity])
        [entity]_data = api_[entity].model_dump()
        return create_success_response([entity]_data)
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"[Entity] not found: {str(e)}")
```

## Validation Checklist

When implementing a new router, ensure:

- [ ] Uses structured filtering with Pydantic models
- [ ] Uses bus/UoW pattern (not internal endpoints)
- [ ] Uses TypeAdapter for JSON serialization
- [ ] Implements proper authentication with dependency injection
- [ ] Uses standardized error handling
- [ ] Uses response helper functions
- [ ] Follows naming conventions
- [ ] Imports are organized correctly
- [ ] No linting errors
- [ ] Can be imported successfully

## Critical Lessons Learned

### ❌ Common Mistakes to Avoid:

1. **Double JSON Conversion**: 
   - `model_dump_json()` returns JSON string, not dict
   - Don't call `json.loads()` on `model_dump_json()` result
   - Use `model_dump()` for dict conversion in FastAPI responses

2. **Wrong Method Names**:
   - Check actual UoW method names (e.g., `list_top_similar_names()`, not `search_similar_name()`)
   - Always verify method signatures in UoW classes

3. **Missing Endpoints**:
   - Review all Lambda handlers to identify all available endpoints
   - Don't assume endpoint patterns without checking actual implementations

4. **Incorrect Response Formats**:
   - Some endpoints return simplified formats (e.g., `{id: name}` mapping)
   - Match Lambda response structure exactly

### ✅ Correct Patterns:

1. **Single Item Response**:
   ```python
   api_entity = ApiEntity.from_domain(entity)
   entity_data = api_entity.model_dump()  # Returns dict
   return create_success_response(entity_data)
   ```

2. **List Response**:
   ```python
   api_entities = [ApiEntity.from_domain(e) for e in result]
   entities_data = [e.model_dump() for e in api_entities]  # List of dicts
   return create_success_response(entities_data)
   ```

3. **Simplified Response**:
   ```python
   api_entities = [ApiEntity.from_domain(e) for e in result]
   response_data = {e.id: e.name for e in api_entities}  # Custom mapping
   return create_success_response(response_data)
   ```

## Benefits of This Pattern

1. **Consistency**: Same business logic patterns as Lambda implementation
2. **Type Safety**: Pydantic validation and correct data conversion
3. **Maintainability**: Easy to add new filters and endpoints
4. **Documentation**: Automatic OpenAPI docs from Pydantic models
5. **Testing**: Easy to test with dependency injection
6. **Performance**: Direct bus/UoW access without extra layers
7. **Accuracy**: Matches Lambda response formats exactly
