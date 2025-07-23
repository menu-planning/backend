# Products Catalog Migration Plan

**Created**: 2024-01-15T20:55:00Z  
**Phase**: 2.1.2 Migration Order Prioritization  
**Based on**: phase_2_endpoint_inventory.md analysis  

## Migration Strategy: Risk-Based Progression

**Philosophy**: Start with lowest-risk endpoints to validate patterns, then progress to complex endpoints with confidence in the utilities.

## Priority Order & Rationale

### Phase 2.2: Simple Endpoints (LOW RISK)
**Goal**: Validate LambdaHelpers integration with minimal risk

#### Priority 1: get_product_by_id.py  
**Risk Level**: LOWEST  
**Rationale**: 
- Simplest pattern (path parameter → single model response)
- Most straightforward LambdaHelpers integration 
- Single point of failure validation
- Quick win to build confidence

**Migration Steps**:
1. Replace `event.get("pathParameters").get("id")` → `LambdaHelpers.extract_path_parameter(event, 'id')`
2. Replace `{"statusCode": 200, "headers": CORS_headers, "body": api.model_dump_json()}` → `LambdaHelpers.format_success_response(api)`
3. Test backward compatibility 
4. Validate performance

#### Priority 2: get_product_source_name_by_id.py
**Risk Level**: LOW  
**Rationale**:
- Similar pattern to Priority 1
- **Bonus**: Fixes existing bug (missing JSON serialization)
- Validates LambdaHelpers with custom response format
- Builds on Priority 1 success

**Migration Steps**:
1. Replace path parameter extraction
2. Fix response serialization bug: `{api.id: api.name}` → `LambdaHelpers.format_success_response({api.id: api.name})`
3. Test bug fix doesn't break existing consumers
4. Validate JSON serialization working

### Phase 2.3: Collection Endpoints (MEDIUM RISK)  
**Goal**: Validate TypeAdapter patterns and collection responses

#### Priority 3: search_product_similar_name.py
**Risk Level**: MEDIUM  
**Rationale**:
- Introduces TypeAdapter collection pattern
- URL decoding complexity (urllib.parse.unquote)
- Collection response but simpler than fetch_product.py
- Tests TypeAdapter performance improvements

**Migration Steps**:
1. Replace path parameter extraction with URL decode handling
2. Implement TypeAdapter for ApiProduct collection
3. Replace `json.dumps([ApiProduct.from_domain(i).model_dump() for i in result], default=custom_serializer)` → TypeAdapter pattern
4. Use `LambdaHelpers.format_success_response()` for collection
5. Performance test TypeAdapter vs. custom_serializer

#### Priority 4: fetch_product_source_name.py  
**Risk Level**: MEDIUM
**Rationale**:
- Query parameter processing (field replacement `-` to `_`)
- Custom response format transformation  
- Validates query parameter utilities
- Prepares for complex fetch_product.py patterns

**Migration Steps**:
1. Replace `event.get("queryStringParameters")` → `LambdaHelpers.extract_query_parameters(event)`
2. Handle field replacement logic in filtering
3. Maintain custom dict transformation `{id: name}` pattern
4. Test query parameter edge cases

### Phase 2.4: Complex Endpoints (HIGH RISK)
**Goal**: Apply comprehensive patterns with full LambdaHelpers integration

#### Priority 5: fetch_product.py
**Risk Level**: HIGH  
**Rationale**:
- Most complex query parameter processing
- Multi-value query parameters
- Pagination logic  
- Large collection responses (performance critical)
- Foundation for similar endpoints in other contexts

**Migration Steps**:
1. Replace `event.get("multiValueQueryStringParameters")` → `LambdaHelpers.extract_multi_value_query_parameters(event)`
2. Implement pagination utilities from shared_kernel
3. Handle complex filtering logic (field replacement, defaults, list flattening)
4. Apply TypeAdapter for large collections (performance validation critical)
5. Test pagination edge cases
6. Comprehensive performance testing

#### Priority 6: create_product.py
**Risk Level**: HIGHEST  
**Rationale**:
- Only POST endpoint (write operation)
- Complex authorization (Permission.MANAGE_PRODUCTS)
- MessageBus integration (most complex business logic)
- Multiple error response paths 
- Status code 201 (non-200 success)
- Last to migrate - validates all patterns working together

**Migration Steps**:
1. Replace `event.get("body", "")` → `LambdaHelpers.extract_request_body(event, ApiAddFoodProduct)`
2. Preserve IAMProvider + permission check patterns (working correctly)
3. Replace manual 201 response → `LambdaHelpers.format_success_response({"message": "Products created successfully"}, status_code=201)`
4. Replace manual 403 error → `LambdaHelpers.format_error_response("User does not have enough privilegies.", status_code=403)`
5. Test authorization scenarios (valid user, invalid user, insufficient permissions)
6. Test MessageBus integration unchanged
7. Comprehensive error handling validation

## Risk Mitigation Strategies

### Low Risk Endpoints (Priorities 1-2)
**Mitigation**: 
- Individual endpoint testing
- Quick rollback capability
- Pattern validation before proceeding

### Medium Risk Endpoints (Priorities 3-4)
**Mitigation**:
- TypeAdapter performance validation required
- Collection response format testing
- Pagination utility validation  
- Query parameter edge case testing

### High Risk Endpoints (Priorities 5-6)
**Mitigation**:
- Comprehensive test suite execution
- Performance baseline comparison mandatory
- Authorization testing scenarios
- Error path validation
- Business logic preservation validation

## Validation Criteria per Priority

### Priority 1-2 (Simple): ✅ Ready if
- [ ] Response format identical to original
- [ ] Performance within 2% (simple endpoints)  
- [ ] All unit tests pass
- [ ] Manual API testing successful

### Priority 3-4 (Medium): ✅ Ready if  
- [ ] Collection responses identical
- [ ] TypeAdapter performance improvement validated
- [ ] Query parameter parsing edge cases covered
- [ ] Performance within 5% of baseline

### Priority 5-6 (Complex): ✅ Ready if
- [ ] All endpoint test suites pass
- [ ] Performance within 5% for fetch_product (high-traffic)
- [ ] Authorization scenarios fully tested
- [ ] Error handling comprehensive  
- [ ] Business logic (MessageBus) unchanged
- [ ] Integration testing successful

## Dependencies & Prerequisites

### Before Starting Priority 1:
✅ LambdaHelpers utility class available  
✅ All 103 shared_kernel tests passing  
✅ Documentation and examples ready  

### Before Starting Priority 3:
- [ ] Priorities 1-2 successfully migrated  
- [ ] TypeAdapter patterns validated  
- [ ] Collection response testing framework ready

### Before Starting Priority 5:  
- [ ] Priorities 1-4 successfully migrated
- [ ] Pagination utilities tested
- [ ] Performance baseline established
- [ ] Complex query parameter patterns validated

## Success Metrics

**Phase 2.2 Success**: Simple endpoints migrated with pattern validation  
**Phase 2.3 Success**: TypeAdapter performance improvements proven  
**Phase 2.4 Success**: All 6 endpoints migrated, 0 breaking changes, performance maintained  

## Rollback Plan

**Immediate Rollback**: Git revert for individual endpoint  
**Pattern Rollback**: Revert to manual patterns if utilities show issues  
**Emergency Rollback**: Feature flag to bypass new patterns  

**Next Task**: 2.1.3 Create migration checklist template 