"""Field mapping configuration for TypeForm client identifier extraction.

This module provides configuration for mapping TypeForm fields to client identifiers
with fallback strategies and confidence scoring.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field, field_validator


class FieldType(str, Enum):
    """TypeForm field types that can contain client identifiers."""
    
    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    DROPDOWN = "dropdown"
    MULTIPLE_CHOICE = "multiple_choice"
    OPINION_SCALE = "opinion_scale"
    RATING = "rating"
    YES_NO = "yes_no"
    LEGAL = "legal"
    DATE = "date"
    NUMBER = "number"
    WEBSITE = "website"


class ClientIdentifierType(str, Enum):
    """Types of client identifiers we can extract."""
    
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    COMPANY = "company"
    TITLE = "title"


class FieldMappingRule(BaseModel):
    """Configuration rule for mapping a TypeForm field to a client identifier."""
    
    identifier_type: ClientIdentifierType
    field_types: List[FieldType] = Field(
        description="TypeForm field types that can contain this identifier"
    )
    keywords: List[str] = Field(
        description="Keywords to look for in field titles/references"
    )
    required: bool = Field(
        default=False,
        description="Whether this identifier is required for successful extraction"
    )
    confidence_weight: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Weight factor for confidence scoring (0.0-2.0)"
    )
    fallback_patterns: List[str] = Field(
        default_factory=list,
        description="Regex patterns to use as fallback extraction methods"
    )
    validation_patterns: List[str] = Field(
        default_factory=list,
        description="Regex patterns to validate extracted values"
    )
    
    @field_validator("keywords")
    def keywords_must_be_lowercase(cls, v: List[str]) -> List[str]:
        """Ensure all keywords are lowercase for consistent matching."""
        return [keyword.lower() for keyword in v]


class FallbackStrategy(BaseModel):
    """Strategy for handling missing or invalid client identifiers."""
    
    identifier_type: ClientIdentifierType
    use_placeholder: bool = Field(
        default=False,
        description="Whether to use a placeholder value when identifier is missing"
    )
    placeholder_pattern: Optional[str] = Field(
        default=None,
        description="Pattern for generating placeholder values"
    )
    require_manual_review: bool = Field(
        default=True,
        description="Whether missing identifiers require manual review"
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score to accept extraction"
    )


class FieldMappingConfig(BaseModel):
    """Complete configuration for field mapping and client identifier extraction."""
    
    rules: List[FieldMappingRule] = Field(
        description="Mapping rules for each identifier type"
    )
    fallback_strategies: List[FallbackStrategy] = Field(
        description="Fallback strategies for missing identifiers"
    )
    global_confidence_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Global minimum confidence threshold"
    )
    max_field_search_depth: int = Field(
        default=10,
        ge=1,
        description="Maximum number of fields to search for identifiers"
    )
    enable_fuzzy_matching: bool = Field(
        default=True,
        description="Whether to enable fuzzy keyword matching"
    )
    fuzzy_match_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Threshold for fuzzy keyword matching"
    )
    
    @field_validator("rules")
    def rules_must_cover_required_identifiers(cls, v: List[FieldMappingRule]) -> List[FieldMappingRule]:
        """Ensure we have rules for essential identifier types."""
        identifier_types = {rule.identifier_type for rule in v}
        required_types = {ClientIdentifierType.NAME, ClientIdentifierType.EMAIL}
        
        missing_types = required_types - identifier_types
        if missing_types:
            raise ValueError(f"Missing rules for required identifier types: {missing_types}")
        
        return v
    
    def get_rules_for_identifier(self, identifier_type: ClientIdentifierType) -> List[FieldMappingRule]:
        """Get all mapping rules for a specific identifier type."""
        return [rule for rule in self.rules if rule.identifier_type == identifier_type]
    
    def get_fallback_strategy(self, identifier_type: ClientIdentifierType) -> Optional[FallbackStrategy]:
        """Get fallback strategy for a specific identifier type."""
        for strategy in self.fallback_strategies:
            if strategy.identifier_type == identifier_type:
                return strategy
        return None
    
    def get_supported_field_types(self) -> Set[FieldType]:
        """Get all field types that have mapping rules."""
        field_types = set()
        for rule in self.rules:
            field_types.update(rule.field_types)
        return field_types


# Default configuration for common TypeForm setups
DEFAULT_FIELD_MAPPING_CONFIG = FieldMappingConfig(
    rules=[
        FieldMappingRule(
            identifier_type=ClientIdentifierType.NAME,
            field_types=[
                FieldType.SHORT_TEXT,
                FieldType.LONG_TEXT
            ],
            keywords=[
                "name", "full name", "first name", "last name", 
                "your name", "client name", "contact name",
                "fname", "lname", "first", "last"
            ],
            required=True,
            confidence_weight=1.2,
            fallback_patterns=[
                r"^[A-Za-z\s\-\'\.]{2,50}$"
            ],
            validation_patterns=[
                r"^[A-Za-z\s\-\'\.]{1,100}$"
            ]
        ),
        FieldMappingRule(
            identifier_type=ClientIdentifierType.EMAIL,
            field_types=[
                FieldType.EMAIL,
                FieldType.SHORT_TEXT
            ],
            keywords=[
                "email", "e-mail", "email address", "contact email",
                "your email", "work email", "business email"
            ],
            required=True,
            confidence_weight=1.5,
            fallback_patterns=[
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
            ],
            validation_patterns=[
                r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            ]
        ),
        FieldMappingRule(
            identifier_type=ClientIdentifierType.PHONE,
            field_types=[
                FieldType.PHONE_NUMBER,
                FieldType.SHORT_TEXT,
                FieldType.NUMBER
            ],
            keywords=[
                "phone", "phone number", "mobile", "cell", "telephone",
                "contact number", "your phone", "work phone"
            ],
            required=False,
            confidence_weight=1.0,
            fallback_patterns=[
                r"[\+]?[1-9]?[\d\s\-\(\)\.]{7,15}",
                r"\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"
            ],
            validation_patterns=[
                r"^[\+]?[1-9]?[\d\s\-\(\)\.]{7,20}$"
            ]
        ),
        FieldMappingRule(
            identifier_type=ClientIdentifierType.COMPANY,
            field_types=[
                FieldType.SHORT_TEXT,
                FieldType.LONG_TEXT
            ],
            keywords=[
                "company", "organization", "business", "employer",
                "company name", "business name", "org", "firm"
            ],
            required=False,
            confidence_weight=0.8,
            fallback_patterns=[
                r"^[A-Za-z0-9\s\&\-\.\,\']{2,100}$"
            ],
            validation_patterns=[
                r"^[A-Za-z0-9\s\&\-\.\,\']{1,150}$"
            ]
        ),
        FieldMappingRule(
            identifier_type=ClientIdentifierType.TITLE,
            field_types=[
                FieldType.SHORT_TEXT,
                FieldType.DROPDOWN,
                FieldType.MULTIPLE_CHOICE
            ],
            keywords=[
                "title", "job title", "position", "role",
                "your title", "work title", "job role"
            ],
            required=False,
            confidence_weight=0.6,
            fallback_patterns=[
                r"^[A-Za-z\s\-\/]{2,50}$"
            ],
            validation_patterns=[
                r"^[A-Za-z\s\-\/]{1,100}$"
            ]
        )
    ],
    fallback_strategies=[
        FallbackStrategy(
            identifier_type=ClientIdentifierType.NAME,
            use_placeholder=False,
            require_manual_review=True,
            confidence_threshold=0.8
        ),
        FallbackStrategy(
            identifier_type=ClientIdentifierType.EMAIL,
            use_placeholder=False,
            require_manual_review=True,
            confidence_threshold=0.9
        ),
        FallbackStrategy(
            identifier_type=ClientIdentifierType.PHONE,
            use_placeholder=True,
            placeholder_pattern="PHONE_MISSING_{form_id}_{response_id}",
            require_manual_review=False,
            confidence_threshold=0.7
        ),
        FallbackStrategy(
            identifier_type=ClientIdentifierType.COMPANY,
            use_placeholder=True,
            placeholder_pattern="COMPANY_NOT_PROVIDED",
            require_manual_review=False,
            confidence_threshold=0.6
        ),
        FallbackStrategy(
            identifier_type=ClientIdentifierType.TITLE,
            use_placeholder=True,
            placeholder_pattern="TITLE_NOT_PROVIDED",
            require_manual_review=False,
            confidence_threshold=0.5
        )
    ],
    global_confidence_threshold=0.6,
    max_field_search_depth=15,
    enable_fuzzy_matching=True,
    fuzzy_match_threshold=0.8
)


class FieldMappingConfigManager:
    """Manager for field mapping configurations with form-specific overrides."""
    
    def __init__(
        self,
        default_config: Optional[FieldMappingConfig] = None
    ) -> None:
        """Initialize with default configuration."""
        self.default_config = default_config or DEFAULT_FIELD_MAPPING_CONFIG
        self._form_specific_configs: Dict[str, FieldMappingConfig] = {}
    
    def get_config(self, form_id: Optional[str] = None) -> FieldMappingConfig:
        """Get configuration for a specific form or default."""
        if form_id and form_id in self._form_specific_configs:
            return self._form_specific_configs[form_id]
        return self.default_config
    
    def set_form_config(self, form_id: str, config: FieldMappingConfig) -> None:
        """Set form-specific configuration."""
        self._form_specific_configs[form_id] = config
    
    def remove_form_config(self, form_id: str) -> None:
        """Remove form-specific configuration."""
        self._form_specific_configs.pop(form_id, None)
    
    def get_form_configs(self) -> Dict[str, FieldMappingConfig]:
        """Get all form-specific configurations."""
        return self._form_specific_configs.copy()
    
    async def validate_config(self, config: FieldMappingConfig) -> List[str]:
        """Validate a field mapping configuration and return any issues."""
        issues = []
        
        # Check for duplicate rules
        identifier_counts = {}
        for rule in config.rules:
            count = identifier_counts.get(rule.identifier_type, 0)
            identifier_counts[rule.identifier_type] = count + 1
        
        for identifier_type, count in identifier_counts.items():
            if count > 1:
                issues.append(f"Multiple rules found for identifier type: {identifier_type}")
        
        # Check fallback strategy coverage
        rule_identifiers = {rule.identifier_type for rule in config.rules}
        strategy_identifiers = {strategy.identifier_type for strategy in config.fallback_strategies}
        
        missing_strategies = rule_identifiers - strategy_identifiers
        if missing_strategies:
            issues.append(f"Missing fallback strategies for: {missing_strategies}")
        
        # Validate confidence thresholds
        if config.global_confidence_threshold > 1.0 or config.global_confidence_threshold < 0.0:
            issues.append("Global confidence threshold must be between 0.0 and 1.0")
        
        return issues 