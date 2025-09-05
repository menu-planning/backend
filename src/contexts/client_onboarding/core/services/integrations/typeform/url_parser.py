from __future__ import annotations

import re
from urllib.parse import urlparse


class TypeformUrlParser:
    """Extract form IDs from TypeForm URLs.

    Provides utilities for parsing TypeForm URLs and extracting form identifiers
    with validation and error handling for various URL formats.
    """

    @staticmethod
    def extract_form_id(input_value: str) -> str:
        """Extract form ID from TypeForm URL or return the input if already a form ID.

        Args:
            input_value: TypeForm URL or form ID string.

        Returns:
            Extracted form ID string.

        Raises:
            ValueError: If input is empty or cannot extract form ID from URL.
        """
        input_value = input_value.strip()
        if not input_value:
            # Normalize error message for consistency with API schema tests
            raise ValueError("Invalid Typeform URL or form ID: input is empty")
        if not input_value.startswith(('http://', 'https://')):
            return input_value
        typeform_pattern = r'https?://[^/]*\.?typeform\.com/to/([a-zA-Z0-9_-]+)'
        match = re.search(typeform_pattern, input_value)
        if match:
            return match.group(1)
        try:
            parsed = urlparse(input_value)
            # Ensure typeform.com is actually the domain (not just present anywhere)
            if parsed.netloc.endswith('typeform.com') and '/to/' in parsed.path:
                path_parts = parsed.path.split('/to/')
                if len(path_parts) > 1:
                    form_id = path_parts[-1].split('/')[0].split('?')[0]
                    if form_id:
                        return form_id
        except Exception:
            pass
        raise ValueError(
            "Invalid Typeform URL or form ID: unable to extract form ID from the provided value"
        )

    @staticmethod
    def is_typeform_url(input_value: str) -> bool:
        """Check if the input value is a TypeForm URL.

        Args:
            input_value: String to check.

        Returns:
            True if the input appears to be a TypeForm URL.
        """
        input_value = input_value.strip().lower()
        if not input_value.startswith(('http://', 'https://')):
            return False
        
        try:
            parsed = urlparse(input_value)
            # Ensure typeform.com is actually the domain (not just present anywhere)
            return parsed.netloc.endswith('typeform.com') and '/to/' in parsed.path
        except Exception:
            return False

    @staticmethod
    def validate_form_id_format(form_id: str) -> str:
        """Validate TypeForm form ID format and constraints.

        Args:
            form_id: Form ID string to validate.

        Returns:
            Validated and trimmed form ID.

        Raises:
            ValueError: If form ID is empty, contains invalid characters, or has invalid length.
        """
        if not form_id or not form_id.strip():
            raise ValueError("Invalid Typeform URL or form ID: form ID is empty")
        form_id = form_id.strip()
        if not re.match(r'^[a-zA-Z0-9_-]+$', form_id):
            raise ValueError(
                "Invalid Typeform URL or form ID: contains invalid characters (allowed: [a-zA-Z0-9_-])"
            )
        if len(form_id) < 3 or len(form_id) > 50:
            raise ValueError(
                "Invalid Typeform URL or form ID: length must be between 3 and 50 characters"
            )
        return form_id


