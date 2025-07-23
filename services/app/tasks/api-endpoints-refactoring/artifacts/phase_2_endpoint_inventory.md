# Products Catalog Endpoint Inventory

**Analysis Date**: 2024-01-15T20:45:00Z  
**Phase**: 2.1.1 Endpoint Inventory  
**Total Endpoints**: 6 endpoints  

## Endpoint Summary

| Endpoint | HTTP Method | Complexity | Migration Priority | 
|----------|-------------|------------|-------------------|
| get_product_by_id.py | GET | LOW | 1 (Start here) |
| get_product_source_name_by_id.py | GET | LOW | 2 |
| search_product_similar_name.py | GET | MEDIUM | 3 |
| fetch_product_source_name.py | GET | MEDIUM | 4 |
| fetch_product.py | GET | HIGH | 5 |
| create_product.py | POST | HIGH | 6 (Most complex) |

## Detailed Analysis

### 1. get_product_by_id.py (LOW COMPLEXITY)
**Purpose**: Retrieve single product by ID  
**HTTP Method**: GET  
**Current Patterns**:
- Auth: `IAMProvider.get(user_id)` (basic auth, no permissions)
- Parsing: `event.get("pathParameters").get("id")` 
- Business Logic: Direct UOW `uow.products.get(product_id)`
- Response: `api.model_dump_json()` with CORS_headers

**Migration Tasks**:
- Replace path parsing with `LambdaHelpers.extract_path_parameter(event, 'id')`
- Replace manual response with `LambdaHelpers.format_success_response(api)`
- Use `LambdaHelpers.get_default_cors_headers()` 

**Risk Level**: LOW (Simple pattern, single model response)

### 2. get_product_source_name_by_id.py (LOW COMPLEXITY)  
**Purpose**: Retrieve source name by ID
**HTTP Method**: GET
**Current Patterns**:
- Auth: `IAMProvider.get(user_id)` (basic auth, no permissions)
- Parsing: `event.get("pathParameters").get("id")`
- Business Logic: Direct UOW `uow.sources.get(source_id)`
- Response: `{api.id: api.name}` **NOT JSON serialized** (bug!)

**Migration Tasks**:
- Replace path parsing with `LambdaHelpers.extract_path_parameter(event, 'id')`
- Fix response serialization with `LambdaHelpers.format_success_response({api.id: api.name})`
- Use `LambdaHelpers.get_default_cors_headers()`

**Risk Level**: LOW (Simple pattern + fixes existing bug)

### 3. search_product_similar_name.py (MEDIUM COMPLEXITY)
**Purpose**: Search products by name similarity  
**HTTP Method**: GET
**Current Patterns**:
- Auth: `IAMProvider.get(user_id)` (basic auth, no permissions)
- Parsing: `event.get("pathParameters").get("name")` + `urllib.parse.unquote()`
- Business Logic: Direct UOW `uow.products.list_top_similar_names(name)`
- Response: List serialization with `custom_serializer`

**Migration Tasks**:
- Replace path parsing with `LambdaHelpers.extract_path_parameter(event, 'name')`
- Handle URL decoding in utility method
- Replace list serialization with TypeAdapter pattern  
- Use `LambdaHelpers.format_success_response()` for collection

**Risk Level**: MEDIUM (Collection response + URL decoding + TypeAdapter)

### 4. fetch_product_source_name.py (MEDIUM COMPLEXITY)
**Purpose**: Query sources with filtering
**HTTP Method**: GET  
**Current Patterns**:
- Auth: `IAMProvider.get(user_id)` (basic auth, no permissions)
- Parsing: `event.get("queryStringParameters")` with field replacement (`-` to `_`)
- Business Logic: Direct UOW `uow.sources.query(filter=filters)`
- Response: Custom dict transformation `{id: name}` for each source

**Migration Tasks**:
- Replace query parsing with `LambdaHelpers.extract_query_parameters(event)`
- Handle field replacement logic in filtering
- Replace custom dict transformation with consistent pattern
- Use `LambdaHelpers.format_success_response()` 

**Risk Level**: MEDIUM (Query parameter processing + custom response format)

### 5. fetch_product.py (HIGH COMPLEXITY)
**Purpose**: Query products with complex filtering and pagination
**HTTP Method**: GET
**Current Patterns**:
- Auth: `IAMProvider.get(user_id)` (basic auth, no permissions) 
- Parsing: `event.get("multiValueQueryStringParameters")` with complex logic:
  - Field replacement (`-` to `_`)
  - Default values (limit=50, sort=-updated_at)
  - List flattening for single values
  - ApiProductFilter validation
- Business Logic: Direct UOW `uow.products.query(filter=filters)`
- Response: List serialization with `custom_serializer`

**Migration Tasks**:
- Replace complex query parsing with `LambdaHelpers.extract_multi_value_query_parameters(event)`
- Implement pagination utilities from shared_kernel
- Replace list serialization with TypeAdapter pattern
- Use `LambdaHelpers.format_success_response()` for collection

**Risk Level**: HIGH (Complex query processing + pagination + collection TypeAdapter)

### 6. create_product.py (HIGH COMPLEXITY)
**Purpose**: Create new product with authorization  
**HTTP Method**: POST
**Current Patterns**:
- Auth: `IAMProvider.get(user_id)` + permission check (`Permission.MANAGE_PRODUCTS`)
- Parsing: `event.get("body", "")` with ApiAddFoodProduct validation
- Business Logic: MessageBus + AddFoodProductBulk command  
- Response: Manual JSON response building with status 201
- Error Handling: Manual 403 response for insufficient permissions

**Migration Tasks**:
- Replace body parsing with `LambdaHelpers.extract_request_body(event, ApiAddFoodProduct)`
- Preserve existing IAM + permission pattern (working correctly)
- Replace manual success response with `LambdaHelpers.format_success_response({"message": "Products created successfully"}, status_code=201)`
- Replace manual error response with `LambdaHelpers.format_error_response("User does not have enough privilegies.", status_code=403)`

**Risk Level**: HIGH (Authorization + permissions + MessageBus + error handling)

## Current Infrastructure Analysis

### CORS Headers
**File**: `CORS_headers.py`
**Current Implementation**:
```python
CORS_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization, Content-Type", 
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
}
```

**Migration**: Replace with `LambdaHelpers.get_default_cors_headers()` everywhere

### Common Patterns to Replace

1. **Manual Event Parsing** → LambdaHelpers utilities:
   - `event.get("pathParameters").get("id")` → `LambdaHelpers.extract_path_parameter(event, 'id')`
   - `event.get("queryStringParameters")` → `LambdaHelpers.extract_query_parameters(event)`
   - `event.get("multiValueQueryStringParameters")` → `LambdaHelpers.extract_multi_value_query_parameters(event)`
   - `event.get("body", "")` → `LambdaHelpers.extract_request_body(event, model_class)`

2. **Manual Response Building** → LambdaHelpers formatting:
   - `{"statusCode": 200, "headers": CORS_headers, "body": json.dumps(...)}` → `LambdaHelpers.format_success_response(...)`
   - `{"statusCode": 201, "headers": CORS_headers, "body": json.dumps(...)}` → `LambdaHelpers.format_success_response(..., status_code=201)`
   - Manual error responses → `LambdaHelpers.format_error_response(...)`

3. **Collection Responses** → TypeAdapter patterns:
   - `json.dumps([model.model_dump() for model in items], default=custom_serializer)` → TypeAdapter collection response
   - Custom list transformations → Standardized collection patterns

4. **Auth Patterns** → Preserve existing (working correctly):
   - `IAMProvider.get(user_id)` patterns work well
   - Permission checks work correctly  
   - Localstack bypass logic preserved

## Migration Strategy

### Phase 2.2: Simple Endpoints (LOW RISK)
**Order**: get_product_by_id.py → get_product_source_name_by_id.py
**Focus**: Basic patterns, validate LambdaHelpers integration

### Phase 2.3: Collection Endpoints (MEDIUM RISK) 
**Order**: search_product_similar_name.py → fetch_product_source_name.py
**Focus**: TypeAdapter patterns, collection responses

### Phase 2.4: Complex Endpoints (HIGH RISK)
**Order**: fetch_product.py → create_product.py  
**Focus**: Complex parsing, authorization, comprehensive patterns

## Validation Requirements

For each migrated endpoint:
- [ ] All tests pass
- [ ] Response format unchanged (backward compatibility)
- [ ] Performance within 5% of baseline
- [ ] CORS headers correctly applied
- [ ] Error responses follow new schema
- [ ] Auth patterns preserved

## Dependencies Ready

✅ **LambdaHelpers utilities** available in `src/contexts/shared_kernel/endpoints/base_endpoint_handler.py`  
✅ **TypeAdapter utilities** available in `src/contexts/shared_kernel/schemas/collection_response.py`  
✅ **Documentation** complete with migration examples  
✅ **Testing framework** established with 103/103 tests passing  

**Ready for Task 2.1.2**: Prioritization and migration planning 