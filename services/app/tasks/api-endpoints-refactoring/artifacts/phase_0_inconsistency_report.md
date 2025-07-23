# Cross-Context Inconsistency Report

## Executive Summary
Analysis of AWS Lambda endpoints across products_catalog, recipes_catalog, and iam contexts reveals significant inconsistencies in authentication patterns, error handling, response formats, and request processing that will be addressed in the standardization effort.

## Context Comparison Overview

| Aspect | Products Catalog | Recipes Catalog | IAM Context |
|--------|------------------|-----------------|-------------|
| **Endpoints Count** | Unknown* | 10 functions | 2 functions |
| **Auth Provider** | IAMProvider* | IAMProvider | Internal get() |
| **User Objects** | SeedUser* | SeedUser | Domain User |
| **UoW Usage** | Standard* | Explicit async with | Direct commands |
| **Error Types** | Standard* | Manual handling | Manual + typos |

*Requires completion of products analysis artifact

## Critical Inconsistencies

### 1. Authentication Architecture

#### Pattern Divergence
- **Recipes/Products**: `IAMProvider.get(user_id)` → `SeedUser` value object
- **IAM**: `internal.get(caller_user_id, "iam")` → Domain `User` object

#### Authorization Flow
- **Recipes**: User extracted from authorizer claims, then IAMProvider call
- **IAM**: Same claims extraction, but internal function call
- **Permission Checks**: 
  - Recipes: `current_user.has_permission(Permission.MANAGE_RECIPES)`
  - IAM: `current_user.has_permission("iam", Permission.MANAGE_ROLES)`

#### Issues
- Different user object types across contexts
- Inconsistent authorization provider usage
- Context-specific permission checking patterns

### 2. Error Response Standards

#### Status Code Inconsistencies
- **Entity Not Found**: 
  - Recipes: Mix of 403 and 404
  - IAM: 404 for not found, 409 for already exists
- **Authorization Errors**: All use 403 but different message formats
- **Validation Errors**: No consistent approach across contexts

#### Response Structure Variations
```json
// Recipes - Manual JSON
{"message": "Recipe not in database."}

// IAM - Manual JSON with typos
{"statuCode": 500, "body": "Internal server error."}  // Bug: statuCode

// No standardized error schema across any context
```

#### Critical Issues
- **IAM Context**: Contains `"statuCode"` typos (should be `"statusCode"`)
- **Missing Error Schemas**: No consistent error response format
- **Mixed Status Codes**: Same errors return different HTTP codes

### 3. Request Processing Patterns

#### Body Parsing
All contexts use manual parsing:
```python
body = json.loads(event.get("body", ""))
```
- No validation layer
- No error handling for malformed JSON
- Repeated boilerplate across all endpoints

#### Path Parameter Extraction
Inconsistent approaches:
```python
# Standard approach
recipe_id = event.get("pathParameters", {}).get("id")

# IAM with error handling
try:
    user_id = event["pathParameters"]["id"]
except KeyError:
    # Manual error response
```

### 4. Response Format Inconsistencies

#### Success Response Variations
- **Pydantic Models**: `api.model_dump_json()` (recipes)
- **Manual JSON**: `json.dumps({"message": "success"})` (all contexts)
- **Event Responses**: Cognito-specific format (IAM create_user)

#### CORS Headers
- **Consistent**: All contexts use shared `CORS_headers`
- **Import Pattern**: Consistent relative import pattern

### 5. Business Logic Integration

#### MessageBus Usage
```python
# All contexts - consistent pattern
bus: MessageBus = Container().bootstrap()
await bus.handle(cmd)
```

#### UnitOfWork Patterns
- **Recipes**: Explicit `async with bus.uow as uow:`
- **IAM**: Direct command handling without explicit UoW
- **Query vs Command**: Different patterns for read vs write operations

### 6. Logging and Observability

#### Correlation IDs
- **Consistent**: All call `generate_correlation_id()` at entry
- **Good Practice**: Enables request tracing across contexts

#### Debug Logging
- **Recipes**: Extensive debug logging of events, bodies, filters
- **IAM**: Minimal logging
- **Structure**: No consistent structured logging format

## Architecture Inconsistencies

### Dependency Initialization
- **Module-level vs Inline**: Mix of `container = Container()` patterns
- **Bootstrap Calls**: Repeated `Container().bootstrap()` boilerplate

### Error Handling Strategy
- **Decorator Usage**: Consistent `@lambda_exception_handler` (good)
- **Manual Exception Handling**: Inconsistent patterns within handlers
- **Response Building**: No centralized error response builder

### Request Validation
- **No Validation Layer**: All contexts do manual parsing
- **Schema Validation**: Pydantic models used inconsistently
- **Error Responses**: No validation error standards

## Performance Implications

### IAM Provider Calls
- **Per-Request Cost**: Every endpoint makes IAM call (except IAM context)
- **Caching Opportunity**: No evidence of IAM response caching
- **Network Overhead**: Repeated calls to same provider

### JSON Processing
- **Manual Parsing**: Could be slower than framework-based parsing
- **Validation Cost**: No early validation means processing invalid requests

## Security Considerations

### Authentication Bypass
- **Localstack Environment**: `IS_LOCALSTACK` check bypasses auth
- **Consistency**: Applied across contexts (good)
- **Risk**: Environment variable injection risk

### Permission Checking
- **Placement Inconsistency**: Before vs after business logic
- **Context Isolation**: IAM uses different permission model
- **User Context**: Some endpoints modify requests with user data

## Proposed Standardization Targets

### 1. Authentication Middleware
- Unified `IAMProvider` usage across all contexts
- Consistent `SeedUser` value object
- Standard permission checking patterns

### 2. Error Response Schema
```python
# Proposed standard
{
    "error": {
        "code": "ENTITY_NOT_FOUND",
        "message": "Recipe not found",
        "details": {"recipe_id": "123"}
    },
    "request_id": "correlation-id"
}
```

### 3. Request Processing Pipeline
- Standard body parsing with validation
- Centralized path parameter extraction
- Consistent query parameter handling

### 4. Response Formatting
- Standard success response schema
- Consistent HTTP status code usage
- Unified CORS header application

## Refactoring Priority Matrix

| Issue | Impact | Effort | Priority |
|-------|---------|--------|----------|
| Error response standardization | High | Medium | P1 |
| Authentication middleware | High | High | P1 |
| IAM typo fixes | Low | Low | P1 |
| Request validation layer | Medium | Medium | P2 |
| Response format unification | Medium | Low | P2 |
| Logging standardization | Low | Medium | P3 |

## Recommendations

### Immediate Actions (Phase 1)
1. Fix IAM `"statuCode"` typos
2. Design standard error response schema
3. Create authentication middleware framework

### Foundation Building (Phase 1)
1. Implement `BaseEndpointHandler` abstract class
2. Create request/response schema standards
3. Build error handling middleware

### Migration Strategy (Phases 2-3)
1. Migrate high-traffic endpoints first
2. Maintain backward compatibility
3. Implement feature flags for gradual rollout

### Quality Assurance
1. Performance benchmarking before/after
2. Integration testing across contexts
3. Monitoring for authentication issues

## Success Metrics
- **100% Error Response Consistency**: All contexts use standard schema
- **Zero Authentication Pattern Variance**: Single middleware approach
- **< 5% Performance Impact**: Benchmarked endpoint response times
- **Zero Breaking Changes**: Backward compatibility maintained 