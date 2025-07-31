# IAMProvider Usage Pattern Analysis

## Overview
Analysis of IAMProvider implementation and usage patterns across all contexts to understand current authentication integration points and identify standardization opportunities.

## IAMProvider Architecture

### Context-Specific Implementations
Each non-IAM context implements its own IAMProvider wrapper:

#### Products Catalog
```python
# src/contexts/products_catalog/core/adapters/internal_providers/iam/api.py
class IAMProvider:
    @staticmethod
    async def get(id: str) -> dict:
        response = await iam_api.get(id=id, caller_context="products_catalog")
        if response.get("statusCode") != 200:
            return response
        user = IAMUser(**json.loads(str(response["body"]))).to_domain()
        return {"statusCode": 200, "body": user}
```

#### Recipes Catalog
```python
# src/contexts/recipes_catalog/core/adapters/internal_providers/iam/api.py
class IAMProvider:
    @staticmethod
    async def get(id: str) -> dict:
        response = await iam_api.get(id=id, caller_context="recipes_catalog")
        if response.get("statusCode") != 200:
            return response
        user = IAMUser(**json.loads(str(response["body"]))).to_domain()
        return {"statusCode": 200, "body": user}
```

#### IAM Context (Direct Internal Call)
```python
# src/contexts/iam/aws_lambda/assign_role.py
response: dict = await internal.get(caller_user_id, "iam")
```

## Usage Patterns Across Endpoints

### Standard Authentication Flow
All non-IAM endpoints follow this pattern:
```python
@lambda_exception_handler
async def async_handler(event, context):
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
        current_user: SeedUser = response["body"]
```

### Endpoints Using IAMProvider

#### Products Catalog (3 endpoints found)
- `get_product_by_id.py` - Standard auth flow
- `get_product_source_name_by_id.py` - Standard auth flow  
- `fetch_product.py` - Standard auth flow
- `fetch_product_source_name.py` - Standard auth flow
- `search_product_similar_name.py` - Standard auth flow
- `create_product.py` - Standard auth + permission check

#### Recipes Catalog (15+ endpoints found)
- All recipe endpoints: create, update, delete, fetch, copy, rate, get_by_id
- All meal endpoints: create, update, delete, fetch, copy, get_by_id
- All client endpoints: create, update, delete, fetch, get_by_id
- All menu endpoints: create, update, delete
- Tag endpoints: fetch, get_by_id

#### IAM Context (1 endpoint using internal call)
- `assign_role.py` - Uses `internal.get()` directly

### Permission Checking Patterns

#### Simple Permission Check
```python
if not current_user.has_permission(Permission.MANAGE_RECIPES):
    return {"statusCode": 403, "headers": CORS_headers, "body": "..."}
```

#### Owner or Permission Check
```python
if not (current_user.has_permission(Permission.MANAGE_RECIPES) or current_user.id == author_id):
    return {"statusCode": 403, "headers": CORS_headers, "body": "..."}
```

#### IAM Context Permission Check
```python
if not current_user.has_permission("iam", Permission.MANAGE_ROLES):
    return {"statusCode": 403, "headers": CORS_headers, "body": "..."}
```

## Integration Points

### Common Integration Components
- **Authorizer Context**: All endpoints extract `user_id` from `event["requestContext"]["authorizer"]["claims"]["sub"]`
- **Localstack Bypass**: Environment variable `IS_LOCALSTACK` universally bypasses authentication
- **Error Handling**: Standard pattern of checking `response.get("statusCode") != 200`
- **User Objects**: Return `SeedUser` value objects for business logic

### Context-Specific Variations
- **Caller Context**: Each IAMProvider passes different `caller_context` parameter
- **User Domain Objects**: IAM context works with domain `User` objects instead of `SeedUser`
- **Permission Context**: IAM requires explicit context parameter for permission checks

## Implementation Details

### Wrapper Complexity
Each context duplicates the same wrapper logic:
1. Call internal IAM endpoint with context parameter
2. Check for error status codes
3. Parse JSON response 
4. Convert to domain `IAMUser` via Pydantic
5. Transform to `SeedUser` via `.to_domain()`
6. Return standardized response format

### Network Calls
- **Per-Request Cost**: Every authenticated endpoint makes IAM provider call
- **No Caching**: No evidence of response caching across contexts
- **Blocking**: Synchronous IAM calls block request processing

### Error Handling Inconsistencies
- **Response Passthrough**: IAM errors passed directly to client
- **No Transformation**: Raw IAM error responses not standardized to context error schemas
- **Status Code Variance**: Different contexts may handle IAM errors differently

## Identified Issues

### Code Duplication
- **Identical Logic**: Products and Recipes IAMProvider implementations are nearly identical
- **Schema Duplication**: Each context defines its own `IAMUser` schema
- **Repeated Boilerplate**: Same user extraction and error handling patterns across all endpoints

### Architectural Inconsistencies
- **IAM Self-Service**: IAM context bypasses its own provider pattern
- **Mixed User Objects**: `SeedUser` vs domain `User` creates integration complexity
- **Context Coupling**: Provider implementations tightly coupled to specific contexts

### Performance Implications
- **Network Overhead**: N+1 IAM calls for authenticated requests
- **No Connection Reuse**: Each call establishes new connection to IAM service
- **Serialization Cost**: JSON parse/serialize cycle for every user lookup

## Standardization Opportunities

### Unified IAMProvider
```python
# Proposed: Single IAMProvider in shared_kernel
class IAMProvider:
    @staticmethod 
    async def get_user(user_id: str, caller_context: str) -> SeedUser:
        # Unified implementation with caching, error handling, logging
```

### Middleware Integration
- **Authentication Middleware**: Extract IAM logic from individual endpoints
- **Caching Layer**: Implement request-scoped user context caching
- **Error Standardization**: Transform IAM errors to consistent response format

### Context Simplification
- **Remove Duplication**: Eliminate per-context IAMProvider implementations
- **Standardize Objects**: Use consistent `SeedUser` across all contexts
- **Permission Unification**: Consistent permission checking API

## Migration Impact

### Breaking Changes
- **Import Changes**: Endpoints will import from `shared_kernel` instead of context-specific paths
- **Method Signatures**: May require parameter adjustments
- **Error Responses**: Standardized error format may differ from current responses

### Performance Benefits
- **Reduced Network Calls**: Caching can eliminate redundant IAM lookups
- **Connection Pooling**: Shared provider can optimize connection reuse
- **Faster Response Times**: Middleware approach reduces per-endpoint overhead

### Implementation Complexity
- **Medium Risk**: Changes affect authentication flow for 20+ endpoints
- **Testing Requirements**: Must validate authentication across all contexts
- **Rollback Strategy**: Need feature flags for gradual migration

## Recommendations

### Phase 1: Foundation
1. Create unified `IAMProvider` in `shared_kernel`
2. Implement request-scoped caching
3. Add comprehensive logging and error handling

### Phase 2: Migration
1. Migrate high-traffic endpoints first
2. Use feature flags for gradual rollout
3. Maintain backward compatibility during transition

### Phase 3: Cleanup
1. Remove context-specific IAMProvider implementations
2. Standardize error response formats
3. Optimize performance with connection pooling

## Success Metrics
- **Code Reduction**: Eliminate 200+ lines of duplicated IAMProvider code
- **Performance**: Reduce authentication latency by 20%+ through caching
- **Consistency**: 100% unified error response format across contexts
- **Maintainability**: Single authentication logic source of truth 