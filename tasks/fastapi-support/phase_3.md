# Phase 3: Context Endpoints

---
phase: 3
depends_on: [phase_2]
estimated_time: 24 hours
risk_level: medium
---

## Objective
Implement FastAPI endpoints for all 4 business contexts (products_catalog, recipes_catalog, client_onboarding, iam) with thread-safe implementations and async-compatible business logic. Ensure API response compatibility with Lambda endpoints.

## ⚠️ Critical Implementation Notes

**MANDATORY**: Each task MUST reference the corresponding AWS Lambda implementations to:
1. **Match exact endpoint patterns** - Use same method names, parameters, and response formats
2. **Avoid JSON conversion errors** - Follow correct `model_dump()` vs `model_dump_json()` patterns
3. **Include all endpoints** - Don't miss endpoints that exist in Lambda but not documented in task descriptions
4. **Use correct UoW methods** - Verify actual method names in UoW classes match Lambda usage
5. **Maintain response compatibility** - FastAPI responses must match Lambda response structures exactly

**Pattern Reference**: Always follow `tasks/fastapi-support/artifacts/fastapi_router_pattern.md`

## Prerequisites
- [ ] Phase 2 completed (authentication system)
- [ ] Cognito JWT validation working
- [ ] FastAPI middleware stack with error handling

# Tasks

## 3.1 Products Catalog Endpoints
- [x] 3.1.1 Create products router using helper functions
  - Files: `src/runtimes/fastapi/routers/products.py`
  - Purpose: Products query, fetch, search, create operations using helper functions and composition
  - AWS Lambda Reference: `src/contexts/products_catalog/aws_lambda/` (fetch_product.py, get_product_by_id.py, search_product_similar_name.py, create_product.py, fetch_product_source_name.py, get_product_source_name_by_id.py)
  - Example:
    ```python
    # src/runtimes/fastapi/routers/products.py
    from fastapi import APIRouter, Depends, Query
    from src.runtimes.fastapi.routers.helpers import (
        create_success_response, 
        create_paginated_response, 
        create_router
    )
    from src.contexts.products_catalog.fastapi.dependencies import get_bus
    
    router = create_router(prefix="/products", tags=["products"])
    
    @router.get("/query")
    async def query_products(
        page: int = Query(1, ge=1),
        limit: int = Query(50, ge=1, le=100),
        bus = Depends(get_bus)
    ):
        """Query products with pagination."""
        # Business logic here
        products = []  # Get from bus
        total = 0      # Get from bus
        
        return create_paginated_response(
            data=products,
            total=total,
            page=page,
            limit=limit
        )
    
    @router.get("/{product_id}")
    async def get_product(
        product_id: str,
        bus = Depends(get_bus)
    ):
        """Get single product."""
        # Business logic here
        product = {}  # Get from bus
        
        return create_success_response(product)
    ```
- [x] 3.1.2 Implement product query endpoints
  - Files: `src/runtimes/fastapi/routers/products.py`
  - Purpose: `/products/query`, `/products/fetch`, `/products/search` using helper functions
  - AWS Lambda Reference: `src/contexts/products_catalog/aws_lambda/fetch_product.py`, `src/contexts/products_catalog/aws_lambda/search_product_similar_name.py`
- [x] 3.1.3 Add product creation endpoints
  - Files: `src/runtimes/fastapi/routers/products.py`
  - Purpose: `/products/create` with validation using helper functions
  - AWS Lambda Reference: `src/contexts/products_catalog/aws_lambda/create_product.py`
  - Example:
    ```python
    # Additional endpoints in products.py
    from fastapi import HTTPException
    from pydantic import BaseModel
    
    class CreateProductRequest(BaseModel):
        name: str
        description: str
        price: float
    
    @router.post("/create")
    async def create_product(
        request: CreateProductRequest,
        bus = Depends(get_bus)
    ):
        """Create new product."""
        try:
            # Business logic here
            product = {}  # Create via bus
            
            return create_success_response(
                product, 
                status_code=201
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    ```
- [x] 3.1.4 Test products endpoints
  - Files: `tests/integration/contexts/fastapi/test_products_endpoints.py`
  - Purpose: Validate products functionality
  - Completed: Behavior-focused tests with fakes instead of mocks, following testing principles

## 3.2 Recipes Catalog Endpoints
- [x] 3.2.1 Create recipes router using established pattern
  - Files: `src/runtimes/fastapi/routers/recipes.py`
  - Purpose: Recipes, meals, clients, shopping lists using established FastAPI router pattern
  - Pattern: `tasks/fastapi-support/artifacts/fastapi_router_pattern.md`
  - AWS Lambda Reference: `src/contexts/recipes_catalog/aws_lambda/` (recipe/, meal/, client/, shopping_list/, tag/)
  - Completed: Comprehensive router with recipes, meals, clients, and shopping list endpoints following established pattern
- [x] 3.2.2 Implement recipe endpoints
  - Files: `src/runtimes/fastapi/routers/recipes.py`
  - Purpose: `/recipes/*` endpoints using helper functions
  - AWS Lambda Reference: `src/contexts/recipes_catalog/aws_lambda/recipe/`
  - Completed: Recipe query and get by ID endpoints with exact Lambda implementation patterns
- [x] 3.2.3 Add meals and clients endpoints
  - Files: `src/runtimes/fastapi/routers/recipes.py`
  - Purpose: `/meals/*`, `/clients/*` endpoints using helper functions
  - AWS Lambda Reference: `src/contexts/recipes_catalog/aws_lambda/meal/`, `src/contexts/recipes_catalog/aws_lambda/client/`
  - Completed: Meal and client query/get endpoints with exact Lambda implementation patterns
- [x] 3.2.4 Implement shopping list endpoints
  - Files: `src/runtimes/fastapi/routers/recipes.py`
  - Purpose: `/shopping-list/*` endpoints using helper functions
  - AWS Lambda Reference: `src/contexts/recipes_catalog/aws_lambda/shopping_list/`
  - Completed: Shopping list recipes endpoint with exact Lambda implementation patterns
- [x] 3.2.5 Test recipes endpoints
  - Files: `tests/integration/contexts/fastapi/test_recipes_endpoints.py`
  - Purpose: Validate recipes functionality
  - Completed: Comprehensive test suite validating endpoint existence, authentication requirements, and router integration

## 3.3 Client Onboarding Endpoints
- [x] 3.3.1 Create client onboarding router using established pattern
  - Files: `src/runtimes/fastapi/routers/client_onboarding.py`
  - Purpose: Forms, webhooks, query responses using established FastAPI router pattern
  - Pattern: `tasks/fastapi-support/artifacts/fastapi_router_pattern.md`
  - AWS Lambda Reference: `src/contexts/client_onboarding/aws_lambda/` (create_form.py, update_form.py, delete_form.py, query_responses.py, bulk_query_responses.py, webhook_processor.py)
  - Completed: Comprehensive router with forms, webhooks, and query responses endpoints following established pattern
- [x] 3.3.2 Implement forms endpoints
  - Files: `src/runtimes/fastapi/routers/client_onboarding.py`
  - Purpose: `/forms/*` endpoints using helper functions
  - AWS Lambda Reference: `src/contexts/client_onboarding/aws_lambda/create_form.py`, `src/contexts/client_onboarding/aws_lambda/update_form.py`, `src/contexts/client_onboarding/aws_lambda/delete_form.py`
  - Completed: POST /forms (create), PATCH /forms/{form_id} (update), DELETE /forms/{form_id} (delete) with exact Lambda implementation patterns
- [x] 3.3.3 Add webhooks endpoints
  - Files: `src/runtimes/fastapi/routers/client_onboarding.py`
  - Purpose: `/webhooks/*` endpoints using helper functions
  - AWS Lambda Reference: `src/contexts/client_onboarding/aws_lambda/webhook_processor.py`
  - Completed: POST /webhook endpoint with exact Lambda implementation patterns
- [x] 3.3.4 Implement query responses endpoints
  - Files: `src/runtimes/fastapi/routers/client_onboarding.py`
  - Purpose: `/query-responses/*` endpoints using helper functions
  - AWS Lambda Reference: `src/contexts/client_onboarding/aws_lambda/query_responses.py`, `src/contexts/client_onboarding/aws_lambda/bulk_query_responses.py`
  - Completed: POST /query-responses (single), POST /bulk-query-responses (bulk) with exact Lambda implementation patterns
- [x] 3.3.5 Test client onboarding endpoints
  - Files: `tests/integration/contexts/fastapi/test_client_onboarding_endpoints.py`
  - Purpose: Validate client onboarding functionality
  - Completed: Comprehensive test suite validating endpoint existence, authentication requirements, router integration, and response format compatibility

## 3.4 IAM Endpoints
- [ ] 3.4.1 Create IAM router using established pattern
  - Files: `src/runtimes/fastapi/routers/iam.py`
  - Purpose: Users, roles, assignments using established FastAPI router pattern
  - Pattern: `tasks/fastapi-support/artifacts/fastapi_router_pattern.md`
  - AWS Lambda Reference: `src/contexts/iam/aws_lambda/` (create_user.py, assign_role.py)
- [ ] 3.4.2 Implement users endpoints
  - Files: `src/runtimes/fastapi/routers/iam.py`
  - Purpose: `/users/*` endpoints using helper functions
  - AWS Lambda Reference: `src/contexts/iam/aws_lambda/create_user.py`
- [ ] 3.4.3 Add roles endpoints
  - Files: `src/runtimes/fastapi/routers/iam.py`
  - Purpose: `/roles/*` endpoints using helper functions
  - AWS Lambda Reference: `src/contexts/iam/aws_lambda/` (check for role-related handlers)
- [ ] 3.4.4 Implement role assignment endpoints
  - Files: `src/runtimes/fastapi/routers/iam.py`
  - Purpose: `/assign-role/*` endpoints using helper functions
  - AWS Lambda Reference: `src/contexts/iam/aws_lambda/assign_role.py`
- [ ] 3.4.5 Test IAM endpoints
  - Files: `tests/integration/contexts/fastapi/test_iam_endpoints.py`
  - Purpose: Validate IAM functionality

## 3.5 Thread Safety & Async Compatibility
- [x] 3.5.1 Ensure all endpoints are thread-safe
  - Files: `src/runtimes/fastapi/routers/`
  - Purpose: No shared mutable state, request-scoped dependencies, helper functions are stateless
  - Completed: Thread safety validated - all endpoints use request-scoped dependencies, stateless helper functions, and proper async patterns
  - Artifacts: `phase_3_thread_safety_analysis.md`
- [x] 3.5.2 Validate async business logic
  - Files: `src/runtimes/fastapi/routers/`
  - Purpose: All I/O operations are async-compatible, helper functions work with async
  - Completed: Async compatibility validated - all endpoints use proper async/await patterns, non-blocking I/O operations, and async-compatible helper functions
  - Artifacts: `phase_3_async_compatibility_analysis.md`
- [x] 3.5.3 Test concurrent request handling
  - Files: `tests/integration/contexts/fastapi/test_concurrent_requests.py`
  - Purpose: Validate thread safety under load
  - Completed: Concurrent request handling validated - comprehensive test suite validates thread safety, isolation, error handling, and AnyIO patterns
  - Artifacts: `test_concurrent_request_patterns.py`

## 3.6 API Compatibility Testing
- [ ] 3.6.1 Create compatibility test suite
  - Files: `tests/integration/contexts/fastapi/test_api_compatibility.py`
  - Purpose: Compare FastAPI vs Lambda responses
- [ ] 3.6.2 Test response format consistency
  - Files: `tests/integration/contexts/fastapi/test_response_format.py`
  - Purpose: Ensure identical response structures
- [ ] 3.6.3 Validate error response compatibility
  - Files: `tests/integration/contexts/fastapi/test_error_responses.py`
  - Purpose: Match Lambda error response format

## Validation
- [ ] All routers: `uv run python -c "from src.runtimes.fastapi.routers import *; print('Routers OK')"`
- [ ] Helper functions: `uv run python -c "from src.runtimes.fastapi.routers.helpers import *; print('Helpers OK')"`
- [ ] Endpoint tests: `uv run python -m pytest tests/integration/contexts/fastapi/test_*_endpoints.py`
- [ ] Compatibility: `uv run python -m pytest tests/integration/contexts/fastapi/test_api_compatibility.py`
- [ ] Performance: `uv run python -m pytest tests/performance/contexts/fastapi/test_endpoint_performance.py`

## AWS Lambda Implementation Reference Summary

### Products Catalog (`src/contexts/products_catalog/aws_lambda/`)
- ✅ **COMPLETED** - All endpoints implemented and tested
- Files: `fetch_product.py`, `get_product_by_id.py`, `search_product_similar_name.py`, `create_product.py`, `fetch_product_source_name.py`, `get_product_source_name_by_id.py`

### Recipes Catalog (`src/contexts/recipes_catalog/aws_lambda/`)
- 📋 **TODO** - Reference subdirectories: `recipe/`, `meal/`, `client/`, `shopping_list/`, `tag/`
- Files: Check each subdirectory for specific Lambda handlers

### Client Onboarding (`src/contexts/client_onboarding/aws_lambda/`)
- 📋 **TODO** - Reference files: `create_form.py`, `update_form.py`, `delete_form.py`, `query_responses.py`, `bulk_query_responses.py`, `webhook_processor.py`
- Also check: `shared/` subdirectory

### IAM (`src/contexts/iam/aws_lambda/`)
- 📋 **TODO** - Reference files: `create_user.py`, `assign_role.py`
- Note: Limited Lambda handlers available - may need to check for additional endpoints
