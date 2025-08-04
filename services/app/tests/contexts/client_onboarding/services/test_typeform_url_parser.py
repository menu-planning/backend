"""
Tests for TypeformUrlParser

Test URL parsing and form ID extraction functionality.
"""

import pytest
from src.contexts.client_onboarding.core.services.typeform_url_parser import TypeformUrlParser


class TestTypeformUrlParser:
    """Test TypeformUrlParser functionality."""
    
    def test_extract_form_id_from_standard_url(self):
        """Test extracting form ID from standard Typeform URL."""
        url = "https://w3rzk8nsj6k.typeform.com/to/o8Qyi3Ix"
        result = TypeformUrlParser.extract_form_id(url)
        assert result == "o8Qyi3Ix"
    
    def test_extract_form_id_from_subdomain_url(self):
        """Test extracting form ID from Typeform URL with subdomain."""
        url = "https://example.typeform.com/to/abc123DEF"
        result = TypeformUrlParser.extract_form_id(url)
        assert result == "abc123DEF"
    
    def test_extract_form_id_from_url_with_query_params(self):
        """Test extracting form ID from URL with query parameters."""
        url = "https://example.typeform.com/to/formId123?embed=true&source=website"
        result = TypeformUrlParser.extract_form_id(url)
        assert result == "formId123"
    
    def test_extract_form_id_from_http_url(self):
        """Test extracting form ID from HTTP (non-HTTPS) URL."""
        url = "http://example.typeform.com/to/test_form_456"
        result = TypeformUrlParser.extract_form_id(url)
        assert result == "test_form_456"
    
    def test_extract_form_id_direct_id_input(self):
        """Test that direct form ID input is returned as-is."""
        form_id = "o8Qyi3Ix"
        result = TypeformUrlParser.extract_form_id(form_id)
        assert result == "o8Qyi3Ix"
    
    def test_extract_form_id_with_hyphens_and_underscores(self):
        """Test form ID with hyphens and underscores."""
        form_id = "test-form_123"
        result = TypeformUrlParser.extract_form_id(form_id)
        assert result == "test-form_123"
    
    def test_extract_form_id_invalid_url(self):
        """Test error handling for invalid URLs."""
        with pytest.raises(ValueError, match="Unable to extract form ID"):
            TypeformUrlParser.extract_form_id("https://example.com/not-typeform")
    
    def test_extract_form_id_empty_input(self):
        """Test error handling for empty input."""
        with pytest.raises(ValueError, match="cannot be empty"):
            TypeformUrlParser.extract_form_id("")
    
    def test_extract_form_id_whitespace_only(self):
        """Test error handling for whitespace-only input."""
        with pytest.raises(ValueError, match="cannot be empty"):
            TypeformUrlParser.extract_form_id("   ")
    
    def test_is_typeform_url_valid_url(self):
        """Test detecting valid Typeform URLs."""
        url = "https://example.typeform.com/to/formId"
        assert TypeformUrlParser.is_typeform_url(url) is True
    
    def test_is_typeform_url_http_url(self):
        """Test detecting HTTP Typeform URLs."""
        url = "http://example.typeform.com/to/formId"
        assert TypeformUrlParser.is_typeform_url(url) is True
    
    def test_is_typeform_url_not_typeform(self):
        """Test detecting non-Typeform URLs."""
        url = "https://example.com/form"
        assert TypeformUrlParser.is_typeform_url(url) is False
    
    def test_is_typeform_url_form_id(self):
        """Test that direct form IDs are not detected as URLs."""
        form_id = "o8Qyi3Ix"
        assert TypeformUrlParser.is_typeform_url(form_id) is False
    
    def test_validate_form_id_format_valid(self):
        """Test validation of valid form ID formats."""
        valid_ids = ["o8Qyi3Ix", "test-form_123", "ABC123", "form_id_test"]
        for form_id in valid_ids:
            result = TypeformUrlParser.validate_form_id_format(form_id)
            assert result == form_id
    
    def test_validate_form_id_format_invalid_characters(self):
        """Test validation fails for invalid characters."""
        with pytest.raises(ValueError, match="contains invalid characters"):
            TypeformUrlParser.validate_form_id_format("form@id!")
    
    def test_validate_form_id_format_too_short(self):
        """Test validation fails for too short form IDs."""
        with pytest.raises(ValueError, match="invalid length"):
            TypeformUrlParser.validate_form_id_format("ab")
    
    def test_validate_form_id_format_too_long(self):
        """Test validation fails for too long form IDs."""
        long_id = "a" * 51  # 51 characters
        with pytest.raises(ValueError, match="invalid length"):
            TypeformUrlParser.validate_form_id_format(long_id)
    
    def test_validate_form_id_format_empty(self):
        """Test validation fails for empty form ID."""
        with pytest.raises(ValueError, match="cannot be empty"):
            TypeformUrlParser.validate_form_id_format("")
    
    def test_validate_form_id_format_whitespace(self):
        """Test validation trims whitespace."""
        form_id = "  test_form_123  "
        result = TypeformUrlParser.validate_form_id_format(form_id)
        assert result == "test_form_123"


class TestIntegrationScenarios:
    """Test realistic usage scenarios."""
    
    def test_real_typeform_url_example(self):
        """Test with actual Typeform URL format."""
        url = "https://w3rzk8nsj6k.typeform.com/to/o8Qyi3Ix"
        form_id = TypeformUrlParser.extract_form_id(url)
        validated_id = TypeformUrlParser.validate_form_id_format(form_id)
        assert validated_id == "o8Qyi3Ix"
    
    def test_mixed_case_form_id(self):
        """Test form ID with mixed case letters."""
        form_id = "AbC123dEf"
        result = TypeformUrlParser.extract_form_id(form_id)
        validated = TypeformUrlParser.validate_form_id_format(result)
        assert validated == "AbC123dEf"
    
    def test_url_with_trailing_slash(self):
        """Test URL with trailing slash."""
        url = "https://example.typeform.com/to/formId123/"
        result = TypeformUrlParser.extract_form_id(url)
        assert result == "formId123"
    
    def test_url_with_path_after_form_id(self):
        """Test URL with additional path after form ID."""
        url = "https://example.typeform.com/to/formId123/preview"
        result = TypeformUrlParser.extract_form_id(url)
        assert result == "formId123"