from __future__ import annotations

import re
from urllib.parse import urlparse


class TypeformUrlParser:
    """Extract form IDs from Typeform URLs."""

    @staticmethod
    def extract_form_id(input_value: str) -> str:
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
            if 'typeform.com' in parsed.netloc and '/to/' in parsed.path:
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
        input_value = input_value.strip().lower()
        return (
            input_value.startswith(('http://', 'https://')) and 'typeform.com' in input_value and '/to/' in input_value
        )

    @staticmethod
    def validate_form_id_format(form_id: str) -> str:
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


