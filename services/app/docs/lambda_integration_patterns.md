# LambdaHelpers Integration with Existing Patterns

This document explains how LambdaHelpers integrates seamlessly with existing proven patterns in the codebase, ensuring **zero breaking changes** while improving consistency.

## Architecture Philosophy

LambdaHelpers follows the **"enhance, don't replace"** principle:

- ✅ **Keep working patterns** - `@lambda_exception_handler`, `MessageBus`, `IAMProvider`
- ✅ **Add consistency utilities** - Event parsing and response formatting
- ✅ **Preserve business logic** - No changes to domain logic or commands
- ✅ **Maintain performance** - No additional overhead, improved TypeAdapter usage

## Integration Map

```
┌─────────────────────────────────────────────────────────────┐
│                     Lambda Handler                         │
├─────────────────────────────────────────────────────────────┤
│ @lambda_exception_handler          ← EXISTING (PRESERVED)  │
│ ├─ LambdaHelpers.extract_*         ← NEW (ADDED)          │
│ ├─ IAMProvider.get() / internal    ← EXISTING (PRESERVED)  │
│ ├─ MessageBus + UnitOfWork         ← EXISTING (PRESERVED)  │
│ └─ LambdaHelpers.format_*_response ← NEW (ADDED)          │
└─────────────────────────────────────────────────────────────┘
```

## Pattern Integration Details

### 1. @lambda_exception_handler Integration

**How it works**: LambdaHelpers works **inside** the exception handler, not around it.

```python
@lambda_exception_handler  # ← Handles ALL exceptions (PRESERVED)
async def async_handler(event, context):
    # LambdaHelpers utilities work safely inside
    user_id = LambdaHelpers.extract_user_id(event)  # ← Safe extraction
    recipe_id = LambdaHelpers.extract_path_parameter(event, "id")
    
    # Any exception here is caught by @lambda_exception_handler
    # including business logic errors, validation errors, etc.
    
    # Business logic (may throw exceptions)
    bus: MessageBus = container.bootstrap()
    async with bus.uow as uow:
        recipe = await uow.recipes.get(recipe_id)  # May throw
    
    # LambdaHelpers response formatting (safe)
    return LambdaHelpers.format_success_response(
        data=ApiRecipe.from_domain(recipe),
        cors_headers=CORS_headers
    )
```

**Key Benefits**:
- ✅ **Exception handler still catches everything** - No duplicate error handling
- ✅ **Safe utilities** - LambdaHelpers methods return None/defaults on errors
- ✅ **Consistent error format** - When exceptions occur, they're handled uniformly
- ✅ **No performance impact** - No additional try/catch blocks

### 2. MessageBus + UnitOfWork Integration

**How it works**: LambdaHelpers handles I/O layers, MessageBus handles business logic.

```python
@lambda_exception_handler
async def async_handler(event, context):
    # INPUT LAYER: LambdaHelpers extracts and validates
    user_id = LambdaHelpers.extract_user_id(event)
    body_dict = LambdaHelpers.extract_request_body(event, as_dict=True)
    
    if not body_dict:
        return LambdaHelpers.format_error_response(
            message="Request body required", 
            status_code=400, 
            cors_headers=CORS_headers
        )
    
    # BUSINESS LAYER: MessageBus handles domain logic (UNCHANGED)
    command = CreateRecipeCommand(**body_dict, author_id=user_id)
    bus: MessageBus = container.bootstrap()
    async with bus.uow as uow:
        result = await bus.handle(command, uow)  # ← Domain logic untouched
        await uow.commit()
    
    # OUTPUT LAYER: LambdaHelpers formats response
    return LambdaHelpers.format_success_response(
        data={"id": str(result.id), "message": "Recipe created"},
        status_code=201,
        cors_headers=CORS_headers
    )
```

**Key Benefits**:
- ✅ **Clean separation** - I/O vs business logic clearly separated
- ✅ **Business logic unchanged** - Commands, handlers, UoW patterns preserved
- ✅ **Consistent I/O handling** - All Lambda handlers parse/format the same way
- ✅ **Testable layers** - Business logic can be tested independently

### 3. IAMProvider Integration

**How it works**: LambdaHelpers simplifies user extraction, IAMProvider handles authorization.

```python
@lambda_exception_handler
async def async_handler(event, context):
    # EXTRACT: LambdaHelpers gets user ID consistently
    user_id = LambdaHelpers.extract_user_id(event)
    
    # AUTHORIZE: IAMProvider handles authorization (UNCHANGED)
    response: dict = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response  # ← IAM response format preserved
    
    current_user: SeedUser = response["body"]
    
    # BUSINESS LOGIC: Use authorized user
    bus: MessageBus = container.bootstrap()
    async with bus.uow as uow:
        recipes = await uow.recipes.get_by_author(current_user.id)
    
    # RESPOND: LambdaHelpers formats response
    return LambdaHelpers.format_success_response(
        data=[ApiRecipe.from_domain(r) for r in recipes],
        cors_headers=CORS_headers
    )
```

**Different Auth Patterns Supported**:

```python
# Recipe context: IAMProvider.get()
response = await IAMProvider.get(user_id)

# IAM context: internal.get()
response = await internal.get(caller_user_id, "iam")

# Development: LocalStack bypass
if LambdaHelpers.is_localstack_environment():
    current_user = SeedUser(id=user_id or "dev_user")
else:
    response = await IAMProvider.get(user_id)
```

### 4. CORS Headers Integration

**How it works**: LambdaHelpers standardizes CORS header inclusion across all responses.

```python
from ..CORS_headers import CORS_headers  # ← Existing CORS configuration

@lambda_exception_handler
async def async_handler(event, context):
    # ... business logic ...
    
    # SUCCESS: CORS headers included automatically
    return LambdaHelpers.format_success_response(
        data=recipe_data,
        cors_headers=CORS_headers  # ← Existing CORS config
    )
    
    # ERROR: CORS headers included in errors too
    return LambdaHelpers.format_error_response(
        message="Not found",
        status_code=404,
        cors_headers=CORS_headers  # ← Don't forget in errors!
    )
```

**Benefits**:
- ✅ **Consistent CORS** - All responses include proper headers
- ✅ **Existing config preserved** - Uses your current CORS_headers settings
- ✅ **Error responses fixed** - CORS headers in error responses too
- ✅ **No configuration changes** - Works with existing CORS setup

### 5. Custom Serializer Integration

**How it works**: LambdaHelpers supports existing custom serialization patterns.

```python
from src.contexts.seedwork.shared.adapters.api_schemas.custom_serializer import custom_serializer

@lambda_exception_handler
async def async_handler(event, context):
    # ... business logic ...
    
    complex_data = {
        "recipes": recipes,
        "metadata": complex_metadata_with_dates,
        "user_preferences": user_prefs
    }
    
    # LambdaHelpers respects custom serializer
    return LambdaHelpers.format_success_response(
        data=complex_data,
        cors_headers=CORS_headers,
        custom_serializer=custom_serializer  # ← Existing serializer
    )
```

**When to use**:
- ✅ **Complex data structures** with custom types
- ✅ **Date/datetime serialization** needs
- ✅ **Backwards compatibility** with existing APIs
- ✅ **Special formatting requirements**

### 6. TypeAdapter Integration

**How it works**: LambdaHelpers works alongside TypeAdapters for collection endpoints.

```python
from pydantic import TypeAdapter
from src.contexts.shared_kernel.schemas.collection_response import (
    create_paginated_response, 
    extract_pagination_from_query
)

# MODULE LEVEL: Create TypeAdapters once per cold start
recipe_list_adapter = TypeAdapter(list[ApiRecipe])
recipe_collection_adapter = TypeAdapter(CollectionResponse[ApiRecipe])

@lambda_exception_handler
async def async_handler(event, context):
    # EXTRACT: LambdaHelpers handles event parsing
    user_id = LambdaHelpers.extract_user_id(event)
    query_params = LambdaHelpers.extract_query_parameters(event)
    page, page_size = extract_pagination_from_query(query_params)
    
    # AUTHORIZE: Existing IAM pattern
    response = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response
    
    # BUSINESS: Existing MessageBus pattern
    bus: MessageBus = container.bootstrap()
    async with bus.uow as uow:
        recipes = await uow.recipes.query(limit=page_size, offset=(page-1)*page_size)
        total_count = await uow.recipes.count()
    
    # FORMAT: Choose between simple list or paginated response
    api_recipes = [ApiRecipe.from_domain(r) for r in recipes]
    
    # Option A: Simple list response
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": recipe_list_adapter.dump_json(api_recipes).decode('utf-8')
    }
    
    # Option B: Paginated response
    collection = create_paginated_response(
        items=api_recipes,
        total_count=total_count,
        page_size=page_size,
        current_page=page
    )
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": recipe_collection_adapter.dump_json(collection).decode('utf-8')
    }
```

**Performance Benefits**:
- ✅ **1.79x faster serialization** (from performance tests)
- ✅ **Module-level creation** - TypeAdapters created once per cold start
- ✅ **Memory efficient** - Reused across all handler invocations
- ✅ **Type safe** - Full compile-time type checking

### 7. Container + Bootstrap Integration

**How it works**: LambdaHelpers doesn't interfere with dependency injection patterns.

```python
from src.contexts.recipes_catalog.core.bootstrap.container import Container

container = Container()  # ← Existing container setup

@lambda_exception_handler
async def async_handler(event, context):
    # LambdaHelpers: Input parsing
    user_id = LambdaHelpers.extract_user_id(event)
    recipe_id = LambdaHelpers.extract_path_parameter(event, "id")
    
    # Container: Dependency injection (UNCHANGED)
    bus: MessageBus = container.bootstrap()
    
    # UnitOfWork: Database context (UNCHANGED)
    async with bus.uow as uow:
        recipe = await uow.recipes.get(recipe_id)
        # ... other repository operations
    
    # LambdaHelpers: Output formatting
    return LambdaHelpers.format_success_response(
        data=ApiRecipe.from_domain(recipe),
        cors_headers=CORS_headers
    )
```

### 8. Validation + Pydantic Integration

**How it works**: LambdaHelpers simplifies request parsing, Pydantic handles validation.

```python
@lambda_exception_handler
async def async_handler(event, context):
    # EXTRACT: LambdaHelpers safely extracts request body
    body_dict = LambdaHelpers.extract_request_body(event, as_dict=True)
    
    if not body_dict:
        return LambdaHelpers.format_error_response(
            message="Request body is required",
            status_code=400,
            cors_headers=CORS_headers
        )
    
    # VALIDATE: Pydantic validation (UNCHANGED)
    try:
        recipe_data = ApiRecipe(**body_dict)
    except ValidationError as e:
        return LambdaHelpers.format_error_response(
            message=f"Validation error: {str(e)}",
            status_code=400,
            cors_headers=CORS_headers
        )
    
    # BUSINESS: Domain conversion (UNCHANGED)
    domain_recipe = recipe_data.to_domain()
    
    # ... rest of handler
```

## Environment-Specific Patterns

### Development vs Production

```python
@lambda_exception_handler
async def async_handler(event, context):
    user_id = LambdaHelpers.extract_user_id(event)
    
    # DEVELOPMENT: Skip auth in LocalStack
    if LambdaHelpers.is_localstack_environment():
        current_user = SeedUser(id=user_id or "dev_user")
    else:
        # PRODUCTION: Full auth required
        response = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
        current_user = response["body"]
    
    # Business logic same for both environments
    # ...
```

### Context-Specific Auth Patterns

```python
def get_auth_for_context(context_name: str, user_id: str):
    """Factory pattern for different auth methods."""
    if context_name == "iam":
        return internal.get(user_id, "iam")
    elif context_name == "recipes":
        return IAMProvider.get(user_id)
    elif context_name == "products":
        return IAMProvider.get(user_id)
    else:
        raise ValueError(f"Unknown context: {context_name}")

@lambda_exception_handler
async def async_handler(event, context):
    user_id = LambdaHelpers.extract_user_id(event)
    
    # Context-aware auth (preserves existing patterns)
    response = await get_auth_for_context("recipes", user_id)
    if response.get("statusCode") != 200:
        return response
    
    # ... rest of handler
```

## Migration Strategy

### Phase 1: Add LambdaHelpers (Zero Breaking Changes)
1. **Import LambdaHelpers** in existing handlers
2. **Replace event parsing** with `extract_*` methods
3. **Replace response building** with `format_*_response` methods
4. **Keep everything else unchanged**

### Phase 2: Optimize Collections (Performance Gains)
1. **Add TypeAdapters** at module level for collection endpoints
2. **Replace manual JSON serialization** with TypeAdapter.dump_json()
3. **Add pagination utilities** where needed

### Phase 3: Standardize Patterns (Consistency)
1. **Standardize error responses** across all contexts
2. **Unify CORS header handling** 
3. **Document best practices** for new endpoints

## Testing Integration

LambdaHelpers preserves existing testing patterns:

```python
# Unit tests: Test business logic independently (UNCHANGED)
async def test_recipe_creation():
    command = CreateRecipeCommand(name="Test Recipe", author_id="user123")
    bus = MockMessageBus()
    async with bus.uow as uow:
        result = await bus.handle(command, uow)
    assert result.name == "Test Recipe"

# Integration tests: Test full Lambda handler (ENHANCED)
async def test_lambda_handler():
    event = {
        "requestContext": {"authorizer": {"claims": {"sub": "user123"}}},
        "pathParameters": {"id": "recipe123"},
        "body": json.dumps({"name": "Test Recipe"})
    }
    
    response = await async_handler(event, {})
    
    assert response["statusCode"] == 200
    assert "Access-Control-Allow-Origin" in response["headers"]  # CORS included
    body = json.loads(response["body"])
    assert body["name"] == "Test Recipe"
```

## Best Practices Summary

1. **Preserve Working Patterns**
   - ✅ Keep `@lambda_exception_handler`
   - ✅ Keep existing auth methods (IAMProvider, internal.get)
   - ✅ Keep MessageBus + UnitOfWork patterns
   - ✅ Keep domain logic unchanged

2. **Enhance with LambdaHelpers**
   - ✅ Use `extract_*` methods for event parsing
   - ✅ Use `format_*_response` for consistent responses
   - ✅ Include CORS headers in all responses
   - ✅ Use TypeAdapters for collections

3. **Performance Optimization**
   - ✅ Create TypeAdapters at module level
   - ✅ Use TypeAdapter.dump_json() for collections
   - ✅ Reuse existing custom_serializer where needed

4. **Consistency Standards**
   - ✅ Always include CORS headers in error responses
   - ✅ Use standard error message formats
   - ✅ Handle LocalStack environment consistently
   - ✅ Follow pagination patterns for collection endpoints

This integration approach ensures **zero breaking changes** while providing **significant improvements** in consistency, performance, and maintainability. 