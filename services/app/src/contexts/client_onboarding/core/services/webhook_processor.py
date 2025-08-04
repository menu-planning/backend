"""
Webhook payload processing for TypeForm webhooks.

This module provides parsing, validation, and processing of TypeForm webhook
payloads, converting them into structured data for storage and client creation.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.core.domain.models.form_response import FormResponse
from src.contexts.client_onboarding.core.services.exceptions import (
    WebhookPayloadError,
    FormResponseProcessingError,
    OnboardingFormNotFoundError,
    DatabaseOperationError,
)


logger = logging.getLogger(__name__)


@dataclass
class FormFieldResponse:
    """Structured representation of a TypeForm field response."""
    field_id: str
    field_type: str
    question: str
    answer: Any
    field_ref: Optional[str] = None


@dataclass
class ProcessedWebhookData:
    """Structured webhook data ready for storage."""
    event_id: str
    event_type: str
    form_id: str
    response_token: str
    submitted_at: datetime
    field_responses: List[FormFieldResponse]
    metadata: Dict[str, Any]
    client_identifiers: Dict[str, str]


class WebhookPayloadProcessor:
    """
    Processor for TypeForm webhook payloads.
    
    Handles parsing, validation, and structuring of webhook data
    for database storage and client creation workflows.
    """
    
    def __init__(self, uow: UnitOfWork):
        """
        Initialize webhook payload processor.
        
        Args:
            uow: Unit of work for database operations
        """
        self.uow = uow
    
    async def process_webhook_payload(
        self, 
        payload_dict: Dict[str, Any]
    ) -> ProcessedWebhookData:
        """
        Process and validate TypeForm webhook payload.
        
        Args:
            payload_dict: Parsed webhook payload dictionary
            
        Returns:
            ProcessedWebhookData with structured information
            
        Raises:
            WebhookPayloadError: For invalid payload structure
            FormResponseProcessingError: For processing failures
            OnboardingFormNotFoundError: If form not found in database
        """
        try:
            logger.info(f"Processing webhook payload for event: {payload_dict.get('event_id', 'unknown')}")
            
            # Extract basic event information
            event_info = await self._extract_event_info(payload_dict)
            
            # Verify form exists in our database
            await self._verify_form_exists(event_info['form_id'])
            
            # Process form response data
            field_responses = await self._process_form_responses(
                payload_dict.get('form_response', {})
            )
            
            # Extract client identification data
            client_identifiers = await self._extract_client_identifiers(field_responses)
            
            # Extract metadata
            metadata = await self._extract_metadata(payload_dict)
            
            processed_data = ProcessedWebhookData(
                event_id=event_info['event_id'],
                event_type=event_info['event_type'],
                form_id=event_info['form_id'],
                response_token=event_info['response_token'],
                submitted_at=event_info['submitted_at'],
                field_responses=field_responses,
                metadata=metadata,
                client_identifiers=client_identifiers
            )
            
            logger.info(f"Successfully processed webhook payload: {processed_data.event_id}")
            return processed_data
            
        except (WebhookPayloadError, FormResponseProcessingError, OnboardingFormNotFoundError):
            # Re-raise known exceptions
            raise
        except Exception as e:
            error_msg = f"Unexpected error processing webhook payload: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise FormResponseProcessingError("unknown", "payload_processing", error_msg) from e
    
    async def _extract_event_info(self, payload_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract basic event information from webhook payload.
        
        Args:
            payload_dict: Webhook payload dictionary
            
        Returns:
            Dictionary with event information
            
        Raises:
            WebhookPayloadError: If required fields are missing
        """
        try:
            form_response = payload_dict.get('form_response', {})
            
            # Parse submitted_at timestamp
            submitted_at_str = form_response.get('submitted_at')
            if not submitted_at_str:
                raise WebhookPayloadError("Missing submitted_at timestamp")
            
            try:
                # TypeForm timestamps are in ISO format
                submitted_at = datetime.fromisoformat(submitted_at_str.replace('Z', '+00:00'))
                # Convert to naive UTC datetime for database storage (TIMESTAMP WITHOUT TIME ZONE)
                submitted_at = submitted_at.astimezone(timezone.utc).replace(tzinfo=None)
            except ValueError as e:
                raise WebhookPayloadError(f"Invalid submitted_at format: {submitted_at_str}") from e
            
            return {
                'event_id': payload_dict.get('event_id'),
                'event_type': payload_dict.get('event_type'),
                'form_id': form_response.get('form_id'),
                'response_token': form_response.get('token'),
                'submitted_at': submitted_at
            }
            
        except Exception as e:
            if isinstance(e, WebhookPayloadError):
                raise
            raise WebhookPayloadError(f"Error extracting event info: {str(e)}") from e
    
    async def _verify_form_exists(self, form_id: str) -> None:
        """
        Verify that the form exists in our database.
        
        Args:
            form_id: TypeForm form ID
            
        Raises:
            OnboardingFormNotFoundError: If form not found
        """
        try:
            form = await self.uow.onboarding_forms.get_by_typeform_id(form_id)
            if not form:
                raise OnboardingFormNotFoundError(f"Form not found: {form_id}")
            
            logger.debug(f"Verified form exists: {form_id} (DB ID: {form.id})")
            
        except Exception as e:
            if isinstance(e, OnboardingFormNotFoundError):
                raise
            raise DatabaseOperationError("form_verification", "onboarding_form", str(e)) from e
    
    async def _process_form_responses(
        self, 
        form_response: Dict[str, Any]
    ) -> List[FormFieldResponse]:
        """
        Process individual field responses from the form.
        
        Args:
            form_response: Form response section of webhook payload
            
        Returns:
            List of structured field responses
            
        Raises:
            WebhookPayloadError: If response data is malformed
        """
        try:
            answers = form_response.get('answers', [])
            if not isinstance(answers, list):
                raise WebhookPayloadError("Form answers must be a list")
            
            field_responses = []
            
            for answer in answers:
                if not isinstance(answer, dict):
                    logger.warning(f"Skipping malformed answer: {answer}")
                    continue
                
                try:
                    field_response = await self._parse_field_answer(answer)
                    if field_response:
                        field_responses.append(field_response)
                except Exception as e:
                    logger.warning(f"Error parsing field answer: {e}, answer: {answer}")
                    # Continue processing other fields
                    continue
            
            logger.debug(f"Processed {len(field_responses)} field responses")
            return field_responses
            
        except Exception as e:
            if isinstance(e, WebhookPayloadError):
                raise
            raise WebhookPayloadError(f"Error processing form responses: {str(e)}") from e
    
    async def _parse_field_answer(self, answer: Dict[str, Any]) -> Optional[FormFieldResponse]:
        """
        Parse a single field answer from TypeForm response.
        
        Args:
            answer: Individual answer dictionary from TypeForm
            
        Returns:
            FormFieldResponse or None if answer is invalid
        """
        try:
            field_info = answer.get('field', {})
            field_id = field_info.get('id')
            field_type = field_info.get('type')
            field_ref = field_info.get('ref')
            
            if not field_id or not field_type:
                logger.warning(f"Missing field ID or type: {answer}")
                return None
            
            # Extract question text
            question = field_info.get('title', 'Unknown Question')
            
            # Extract answer value based on field type
            answer_value = await self._extract_answer_value(answer, field_type)
            
            return FormFieldResponse(
                field_id=field_id,
                field_type=field_type,
                question=question,
                answer=answer_value,
                field_ref=field_ref
            )
            
        except Exception as e:
            logger.error(f"Error parsing field answer: {e}")
            return None
    
    async def _extract_answer_value(self, answer: Dict[str, Any], field_type: str) -> Any:
        """
        Extract the answer value based on TypeForm field type.
        
        Args:
            answer: Answer dictionary
            field_type: TypeForm field type
            
        Returns:
            Extracted answer value
        """
        # TypeForm answer structure varies by field type
        answer_data = answer.get('answer', answer)
        
        # Handle different field types
        if field_type in ['short_text', 'long_text', 'email', 'website', 'phone_number']:
            return answer_data.get('text', '')
        
        elif field_type == 'number':
            return answer_data.get('number')
        
        elif field_type == 'boolean':
            return answer_data.get('boolean')
        
        elif field_type in ['choice', 'multiple_choice']:
            # multiple_choice fields can have single choice answers
            choice = answer_data.get('choice', {})
            return {
                'id': choice.get('id'),
                'label': choice.get('label'),
                'ref': choice.get('ref')
            }
        
        elif field_type == 'choices':
            choices = answer_data.get('choices', [])
            return [
                {
                    'id': choice.get('id'),
                    'label': choice.get('label'),
                    'ref': choice.get('ref')
                }
                for choice in choices
            ]
        
        elif field_type == 'date':
            return answer_data.get('date')
        
        elif field_type == 'file_url':
            return answer_data.get('file_url')
        
        elif field_type == 'payment':
            return {
                'amount': answer_data.get('amount'),
                'last4': answer_data.get('last4'),
                'name': answer_data.get('name')
            }
        
        else:
            # For unknown types, store the raw answer data
            logger.warning(f"Unknown field type: {field_type}, storing raw data")
            return answer_data
    
    async def _extract_client_identifiers(
        self, 
        field_responses: List[FormFieldResponse]
    ) -> Dict[str, str]:
        """
        Extract client identification information from field responses.
        
        Args:
            field_responses: List of processed field responses
            
        Returns:
            Dictionary with client identifier fields
        """
        identifiers = {}
        
        # Look for common client identification fields
        identifier_patterns = {
            'name': ['name', 'full_name', 'client_name', 'your_name'],
            'email': ['email', 'email_address', 'contact_email'],
            'phone': ['phone', 'phone_number', 'contact_phone', 'mobile'],
            'company': ['company', 'company_name', 'organization', 'business_name']
        }
        
        for field_response in field_responses:
            field_ref = (field_response.field_ref or '').lower()
            question = field_response.question.lower()
            
            # Check if this field matches any identifier patterns
            for identifier_type, patterns in identifier_patterns.items():
                if any(pattern in field_ref or pattern in question for pattern in patterns):
                    if field_response.answer:
                        identifiers[identifier_type] = str(field_response.answer)
                        break
        
        logger.debug(f"Extracted client identifiers: {list(identifiers.keys())}")
        return identifiers
    
    async def _extract_metadata(self, payload_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from webhook payload.
        
        Args:
            payload_dict: Full webhook payload
            
        Returns:
            Dictionary with metadata information
        """
        form_response = payload_dict.get('form_response', {})
        
        metadata = {
            'webhook_received_at': datetime.now().isoformat(),
            'typeform_event_id': payload_dict.get('event_id'),
            'typeform_event_type': payload_dict.get('event_type'),
            'form_response_id': form_response.get('response_id'),
            'landed_at': form_response.get('landed_at'),
            'calculated_score': form_response.get('calculated', {}).get('score'),
            'hidden_fields': form_response.get('hidden', {}),
            'variables': form_response.get('variables', [])
        }
        
        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return metadata
    
    async def store_form_response(
        self, 
        processed_data: ProcessedWebhookData
    ) -> str:
        """
        Store processed webhook data in the database.
        
        Args:
            processed_data: Processed webhook data
            
        Returns:
            ID of the stored form response
            
        Raises:
            DatabaseOperationError: If storage fails
        """
        try:
            # Get the onboarding form record
            form = await self.uow.onboarding_forms.get_by_typeform_id(processed_data.form_id)
            if not form:
                raise OnboardingFormNotFoundError(f"Form not found: {processed_data.form_id}")
            
            # Prepare response data for storage
            response_data = {
                'event_id': processed_data.event_id,
                'event_type': processed_data.event_type,
                'response_token': processed_data.response_token,
                'submitted_at': processed_data.submitted_at.isoformat(),
                'field_responses': [
                    {
                        'field_id': fr.field_id,
                        'field_type': fr.field_type,
                        'question': fr.question,
                        'answer': fr.answer,
                        'field_ref': fr.field_ref
                    }
                    for fr in processed_data.field_responses
                ],
                'client_identifiers': processed_data.client_identifiers,
                'metadata': processed_data.metadata
            }
            
            # Create form response record
            form_response = FormResponse(
                form_id=form.id,
                response_id=processed_data.response_token,
                response_data=response_data,
                client_identifiers=processed_data.client_identifiers,
                submitted_at=processed_data.submitted_at
            )
            
            await self.uow.form_responses.add(form_response)
            await self.uow.commit()
            
            logger.info(f"Stored form response: {form_response.id} for form: {form.id}")
            return processed_data.response_token
            
        except Exception as e:
            await self.uow.rollback()
            if isinstance(e, (OnboardingFormNotFoundError, DatabaseOperationError)):
                raise
            error_msg = f"Error storing form response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DatabaseOperationError("form_response_creation", "form_response", error_msg) from e


class WebhookProcessor:
    """
    High-level webhook processor combining security and payload processing.
    
    This class provides a complete webhook processing pipeline including
    security verification, payload parsing, and data storage.
    """
    
    def __init__(self, uow_factory):
        """
        Initialize webhook processor.
        
        Args:
            uow_factory: Factory function for creating UnitOfWork instances
        """
        self.uow_factory = uow_factory
    
    async def process_webhook(
        self, 
        payload: str, 
        headers: Dict[str, str]
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Process complete webhook request with security and payload handling.
        
        Args:
            payload: Raw webhook payload
            headers: Request headers
            
        Returns:
            Tuple of (success, error_message, response_id)
        """
        async with self.uow_factory() as uow:
            try:
                processor = WebhookPayloadProcessor(uow)
                
                # Parse payload
                try:
                    payload_dict = json.loads(payload)
                except json.JSONDecodeError as e:
                    return False, f"Invalid JSON payload: {str(e)}", None
                
                # Process payload
                processed_data = await processor.process_webhook_payload(payload_dict)
                
                # Store in database
                response_id = await processor.store_form_response(processed_data)
                
                return True, None, response_id
                
            except Exception as e:
                logger.error(f"Webhook processing failed: {str(e)}", exc_info=True)
                return False, str(e), None


# Convenience functions
async def process_typeform_webhook(
    payload: str, 
    headers: Dict[str, str],
    uow_factory
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Convenience function to process TypeForm webhook.
    
    Args:
        payload: Raw webhook payload
        headers: Request headers
        uow_factory: UnitOfWork factory function
        
    Returns:
        Tuple of (success, error_message, response_id)
    """
    processor = WebhookProcessor(uow_factory)
    return await processor.process_webhook(payload, headers) 