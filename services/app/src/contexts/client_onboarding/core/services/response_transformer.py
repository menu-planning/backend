"""
Response Transformation Service

Transform validated TypeForm responses to internal storage format.
Converts processed response data and extracted client identifiers into 
optimized JSONB format for database storage and efficient querying.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from src.contexts.client_onboarding.core.adapters.api_schemas.responses.form_response_data import (
    FormResponseDataValidation,
    NormalizedFieldResponse,
    ResponseFieldType
)
from src.contexts.client_onboarding.core.adapters.api_schemas.responses.client_identifiers import (
    IdentifierExtractionResult
)
from src.contexts.client_onboarding.core.adapters.api_schemas.webhook.typeform_webhook_payload import (
    FormResponse as WebhookFormResponse
)
from src.contexts.client_onboarding.core.services.exceptions import (
    FormResponseProcessingError
)

logger = logging.getLogger(__name__)


@dataclass
class TransformationContext:
    """Context for response transformation process."""
    form_id: str
    response_token: str
    user_id: Optional[int] = None
    include_metadata: bool = True
    optimize_for_queries: bool = True


@dataclass
class TransformedResponseData:
    """Container for transformed response data ready for database storage."""
    response_data: Dict[str, Any]
    client_identifiers: Optional[Dict[str, Any]]
    response_id: str
    submission_id: Optional[str]
    submitted_at: datetime
    metadata: Dict[str, Any]


class ResponseTransformer:
    """
    Transform validated TypeForm responses to internal storage format.
    
    Converts processed response data and client identifiers into optimized
    JSONB format for database storage while preserving data integrity
    and enabling efficient queries.
    """
    
    def __init__(self):
        """Initialize response transformer."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def transform_response(
        self,
        validated_response: FormResponseDataValidation,
        webhook_response: WebhookFormResponse,
        client_identifiers: Optional[IdentifierExtractionResult] = None,
        context: Optional[TransformationContext] = None
    ) -> TransformedResponseData:
        """
        Transform validated response data to internal storage format.
        
        Args:
            validated_response: Processed and validated form response data
            webhook_response: Original webhook response for metadata
            client_identifiers: Optional extracted client identifiers
            context: Optional transformation context
            
        Returns:
            TransformedResponseData ready for database storage
            
        Raises:
            FormResponseProcessingError: For transformation failures
        """
        try:
            self.logger.info(f"Transforming response for form {validated_response.form_id}, "
                           f"token {validated_response.response_token}")
            
            # Build transformation context
            if context is None:
                context = TransformationContext(
                    form_id=validated_response.form_id,
                    response_token=validated_response.response_token
                )
            
            # Transform field responses to JSONB format
            response_data = await self._transform_field_responses(
                validated_response.validated_fields, context
            )
            
            # Transform client identifiers to JSONB format
            client_identifiers_data = await self._transform_client_identifiers(
                client_identifiers, context
            ) if client_identifiers else None
            
            # Extract metadata from webhook response
            metadata = await self._extract_response_metadata(
                webhook_response, validated_response, context
            )
            
            # Build transformed result
            transformed_data = TransformedResponseData(
                response_data=response_data,
                client_identifiers=client_identifiers_data,
                response_id=webhook_response.token,
                submission_id=self._extract_submission_id(webhook_response),
                submitted_at=webhook_response.submitted_at,
                metadata=metadata
            )
            
            self.logger.info(f"Successfully transformed response: {len(response_data)} fields, "
                           f"client_identifiers={'present' if client_identifiers_data else 'none'}")
            
            return transformed_data
            
        except Exception as e:
            error_msg = f"Error transforming response for form {validated_response.form_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise FormResponseProcessingError(
                "response_transformation",
                validated_response.form_id,
                error_msg
            )
    
    async def _transform_field_responses(
        self,
        validated_fields: list[NormalizedFieldResponse],
        context: TransformationContext
    ) -> Dict[str, Any]:
        """
        Transform validated field responses to optimized JSONB format.
        
        Args:
            validated_fields: List of validated and normalized field responses
            context: Transformation context
            
        Returns:
            Dict optimized for JSONB storage and querying
        """
        response_data = {
            "fields": {},
            "field_mapping": {},
            "completion_metrics": {},
            "processing_metadata": {}
        }
        
        # Process each field
        for field in validated_fields:
            field_data = await self._transform_single_field(field, context)
            
            # Store by field ID for direct access
            response_data["fields"][field.field_id] = field_data
            
            # Create mapping for field titles (for queries)
            if context.optimize_for_queries:
                title_key = self._normalize_field_title(field.field_title)
                response_data["field_mapping"][title_key] = field.field_id
        
        # Add completion metrics for analytics
        response_data["completion_metrics"] = {
            "total_fields": len(validated_fields),
            "field_types": self._count_field_types(validated_fields),
            "has_identifiers": any(
                field.field_type in [ResponseFieldType.EMAIL, ResponseFieldType.PHONE_NUMBER]
                for field in validated_fields
            )
        }
        
        # Add processing metadata
        response_data["processing_metadata"] = {
            "transformation_timestamp": datetime.now().isoformat(),
            "transformer_version": "1.0.0",
            "optimization_enabled": context.optimize_for_queries
        }
        
        return response_data
    
    async def _transform_single_field(
        self,
        field: NormalizedFieldResponse,
        context: TransformationContext
    ) -> Dict[str, Any]:
        """
        Transform a single field response to storage format.
        
        Args:
            field: Normalized field response
            context: Transformation context
            
        Returns:
            Dict with field data optimized for storage
        """
        field_data = {
            "field_type": field.field_type.value,
            "field_title": field.field_title,
            "storage_value": field.storage_value,
            "display_value": field.display_value,
            "processing_metadata": {
                "field_id": field.field_id,
                "field_ref": field.field_ref
            }
        }
        
        # Include type-specific response data if available
        if field.text_response:
            field_data["text_data"] = {
                "sanitized_value": field.text_response.sanitized_value,
                "character_count": field.text_response.character_count,
                "word_count": field.text_response.word_count,
                "is_truncated": field.text_response.is_truncated
            }
        
        if field.email_response:
            field_data["email_data"] = {
                "email": field.email_response.email,
                "domain": field.email_response.domain,
                "is_business_email": field.email_response.is_business_email,
                "is_valid_format": field.email_response.is_valid_format
            }
        
        if field.phone_response:
            field_data["phone_data"] = {
                "raw_phone": field.phone_response.raw_phone,
                "formatted_phone": field.phone_response.formatted_phone,
                "country_code": field.phone_response.country_code,
                "is_valid": field.phone_response.is_valid
            }
        
        if field.number_response:
            field_data["number_data"] = {
                "raw_value": field.number_response.raw_value,
                "numeric_value": field.number_response.numeric_value,
                "is_integer": field.number_response.is_integer,
                "is_positive": field.number_response.is_positive
            }
        
        if field.choice_response:
            field_data["choice_data"] = {
                "choice_id": field.choice_response.choice_id,
                "choice_label": field.choice_response.choice_label,
                "choice_ref": field.choice_response.choice_ref,
                "is_other": field.choice_response.is_other,
                "other_text": field.choice_response.other_text
            }
        
        if field.date_response:
            field_data["date_data"] = {
                "raw_date": field.date_response.raw_date,
                "parsed_date": field.date_response.parsed_date.isoformat() if field.date_response.parsed_date else None,
                "iso_format": field.date_response.iso_format,
                "is_future": field.date_response.is_future
            }
        
        # Add indexable values for common query patterns
        if context.optimize_for_queries:
            field_data["searchable"] = self._create_searchable_values(field)
        
        return field_data
    
    async def _transform_client_identifiers(
        self,
        extraction_result: IdentifierExtractionResult,
        context: TransformationContext
    ) -> Dict[str, Any]:
        """
        Transform client identifiers to storage format.
        
        Args:
            extraction_result: Extracted client identifiers
            context: Transformation context
            
        Returns:
            Dict with client identifiers optimized for correlation
        """
        identifiers = extraction_result.identifiers
        
        client_data = {
            "primary_identifiers": {},
            "alternate_identifiers": {},
            "extraction_metadata": {},
            "correlation_keys": {}
        }
        
        # Primary identifiers
        if identifiers.email:
            # Extract domain from email
            email_domain = identifiers.email.email.split('@')[1] if '@' in identifiers.email.email else ""
            client_data["primary_identifiers"]["email"] = {
                "address": identifiers.email.email,
                "domain": email_domain,
                "confidence": identifiers.email.confidence,
                "source_field": identifiers.email.source_field
            }
            # Add searchable key
            client_data["correlation_keys"]["email_key"] = identifiers.email.email.lower()
        
        if identifiers.phone:
            client_data["primary_identifiers"]["phone"] = {
                "number": identifiers.phone.normalized_phone,
                "raw_number": identifiers.phone.raw_phone,
                "country_code": identifiers.phone.country_code,
                "confidence": identifiers.phone.confidence,
                "source_field": identifiers.phone.source_field,
                "is_valid": identifiers.phone.is_valid
            }
            # Add searchable key
            client_data["correlation_keys"]["phone_key"] = identifiers.phone.normalized_phone
        
        if identifiers.full_name:
            client_data["primary_identifiers"]["name"] = {
                "full_name": identifiers.full_name.sanitized_name,
                "raw_name": identifiers.full_name.raw_name,
                "confidence": identifiers.full_name.confidence,
                "source_field": identifiers.full_name.source_field,
                "is_complete": identifiers.full_name.is_complete
            }
            # Add searchable key
            client_data["correlation_keys"]["name_key"] = identifiers.full_name.sanitized_name.lower()
        
        if identifiers.first_name:
            client_data["primary_identifiers"]["first_name"] = {
                "name": identifiers.first_name.sanitized_name,
                "raw_name": identifiers.first_name.raw_name,
                "confidence": identifiers.first_name.confidence,
                "source_field": identifiers.first_name.source_field
            }
        
        if identifiers.last_name:
            client_data["primary_identifiers"]["last_name"] = {
                "name": identifiers.last_name.sanitized_name,
                "raw_name": identifiers.last_name.raw_name,
                "confidence": identifiers.last_name.confidence,
                "source_field": identifiers.last_name.source_field
            }
        
        if identifiers.company_name:
            client_data["primary_identifiers"]["company_name"] = {
                "name": identifiers.company_name.sanitized_name,
                "raw_name": identifiers.company_name.raw_name,
                "confidence": identifiers.company_name.confidence,
                "source_field": identifiers.company_name.source_field
            }
        
        # Alternate identifiers
        if identifiers.alternate_emails:
            client_data["alternate_identifiers"]["emails"] = [
                {
                    "address": email.email,
                    "domain": email.email.split('@')[1] if '@' in email.email else "",
                    "confidence": email.confidence,
                    "source_field": email.source_field
                }
                for email in identifiers.alternate_emails
            ]
        
        if identifiers.alternate_phones:
            client_data["alternate_identifiers"]["phones"] = [
                {
                    "number": phone.normalized_phone,
                    "raw_number": phone.raw_phone,
                    "country_code": phone.country_code,
                    "confidence": phone.confidence,
                    "source_field": phone.source_field,
                    "is_valid": phone.is_valid
                }
                for phone in identifiers.alternate_phones
            ]
        
        # Extraction metadata
        client_data["extraction_metadata"] = {
            "extraction_status": extraction_result.extraction_status.value,
            "overall_confidence": identifiers.overall_confidence,
            "extraction_timestamp": identifiers.extraction_timestamp.isoformat(),
            "field_mappings": extraction_result.field_mappings,
            "unmapped_fields": extraction_result.unmapped_fields
        }
        
        # User correlation
        if identifiers.user_id:
            client_data["correlation_keys"]["user_id"] = identifiers.user_id
        
        return client_data
    
    async def _extract_response_metadata(
        self,
        webhook_response: WebhookFormResponse,
        validated_response: FormResponseDataValidation,
        context: TransformationContext
    ) -> Dict[str, Any]:
        """
        Extract metadata from webhook response for storage.
        
        Args:
            webhook_response: Original webhook response
            validated_response: Validated response data
            context: Transformation context
            
        Returns:
            Dict with response metadata
        """
        metadata = {
            "form_metadata": {
                "form_id": webhook_response.form_id,
                "response_token": webhook_response.token,
                "landed_at": webhook_response.landed_at.isoformat(),
                "submitted_at": webhook_response.submitted_at.isoformat()
            },
            "validation_metadata": {
                "total_fields": validated_response.total_fields,
                "valid_fields": validated_response.valid_fields,
                "completion_rate": validated_response.completion_rate,
                "validation_errors": validated_response.validation_errors,
                "validation_warnings": validated_response.validation_warnings
            },
            "processing_metadata": {
                "transformation_timestamp": datetime.now().isoformat(),
                "context_user_id": context.user_id
            }
        }
        
        # Include additional webhook metadata if available
        if webhook_response.calculated:
            metadata["calculated_values"] = webhook_response.calculated
        
        if webhook_response.variables:
            metadata["hidden_variables"] = webhook_response.variables
        
        if webhook_response.metadata:
            metadata["typeform_metadata"] = webhook_response.metadata
        
        return metadata
    
    def _extract_submission_id(self, webhook_response: WebhookFormResponse) -> Optional[str]:
        """
        Extract submission ID from webhook response.
        
        Args:
            webhook_response: Webhook response
            
        Returns:
            Submission ID if available
        """
        # TypeForm may include submission ID in metadata
        if webhook_response.metadata and "submission_id" in webhook_response.metadata:
            return webhook_response.metadata["submission_id"]
        
        # Fall back to token as submission ID
        return webhook_response.token
    
    def _serialize_response_value(self, response: Any) -> Any:
        """
        Serialize response value for JSON storage.
        
        Args:
            response: Response value to serialize
            
        Returns:
            JSON-serializable value
        """
        # Handle Pydantic models
        if hasattr(response, 'model_dump'):
            return response.model_dump()
        
        # Handle datetime objects
        if isinstance(response, datetime):
            return response.isoformat()
        
        # Handle other types
        return response
    
    def _normalize_field_title(self, title: str) -> str:
        """
        Normalize field title for mapping keys.
        
        Args:
            title: Field title
            
        Returns:
            Normalized title for use as mapping key
        """
        # Convert to lowercase and replace spaces/special chars
        normalized = title.lower()
        normalized = ''.join(c if c.isalnum() else '_' for c in normalized)
        normalized = '_'.join(part for part in normalized.split('_') if part)
        return normalized[:50]  # Limit length
    
    def _count_field_types(self, fields: list[NormalizedFieldResponse]) -> Dict[str, int]:
        """
        Count field types for analytics.
        
        Args:
            fields: List of normalized field responses
            
        Returns:
            Dict with field type counts
        """
        type_counts = {}
        for field in fields:
            field_type = field.field_type.value
            type_counts[field_type] = type_counts.get(field_type, 0) + 1
        return type_counts
    
    def _create_searchable_values(self, field: NormalizedFieldResponse) -> Dict[str, Any]:
        """
        Create searchable values for field optimization.
        
        Args:
            field: Normalized field response
            
        Returns:
            Dict with searchable/indexable values
        """
        searchable = {}
        
        # Add text-based search values
        if field.field_type in [ResponseFieldType.SHORT_TEXT, ResponseFieldType.LONG_TEXT]:
            if field.text_response and hasattr(field.text_response, 'sanitized_value'):
                searchable["text_value"] = field.text_response.sanitized_value.lower()
        
        # Add email search values
        elif field.field_type == ResponseFieldType.EMAIL:
            if field.email_response and hasattr(field.email_response, 'email'):
                searchable["email_value"] = field.email_response.email.lower()
                searchable["email_domain"] = field.email_response.domain.lower()
        
        # Add phone search values
        elif field.field_type == ResponseFieldType.PHONE_NUMBER:
            if field.phone_response and hasattr(field.phone_response, 'formatted_phone'):
                searchable["phone_value"] = field.phone_response.formatted_phone
                searchable["raw_phone_value"] = field.phone_response.raw_phone
        
        # Add choice search values
        elif field.field_type in [ResponseFieldType.MULTIPLE_CHOICE, ResponseFieldType.DROPDOWN]:
            if field.choice_response and hasattr(field.choice_response, 'choice_label'):
                searchable["choice_value"] = field.choice_response.choice_label.lower()
                if field.choice_response.is_other and field.choice_response.other_text:
                    searchable["other_text_value"] = field.choice_response.other_text.lower()
        
        # Add number search values
        elif field.field_type == ResponseFieldType.NUMBER:
            if field.number_response and hasattr(field.number_response, 'numeric_value'):
                searchable["number_value"] = field.number_response.numeric_value
        
        # Add date search values
        elif field.field_type == ResponseFieldType.DATE:
            if field.date_response and hasattr(field.date_response, 'iso_format'):
                searchable["date_value"] = field.date_response.iso_format
        
        # Add general storage value for fallback
        if field.storage_value:
            searchable["storage_value"] = str(field.storage_value).lower()
        
        return searchable 