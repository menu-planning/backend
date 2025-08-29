"""
Client Identifier Extraction Service

Extract name, email, phone from validated response data using field mapping.
Processes normalized TypeForm responses to identify and extract client identifiers
with confidence scoring and validation.
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass

from src.contexts.client_onboarding.core.adapters.api_schemas.responses.form_response_data import (
    FormResponseDataValidation,
    NormalizedFieldResponse,
    ResponseFieldType
)
from src.contexts.client_onboarding.core.adapters.api_schemas.responses.client_identifiers import (
    ClientIdentifierType,
    ValidatedEmail,
    ValidatedPhoneNumber,
    ValidatedName,
    ClientIdentifierSet,
    IdentifierExtractionResult,
    IdentifierExtractionStatus
)
from src.contexts.client_onboarding.core.services.exceptions import (
    FormResponseProcessingError
)

logger = logging.getLogger(__name__)


@dataclass
class FieldMapping:
    """Configuration for mapping TypeForm fields to client identifiers."""
    field_id: str
    field_title: str
    identifier_type: ClientIdentifierType
    confidence: float
    is_primary: bool = True


@dataclass
class ExtractionContext:
    """Context for identifier extraction process."""
    form_id: str
    response_token: str
    field_mappings: Dict[str, FieldMapping]
    confidence_threshold: float = 0.7
    required_identifiers: Optional[List[ClientIdentifierType]] = None
    
    def __post_init__(self):
        if self.required_identifiers is None:
            self.required_identifiers = [ClientIdentifierType.EMAIL]


class ClientIdentifierExtractor:
    """
    Extract and validate client identifiers from normalized TypeForm responses.
    
    Uses intelligent field mapping and confidence scoring to identify client
    information (name, email, phone) from form response data with fallback
    strategies for handling incomplete or ambiguous data.
    """
    
    def __init__(self):
        """Initialize client identifier extractor."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._confidence_weights = {
            'field_type_match': 0.4,
            'field_title_match': 0.3,
            'data_quality': 0.2,
            'validation_success': 0.1
        }
    
    async def extract_identifiers(
        self,
        validated_response: FormResponseDataValidation,
        field_mappings: Optional[Dict[str, ClientIdentifierType]] = None,
        required_identifiers: Optional[List[ClientIdentifierType]] = None
    ) -> IdentifierExtractionResult:
        """
        Extract client identifiers from validated form response.
        
        Args:
            validated_response: Validated form response data
            field_mappings: Optional explicit field mappings
            required_identifiers: Required identifier types for validation
            
        Returns:
            IdentifierExtractionResult with extracted identifiers and metadata
            
        Raises:
            FormResponseProcessingError: For extraction failures
        """
        try:
            self.logger.info(f"Extracting identifiers from form {validated_response.form_id}, "
                           f"response {validated_response.response_token}")
            
            # Build extraction context
            context = await self._build_extraction_context(
                validated_response, field_mappings, required_identifiers
            )
            
            # Extract identifiers by type
            email_data = await self._extract_emails(validated_response, context)
            phone_data = await self._extract_phones(validated_response, context)
            name_data = await self._extract_names(validated_response, context)
            
            # Build identifier set
            identifier_set = ClientIdentifierSet(
                email=email_data.get('primary'),
                alternate_emails=email_data.get('alternates', []),
                phone=phone_data.get('primary'),
                alternate_phones=phone_data.get('alternates', []),
                full_name=name_data.get('full_name'),
                first_name=name_data.get('first_name'),
                last_name=name_data.get('last_name'),
                company_name=name_data.get('company_name'),
                user_id=None,
                extraction_timestamp=datetime.now(),
                extraction_source=validated_response.response_token,
                overall_confidence=self._calculate_overall_confidence(email_data, phone_data, name_data)
            )
            
            # Evaluate extraction status and quality
            extraction_status = self._determine_extraction_status(identifier_set, context)
            quality_metrics = self._calculate_quality_metrics(identifier_set, context)
            
            result = IdentifierExtractionResult(
                identifiers=identifier_set,
                extraction_status=extraction_status,
                field_mappings={mapping.field_id: mapping.identifier_type.value 
                              for mapping in context.field_mappings.values()},
                unmapped_fields=self._find_unmapped_fields(validated_response, context),
                required_fields_present=quality_metrics['present'],
                missing_required_fields=quality_metrics['missing'],
                data_quality_score=quality_metrics['quality_score'],
                processing_errors=[],
                processing_warnings=quality_metrics['warnings'],
                fallback_strategies_used=quality_metrics['fallbacks']
            )
            
            self.logger.info(f"Successfully extracted identifiers with overall confidence: "
                           f"{identifier_set.overall_confidence:.2f}")
            return result
            
        except Exception as e:
            error_msg = f"Error extracting identifiers from form {validated_response.form_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise FormResponseProcessingError(
                "identifier_extraction",
                validated_response.form_id,
                error_msg
            ) from e
    
    async def _build_extraction_context(
        self,
        validated_response: FormResponseDataValidation,
        explicit_mappings: Optional[Dict[str, ClientIdentifierType]],
        required_identifiers: Optional[List[ClientIdentifierType]]
    ) -> ExtractionContext:
        """Build extraction context with field mappings."""
        field_mappings = {}
        
        # Use explicit mappings if provided, otherwise auto-detect
        if explicit_mappings:
            for field in validated_response.validated_fields:
                if field.field_id in explicit_mappings:
                    field_mappings[field.field_id] = FieldMapping(
                        field_id=field.field_id,
                        field_title=field.field_title,
                        identifier_type=explicit_mappings[field.field_id],
                        confidence=1.0,  # Explicit mappings get full confidence
                        is_primary=True
                    )
        else:
            # Auto-detect field mappings
            field_mappings = await self._auto_detect_field_mappings(validated_response)
        
        return ExtractionContext(
            form_id=validated_response.form_id,
            response_token=validated_response.response_token,
            field_mappings=field_mappings,
            required_identifiers=required_identifiers or [ClientIdentifierType.EMAIL]
        )
    
    async def _auto_detect_field_mappings(
        self, 
        validated_response: FormResponseDataValidation
    ) -> Dict[str, FieldMapping]:
        """Auto-detect field mappings based on field types and titles."""
        mappings = {}
        
        for field in validated_response.validated_fields:
            # Detect by field type first
            identifier_type, type_confidence = self._detect_by_field_type(field)
            
            if identifier_type:
                # Enhance confidence with title analysis
                title_confidence = self._analyze_field_title(field.field_title, identifier_type)
                combined_confidence = (type_confidence * 0.7) + (title_confidence * 0.3)
                
                if combined_confidence >= 0.5:  # Minimum confidence threshold
                    mappings[field.field_id] = FieldMapping(
                        field_id=field.field_id,
                        field_title=field.field_title,
                        identifier_type=identifier_type,
                        confidence=combined_confidence,
                        is_primary=combined_confidence >= 0.8
                    )
        
        return mappings
    
    def _detect_by_field_type(self, field: NormalizedFieldResponse) -> Tuple[Optional[ClientIdentifierType], float]:
        """Detect identifier type by field type with confidence."""
        type_mappings = {
            ResponseFieldType.EMAIL: (ClientIdentifierType.EMAIL, 0.95),
            ResponseFieldType.PHONE_NUMBER: (ClientIdentifierType.PHONE, 0.95),
            ResponseFieldType.SHORT_TEXT: None,  # Needs title analysis
            ResponseFieldType.LONG_TEXT: None,   # Needs title analysis
        }
        
        direct_mapping = type_mappings.get(field.field_type)
        if direct_mapping:
            return direct_mapping
        
        # For text fields, try to infer from content
        if field.field_type in [ResponseFieldType.SHORT_TEXT, ResponseFieldType.LONG_TEXT]:
            if field.text_response:
                return self._infer_from_text_content(field.text_response.sanitized_value)
        
        return None, 0.0
    
    def _analyze_field_title(self, title: str, suspected_type: ClientIdentifierType) -> float:
        """Analyze field title to enhance confidence in identifier type."""
        title_lower = title.lower()
        
        # Define keywords for each identifier type
        keywords = {
            ClientIdentifierType.EMAIL: ['email', 'e-mail', 'address', 'contact'],
            ClientIdentifierType.PHONE: ['phone', 'mobile', 'cell', 'telephone', 'contact'],
            ClientIdentifierType.FIRST_NAME: ['first', 'given', 'name'],
            ClientIdentifierType.LAST_NAME: ['last', 'family', 'surname'],
            ClientIdentifierType.FULL_NAME: ['full name', 'name', 'your name'],
            ClientIdentifierType.COMPANY_NAME: ['company', 'organization', 'business', 'firm']
        }
        
        type_keywords = keywords.get(suspected_type, [])
        matches = sum(1 for keyword in type_keywords if keyword in title_lower)
        
        return min(1.0, matches * 0.4)  # Each keyword match adds 0.4 confidence
    
    def _infer_from_text_content(self, content: str) -> Tuple[Optional[ClientIdentifierType], float]:
        """Infer identifier type from text content patterns."""
        if not content:
            return None, 0.0
        
        content_lower = content.lower().strip()
        
        # Email pattern
        if '@' in content_lower and '.' in content_lower:
            return ClientIdentifierType.EMAIL, 0.8
        
        # Phone pattern
        if re.match(r'^[\+]?[\d\s\-\(\)]+$', content) and len(re.sub(r'[^\d]', '', content)) >= 7:
            return ClientIdentifierType.PHONE, 0.8
        
        # Name patterns (heuristic based on word count and capitalization)
        words = content.split()
        if 1 <= len(words) <= 3 and all(word.istitle() for word in words):
            if len(words) == 1:
                return ClientIdentifierType.FIRST_NAME, 0.6
            elif len(words) == 2:
                return ClientIdentifierType.FULL_NAME, 0.7
        
        return None, 0.0
    
    async def _extract_emails(
        self, 
        validated_response: FormResponseDataValidation,
        context: ExtractionContext
    ) -> Dict[str, Any]:
        """Extract email identifiers from validated response."""
        emails = []
        
        for field in validated_response.validated_fields:
            mapping = context.field_mappings.get(field.field_id)
            if mapping and mapping.identifier_type == ClientIdentifierType.EMAIL:
                
                if field.email_response and field.email_response.is_valid_format:
                    email = ValidatedEmail(
                        email=field.email_response.email,
                        source_field=field.field_id,
                        confidence=mapping.confidence * (1.0 if field.email_response.is_valid_format else 0.7),
                        is_primary=mapping.is_primary
                    )
                    emails.append(email)
                elif field.text_response:
                    # Try to extract email from text field
                    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                                          field.text_response.sanitized_value)
                    if email_match:
                        email = ValidatedEmail(
                            email=email_match.group().lower(),
                            source_field=field.field_id,
                            confidence=mapping.confidence * 0.8,  # Lower confidence for text extraction
                            is_primary=mapping.is_primary
                        )
                        emails.append(email)
        
        # Sort by confidence and primary status
        emails.sort(key=lambda x: (x.is_primary, x.confidence), reverse=True)
        
        return {
            'primary': emails[0] if emails else None,
            'alternates': emails[1:] if len(emails) > 1 else []
        }
    
    async def _extract_phones(
        self, 
        validated_response: FormResponseDataValidation,
        context: ExtractionContext
    ) -> Dict[str, Any]:
        """Extract phone number identifiers from validated response."""
        phones = []
        
        for field in validated_response.validated_fields:
            mapping = context.field_mappings.get(field.field_id)
            if mapping and mapping.identifier_type == ClientIdentifierType.PHONE:
                
                if field.phone_response and field.phone_response.is_valid:
                    phone = ValidatedPhoneNumber(
                        raw_phone=field.phone_response.raw_phone,
                        normalized_phone=field.phone_response.formatted_phone,
                        country_code=field.phone_response.country_code,
                        source_field=field.field_id,
                        confidence=mapping.confidence * (1.0 if field.phone_response.is_valid else 0.7),
                        is_valid=field.phone_response.is_valid
                    )
                    phones.append(phone)
                elif field.text_response:
                    # Try to extract phone from text field
                    phone_text = field.text_response.sanitized_value
                    digits_only = re.sub(r'[^\d]', '', phone_text)
                    
                    if len(digits_only) >= 7:
                        phone = ValidatedPhoneNumber(
                            raw_phone=phone_text,
                            normalized_phone=phone_text,
                            country_code=None,
                            source_field=field.field_id,
                            confidence=mapping.confidence * 0.8,
                            is_valid=len(digits_only) >= 10
                        )
                        phones.append(phone)
        
        # Sort by confidence and validity
        phones.sort(key=lambda x: (x.is_valid, x.confidence), reverse=True)
        
        return {
            'primary': phones[0] if phones else None,
            'alternates': phones[1:] if len(phones) > 1 else []
        }
    
    async def _extract_names(
        self, 
        validated_response: FormResponseDataValidation,
        context: ExtractionContext
    ) -> Dict[str, Any]:
        """Extract name identifiers from validated response."""
        names: Dict[str, Optional[ValidatedName]] = {
            'full_name': None,
            'first_name': None,
            'last_name': None,
            'company_name': None
        }
        
        for field in validated_response.validated_fields:
            mapping = context.field_mappings.get(field.field_id)
            if mapping and mapping.identifier_type in [
                ClientIdentifierType.FULL_NAME, 
                ClientIdentifierType.FIRST_NAME,
                ClientIdentifierType.LAST_NAME,
                ClientIdentifierType.COMPANY_NAME
            ]:
                
                if field.text_response and field.text_response.sanitized_value:
                    name_text = field.text_response.sanitized_value
                    
                    # Validate name content
                    if self._is_valid_name(name_text):
                        name = ValidatedName(
                            raw_name=name_text,
                            sanitized_name=self._sanitize_name(name_text),
                            source_field=field.field_id,
                            confidence=mapping.confidence,
                            is_complete=len(name_text.split()) >= 2 if mapping.identifier_type == ClientIdentifierType.FULL_NAME else True
                        )
                        
                        # Map to appropriate name type
                        if mapping.identifier_type == ClientIdentifierType.FULL_NAME:
                            names['full_name'] = name
                        elif mapping.identifier_type == ClientIdentifierType.FIRST_NAME:
                            names['first_name'] = name
                        elif mapping.identifier_type == ClientIdentifierType.LAST_NAME:
                            names['last_name'] = name
                        elif mapping.identifier_type == ClientIdentifierType.COMPANY_NAME:
                            names['company_name'] = name
        
        return names
    
    def _is_valid_name(self, name_text: str) -> bool:
        """Validate that text appears to be a name."""
        if not name_text or len(name_text.strip()) < 2:
            return False
        
        # Check for reasonable name patterns
        name_pattern = re.compile(r"^[a-zA-Z\s\'\-\.]+$")
        return bool(name_pattern.match(name_text))
    
    def _sanitize_name(self, name_text: str) -> str:
        """Sanitize name text for storage."""
        # Remove extra whitespace and normalize
        sanitized = ' '.join(name_text.split())
        
        # Title case
        sanitized = sanitized.title()
        
        return sanitized
    
    def _calculate_overall_confidence(self, email_data: Dict, phone_data: Dict, name_data: Dict) -> float:
        """Calculate overall confidence score for extracted identifiers."""
        confidences = []
        
        # Email confidence
        if email_data.get('primary'):
            confidences.append(email_data['primary'].confidence)
        
        # Phone confidence
        if phone_data.get('primary'):
            confidences.append(phone_data['primary'].confidence)
        
        # Name confidences
        for name_type in ['full_name', 'first_name', 'last_name', 'company_name']:
            name_obj = name_data.get(name_type)
            if name_obj:
                confidences.append(name_obj.confidence)
        
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _determine_extraction_status(
        self, 
        identifier_set: ClientIdentifierSet, 
        context: ExtractionContext
    ) -> IdentifierExtractionStatus:
        """Determine overall extraction status."""
        if not context.required_identifiers:
            return IdentifierExtractionStatus.EXTRACTED
        
        required_present = 0
        for required_type in context.required_identifiers:
            if required_type == ClientIdentifierType.EMAIL and identifier_set.email:
                required_present += 1
            elif required_type == ClientIdentifierType.PHONE and identifier_set.phone:
                required_present += 1
            elif required_type == ClientIdentifierType.FULL_NAME and identifier_set.full_name:
                required_present += 1
            elif required_type == ClientIdentifierType.FIRST_NAME and identifier_set.first_name:
                required_present += 1
            elif required_type == ClientIdentifierType.LAST_NAME and identifier_set.last_name:
                required_present += 1
            elif required_type == ClientIdentifierType.COMPANY_NAME and identifier_set.company_name:
                required_present += 1
        
        if required_present == len(context.required_identifiers):
            return IdentifierExtractionStatus.EXTRACTED
        elif required_present > 0:
            return IdentifierExtractionStatus.PARTIAL
        else:
            return IdentifierExtractionStatus.MISSING
    
    def _calculate_quality_metrics(
        self, 
        identifier_set: ClientIdentifierSet, 
        context: ExtractionContext
    ) -> Dict[str, Any]:
        """Calculate quality metrics for extracted identifiers."""
        present = []
        missing = []
        warnings = []
        fallbacks = []
        
        # Check required identifiers
        if context.required_identifiers:
            for required_type in context.required_identifiers:
                if required_type == ClientIdentifierType.EMAIL:
                    if identifier_set.email:
                        present.append(required_type)
                    else:
                        missing.append(required_type)
                        warnings.append("Required email identifier not found")
                elif required_type == ClientIdentifierType.PHONE:
                    if identifier_set.phone:
                        present.append(required_type)
                    else:
                        missing.append(required_type)
                        warnings.append("Required phone identifier not found")
                # Add other required types as needed
        
        # Calculate quality score
        quality_factors = []
        
        # Identifier completeness
        total_required = len(context.required_identifiers) if context.required_identifiers else 1
        completeness = len(present) / total_required
        quality_factors.append(completeness * 0.4)
        
        # Overall confidence
        quality_factors.append(identifier_set.overall_confidence * 0.4)
        
        # Data validity
        validity_score = 1.0
        if identifier_set.email and not identifier_set.email.email:
            validity_score -= 0.3
        if identifier_set.phone and not identifier_set.phone.is_valid:
            validity_score -= 0.3
        quality_factors.append(max(0.0, validity_score) * 0.2)
        
        quality_score = sum(quality_factors)
        
        return {
            'present': present,
            'missing': missing,
            'warnings': warnings,
            'fallbacks': fallbacks,
            'quality_score': quality_score
        }
    
    def _find_unmapped_fields(
        self, 
        validated_response: FormResponseDataValidation,
        context: ExtractionContext
    ) -> List[str]:
        """Find fields that weren't mapped to any identifier type."""
        mapped_field_ids = set(context.field_mappings.keys())
        all_field_ids = {field.field_id for field in validated_response.validated_fields}
        return list(all_field_ids - mapped_field_ids)


# Convenience functions
async def extract_client_identifiers(
    validated_response: FormResponseDataValidation,
    field_mappings: Optional[Dict[str, ClientIdentifierType]] = None,
    required_identifiers: Optional[List[ClientIdentifierType]] = None
) -> IdentifierExtractionResult:
    """
    Convenience function to extract client identifiers.
    
    Args:
        validated_response: Validated form response data
        field_mappings: Optional explicit field mappings
        required_identifiers: Required identifier types for validation
        
    Returns:
        IdentifierExtractionResult with extracted identifiers
    """
    extractor = ClientIdentifierExtractor()
    return await extractor.extract_identifiers(validated_response, field_mappings, required_identifiers) 