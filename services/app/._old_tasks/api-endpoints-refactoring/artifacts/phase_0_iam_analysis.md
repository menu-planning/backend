# IAM Context Endpoints Analysis

## Overview
Analysis of IAM AWS Lambda endpoints to understand current implementation patterns and unique characteristics compared to other contexts.

## Endpoint Structure

### Directory Layout
```
src/contexts/iam/aws_lambda/
├── CORS_headers.py
├── create_user.py
└── assign_role.py
```

## Endpoint Details

### create_user.py
- **Purpose**: Post-confirmation trigger for new user creation
- **Trigger Type**: Cognito post-confirmation (not API Gateway)
- **Input**: Cognito event with userName
- **Logic**: Check if user exists, create if not, handle duplicates

### assign_role.py  
- **Purpose**: Assign roles to existing users
- **Auth**: Uses internal.get() for authorization (different from other contexts)
- **Permission**: Requires MANAGE_ROLES permission
- **Input**: User ID from path, role data from body

## Unique Patterns Identified

### Authentication Differences
- **No IAMProvider Import**: Uses internal `src.contexts.iam.core.endpoints.internal.get`
- **Internal Authorization**: `await internal.get(caller_user_id, "iam")` instead of IAMProvider.get()
- **Permission Model**: Context-specific permission checking with "iam" context parameter
- **User Domain Objects**: Works directly with `User` domain objects vs `SeedUser`

### Error Handling Patterns
- **Consistent Decorator**: Uses `@lambda_exception_handler` like other contexts
- **Status Code Issues**: Contains typos: `"statuCode"` instead of `"statusCode"`
- **CORS Headers**: Same pattern as other contexts
- **Custom Error Messages**: IAM-specific error messages for role management

### Request Processing
- **Body Parsing**: Same manual `json.loads(event.get("body", ""))` pattern
- **Path Parameters**: Standard `event["pathParameters"]["id"]` extraction
- **Validation**: Manual try/catch for missing parameters

### Business Logic Integration
- **MessageBus**: Same `Container().bootstrap()` pattern
- **Command Pattern**: Same `.to_domain()` conversion pattern
- **No UnitOfWork**: Direct command handling without explicit UoW context

### Response Patterns
- **Success Responses**: Manual JSON responses with success messages
- **Error Responses**: Manual JSON with error messages
- **Status Codes**: Standard 200, 403, 409 usage
- **CORS Headers**: Consistent with other contexts

## Inconsistencies with Other Contexts

### Authentication Architecture
- **Different Provider**: Internal endpoint vs IAMProvider
- **Permission Context**: Requires context parameter ("iam")
- **User Objects**: Domain User vs SeedUser value objects
- **Authorization Flow**: Internal function call vs external provider pattern

### Error Response Format
- **Typo Bugs**: `"statuCode"` spelling errors (lines create_user.py:48, 52)
- **Inconsistent Error Structure**: Mix of message formats
- **Missing Standard Error Schema**: No consistent error response format

### Business Logic Patterns
- **Simpler UoW Usage**: Less explicit UoW management compared to recipes/products
- **Direct Command Handling**: More streamlined command processing
- **Event-Driven**: create_user.py handles Cognito events, not REST API

## Special Considerations

### Cognito Integration
- **create_user.py**: Cognito post-confirmation trigger (event-driven)
- **Event Format**: Different from API Gateway events
- **Response Format**: Must return Cognito-compatible response structure
- **Auto-confirm Logic**: Sets autoConfirmUser and autoVerifyEmail

### Role Management
- **Domain-Specific**: IAM context handles its own role assignments
- **Permission Model**: Context-aware permission checking
- **Administrative Functions**: Higher privilege requirements

## Architecture Strengths
- **Domain Separation**: Clear IAM context boundary
- **Permission Model**: Sophisticated context-aware permissions
- **Event Integration**: Proper Cognito trigger handling
- **Command Pattern**: Consistent with other contexts

## Issues to Address
1. **Spelling Errors**: Fix "statuCode" typos in create_user.py
2. **Error Standardization**: Align error response formats with other contexts  
3. **Authentication Pattern**: Decide on internal vs external authorization approach
4. **Response Consistency**: Standardize success response formats

## Files Analyzed
- `create_user.py` - Cognito post-confirmation trigger
- `assign_role.py` - Role assignment endpoint
- `CORS_headers.py` - Shared CORS configuration

**Total Endpoints**: 2 Lambda functions (1 trigger, 1 API)
**Unique Dependencies**: Internal IAM authorization, Context-aware permissions
**Estimated Refactoring Complexity**: Medium - simpler structure but unique patterns 