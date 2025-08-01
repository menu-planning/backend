"""
Client Identifier Validation Schemas

Pydantic models for validating extracted client data (name, email, phone).
Handles client identification data extraction and validation from TypeForm responses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import re
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, field_validator


class ClientIdentifierType(str, Enum):
    """Types of client identifiers that can be extracted."""
    EMAIL = "email"
    PHONE = "phone"
    FULL_NAME = "full_name"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    COMPANY_NAME = "company_name"
    USER_ID = "user_id"


class IdentifierExtractionStatus(str, Enum):
    """Status of identifier extraction from form response."""
    EXTRACTED = "extracted"
    PARTIAL = "partial"
    MISSING = "missing"
    INVALID = "invalid"


class ValidatedEmail(BaseModel):
    """Validated email identifier with confidence scoring."""
    
    email: EmailStr = Field(..., description="Validated email address")
    source_field: str = Field(..., description="TypeForm field ID that provided this email")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for extraction")
    is_primary: bool = Field(True, description="Whether this is the primary email")
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Additional email validation beyond EmailStr."""
        if not v or not v.strip():
            raise ValueError("Email cannot be empty")
        return v.lower().strip()


class ValidatedPhoneNumber(BaseModel):
    """Validated phone number with normalized format."""
    
    raw_phone: str = Field(..., description="Raw phone number from form")
    normalized_phone: str = Field(..., description="Normalized phone number")
    country_code: Optional[str] = Field(None, description="Detected country code")
    source_field: str = Field(..., description="TypeForm field ID that provided this phone")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for extraction")
    is_valid: bool = Field(..., description="Whether phone number passed validation")
    
    @field_validator('raw_phone')
    @classmethod
    def validate_raw_phone(cls, v: str) -> str:
        """Basic validation for raw phone input."""
        if not v or not v.strip():
            raise ValueError("Phone number cannot be empty")
        return v.strip()
    
    @field_validator('normalized_phone')
    @classmethod
    def validate_normalized_phone(cls, v: str) -> str:
        """Validate normalized phone format."""
        # Basic phone number validation (digits, spaces, dashes, parentheses, plus)
        phone_pattern = re.compile(r'^[\+]?[\d\s\-\(\)]+$')
        if not phone_pattern.match(v):
            raise ValueError("Invalid phone number format")
        return v


class ValidatedName(BaseModel):
    """Validated name component with sanitization."""
    
    raw_name: str = Field(..., description="Raw name from form")
    sanitized_name: str = Field(..., description="Sanitized name value")
    source_field: str = Field(..., description="TypeForm field ID that provided this name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for extraction")
    is_complete: bool = Field(..., description="Whether name appears complete")
    
    @field_validator('raw_name', 'sanitized_name')
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Ensure name is not empty."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
    
    @field_validator('sanitized_name')
    @classmethod
    def validate_sanitized_name(cls, v: str) -> str:
        """Validate sanitized name contains only acceptable characters."""
        # Allow letters, spaces, apostrophes, hyphens, periods
        name_pattern = re.compile(r"^[a-zA-Z\s\'\-\.]+$")
        if not name_pattern.match(v):
            raise ValueError("Name contains invalid characters")
        return v


class ClientIdentifierSet(BaseModel):
    """Complete set of extracted client identifiers."""
    
    email: Optional[ValidatedEmail] = Field(None, description="Primary email identifier")
    alternate_emails: List[ValidatedEmail] = Field(default=[], description="Additional email addresses")
    phone: Optional[ValidatedPhoneNumber] = Field(None, description="Primary phone number")
    alternate_phones: List[ValidatedPhoneNumber] = Field(default=[], description="Additional phone numbers")
    
    full_name: Optional[ValidatedName] = Field(None, description="Complete full name")
    first_name: Optional[ValidatedName] = Field(None, description="First name only")
    last_name: Optional[ValidatedName] = Field(None, description="Last name only")
    company_name: Optional[ValidatedName] = Field(None, description="Company or organization name")
    
    # Additional identifiers
    user_id: Optional[str] = Field(None, description="External user ID if provided")
    custom_identifiers: Dict[str, Any] = Field(default={}, description="Additional custom identifiers")
    
    # Extraction metadata
    extraction_timestamp: datetime = Field(default_factory=datetime.now, description="When identifiers were extracted")
    extraction_source: str = Field(..., description="TypeForm response ID source")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in identifier set")
    
    @field_validator('overall_confidence')
    @classmethod
    def validate_overall_confidence(cls, v: float) -> float:
        """Ensure confidence is within valid range."""
        return max(0.0, min(1.0, v))


class IdentifierExtractionResult(BaseModel):
    """Result of client identifier extraction process."""
    
    identifiers: ClientIdentifierSet = Field(..., description="Extracted and validated identifiers")
    extraction_status: IdentifierExtractionStatus = Field(..., description="Overall extraction status")
    
    # Field mapping information
    field_mappings: Dict[str, str] = Field(default={}, description="TypeForm field ID to identifier type mappings")
    unmapped_fields: List[str] = Field(default=[], description="TypeForm fields that couldn't be mapped")
    
    # Quality metrics
    required_fields_present: List[ClientIdentifierType] = Field(default=[], description="Required fields that were found")
    missing_required_fields: List[ClientIdentifierType] = Field(default=[], description="Required fields that are missing")
    data_quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall data quality score")
    
    # Processing metadata
    processing_errors: List[str] = Field(default=[], description="Errors encountered during extraction")
    processing_warnings: List[str] = Field(default=[], description="Warnings from extraction process")
    fallback_strategies_used: List[str] = Field(default=[], description="Fallback strategies that were applied")
    
    @field_validator('data_quality_score')
    @classmethod
    def validate_quality_score(cls, v: float) -> float:
        """Ensure quality score is within valid range."""
        return max(0.0, min(1.0, v))


class IdentifierValidationRequest(BaseModel):
    """Request for validating a set of client identifiers."""
    
    raw_identifiers: Dict[str, Any] = Field(..., description="Raw identifier data from form response")
    field_mappings: Dict[str, ClientIdentifierType] = Field(..., description="Field to identifier type mappings")
    required_fields: List[ClientIdentifierType] = Field(default=[], description="Required identifier types")
    validation_strictness: float = Field(0.8, ge=0.0, le=1.0, description="Validation strictness level")
    
    @field_validator('validation_strictness')
    @classmethod
    def validate_strictness(cls, v: float) -> float:
        """Ensure strictness is within valid range."""
        return max(0.0, min(1.0, v))


class IdentifierValidationResponse(BaseModel):
    """Response from identifier validation process."""
    
    validation_result: IdentifierExtractionResult = Field(..., description="Validation results")
    is_valid: bool = Field(..., description="Whether validation passed")
    validation_score: float = Field(..., ge=0.0, le=1.0, description="Overall validation score")
    recommendations: List[str] = Field(default=[], description="Recommendations for improving data quality")
    
    @field_validator('validation_score')
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Ensure validation score is within valid range."""
        return max(0.0, min(1.0, v)) 