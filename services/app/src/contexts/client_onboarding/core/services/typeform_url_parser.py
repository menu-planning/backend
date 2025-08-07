"""
Typeform URL Parser

Utility for extracting form IDs from Typeform URLs for better UX.
Users typically have the full Typeform URL, not just the form ID.
"""

import re
from typing import Optional
from urllib.parse import urlparse


class TypeformUrlParser:
    """Extract form IDs from Typeform URLs."""
    
    @staticmethod
    def extract_form_id(input_value: str) -> str:
        """
        Extract form ID from URL or return as-is if already a form ID.
        
        Args:
            input_value: Either a Typeform URL or form ID
            
        Returns:
            Extracted or validated form ID
            
        Examples:
            extract_form_id("https://w3rzk8nsj6k.typeform.com/to/fOrmID") -> "fOrmID"
            extract_form_id("fOrmID") -> "fOrmID"
            
        Raises:
            ValueError: If URL is invalid or form ID cannot be extracted
        """
        input_value = input_value.strip()
        
        if not input_value:
            raise ValueError("Typeform URL or form ID cannot be empty")
        
        # If it's already a form ID (no URL scheme), return as-is
        if not input_value.startswith(('http://', 'https://')):
            return input_value
            
        # Parse Typeform URL pattern
        # Matches patterns like: https://subdomain.typeform.com/to/FORM_ID
        typeform_pattern = r'https?://[^/]*\.?typeform\.com/to/([a-zA-Z0-9_-]+)'
        match = re.search(typeform_pattern, input_value)
        
        if match:
            return match.group(1)
        
        # If URL doesn't match primary pattern, try path extraction as fallback
        try:
            parsed = urlparse(input_value)
            if 'typeform.com' in parsed.netloc and '/to/' in parsed.path:
                path_parts = parsed.path.split('/to/')
                if len(path_parts) > 1:
                    form_id = path_parts[-1].split('/')[0].split('?')[0]
                    if form_id:
                        return form_id
        except Exception:
            pass
            
        # If all parsing fails, raise error
        raise ValueError(
            f"Unable to extract form ID from '{input_value}'. "
            "Please provide a valid Typeform URL (e.g., https://example.typeform.com/to/FORM_ID) "
            "or form ID directly."
        )
    
    @staticmethod
    def is_typeform_url(input_value: str) -> bool:
        """
        Check if input appears to be a Typeform URL.
        
        Args:
            input_value: Input string to check
            
        Returns:
            True if appears to be a Typeform URL
        """
        input_value = input_value.strip().lower()
        return (
            input_value.startswith(('http://', 'https://')) and
            'typeform.com' in input_value and
            '/to/' in input_value
        )
    
    @staticmethod
    def validate_form_id_format(form_id: str) -> str:
        """
        Validate form ID format after extraction.
        
        Args:
            form_id: Extracted form ID
            
        Returns:
            Validated form ID
            
        Raises:
            ValueError: If form ID format is invalid
        """
        if not form_id or not form_id.strip():
            raise ValueError("Form ID cannot be empty")
        
        form_id = form_id.strip()
        
        # Typeform IDs are typically alphanumeric with hyphens/underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', form_id):
            raise ValueError(
                f"Form ID '{form_id}' contains invalid characters. "
                "Form IDs should only contain letters, numbers, hyphens, and underscores."
            )
        
        if len(form_id) < 3 or len(form_id) > 50:
            raise ValueError(
                f"Form ID '{form_id}' has invalid length. "
                "Form IDs should be between 3 and 50 characters."
            )
        
        return form_id