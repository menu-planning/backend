"""
Form Response Data Validation Schemas

Pydantic models for validating and sanitizing various TypeForm question types.
Handles response data processing, normalization, and validation for storage.
"""

from typing import Optional, List, Any, Union
from datetime import datetime, date
from enum import Enum
import re
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator


class ResponseFieldType(str, Enum):
    """Response field types for validation."""
    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    MULTIPLE_CHOICE = "multiple_choice" 
    PICTURE_CHOICE = "picture_choice"
    YES_NO = "yes_no"
    DROPDOWN = "dropdown"
    NUMBER = "number"
    RATING = "rating"
    EMAIL = "email"
    WEBSITE = "website"
    FILE_UPLOAD = "file_upload"
    DATE = "date"
    PHONE_NUMBER = "phone_number"
    PAYMENT = "payment"
    LEGAL = "legal"
    OPINION_SCALE = "opinion_scale"


class SanitizedTextResponse(BaseModel):
    """Sanitized text response with length validation."""
    
    raw_value: str = Field(..., description="Raw text value")
    sanitized_value: str = Field(..., description="Sanitized text value")
    character_count: int = Field(..., description="Character count")
    word_count: int = Field(..., description="Word count")
    is_truncated: bool = Field(False, description="Whether value was truncated")
    
    @field_validator('raw_value')
    @classmethod
    def validate_raw_value(cls, v: str) -> str:
        """Basic validation for raw text value."""
        if not isinstance(v, str):
            raise ValueError("Raw value must be a string")
        return v
    
    @field_validator('sanitized_value')
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        """Sanitize text value by removing harmful content."""
        if not v:
            return ""
        
        # Remove potential script tags and HTML
        sanitized = re.sub(r'<[^>]*>', '', v)
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        # Limit length to prevent abuse
        max_length = 5000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @model_validator(mode='after')
    @staticmethod
    def calculate_metrics(values: 'SanitizedTextResponse') -> 'SanitizedTextResponse':
        """Calculate text metrics after sanitization."""
        sanitized = values.sanitized_value
        values.character_count = len(sanitized)
        values.word_count = len(sanitized.split()) if sanitized else 0
        values.is_truncated = len(values.raw_value) > len(sanitized)
        return values


class ValidatedEmailResponse(BaseModel):
    """Validated email response with domain extraction."""
    
    email: str = Field(..., description="Email address")
    domain: str = Field(..., description="Email domain")
    is_business_email: bool = Field(..., description="Whether likely business email")
    is_valid_format: bool = Field(..., description="Whether format is valid")
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v.lower().strip()
    
    @model_validator(mode='after')
    @staticmethod
    def extract_domain_info(values: 'ValidatedEmailResponse') -> 'ValidatedEmailResponse':
        """Extract domain information from email."""
        email = values.email
        domain = email.split('@')[1] if '@' in email else ""
        values.domain = domain
        
        # Check if business email (not common consumer domains)
        consumer_domains = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'aol.com', 'icloud.com', 'protonmail.com'
        }
        values.is_business_email = domain not in consumer_domains
        values.is_valid_format = bool(domain and '.' in domain)
        
        return values


class ValidatedUrlResponse(BaseModel):
    """Validated URL response with domain extraction."""
    
    url: str = Field(..., description="URL value")
    domain: str = Field(..., description="Domain from URL")
    scheme: str = Field(..., description="URL scheme (http/https)")
    is_secure: bool = Field(..., description="Whether HTTPS")
    is_valid: bool = Field(..., description="Whether URL is valid")
    
    @field_validator('url')
    @classmethod
    def validate_url_format(cls, v: str) -> str:
        """Validate and normalize URL."""
        if not v.startswith(('http://', 'https://')):
            v = f'https://{v}'
        
        try:
            parsed = urlparse(v)
            if not parsed.netloc:
                raise ValueError("Invalid URL format")
        except Exception:
            raise ValueError("Invalid URL format")
        
        return v
    
    @model_validator(mode='after')
    @staticmethod
    def extract_url_info(values: 'ValidatedUrlResponse') -> 'ValidatedUrlResponse':
        """Extract URL information."""
        try:
            parsed = urlparse(values.url)
            values.domain = parsed.netloc
            values.scheme = parsed.scheme
            values.is_secure = parsed.scheme == 'https'
            values.is_valid = bool(parsed.netloc and parsed.scheme)
        except Exception:
            values.domain = ""
            values.scheme = ""
            values.is_secure = False
            values.is_valid = False
        
        return values


class ValidatedNumberResponse(BaseModel):
    """Validated number response with type detection."""
    
    raw_value: Union[int, float, str] = Field(..., description="Raw number value")
    numeric_value: Union[int, float] = Field(..., description="Parsed numeric value")
    is_integer: bool = Field(..., description="Whether value is integer")
    is_positive: bool = Field(..., description="Whether value is positive")
    
    @field_validator('raw_value', mode='before')
    @classmethod
    def parse_number(cls, v: Union[int, float, str]) -> Union[int, float]:
        """Parse number from various input types."""
        if isinstance(v, (int, float)):
            return v
        
        if isinstance(v, str):
            # Remove common formatting
            cleaned = v.replace(',', '').replace('$', '').strip()
            try:
                # Try integer first
                if '.' not in cleaned:
                    return int(cleaned)
                return float(cleaned)
            except ValueError:
                raise ValueError(f"Cannot parse number from: {v}")
        
        raise ValueError(f"Invalid number type: {type(v)}")
    
    @model_validator(mode='after')
    @staticmethod
    def analyze_number(values: 'ValidatedNumberResponse') -> 'ValidatedNumberResponse':
        """Analyze number properties."""
        num_val = values.numeric_value
        values.is_integer = isinstance(num_val, int) or (isinstance(num_val, float) and num_val.is_integer())
        values.is_positive = num_val > 0
        return values


class ValidatedPhoneResponse(BaseModel):
    """Validated phone number response with formatting."""
    
    raw_phone: str = Field(..., description="Raw phone number")
    formatted_phone: str = Field(..., description="Formatted phone number")
    country_code: Optional[str] = Field(None, description="Detected country code")
    is_valid: bool = Field(..., description="Whether phone number appears valid")
    
    @field_validator('raw_phone')
    @classmethod
    def validate_phone_input(cls, v: str) -> str:
        """Basic phone number validation."""
        if not v or len(v.strip()) < 7:
            raise ValueError("Phone number too short")
        return v.strip()
    
    @model_validator(mode='after')
    @staticmethod
    def format_phone(values: 'ValidatedPhoneResponse') -> 'ValidatedPhoneResponse':
        """Format phone number."""
        raw = values.raw_phone
        # Remove all non-digit characters
        digits_only = re.sub(r'[^\d]', '', raw)
        
        # Basic formatting logic
        if len(digits_only) == 10:
            # US format
            values.formatted_phone = f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
            values.country_code = "US"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            # US with country code
            values.formatted_phone = f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
            values.country_code = "US"
        else:
            # International or unknown format
            values.formatted_phone = f"+{digits_only}"
            values.country_code = None
        
        values.is_valid = len(digits_only) >= 7
        return values


class ValidatedDateResponse(BaseModel):
    """Validated date response with parsing."""
    
    raw_date: str = Field(..., description="Raw date value")
    parsed_date: date = Field(..., description="Parsed date object")
    iso_format: str = Field(..., description="ISO format date string")
    is_future: bool = Field(..., description="Whether date is in future")
    
    @field_validator('raw_date')
    @classmethod
    def parse_date_value(cls, v: str) -> str:
        """Parse date from string."""
        if not v:
            raise ValueError("Date value cannot be empty")
        return v.strip()
    
    @model_validator(mode='after')
    @staticmethod
    def process_date(values: 'ValidatedDateResponse') -> 'ValidatedDateResponse':
        """Process and validate date."""
        raw_date = values.raw_date
        
        try:
            # Try ISO format first
            if 'T' in raw_date:
                parsed_dt = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
                parsed_date = parsed_dt.date()
            else:
                parsed_date = date.fromisoformat(raw_date)
            
            values.parsed_date = parsed_date
            values.iso_format = parsed_date.isoformat()
            values.is_future = parsed_date > date.today()
            
        except ValueError:
            raise ValueError(f"Cannot parse date from: {raw_date}")
        
        return values


class ValidatedChoiceResponse(BaseModel):
    """Validated choice response for multiple choice questions."""
    
    choice_id: str = Field(..., description="Choice ID")
    choice_label: str = Field(..., description="Choice label")
    choice_ref: Optional[str] = Field(None, description="Choice reference")
    is_other: bool = Field(False, description="Whether this is 'other' choice")
    other_text: Optional[str] = Field(None, description="Text for 'other' choice")
    
    @field_validator('choice_id')
    @classmethod
    def validate_choice_id(cls, v: str) -> str:
        """Validate choice ID is not empty."""
        if not v or not v.strip():
            raise ValueError("Choice ID cannot be empty")
        return v.strip()
    
    @field_validator('choice_label')
    @classmethod
    def validate_choice_label(cls, v: str) -> str:
        """Validate choice label."""
        if not v or not v.strip():
            raise ValueError("Choice label cannot be empty")
        return v.strip()


class NormalizedFieldResponse(BaseModel):
    """Normalized field response ready for storage."""
    
    field_id: str = Field(..., description="Field ID")
    field_ref: Optional[str] = Field(None, description="Field reference")
    field_title: str = Field(..., description="Field title/question")
    field_type: ResponseFieldType = Field(..., description="Field type")
    
    # Processed response data
    text_response: Optional[SanitizedTextResponse] = Field(None, description="Text response data")
    email_response: Optional[ValidatedEmailResponse] = Field(None, description="Email response data")
    url_response: Optional[ValidatedUrlResponse] = Field(None, description="URL response data")
    number_response: Optional[ValidatedNumberResponse] = Field(None, description="Number response data")
    phone_response: Optional[ValidatedPhoneResponse] = Field(None, description="Phone response data")
    date_response: Optional[ValidatedDateResponse] = Field(None, description="Date response data")
    choice_response: Optional[ValidatedChoiceResponse] = Field(None, description="Single choice response")
    choices_response: Optional[List[ValidatedChoiceResponse]] = Field(None, description="Multiple choice responses")
    boolean_response: Optional[bool] = Field(None, description="Boolean response")
    
    # Storage representation
    storage_value: Any = Field(..., description="Value optimized for storage")
    display_value: str = Field(..., description="Human-readable display value")
    
    @field_validator('field_id')
    @classmethod
    def validate_field_id(cls, v: str) -> str:
        """Validate field ID."""
        if not v or not v.strip():
            raise ValueError("Field ID cannot be empty")
        return v.strip()
    
    @field_validator('field_title')
    @classmethod
    def validate_field_title(cls, v: str) -> str:
        """Validate field title."""
        if not v or not v.strip():
            raise ValueError("Field title cannot be empty")
        return v.strip()


class FormResponseDataValidation(BaseModel):
    """Complete form response data validation result."""
    
    form_id: str = Field(..., description="Form ID")
    response_token: str = Field(..., description="Response token")
    validated_fields: List[NormalizedFieldResponse] = Field(..., description="Validated field responses")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    validation_warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    total_fields: int = Field(..., description="Total number of fields")
    valid_fields: int = Field(..., description="Number of valid fields")
    completion_rate: float = Field(..., description="Completion rate (0.0-1.0)")
    
    @model_validator(mode='after')
    @staticmethod
    def calculate_completion(values: 'FormResponseDataValidation') -> 'FormResponseDataValidation':
        """Calculate completion metrics."""
        total = values.total_fields
        valid = values.valid_fields
        values.completion_rate = valid / total if total > 0 else 0.0
        return values 