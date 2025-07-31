# Phase 3: recipes_catalog Integration

---
phase: 3
depends_on: [1, 2]
estimated_time: 20-25 hours
---

## Objective
Integrate client_onboarding context with recipes_catalog to enable Client creation using stored form responses, following proper cross-context integration patterns with internal providers and maintaining backward compatibility.

## Prerequisites
- [ ] Phase 2 completed: Data processing and storage working with proper API schemas
- [ ] Form responses successfully stored with validated client identifiers
- [ ] recipes_catalog Client model structure and API patterns understood

# Tasks

## 3.1 Client Model Enhancement
- [ ] 3.1.1 Add onboarding_data field to Client entity
  - Files: `src/contexts/recipes_catalog/core/domain/client/root_aggregate/client.py`
  - Purpose: Add JSONB field to store original form response data with proper typing
- [ ] 3.1.2 Update Client creation methods
  - Files: `src/contexts/recipes_catalog/core/domain/client/root_aggregate/client.py`
  - Purpose: Support optional onboarding_data parameter in Client.create methods
- [ ] 3.1.3 Create database migration for Client table
  - Files: `migrations/versions/add_client_onboarding_data.py`
  - Purpose: Add onboarding_data JSONB column with proper indexing and constraints
- [ ] 3.1.4 Create API schemas for enhanced Client creation
  - Files: `src/contexts/recipes_catalog/core/adapters/client/api_schemas/commands/api_create_client_with_onboarding.py`
  - Purpose: Pydantic models for Client creation with onboarding data support

## 3.2 Cross-Context Integration Layer
- [ ] 3.2.1 Create recipes_catalog internal provider
  - Files: `src/contexts/client_onboarding/core/adapters/internal_providers/recipes_catalog/client_provider.py`
  - Purpose: Internal provider for recipes_catalog integration following existing IAM pattern
- [ ] 3.2.2 Create form response to Client mappers
  - Files: `src/contexts/client_onboarding/core/adapters/mappers/form_response_to_client_mapper.py`
  - Purpose: Map validated form response data to Client Profile, ContactInfo, and Address
- [ ] 3.2.3 Add integration API schemas
  - Files: `src/contexts/client_onboarding/core/adapters/internal_providers/recipes_catalog/schemas.py`
  - Purpose: API schemas for cross-context communication with recipes_catalog
- [ ] 3.2.4 Create data enrichment service
  - Files: `src/contexts/client_onboarding/core/services/data_enrichment.py`
  - Purpose: Enhance mapped form data with defaults, validation, and formatting

## 3.3 Enhanced Client Creation
- [ ] 3.3.1 Create new Client creation command for onboarding
  - Files: `src/contexts/recipes_catalog/core/domain/client/commands/create_client_with_onboarding.py`
  - Purpose: New domain command for Client creation with onboarding data
- [ ] 3.3.2 Implement enhanced Client creation command handler
  - Files: `src/contexts/recipes_catalog/core/services/client/command_handlers/create_client_with_onboarding.py`
  - Purpose: Command handler for Client creation with pre-filled form data
- [ ] 3.3.3 Add Client creation Lambda endpoint
  - Files: `src/contexts/recipes_catalog/aws_lambda/client/create_client_with_onboarding.py`
  - Purpose: Lambda endpoint for creating clients from form responses
- [ ] 3.3.4 Update bootstrap with new command handler
  - Files: `src/contexts/recipes_catalog/core/bootstrap/bootstrap.py`
  - Purpose: Register new command handler in message bus

## 3.4 Data Extraction & Mapping Services
- [ ] 3.4.1 Create Profile data extraction service
  - Files: `src/contexts/client_onboarding/core/services/extractors/profile_data_extractor.py`
  - Purpose: Extract name, age, dietary preferences from validated form responses
- [ ] 3.4.2 Build ContactInfo data extraction service
  - Files: `src/contexts/client_onboarding/core/services/extractors/contact_data_extractor.py`
  - Purpose: Extract email, phone, preferred contact method from validated responses
- [ ] 3.4.3 Create Address data extraction service
  - Files: `src/contexts/client_onboarding/core/services/extractors/address_data_extractor.py`
  - Purpose: Extract address information if available in validated form responses
- [ ] 3.4.4 Add data extraction validation schemas
  - Files: `src/contexts/client_onboarding/api_schemas/extraction/client_data_schemas.py`
  - Purpose: Pydantic models for validating extracted client data before mapping

## 3.5 Backward Compatibility & Validation
- [ ] 3.5.1 Ensure existing Client creation remains unchanged
  - Files: Validation in existing Client tests and command handlers
  - Purpose: Verify no breaking changes to current Client creation flows
- [ ] 3.5.2 Add optional onboarding data handling
  - Files: `src/contexts/recipes_catalog/core/domain/client/root_aggregate/client.py`
  - Purpose: Handle None values gracefully for onboarding_data field with proper defaults
- [ ] 3.5.3 Create comprehensive migration tests
  - Files: `tests/contexts/recipes_catalog/integration/client_migration/`
  - Purpose: Ensure database migration works with existing Client data without issues
- [ ] 3.5.4 Add API backward compatibility validation
  - Files: `tests/contexts/recipes_catalog/integration/api_compatibility/`
  - Purpose: Ensure existing API endpoints continue to work as expected

## 3.6 Integration Lambda Endpoints
- [ ] 3.6.1 Create form response to Client Lambda
  - Files: `src/contexts/client_onboarding/aws_lambda/client_creation_from_response.py`
  - Purpose: Lambda endpoint to create Client from stored form response
- [ ] 3.6.2 Add available responses listing Lambda
  - Files: `src/contexts/client_onboarding/aws_lambda/list_available_responses.py`
  - Purpose: Lambda to list form responses available for Client creation with proper authorization
- [ ] 3.6.3 Implement Client preview Lambda
  - Files: `src/contexts/client_onboarding/aws_lambda/preview_client_data.py`
  - Purpose: Lambda to preview what Client data would look like before creation
- [ ] 3.6.4 Create integration workflow Lambda
  - Files: `src/contexts/client_onboarding/aws_lambda/integration_workflow.py`
  - Purpose: Orchestrate the complete form-to-client creation workflow

## 3.7 Integration Error Handling & Validation
- [ ] 3.7.1 Create cross-context validation middleware
  - Files: `src/contexts/client_onboarding/core/adapters/middleware/cross_context_validation.py`
  - Purpose: Validate form data compatibility with Client requirements using middleware pattern
- [ ] 3.7.2 Add integration error handling
  - Files: `src/contexts/client_onboarding/core/adapters/middleware/integration_error_middleware.py`
  - Purpose: Handle failures in cross-context communication with proper error mapping
- [ ] 3.7.3 Create missing data validation schemas
  - Files: `src/contexts/client_onboarding/api_schemas/validation/missing_data_schemas.py`
  - Purpose: Pydantic models for handling incomplete form data scenarios
- [ ] 3.7.4 Implement integration validation service
  - Files: `src/contexts/client_onboarding/core/services/integration_validator.py`
  - Purpose: Service for validating complete integration workflow before execution

## Validation
- [ ] Tests: `poetry run python pytest tests/contexts/client_onboarding/unit/phase_3/`
- [ ] Integration: `poetry run python pytest tests/integration/client_onboarding_catalog/`
- [ ] Migration: `alembic upgrade head` and verify existing Clients unaffected
- [ ] Backward compatibility: Run existing Client creation tests
- [ ] E2E workflow: Form response → Client creation → data verification

## Success Criteria
- [ ] Client creation pre-fills Profile, ContactInfo, and Address from form data
- [ ] 50% reduction in Client creation time when using form responses
- [ ] 100% backward compatibility with existing Client creation workflows
- [ ] onboarding_data properly stored and queryable in Client records
- [ ] Cross-context integration handles errors gracefully 