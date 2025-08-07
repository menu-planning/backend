# Phase 3: recipes_catalog Integration

---
phase: 3
depends_on: [1, 2]
estimated_time: 20-25 hours
---

## Objective
Integrate client_onboarding context with recipes_catalog to enable both automated Client creation and manual workflow with form response data transfer, following proper cross-context integration patterns with internal providers and maintaining backward compatibility.

## Prerequisites
- [ ] Phase 2 completed: Data processing and storage working with proper API schemas
- [ ] Form responses successfully stored with validated client identifiers  
- [ ] Existing `query_responses.py`, `create_client.py`, and `update_client.py` endpoints working
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
- [ ] 3.2.0 Create client_onboarding internal provider endpoint
  - Files: `src/contexts/client_onboarding/core/endpoints/internal/get.py` and `src/contexts/client_onboarding/core/endpoints/internal/get_all.py`
  - Purpose: Internal provider for exposing client_onboarding data, similar to `src/contexts/iam/core/endpoints/internal/get.py`
- [ ] 3.2.1 Create client_onboarding internal provider for recipes_catalog
  - Files: `src/contexts/recipes_catalog/core/adapters/internal_providers/client_onboarding/client_onboarding_provider.py`
  - Purpose: Internal provider for accessing client_onboarding data, similar to `src/contexts/recipes_catalog/core/adapters/internal_providers/iam/iam_provider_api_for_recipes_catalog.py` but simpler as it does not need to have a base class and only needs to expose the get and get_all methods
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
- [ ] 3.3.1 Update existing Client creation command to support onboarding_data
  - Files: `src/contexts/recipes_catalog/core/domain/client/commands/create_client.py`
  - Purpose: Add optional onboarding_data parameter to existing CreateClient command
- [ ] 3.3.2 Update existing Client creation command handler
  - Files: `src/contexts/recipes_catalog/core/services/client/command_handlers/create_client.py`
  - Purpose: Enhance existing command handler to handle onboarding_data from form responses
- [ ] 3.3.3 Update Client API schemas to support onboarding_data
  - Files: `src/contexts/recipes_catalog/core/adapters/client/api_schemas/root_aggregate/api_client.py`
  - Purpose: Add onboarding_data field to API schemas
- [ ] 3.3.4 Update Client API update command schema
  - Files: `src/contexts/recipes_catalog/core/adapters/client/api_schemas/commands/api_update_client.py`
  - Purpose: Support onboarding_data in update operations

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

## 3.5 Manual Workflow Integration  
- [ ] 3.5.1 Create manual workflow documentation
  - Files: `docs/workflows/manual_client_onboarding.md`
  - Purpose: Document the manual workflow: webhook → query responses → create client → transfer data
- [ ] 3.5.2 Add form response selection API for frontend
  - Files: Enhance existing `query_responses.py` with client-specific filtering
  - Purpose: Enable frontend to list available form responses for client data transfer
- [ ] 3.5.3 Create form response preview service
  - Files: `src/contexts/recipes_catalog/core/services/client/form_response_preview.py`  
  - Purpose: Preview what client data would look like before transfer
- [ ] 3.5.4 Enhance update_client command handler for form response data
  - Files: `src/contexts/recipes_catalog/core/services/client/command_handlers/update_client.py`
  - Purpose: Add form response data processing to existing update_client handler

## 3.6 Client Model Infrastructure Updates
- [ ] 3.6.1 Update Client domain entity with onboarding_data property
  - Files: `src/contexts/recipes_catalog/core/domain/client/root_aggregate/client.py`
  - Purpose: Add onboarding_data property with getter/setter and update_properties support
- [ ] 3.6.2 Update Client ORM model
  - Files: `src/contexts/recipes_catalog/core/adapters/client/ORM/sa_models/client_sa_model.py`
  - Purpose: Add onboarding_data JSONB field to SQLAlchemy model
- [ ] 3.6.3 Update Client ORM mapper
  - Files: `src/contexts/recipes_catalog/core/adapters/client/ORM/mappers/client_mapper.py`
  - Purpose: Handle onboarding_data field in domain ↔ ORM mapping
- [ ] 3.6.4 Create form response transfer service
  - Files: `src/contexts/recipes_catalog/core/services/client/form_response_transfer.py`
  - Purpose: Service to transfer form response data to existing clients via update_client

## 3.7 Backward Compatibility & Validation
- [ ] 3.7.1 Ensure existing Client creation remains unchanged
  - Files: Validation in existing Client tests and command handlers
  - Purpose: Verify no breaking changes to current Client creation flows
- [ ] 3.7.2 Add optional onboarding data handling
  - Files: `src/contexts/recipes_catalog/core/domain/client/root_aggregate/client.py`
  - Purpose: Handle None values gracefully for onboarding_data field with proper defaults
- [ ] 3.7.3 Create comprehensive migration tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/client/ORM/mappers/test_client_mapper.py`
  - Purpose: Ensure database migration works with existing Client data without issues
- [ ] 3.7.4 Add API backward compatibility validation
  - Files: `tests/contexts/recipes_catalog/aws_lambda/client/test_api_compatibility.py`
  - Purpose: Ensure existing API endpoints continue to work as expected

## 3.8 Integration Error Handling & Validation
- [ ] 3.8.1 Create cross-context validation middleware
  - Files: `src/contexts/client_onboarding/core/adapters/middleware/cross_context_validation.py`
  - Purpose: Validate form data compatibility with Client requirements using middleware pattern
- [ ] 3.8.2 Add integration error handling
  - Files: `src/contexts/client_onboarding/core/adapters/middleware/integration_error_middleware.py`
  - Purpose: Handle failures in cross-context communication with proper error mapping
- [ ] 3.8.3 Create missing data validation schemas
  - Files: `src/contexts/client_onboarding/core/adapters/api_schemas/validation/missing_data_schemas.py`
  - Purpose: Pydantic models for handling incomplete form data scenarios
- [ ] 3.8.4 Implement integration validation service
  - Files: `src/contexts/client_onboarding/core/services/integration_validator.py`
  - Purpose: Service for validating complete integration workflow before execution

## Validation
- [ ] Unit Tests: `poetry run python pytest tests/contexts/client_onboarding/core/ tests/contexts/recipes_catalog/core/ -m "not slow and not integration"`
- [ ] Integration Tests: `poetry run python pytest tests/contexts/recipes_catalog/aws_lambda/client/ -m integration`
- [ ] Cross-Context Tests: `poetry run python pytest tests/contexts/recipes_catalog/core/adapters/internal_providers/client_onboarding/ -m "integration and anyio"`
- [ ] Migration: `alembic upgrade head` and verify existing Clients unaffected
- [ ] Backward compatibility: Run existing Client creation tests
- [ ] Manual workflow: Webhook → Query responses → Create client → Transfer form data
- [ ] E2E workflow: Form response → Client creation → data verification

## Success Criteria
- [ ] Both automated and manual workflows: App users can create clients with form data via automated creation or manual transfer
- [ ] Client creation pre-fills Profile, ContactInfo, and Address from form data using existing `create_client.py` endpoint
- [ ] 50% reduction in Client creation time when using form responses (automated workflow)
- [ ] 70% reduction in manual data entry when transferring form responses (manual workflow)
- [ ] 100% backward compatibility with existing Client creation workflows
- [ ] onboarding_data properly stored and queryable in Client records
- [ ] Cross-context integration handles errors gracefully
- [ ] Existing `update_client.py` endpoint supports form response data transfer
- [ ] Client.update_properties() method handles onboarding_data field 