# Endpoint Migration Checklist Template

**Purpose**: Standardized checklist for migrating Lambda endpoints to use LambdaHelpers utilities  
**Created**: 2024-01-15T21:05:00Z  
**Version**: 1.0  

## Pre-Migration Assessment

### Endpoint Information
- [ ] **Endpoint Name**: `[endpoint_filename].py`
- [ ] **HTTP Method**: `[GET|POST|PUT|DELETE]`
- [ ] **Complexity Level**: `[LOW|MEDIUM|HIGH]`
- [ ] **Migration Priority**: `[1-6 based on risk assessment]`

### Current Pattern Analysis
- [ ] **Auth Pattern**: Document current IAMProvider usage
- [ ] **Parsing Pattern**: Document current event parsing
- [ ] **Business Logic**: Document MessageBus vs. direct UOW usage
- [ ] **Response Pattern**: Document current response building
- [ ] **Error Handling**: Document current error response patterns
- [ ] **CORS Handling**: Document current CORS header usage

### Dependencies Check
- [ ] **LambdaHelpers Available**: Verify `src/contexts/shared_kernel/endpoints/base_endpoint_handler.py` accessible
- [ ] **TypeAdapter Available**: Verify `src/contexts/shared_kernel/schemas/collection_response.py` accessible (for collections)
- [ ] **Documentation Ready**: Verify migration examples available
- [ ] **Tests Baseline**: Run existing endpoint tests and document baseline

## Migration Execution Checklist

### Phase 1: Event Parsing Migration
- [ ] **Import LambdaHelpers**: Add `from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers`
- [ ] **Path Parameters**: Replace `event.get("pathParameters").get("param")` → `LambdaHelpers.extract_path_parameter(event, "param")`
- [ ] **Query Parameters**: Replace `event.get("queryStringParameters")` → `LambdaHelpers.extract_query_parameters(event)`
- [ ] **Multi-Value Query**: Replace `event.get("multiValueQueryStringParameters")` → `LambdaHelpers.extract_multi_value_query_parameters(event)`
- [ ] **Request Body**: Replace `event.get("body", "")` → `LambdaHelpers.extract_request_body(event, ModelClass)` (for POST/PUT)
- [ ] **User ID**: Replace manual user extraction → `LambdaHelpers.extract_user_id(event)` (if applicable)

### Phase 2: Response Migration  
- [ ] **Success Response**: Replace manual response dict → `LambdaHelpers.format_success_response(data, status_code=200)`
- [ ] **Error Response**: Replace manual error dict → `LambdaHelpers.format_error_response(message, status_code=4xx)`
- [ ] **Created Response**: Use `status_code=201` for POST endpoints
- [ ] **CORS Headers**: Remove manual `CORS_headers` import (handled automatically)
- [ ] **Collection Response**: Apply TypeAdapter pattern for list responses (if applicable)

### Phase 3: Collection Response (if applicable)
- [ ] **TypeAdapter Import**: Add `from src.contexts.shared_kernel.schemas.collection_response import create_paginated_response`
- [ ] **Replace Custom Serializer**: Remove `json.dumps(..., default=custom_serializer)`
- [ ] **Apply TypeAdapter**: Use `create_paginated_response()` for collections
- [ ] **Performance Test**: Validate TypeAdapter performance improvement

### Phase 4: Error Handling Enhancement
- [ ] **Preserve Exception Handler**: Keep `@lambda_exception_handler` decorator
- [ ] **Standard Error Format**: Use `LambdaHelpers.format_error_response()` for consistent error schema
- [ ] **Auth Error Handling**: Update 403/401 responses to use standard format
- [ ] **Validation Error Handling**: Update 400 responses to use standard format

## Testing Checklist

### Unit Testing
- [ ] **Existing Tests Pass**: All original tests continue to pass
- [ ] **New Pattern Tests**: Add tests for LambdaHelpers usage patterns
- [ ] **Edge Case Tests**: Test edge cases (empty params, malformed data, etc.)
- [ ] **Error Scenario Tests**: Test error handling scenarios

### Integration Testing  
- [ ] **API Response Format**: Verify API responses identical to original
- [ ] **CORS Headers**: Verify CORS headers present and correct
- [ ] **Status Codes**: Verify status codes unchanged
- [ ] **Content-Type**: Verify Content-Type headers correct

### Performance Testing
- [ ] **Response Time**: Measure response time vs. baseline
- [ ] **Memory Usage**: Check memory usage (if applicable)
- [ ] **TypeAdapter Performance**: Validate performance improvement for collections
- [ ] **Performance Regression**: Ensure performance within 5% of baseline

## Backward Compatibility Validation

### Response Format Validation
- [ ] **JSON Structure**: Verify JSON response structure unchanged
- [ ] **Field Names**: Verify all field names unchanged  
- [ ] **Data Types**: Verify data types unchanged
- [ ] **Error Response Format**: Verify error responses follow expected schema

### API Contract Validation
- [ ] **Request Parameters**: Verify all request parameters still accepted
- [ ] **Optional Parameters**: Verify optional parameters handled correctly
- [ ] **Default Values**: Verify default values unchanged
- [ ] **Validation Rules**: Verify validation behavior unchanged

## Deployment Checklist

### Pre-Deployment
- [ ] **Code Review**: Complete code review of migration changes
- [ ] **Test Coverage**: Verify test coverage maintained or improved
- [ ] **Documentation Update**: Update endpoint documentation if needed
- [ ] **Performance Metrics**: Document performance comparison

### Deployment Validation
- [ ] **Staging Deployment**: Deploy to staging environment
- [ ] **Staging Testing**: Run full test suite in staging
- [ ] **API Testing**: Manual API testing in staging
- [ ] **Production Deployment**: Deploy to production (if staging successful)

### Post-Deployment Monitoring
- [ ] **Error Rate Monitoring**: Monitor error rates for 24 hours
- [ ] **Performance Monitoring**: Monitor response times
- [ ] **Log Analysis**: Verify correlation IDs and proper logging
- [ ] **Rollback Plan**: Confirm rollback procedure if issues detected

## Completion Verification

### Final Validation
- [ ] **All Tests Pass**: Complete test suite passes
- [ ] **Performance Acceptable**: Performance within 5% of baseline
- [ ] **Zero Breaking Changes**: No breaking changes detected
- [ ] **Documentation Complete**: Migration documented with before/after examples
- [ ] **Artifacts Updated**: Phase artifacts updated with findings

### Sign-off Criteria
- [ ] **Code Quality**: Code review approved
- [ ] **Testing Complete**: All testing checklists completed
- [ ] **Performance Validated**: Performance benchmarks met
- [ ] **Production Stable**: 24-hour production stability confirmed

## Migration Specific Notes

### Endpoint-Specific Considerations
```
[Add endpoint-specific notes here, such as:]
- Custom business logic considerations
- Special authorization requirements  
- Unique response format requirements
- Performance-critical considerations
- Integration dependencies
```

### Issues Encountered
```
[Document any issues encountered during migration:]
- Problem description
- Solution applied
- Lessons learned
- Recommendations for similar endpoints
```

### Performance Results
```
[Document performance comparison:]
- Baseline metrics
- Post-migration metrics  
- Performance improvement/degradation
- TypeAdapter performance results (if applicable)
```

## Rollback Information

### Rollback Triggers
- [ ] **Error Rate Increase**: > 5% error rate increase
- [ ] **Performance Degradation**: > 10% response time increase
- [ ] **Breaking Changes**: Any breaking changes detected
- [ ] **Business Logic Issues**: Any business logic errors

### Rollback Procedure
1. **Immediate**: Git revert migration commit
2. **Deploy**: Redeploy previous version
3. **Validate**: Confirm rollback successful
4. **Investigate**: Analyze root cause
5. **Document**: Document rollback reason and learnings

---

**Template Usage**: Copy this checklist for each endpoint migration and fill in endpoint-specific details.  
**Checklist Updates**: Update this template based on migration learnings and feedback. 