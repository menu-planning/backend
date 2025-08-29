# Phase 3: Migration and Testing

---
phase: 3
depends_on: 2
estimated_time: 3-4 weeks
---

## Objective
Migrate all Lambda functions to use the unified middleware stack incrementally by context, leveraging the new timeout and cancel scope capabilities.

## Migration Pattern Discovered ✅

**IMPORTANT**: The unified middleware system is designed to **REPLACE** manual implementations, not add to them. The correct migration approach is:

### ❌ WRONG APPROACH (What We Initially Did)
```python
@lambda_handler(
    StructuredLoggingMiddleware(...),
    AuthenticationMiddleware(...),
    ExceptionHandlerMiddleware(...),
)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
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

### ✅ CORRECT APPROACH (Current Implementation)
```python
@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="context.handler_name",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,  # Handles event data extraction automatically
    ),
    client_onboarding_aws_auth_middleware(),  # Context-specific auth middleware
    aws_lambda_exception_handler_middleware(
        name="handler_exception_handler",
        logger_name="context.handler_name.errors",
    ),
    timeout=30.0,
    name="handler_name",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """
    Handler focuses purely on business logic. All cross-cutting concerns
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
        use_multi_value=True
    )
    
    # ✅ Business logic only - no manual logging, auth, or error handling
    # ✅ Just raise exceptions - middleware catches and formats them
    if not raw_body.strip():
        raise ValueError("Request body is required")
    
    # ✅ Execute business logic
    result = await business_service.do_something()
    
    # ✅ Return success response with LambdaHelpers CORS headers
    return {
        "statusCode": 200,
        "headers": LambdaHelpers.get_default_cors_headers(),
        "body": json.dumps(result)
    }

def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda function handler entry point."""
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
```

### Current Implementation Approach

**Decorator-Based Middleware**: The current implementation uses the `@async_endpoint_handler` decorator which:
1. ✅ **Provides clean, readable syntax** for middleware composition
2. ✅ **Handles all cross-cutting concerns** automatically
3. ✅ **Maintains type safety** with proper type annotations
4. ✅ **Integrates seamlessly** with the existing middleware system

**Key Benefits**:
- **Cleaner Code**: Decorator syntax is more intuitive than manual composition
- **Automatic Integration**: Middleware components work together seamlessly
- **Type Safety**: Full type checking support with ruff
- **Consistent Pattern**: All handlers follow the same middleware application pattern

### Key Benefits of Correct Approach
1. **No Code Duplication**: Middleware handles all cross-cutting concerns
2. **Cleaner Handlers**: Focus only on business logic
3. **Consistent Behavior**: All handlers use same middleware patterns
4. **Better Performance**: No redundant operations
5. **Easier Maintenance**: Single source of truth for each concern
6. **No Type Checking Issues**: Compatible with ruff and other type checkers

## Refactored LambdaHelpers Usage ✅

**IMPORTANT**: After refactoring `base_endpoint_handler.py`, the remaining `LambdaHelpers` are focused on:

### ✅ What LambdaHelpers Still Provides (Use These)
- **Event Parsing**: `extract_path_parameter()`, `extract_query_parameters()`, `extract_request_body()`
- **Query Processing**: `process_query_filters_from_aws_event()`, `normalize_kebab_case_keys()`, `flatten_single_item_lists()`
- **Response Formatting**: `get_default_cors_headers()`
- **Filter Validation**: `normalize_filter_values()`, `extract_pagination_params()`

### ❌ What LambdaHelpers No Longer Provides (Now Handled by Middleware)
- **Authentication**: `validate_user_authentication()` - Use auth middleware instead
- **Logging**: `extract_log_data()` - Use logging middleware instead
- **Error Handling**: `format_error_response()` - Use exception handler middleware instead
- **Environment Detection**: `is_localstack_environment()` - Use auth middleware instead

### Proper Usage Pattern
```python
# ✅ CORRECT: Use LambdaHelpers for event parsing and query processing
filters = LambdaHelpers.process_query_filters_from_aws_event(
    event=event,
    filter_schema_class=ApiRecipeFilter,
    use_multi_value=True
)

# ✅ CORRECT: Use LambdaHelpers for CORS headers
return {
    "statusCode": 200,
    "headers": LambdaHelpers.get_default_cors_headers(),
    "body": response_body
}

# ❌ WRONG: Don't use removed methods
# auth_result = await LambdaHelpers.validate_user_authentication(...)  # REMOVED
# log_data = LambdaHelpers.extract_log_data(event)  # REMOVED
# error_response = LambdaHelpers.format_error_response(...)  # REMOVED
```

# Tasks
- [x] 3.1 Migrate shared_kernel Lambda functions
  - Files: All Lambda handlers in `src/contexts/shared_kernel/`
  - Purpose: Test unified middleware with timeout handling in core context first
- [x] 3.2 Migrate client_onboarding context
  - Files: Lambda handlers in `src/contexts/client_onboarding/aws_lambda/`
  - Purpose: Apply unified middleware with timeout configuration to onboarding functions
  - **Pattern**: Use event["_auth_context"] from middleware, no manual auth/error handling
  - **Status**: COMPLETED ✅ - All 6 Lambda handlers migrated using @async_endpoint_handler decorator
  - **Migrated**: create_form.py, update_form.py, webhook_processor.py, bulk_query_responses.py, query_responses.py, delete_form.py
  - **Current Pattern**: @async_endpoint_handler with context-specific auth middleware and unified error handling
- [x] 3.3 Migrate products_catalog context
  - Files: Lambda handlers in `src/contexts/products_catalog/aws_lambda/`
  - Purpose: Apply unified middleware with timeout configuration to product functions
  - **Pattern**: Follow the @async_endpoint_handler decorator pattern documented above
  - **Status**: COMPLETED ✅ - All 6 Lambda handlers migrated using @async_endpoint_handler decorator
  - **Migrated**: create_product.py, fetch_product.py, get_product_by_id.py, search_product_similar_name.py, fetch_product_source_name.py, get_product_source_name_by_id.py
  - **Current Pattern**: @async_endpoint_handler with products_aws_auth_middleware and unified error handling
- [x] 3.4 Migrate recipes_catalog context
  - Files: Lambda handlers in `src/contexts/recipes_catalog/aws_lambda/`
  - Purpose: Apply unified middleware with timeout configuration to recipe functions
  - **Pattern**: Follow the @async_endpoint_handler decorator pattern documented above
  - **Status**: COMPLETED ✅ - All 8 Lambda handlers migrated using @async_endpoint_handler decorator
  - **Migrated**: create_recipe.py, fetch_recipe.py, get_recipe_by_id.py, update_recipe.py, delete_recipe.py, copy_recipe.py, rate_recipe.py
  - **Current Pattern**: @async_endpoint_handler with recipes_aws_auth_middleware and unified error handling
- [x] 3.5 Refactor base_endpoint_handler.py
  - Files: `src/contexts/shared_kernel/endpoints/base_endpoint_handler.py`
  - Purpose: Remove functionality now handled by middlewares and keep only essential event parsing and query processing helpers
  - **Status**: COMPLETED ✅ - Removed auth, logging, and error handling methods, kept event parsing and query processing helpers
  - **Removed Methods**: `validate_user_authentication()`, `extract_log_data()`, `format_error_response()`, `is_localstack_environment()`, `extract_user_id()`
  - **Kept Methods**: `extract_path_parameter()`, `process_query_filters_from_aws_event()`, `get_default_cors_headers()`, etc.
- [x] 3.6 Enforce proper LambdaHelpers usage across all contexts
  - Files: All Lambda handlers in migrated contexts
  - Purpose: Ensure all handlers use the refactored LambdaHelpers correctly and don't call removed methods
  - **Pattern**: Use LambdaHelpers only for event parsing, query processing, and CORS headers
  - **Validation**: Check that no handlers call removed methods like `validate_user_authentication()`
  - **Examples**: Update examples.md with proper usage patterns
  - **Status**: COMPLETED ✅ - All 20 Lambda handlers migrated to unified middleware pattern
  - **Migrated**: All meal, client, tag, and shopping list handlers in recipes_catalog context
  - **Removed**: rate_meal.py (not needed - no meal rating functionality exists)
  - **Validation**: No calls to removed LambdaHelpers methods, all handlers use proper middleware pattern
- [ ] 3.7 Comprehensive integration testing
  - Files: Test files across all contexts
  - Purpose: Ensure all functions work with unified middleware and timeout handling
- [ ] 3.8 FastAPI compatibility testing
  - Files: Test FastAPI integration scenarios
  - Purpose: Validate middleware works with web framework deployment

## Migration Benefits
- **Timeout Management**: Each context can configure appropriate timeouts
- **Cancel Scope Handling**: Proper exception propagation and cleanup
- **Exception Groups**: Better error handling and debugging
- **Performance**: Consistent middleware overhead across all contexts
- **Code Quality**: No duplication of cross-cutting concerns
- **Type Safety**: No type checking errors with ruff
- **Cleaner Handlers**: Focus only on business logic, use LambdaHelpers for event processing

## Validation
- [x] All Lambda functions use unified middleware: ✓
- [x] base_endpoint_handler.py refactored: ✓
- [x] Proper LambdaHelpers usage enforced: ✓ (Task 3.6 COMPLETED)
- [ ] Integration tests passing: `uv run python pytest tests/contexts/`
- [ ] Performance tests: Middleware overhead <5ms
- [ ] Error handling consistent across all contexts
- [ ] Authentication working uniformly
- [ ] **New**: Timeout handling working correctly in all contexts
- [ ] **New**: Cancel scope behavior validated across all scenarios
- [ ] **New**: No manual auth/error handling code duplication
- [ ] **New**: No type checking errors with ruff
- [x] **New**: No calls to removed LambdaHelpers methods ✓ 