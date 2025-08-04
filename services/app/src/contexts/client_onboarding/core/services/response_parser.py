"""
Response Data Parser Service

Parse various TypeForm question types using validated schemas into normalized JSONB.
Transforms validated TypeForm responses to internal storage format following existing patterns.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass

from src.contexts.client_onboarding.core.adapters.api_schemas.webhook.typeform_webhook_payload import (
    FieldAnswer, 
    FieldType,
    FormResponse as WebhookFormResponse
)
from src.contexts.client_onboarding.core.adapters.api_schemas.responses.form_response_data import (
    ResponseFieldType,
    SanitizedTextResponse,
    ValidatedEmailResponse,
    ValidatedUrlResponse,
    ValidatedNumberResponse,
    ValidatedPhoneResponse,
    ValidatedDateResponse,
    ValidatedChoiceResponse,
    NormalizedFieldResponse,
    FormResponseDataValidation
)
from src.contexts.client_onboarding.core.services.exceptions import (
    FormResponseProcessingError,
    WebhookPayloadError
)

logger = logging.getLogger(__name__)


@dataclass
class ParsedFieldData:
    """Container for parsed field data."""
    field_id: str
    field_type: ResponseFieldType
    field_title: str
    normalized_response: NormalizedFieldResponse
    storage_ready: bool = True


class ResponseDataParser:
    """
    Parse and normalize TypeForm response data using validated schemas.
    
    Converts raw TypeForm webhook response data into structured, validated
    format optimized for JSONB storage and client identifier extraction.
    """
    
    def __init__(self):
        """Initialize response data parser."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def parse_form_response(
        self, 
        webhook_response: WebhookFormResponse
    ) -> FormResponseDataValidation:
        """
        Parse complete form response data from webhook payload.
        
        Args:
            webhook_response: Validated webhook form response
            
        Returns:
            FormResponseDataValidation with normalized field responses
            
        Raises:
            FormResponseProcessingError: For parsing failures
        """
        try:
            self.logger.info(f"Parsing form response for form {webhook_response.form_id}, token {webhook_response.token}")
            
            # Process each field answer
            validated_fields = []
            for answer in webhook_response.answers:
                try:
                    parsed_field = await self._parse_field_answer(answer)
                    if parsed_field.storage_ready:
                        validated_fields.append(parsed_field.normalized_response)
                    else:
                        self.logger.warning(f"Field {parsed_field.field_id} not ready for storage, skipping")
                        
                except Exception as e:
                    self.logger.error(f"Error parsing field {answer.field.id}: {str(e)}")
                    # Continue processing other fields rather than failing entirely
                    continue
            
            # Create validation result
            form_validation = FormResponseDataValidation(
                form_id=webhook_response.form_id,
                response_token=webhook_response.token,
                validated_fields=validated_fields,
                total_fields=len(webhook_response.answers),
                valid_fields=len(validated_fields),
                completion_rate=len(validated_fields) / len(webhook_response.answers) if webhook_response.answers else 1.0
            )
            
            self.logger.info(f"Successfully parsed form response: {len(validated_fields)}/{len(webhook_response.answers)} fields processed")
            return form_validation
            
        except Exception as e:
            error_msg = f"Error parsing form response for form {webhook_response.form_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise FormResponseProcessingError(
                "response_parsing",
                webhook_response.form_id,
                error_msg
            ) from e
    
    async def _parse_field_answer(self, answer: FieldAnswer) -> ParsedFieldData:
        """
        Parse individual field answer based on its type.
        
        Args:
            answer: Field answer from webhook
            
        Returns:
            ParsedFieldData with normalized response
        """
        field_type = self._map_field_type(answer.type)
        field_title = answer.field.title or f"Field {answer.field.id}"
        
        # Parse based on field type
        normalized_response = await self._create_normalized_response(answer, field_type, field_title)
        
        return ParsedFieldData(
            field_id=answer.field.id,
            field_type=field_type,
            field_title=field_title,
            normalized_response=normalized_response,
            storage_ready=True
        )
    
    async def _create_normalized_response(
        self, 
        answer: FieldAnswer, 
        field_type: ResponseFieldType,
        field_title: str
    ) -> NormalizedFieldResponse:
        """
        Create normalized field response based on field type.
        
        Args:
            answer: Field answer from webhook
            field_type: Mapped response field type
            field_title: Field title/question
            
        Returns:
            NormalizedFieldResponse with appropriate type-specific data
        """
        # Initialize response data containers
        text_response = None
        email_response = None
        url_response = None
        number_response = None
        phone_response = None
        date_response = None
        choice_response = None
        choices_response = None
        boolean_response = None
        
        # Process based on field type
        if field_type in [ResponseFieldType.SHORT_TEXT, ResponseFieldType.LONG_TEXT]:
            text_response = await self._parse_text_response(answer.text)
            storage_value = answer.text
            display_value = answer.text or ""
            
        elif field_type == ResponseFieldType.EMAIL:
            email_response = await self._parse_email_response(answer.email)
            storage_value = answer.email
            display_value = answer.email or ""
            
        elif field_type == ResponseFieldType.WEBSITE:
            url_response = await self._parse_url_response(answer.url)
            storage_value = answer.url
            display_value = answer.url or ""
            
        elif field_type in [ResponseFieldType.NUMBER, ResponseFieldType.RATING, ResponseFieldType.OPINION_SCALE]:
            number_response = await self._parse_number_response(answer.number, field_type)
            storage_value = answer.number
            display_value = str(answer.number) if answer.number is not None else ""
            
        elif field_type == ResponseFieldType.PHONE_NUMBER:
            phone_response = await self._parse_phone_response(answer.phone_number)
            storage_value = answer.phone_number
            display_value = answer.phone_number or ""
            
        elif field_type == ResponseFieldType.DATE:
            date_response = await self._parse_date_response(answer.date)
            storage_value = answer.date
            display_value = answer.date or ""
            
        elif field_type == ResponseFieldType.YES_NO:
            boolean_response = answer.boolean
            storage_value = answer.boolean
            display_value = "Yes" if answer.boolean else "No" if answer.boolean is not None else ""
            
        elif field_type in [ResponseFieldType.MULTIPLE_CHOICE, ResponseFieldType.PICTURE_CHOICE, ResponseFieldType.DROPDOWN]:
            if answer.choices:  # Multiple choices
                choices_response = await self._parse_multiple_choice_response(answer.choices)
                storage_value = [choice.label for choice in answer.choices if choice.label]
                display_value = ", ".join([choice.label for choice in answer.choices if choice.label])
            elif answer.choice:  # Single choice
                choice_response = await self._parse_single_choice_response(answer.choice)
                storage_value = answer.choice.label
                display_value = answer.choice.label or ""
            else:
                storage_value = None
                display_value = ""
                
        elif field_type == ResponseFieldType.FILE_UPLOAD:
            storage_value = answer.file_url
            display_value = answer.file_url or ""
            
        elif field_type == ResponseFieldType.PAYMENT:
            storage_value = answer.payment
            display_value = str(answer.payment) if answer.payment else ""
            
        else:
            # Generic handling for unsupported types
            storage_value = self._extract_generic_value(answer)
            display_value = str(storage_value) if storage_value is not None else ""
        
        return NormalizedFieldResponse(
            field_id=answer.field.id,
            field_ref=answer.field.ref,
            field_title=field_title,
            field_type=field_type,
            text_response=text_response,
            email_response=email_response,
            url_response=url_response,
            number_response=number_response,
            phone_response=phone_response,
            date_response=date_response,
            choice_response=choice_response,
            choices_response=choices_response,
            boolean_response=boolean_response,
            storage_value=storage_value,
            display_value=display_value
        )
    
    async def _parse_text_response(self, text_value: Optional[str]) -> Optional[SanitizedTextResponse]:
        """Parse and sanitize text response."""
        if not text_value:
            return None
            
        sanitized_value = text_value.strip()
        return SanitizedTextResponse(
            raw_value=text_value,
            sanitized_value=sanitized_value,
            character_count=len(sanitized_value),
            word_count=len(sanitized_value.split()) if sanitized_value else 0,
            is_truncated=False # Added missing parameter
        )
    
    async def _parse_email_response(self, email_value: Optional[str]) -> Optional[ValidatedEmailResponse]:
        """Parse and validate email response."""
        if not email_value:
            return None
            
        # Basic validation
        is_valid = '@' in email_value and '.' in email_value.split('@')[1]
        normalized_email = email_value.lower().strip()
        domain = normalized_email.split('@')[1] if '@' in normalized_email else ""
        
        # Check if business email
        consumer_domains = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'aol.com', 'icloud.com', 'protonmail.com'
        }
        is_business_email = domain not in consumer_domains
        
        return ValidatedEmailResponse(
            email=normalized_email,
            domain=domain,
            is_business_email=is_business_email,
            is_valid_format=is_valid
        )
    
    async def _parse_url_response(self, url_value: Optional[str]) -> Optional[ValidatedUrlResponse]:
        """Parse and validate URL response."""
        if not url_value:
            return None
            
        # Normalize URL
        normalized_url = url_value.strip()
        if not normalized_url.startswith(('http://', 'https://')):
            normalized_url = f'https://{normalized_url}'
        
        # Extract URL components
        try:
            from urllib.parse import urlparse
            parsed = urlparse(normalized_url)
            domain = parsed.netloc
            scheme = parsed.scheme
            is_secure = scheme == 'https'
            is_valid = bool(domain and scheme)
        except Exception:
            domain = ""
            scheme = "unknown"
            is_secure = False
            is_valid = False
        
        return ValidatedUrlResponse(
            url=normalized_url,
            domain=domain,
            scheme=scheme,
            is_secure=is_secure,
            is_valid=is_valid
        )
    
    async def _parse_number_response(
        self, 
        number_value: Optional[Union[int, float]], 
        field_type: ResponseFieldType
    ) -> Optional[ValidatedNumberResponse]:
        """Parse and validate number response."""
        if number_value is None:
            return None
            
        numeric_value = float(number_value)
        is_integer = isinstance(number_value, int) or (isinstance(number_value, float) and number_value.is_integer())
        is_positive = numeric_value > 0
            
        return ValidatedNumberResponse(
            raw_value=number_value,
            numeric_value=numeric_value,
            is_integer=is_integer,
            is_positive=is_positive
        )
    
    async def _parse_phone_response(self, phone_value: Optional[str]) -> Optional[ValidatedPhoneResponse]:
        """Parse and validate phone response."""
        if not phone_value:
            return None
            
        # Basic phone validation - contains only digits, spaces, hyphens, parentheses, plus
        import re
        digits_only = re.sub(r'[^\d]', '', phone_value)
        
        # Basic formatting logic
        if len(digits_only) == 10:
            # US format
            formatted_phone = f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
            country_code = "US"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            # US with country code
            formatted_phone = f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
            country_code = "US"
        else:
            # International or unknown format
            formatted_phone = f"+{digits_only}" if digits_only else phone_value
            country_code = None
        
        is_valid = len(digits_only) >= 7
        
        return ValidatedPhoneResponse(
            raw_phone=phone_value,
            formatted_phone=formatted_phone,
            country_code=country_code,
            is_valid=is_valid
        )
    
    async def _parse_date_response(self, date_value: Optional[str]) -> Optional[ValidatedDateResponse]:
        """Parse and validate date response."""
        if not date_value:
            return None
            
        try:
            parsed_date = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            from datetime import date
            date_obj = parsed_date.date()
            iso_format = date_obj.isoformat()
            is_future = date_obj > date.today()
            
            return ValidatedDateResponse(
                raw_date=date_value,
                parsed_date=date_obj,
                iso_format=iso_format,
                is_future=is_future
            )
        except (ValueError, AttributeError):
            from datetime import date
            return ValidatedDateResponse(
                raw_date=date_value,
                parsed_date=date.today(),  # Fallback to today's date
                iso_format="",
                is_future=False
            )
    
    async def _parse_single_choice_response(self, choice) -> ValidatedChoiceResponse:
        """Parse single choice response."""
        return ValidatedChoiceResponse(
            choice_id=choice.id,
            choice_label=choice.label,
            choice_ref=getattr(choice, 'ref', None),
            is_other=False,
            other_text=None
        )
    
    async def _parse_multiple_choice_response(self, choices) -> List[ValidatedChoiceResponse]:
        """Parse multiple choice responses."""
        return [
            ValidatedChoiceResponse(
                choice_id=choice.id,
                choice_label=choice.label,
                choice_ref=getattr(choice, 'ref', None),
                is_other=False,
                other_text=None
            )
            for choice in choices
        ]
    
    def _map_field_type(self, webhook_field_type: FieldType) -> ResponseFieldType:
        """
        Map webhook field type to response field type.
        
        Args:
            webhook_field_type: Field type from webhook
            
        Returns:
            Mapped ResponseFieldType
        """
        type_mapping = {
            FieldType.SHORT_TEXT: ResponseFieldType.SHORT_TEXT,
            FieldType.LONG_TEXT: ResponseFieldType.LONG_TEXT,
            FieldType.MULTIPLE_CHOICE: ResponseFieldType.MULTIPLE_CHOICE,
            FieldType.PICTURE_CHOICE: ResponseFieldType.PICTURE_CHOICE,
            FieldType.YES_NO: ResponseFieldType.YES_NO,
            FieldType.DROPDOWN: ResponseFieldType.DROPDOWN,
            FieldType.NUMBER: ResponseFieldType.NUMBER,
            FieldType.RATING: ResponseFieldType.RATING,
            FieldType.EMAIL: ResponseFieldType.EMAIL,
            FieldType.WEBSITE: ResponseFieldType.WEBSITE,
            FieldType.FILE_UPLOAD: ResponseFieldType.FILE_UPLOAD,
            FieldType.DATE: ResponseFieldType.DATE,
            FieldType.PHONE_NUMBER: ResponseFieldType.PHONE_NUMBER,
            FieldType.PAYMENT: ResponseFieldType.PAYMENT,
            FieldType.LEGAL: ResponseFieldType.LEGAL,
            FieldType.OPINION_SCALE: ResponseFieldType.OPINION_SCALE
        }
        
        return type_mapping.get(webhook_field_type, ResponseFieldType.SHORT_TEXT)
    
    def _extract_generic_value(self, answer: FieldAnswer) -> Any:
        """
        Extract value from field answer for unsupported types.
        
        Args:
            answer: Field answer
            
        Returns:
            Best guess at the answer value
        """
        # Try different value fields in order of preference
        for field_name in ['text', 'email', 'url', 'number', 'boolean', 'date', 'phone_number']:
            value = getattr(answer, field_name, None)
            if value is not None:
                return value
        
        # Try choice values
        if answer.choice:
            return answer.choice.label
        if answer.choices:
            return [choice.label for choice in answer.choices]
        
        # Try other complex fields
        if answer.file_url:
            return answer.file_url
        if answer.payment:
            return answer.payment
            
        return None


# Convenience functions for common parsing operations
async def parse_webhook_form_response(webhook_response: WebhookFormResponse) -> FormResponseDataValidation:
    """
    Convenience function to parse webhook form response.
    
    Args:
        webhook_response: Validated webhook form response
        
    Returns:
        FormResponseDataValidation with normalized field responses
    """
    parser = ResponseDataParser()
    return await parser.parse_form_response(webhook_response)


async def parse_field_answers(answers: List[FieldAnswer]) -> List[NormalizedFieldResponse]:
    """
    Convenience function to parse list of field answers.
    
    Args:
        answers: List of field answers
        
    Returns:
        List of normalized field responses
    """
    parser = ResponseDataParser()
    normalized_responses = []
    
    for answer in answers:
        try:
            parsed_field = await parser._parse_field_answer(answer)
            if parsed_field.storage_ready:
                normalized_responses.append(parsed_field.normalized_response)
        except Exception as e:
            logger.error(f"Error parsing field answer {answer.field.id}: {str(e)}")
            continue
            
    return normalized_responses 