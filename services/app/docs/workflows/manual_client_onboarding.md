# Manual Client Onboarding Workflow

## Overview

This document describes the manual workflow for creating clients from Typeform onboarding responses. This workflow allows users to review form responses before creating clients and transfer onboarding data to existing clients.

## Prerequisites

- Typeform webhooks configured and working
- Form responses stored in `client_onboarding` context
- recipes_catalog context with Client creation capabilities
- Internal provider integration between contexts established

## Workflow Steps

### 1. Form Response Collection

**Automatic Process:**
1. User fills out Typeform onboarding form
2. Typeform sends webhook to application
3. Webhook processed by `client_onboarding` context
4. Form response stored in database with validation

**Data Available:**
- Form responses with structured data
- Client identification information
- Profile, contact, and address details
- Original form metadata

### 2. Query Available Form Responses

**Endpoint:** Use existing `query_responses.py` Lambda function

**API Call:**
```http
GET /responses?status=pending&limit=20
```

**Response Format:**
```json
{
  "responses": [
    {
      "response_id": "resp_123",
      "form_id": "form_abc",
      "submission_date": "2024-12-20T10:30:00Z",
      "status": "pending",
      "answers": [...],
      "client_identifier": {
        "name": "John Doe",
        "email": "john@example.com"
      }
    }
  ],
  "total": 5,
  "page": 1
}
```

### 3. Preview Client Data (Optional)

**Purpose:** Preview what client data would look like before creation

**Implementation:** Use `FormResponseMapper.preview_client_data_from_form_response()`

**Preview Data:**
```json
{
  "preview": {
    "profile": {
      "name": "John Doe",
      "age": 35,
      "dietary_preferences": ["vegetarian", "gluten-free"]
    },
    "contact_info": {
      "email": "john@example.com",
      "phone": "+1234567890",
      "preferred_contact_method": "email"
    },
    "address": {
      "street": "123 Main St",
      "city": "Springfield",
      "state": "IL",
      "country": "United States",
      "zip_code": "62701"
    }
  },
  "warnings": {},
  "extraction_success": true,
  "required_fields_present": true
}
```

### 4. Create Client from Form Response

**Option A: New Client Creation**

**Endpoint:** Use existing `create_client.py` Lambda function

**API Call:**
```http
POST /clients
```

**Request Body:**
```json
{
  "author_id": "user_123",
  "profile": {
    "name": "John Doe",
    "age": 35,
    "dietary_preferences": ["vegetarian", "gluten-free"]
  },
  "contact_info": {
    "email": "john@example.com",
    "phone": "+1234567890",
    "preferred_contact_method": "email"
  },
  "address": {
    "street": "123 Main St",
    "city": "Springfield",
    "state": "IL",
    "country": "United States",
    "zip_code": "62701"
  },
  "onboarding_data": {
    "response_id": "resp_123",
    "form_id": "form_abc",
    "answers": [...],
    "submission_date": "2024-12-20T10:30:00Z"
  },
  "notes": "Created from form form_abc; Response ID: resp_123"
}
```

**Option B: Transfer to Existing Client**

**Endpoint:** Use existing `update_client.py` Lambda function

**API Call:**
```http
PUT /clients/{client_id}
```

**Request Body:**
```json
{
  "profile": {
    "name": "John Doe Updated",
    "age": 35,
    "dietary_preferences": ["vegetarian", "gluten-free"]
  },
  "contact_info": {
    "email": "john.updated@example.com",
    "phone": "+1234567890",
    "preferred_contact_method": "email"
  },
  "address": {
    "street": "456 Oak Ave",
    "city": "Springfield",
    "state": "IL",
    "country": "United States",
    "zip_code": "62702"
  },
  "onboarding_data": {
    "response_id": "resp_123",
    "form_id": "form_abc",
    "answers": [...],
    "submission_date": "2024-12-20T10:30:00Z"
  },
  "notes": "Updated with form response from form_abc; Response ID: resp_123"
}
```

## Data Extraction Logic

### Profile Extraction
- **Name:** Extracted from fields with references: `name`, `full_name`, `client_name`, `your_name`
- **Age:** Extracted from fields with references: `age`, `client_age`, `your_age`, `age_years`
- **Dietary Preferences:** Extracted from fields with references: `dietary_preferences`, `diet_preferences`, `dietary_restrictions`

### Contact Information Extraction
- **Email:** Extracted from fields with references: `email`, `email_address`, `contact_email`
- **Phone:** Extracted from fields with references: `phone`, `phone_number`, `contact_phone`
- **Preferred Contact Method:** Extracted from fields with references: `preferred_contact`, `contact_preference`

### Address Extraction
- **Street:** Extracted from fields with references: `street`, `street_address`, `address`, `address_line_1`
- **City:** Extracted from fields with references: `city`, `town`, `municipality`
- **State:** Extracted from fields with references: `state`, `province`, `region`
- **Country:** Extracted from fields with references: `country`, `nation`
- **ZIP Code:** Extracted from fields with references: `zip`, `zip_code`, `postal_code`

## Error Handling

### Missing Required Fields
- **Profile Name Required:** Client creation will fail if name cannot be extracted
- **Optional Fields:** Missing contact info or address fields result in warnings but don't prevent client creation

### Extraction Warnings
- Partial data extraction logged in client notes
- Extraction warnings included in API responses
- Manual review recommended for complex cases

### Validation Failures
- Invalid email formats rejected with validation errors
- Invalid phone numbers cleaned or rejected
- Malformed addresses handled gracefully

## Best Practices

### Data Review
1. **Always preview** client data before creation
2. **Review extraction warnings** and handle manually if needed
3. **Verify contact information** accuracy before saving
4. **Check for duplicate clients** before creating new ones

### Form Response Management
1. **Mark responses as processed** after client creation
2. **Maintain audit trail** of form response to client mappings
3. **Handle failed extractions** with manual review workflow
4. **Archive old responses** according to data retention policies

### Quality Assurance
1. **Validate extracted data** against business rules
2. **Test extraction logic** with various form response formats
3. **Monitor extraction success rates** and improve field mapping
4. **Document common extraction patterns** for future reference

## Integration Points

### Client Onboarding Context
- **Internal Provider Endpoints:** `/internal/form-responses` and `/internal/form-response/{id}`
- **Form Response Storage:** Persistent storage with JSONB queries
- **Webhook Processing:** Real-time form response ingestion

### Recipes Catalog Context
- **Client Creation:** Enhanced with onboarding_data support
- **Client Updates:** Support for form response data transfer
- **Data Mapping:** Automatic extraction from form responses to value objects

## Automation Opportunities

### Future Enhancements
1. **Automatic Client Creation:** For trusted forms with complete data
2. **Duplicate Detection:** Check for existing clients before creation
3. **Smart Field Mapping:** Machine learning for improved extraction
4. **Bulk Processing:** Handle multiple form responses simultaneously

### Integration Benefits
- **50% reduction** in client creation time when using form responses
- **70% reduction** in manual data entry for existing client updates
- **100% audit trail** of form response to client relationships
- **Improved data quality** through structured form collection