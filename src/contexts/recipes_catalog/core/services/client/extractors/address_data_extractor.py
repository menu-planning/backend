"""Address data extraction service for form response data."""

from typing import Any, Optional

from src.contexts.shared_kernel.domain.enums import State
from src.contexts.shared_kernel.domain.value_objects.address import Address


class AddressDataExtractor:
    """Extract Address data from form responses to create Address value objects."""

    def __init__(self):
        """Initialize the Address data extractor."""
        pass

    def extract_address_from_form_response(self, form_response: dict[str, Any]) -> Address | None:
        """
        Extract Address information from form response data.

        Args:
            form_response: The form response data from client_onboarding context

        Returns:
            Address value object or None if no address information found

        Raises:
            ValueError: If form response data is invalid
        """
        if not form_response:
            raise ValueError("Form response data cannot be empty")

        answers = form_response.get("answers", [])
        if not answers:
            raise ValueError("Form response must contain answers")

        # Extract answers by field reference or field type
        extracted_data = self._extract_answers_by_type(answers)

        # Extract address fields
        street = self._extract_street(extracted_data)
        city = self._extract_city(extracted_data)
        state = self._extract_state(extracted_data)
        zip_code = self._extract_zip_code(extracted_data)

        # Return None if no meaningful address information found
        if not street and not city:
            return None

        return Address(
            street=street,
            city=city,
            state=self._map_state_to_enum(state),
            zip_code=zip_code
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
                extracted[key] = answer.get("text") or answer.get("choice", {}).get("label")

        return extracted

    def _extract_street(self, extracted_data: dict[str, Any]) -> str | None:
        """
        Extract street address from form response data.

        Args:
            extracted_data: Processed form answers

        Returns:
            Street address string or None if not found
        """
        # Common field references/types for street address
        street_fields = [
            "street", "street_address", "address", "address_line_1",
            "street_1", "address1", "home_address", "mailing_address",
            "full_address", "client_address",
            "short_text", "long_text"  # Fallback field types
        ]

        for field in street_fields:
            if extracted_data.get(field):
                street = str(extracted_data[field]).strip()
                if street:
                    return street

        return None

    def _extract_city(self, extracted_data: dict[str, Any]) -> str | None:
        """
        Extract city from form response data.

        Args:
            extracted_data: Processed form answers

        Returns:
            City string or None if not found
        """
        # Common field references/types for city
        city_fields = [
            "city", "town", "municipality", "locality",
            "address_city", "client_city", "home_city",
            "short_text"  # Fallback field type
        ]

        for field in city_fields:
            if extracted_data.get(field):
                city = str(extracted_data[field]).strip()
                if city:
                    return city

        return None

    def _extract_state(self, extracted_data: dict[str, Any]) -> str | None:
        """
        Extract state/province from form response data.

        Args:
            extracted_data: Processed form answers

        Returns:
            State/province string or None if not found
        """
        # Common field references/types for state/province
        state_fields = [
            "state", "province", "region", "state_province",
            "address_state", "client_state", "home_state",
            "dropdown", "choice"  # Fallback field types
        ]

        for field in state_fields:
            if extracted_data.get(field):
                state = str(extracted_data[field]).strip()
                if state:
                    return state

        return None

    def _extract_country(self, extracted_data: dict[str, Any]) -> str | None:
        """
        Extract country from form response data.

        Args:
            extracted_data: Processed form answers

        Returns:
            Country string or None if not found
        """
        # Common field references/types for country
        country_fields = [
            "country", "nation", "address_country",
            "client_country", "home_country",
            "dropdown", "choice"  # Fallback field types
        ]

        for field in country_fields:
            if extracted_data.get(field):
                country = str(extracted_data[field]).strip()
                if country:
                    return self._normalize_country(country)

        return None

    def _extract_zip_code(self, extracted_data: dict[str, Any]) -> str | None:
        """
        Extract ZIP/postal code from form response data.

        Args:
            extracted_data: Processed form answers

        Returns:
            ZIP/postal code string or None if not found
        """
        # Common field references/types for ZIP/postal code
        zip_fields = [
            "zip", "zip_code", "postal_code", "postcode",
            "address_zip", "client_zip", "home_zip",
            "short_text", "number"  # Fallback field types
        ]

        for field in zip_fields:
            if extracted_data.get(field):
                zip_code = str(extracted_data[field]).strip()
                if zip_code:
                    return zip_code

        return None

    def _normalize_country(self, country: str) -> str:
        """
        Normalize country name to common format.

        Args:
            country: Country name to normalize

        Returns:
            Normalized country name
        """
        country_lower = country.lower().strip()

        # Common country name normalizations
        country_mappings = {
            "usa": "United States",
            "us": "United States",
            "united states of america": "United States",
            "uk": "United Kingdom",
            "britain": "United Kingdom",
            "great britain": "United Kingdom",
            "england": "United Kingdom",
            "scotland": "United Kingdom",
            "wales": "United Kingdom",
            "northern ireland": "United Kingdom",
        }

        return country_mappings.get(country_lower, country.title())

    def _map_state_to_enum(self, state_str: str | None) -> State | None:
        """
        Map state string to State enum.

        Args:
            state_str: State string from form response

        Returns:
            State enum value or None if not found
        """
        if not state_str:
            return None

        state_upper = state_str.upper().strip()

        # Try direct mapping to Brazilian state codes
        try:
            return State(state_upper)
        except ValueError:
            pass

        # Try mapping common state names to codes (Brazilian states)
        state_name_mapping = {
            "ACRE": State.AC,
            "ALAGOAS": State.AL,
            "AMAPÁ": State.AP,
            "AMAPA": State.AP,
            "AMAZONAS": State.AM,
            "BAHIA": State.BA,
            "CEARÁ": State.CE,
            "CEARA": State.CE,
            "DISTRITO FEDERAL": State.DF,
            "ESPÍRITO SANTO": State.ES,
            "ESPIRITO SANTO": State.ES,
            "GOIÁS": State.GO,
            "GOIAS": State.GO,
            "MARANHÃO": State.MA,
            "MARANHAO": State.MA,
            "MATO GROSSO": State.MT,
            "MATO GROSSO DO SUL": State.MS,
            "MINAS GERAIS": State.MG,
            "PARÁ": State.PA,
            "PARA": State.PA,
            "PARAÍBA": State.PB,
            "PARAIBA": State.PB,
            "PARANÁ": State.PR,
            "PARANA": State.PR,
            "PERNAMBUCO": State.PE,
            "PIAUÍ": State.PI,
            "PIAUI": State.PI,
            "RIO DE JANEIRO": State.RJ,
            "RIO GRANDE DO NORTE": State.RN,
            "RIO GRANDE DO SUL": State.RS,
            "RONDÔNIA": State.RO,
            "RONDONIA": State.RO,
            "RORAIMA": State.RR,
            "SANTA CATARINA": State.SC,
            "SÃO PAULO": State.SP,
            "SAO PAULO": State.SP,
            "SERGIPE": State.SE,
            "TOCANTINS": State.TO,
        }

        return state_name_mapping.get(state_upper)
