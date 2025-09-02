"""Profile data extraction service for form response data."""

from datetime import date, datetime
from typing import Any, Optional

from src.contexts.shared_kernel.domain.value_objects.profile import Profile


class ProfileDataExtractor:
    """Extract Profile data from form responses to create Profile value objects."""

    def __init__(self):
        """Initialize the Profile data extractor."""
        pass

    def extract_profile_from_form_response(self, form_response: dict[str, Any]) -> Profile | None:
        """
        Extract Profile information from form response data.

        Args:
            form_response: The form response data from client_onboarding context

        Returns:
            Profile value object or None if required fields are missing

        Raises:
            ValueError: If form response data is invalid or missing required fields
        """
        if not form_response:
            raise ValueError("Form response data cannot be empty")

        answers = form_response.get("answers", [])
        if not answers:
            raise ValueError("Form response must contain answers")

        # Extract answers by field reference or field type
        extracted_data = self._extract_answers_by_type(answers)

        # Extract required profile fields
        name = self._extract_name(extracted_data)
        if not name:
            raise ValueError("Name is required for Profile creation")

        age = self._extract_age(extracted_data)

        return Profile(
            name=name,
            sex="unknown",  # Default since not extractable from form
            birthday=self._extract_birthday(extracted_data, age)
        )

    def _extract_answers_by_type(self, answers: list) -> dict[str, Any]:
        """
        Extract answers organized by field type and reference.

        Args:
            answers: List of answer objects from form response

        Returns:
            Dictionary with field references/types as keys and values
        """
        extracted = {}

        for answer in answers:
            if not isinstance(answer, dict):
                continue

            field = answer.get("field", {})
            field_ref = field.get("ref", "")
            field_type = field.get("type", "")

            # Store answer value by field reference (preferred) or type
            key = field_ref if field_ref else field_type
            if key:
                extracted[key] = answer.get("text") or answer.get("number") or answer.get("choice", {}).get("label")

        return extracted

    def _extract_name(self, extracted_data: dict[str, Any]) -> str | None:
        """
        Extract name from form response data.

        Args:
            extracted_data: Processed form answers

        Returns:
            Name string or None if not found
        """
        # Common field references/types for name
        name_fields = [
            "name", "full_name", "client_name", "your_name",
            "short_text", "long_text"  # Fallback field types
        ]

        for field in name_fields:
            if extracted_data.get(field):
                name = str(extracted_data[field]).strip()
                if name:
                    return name

        return None

    def _extract_age(self, extracted_data: dict[str, Any]) -> int | None:
        """
        Extract age from form response data.

        Args:
            extracted_data: Processed form answers

        Returns:
            Age integer or None if not found/invalid
        """
        # Common field references/types for age
        age_fields = [
            "age", "client_age", "your_age", "age_years",
            "number"  # Fallback field type
        ]

        for field in age_fields:
            if field in extracted_data and extracted_data[field] is not None:
                try:
                    age = int(extracted_data[field])
                    if 0 <= age <= 150:  # Reasonable age range
                        return age
                except (ValueError, TypeError):
                    continue

        return None

    def _extract_birthday(self, extracted_data: dict[str, Any], age: int | None) -> 'date':
        """
        Extract or calculate birthday from form response data.

        Args:
            extracted_data: Processed form answers
            age: Extracted age if available

        Returns:
            Date object for birthday (estimated if only age available)
        """
        from datetime import date

        # Try to find explicit birthday/birthdate fields
        birthday_fields = [
            "birthday", "birth_date", "date_of_birth", "birthdate"
        ]

        for field in birthday_fields:
            if extracted_data.get(field):
                try:
                    # Try to parse date string
                    date_str = str(extracted_data[field])
                    # Handle common date formats
                    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt).date()
                            return parsed_date
                        except ValueError:
                            continue
                except (ValueError, TypeError):
                    continue

        # If no explicit birthday but we have age, estimate birthday
        if age is not None:
            today = date.today()
            estimated_birth_year = today.year - age
            return date(estimated_birth_year, 1, 1)  # January 1st as default

        # Default fallback - use a reasonable default date
        return date(1990, 1, 1)

    def _extract_dietary_preferences(self, extracted_data: dict[str, Any]) -> list[str] | None:
        """
        Extract dietary preferences from form response data.

        Args:
            extracted_data: Processed form answers

        Returns:
            List of dietary preferences or None if not found
        """
        # Common field references/types for dietary preferences
        dietary_fields = [
            "dietary_preferences", "diet_preferences", "dietary_restrictions",
            "food_preferences", "diet_type", "eating_style",
            "multiple_choice", "checkboxes"  # Fallback field types
        ]

        for field in dietary_fields:
            if extracted_data.get(field):
                preferences = extracted_data[field]

                # Handle different response formats
                if isinstance(preferences, str):
                    # Single preference or comma-separated
                    return [pref.strip() for pref in preferences.split(",") if pref.strip()]
                elif isinstance(preferences, list):
                    # Multiple preferences
                    return [str(pref).strip() for pref in preferences if pref]

        return None
