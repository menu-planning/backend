# Recipes Catalog Endpoints Analysis

## Overview
Analysis of recipes_catalog AWS Lambda endpoints to understand current implementation patterns and identify inconsistencies.

## Endpoint Structure

### Directory Layout
```
src/contexts/recipes_catalog/aws_lambda/
├── CORS_headers.py
├── recipe/
│   ├── fetch_recipe.py
│   ├── create_recipe.py
│   ├── update_recipe.py
│   ├── get_recipe_by_id.py
│   ├── copy_recipe.py
│   ├── delete_recipe.py
│   └── rate_recipe.py
├── shopping_list/
│   └── fetch_recipe.py
├── client/
│   └── create_client.py
└── meal/
    └── get_meal_by_id.py
```

## Common Patterns Identified

### Authentication & Authorization
- **IAMProvider Integration**: All endpoints use `IAMProvider.get(user_id)` for user verification
- **Localstack Bypass**: Environment check `IS_LOCALSTACK` to skip auth in development
- **User Context**: Extracts user_id from `event["requestContext"]["authorizer"]["claims"]["sub"]`
- **Permission Checks**: Some endpoints check `Permission.MANAGE_RECIPES` vs user.id

### Error Handling
- **Decorator**: All use `@lambda_exception_handler` decorator
- **IAM Response Handling**: Check `response.get("statusCode") != 200` and return early
- **Entity Not Found**: Manual `EntityNotFoundException` handling with custom error responses
- **Status Codes**: Inconsistent use of 403 vs 404 for not found entities

### Request/Response Patterns
- **CORS Headers**: All return `CORS_headers` from shared module
- **Body Parsing**: Manual `json.loads(event.get("body", ""))` 
- **Path Parameters**: `event.get("pathParameters", {}).get("id")`
- **Query Parameters**: Complex handling in fetch endpoints with multiValueQueryStringParameters
- **Response Format**: Mix of manual JSON responses vs Pydantic model serialization

### Business Logic Integration
- **MessageBus**: All use `Container().bootstrap()` to get MessageBus
- **UnitOfWork**: Pattern: `async with bus.uow as uow:`
- **Command Pattern**: Convert API schemas to domain commands with `.to_domain()`
- **Repository Pattern**: Direct UoW repository access for queries

### Logging
- **Correlation IDs**: All call `generate_correlation_id()` at entry point
- **Debug Logging**: Extensive `logger.debug()` calls throughout handlers
- **Structured Data**: Log events, bodies, API objects, and filters

## Inconsistencies Identified

### Error Response Formats
- **Status Code Variance**: 
  - Entity not found: Some use 403, others use 404
  - User not authorized: Mix of 403 and different message formats
- **Response Structure**: 
  - Manual JSON: `{"message": "..."}`
  - No standardized error schema

### Authentication Patterns
- **Permission Checking**: Inconsistent placement (before vs after business logic)
- **User Context**: Some endpoints modify body with current_user.id, others don't
- **Error Responses**: Different IAM error handling approaches

### Request Processing
- **Body Parsing**: All manual, no validation layer
- **Query Parameter Handling**: Complex custom logic in fetch endpoints
- **Path Parameter Extraction**: Repeated boilerplate

### Response Handling
- **Success Responses**: 
  - Some return Pydantic JSON: `api.model_dump_json()`
  - Others return manual JSON: `json.dumps({"message": "..."})`
- **Status Codes**: Inconsistent success codes (200 vs 201)

### Dependency Initialization
- **Container**: Mix of module-level `container = Container()` vs inline
- **Bus Bootstrap**: Repeated `Container().bootstrap()` calls

## Performance Considerations
- **Multiple IAM Calls**: Each endpoint makes IAM provider call (potential optimization target)
- **UoW Pattern**: Proper async context management
- **Repository Queries**: Direct repository access, potential for query optimization
- **JSON Parsing**: Manual parsing without validation could be slower

## Architecture Strengths
- **Consistent Command Pattern**: Good separation of API schemas and domain commands
- **Async Architecture**: Proper use of async/await throughout
- **Domain Boundaries**: Clear separation between adapters, domain, and infrastructure
- **Error Decoration**: Centralized exception handling via decorator

## Refactoring Opportunities
1. **Standardized Error Responses**: Common error schemas and status codes
2. **Request Validation**: Centralized body parsing and validation
3. **Authentication Middleware**: Extract IAM provider logic to middleware
4. **Response Formatting**: Consistent success response patterns
5. **Dependency Injection**: Reduce boilerplate container bootstrap code

## Files Analyzed
- `fetch_recipe.py` (2 instances)
- `create_recipe.py`
- `update_recipe.py` 
- `get_recipe_by_id.py`
- `copy_recipe.py`
- `delete_recipe.py`
- `rate_recipe.py`
- `create_client.py`
- `get_meal_by_id.py`
- `CORS_headers.py`

**Total Endpoints**: 10 Lambda functions
**Common Dependencies**: IAMProvider, MessageBus, UnitOfWork, lambda_exception_handler
**Estimated Refactoring Complexity**: High due to authorization integration and business logic coupling 