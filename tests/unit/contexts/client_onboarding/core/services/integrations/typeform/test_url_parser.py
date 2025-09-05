"""Unit tests for TypeformUrlParser.

Tests URL parsing, form ID extraction, and validation with security focus.
Follows testing principles: no I/O, fakes only, behavior-focused assertions.
"""
import pytest

from src.contexts.client_onboarding.core.services.integrations.typeform.url_parser import (
    TypeformUrlParser,
)


class TestTypeformUrlParserExtractFormId:
    """Test form ID extraction from various URL formats."""

    def test_extract_form_id_from_valid_https_url(self):
        """Validates extraction from standard HTTPS Typeform URL."""
        # Given: valid HTTPS Typeform URL
        url = "https://typeform.com/to/abc123"
        
        # When: extract form ID
        result = TypeformUrlParser.extract_form_id(url)
        
        # Then: correct form ID is returned
        assert result == "abc123"

    def test_extract_form_id_from_valid_http_url(self):
        """Validates extraction from HTTP Typeform URL."""
        # Given: valid HTTP Typeform URL
        url = "http://typeform.com/to/def456"
        
        # When: extract form ID
        result = TypeformUrlParser.extract_form_id(url)
        
        # Then: correct form ID is returned
        assert result == "def456"

    def test_extract_form_id_from_subdomain_url(self):
        """Validates extraction from subdomain Typeform URL."""
        # Given: valid subdomain Typeform URL
        url = "https://www.typeform.com/to/ghi789"
        
        # When: extract form ID
        result = TypeformUrlParser.extract_form_id(url)
        
        # Then: correct form ID is returned
        assert result == "ghi789"

    def test_extract_form_id_from_url_with_query_params(self):
        """Validates extraction from URL with query parameters."""
        # Given: Typeform URL with query parameters
        url = "https://typeform.com/to/jkl012?utm_source=test&utm_medium=email"
        
        # When: extract form ID
        result = TypeformUrlParser.extract_form_id(url)
        
        # Then: correct form ID is returned (query params ignored)
        assert result == "jkl012"

    def test_extract_form_id_from_url_with_fragment(self):
        """Validates extraction from URL with fragment."""
        # Given: Typeform URL with fragment
        url = "https://typeform.com/to/mno345#section1"
        
        # When: extract form ID
        result = TypeformUrlParser.extract_form_id(url)
        
        # Then: correct form ID is returned (fragment ignored)
        assert result == "mno345"

    def test_extract_form_id_from_url_with_path_after_form_id(self):
        """Validates extraction from URL with additional path after form ID."""
        # Given: Typeform URL with additional path
        url = "https://typeform.com/to/pqr678/extra/path"
        
        # When: extract form ID
        result = TypeformUrlParser.extract_form_id(url)
        
        # Then: correct form ID is returned (additional path ignored)
        assert result == "pqr678"

    def test_extract_form_id_returns_input_when_not_url(self):
        """Validates that non-URL input is returned as-is."""
        # Given: form ID string (not a URL)
        form_id = "stu901"
        
        # When: extract form ID
        result = TypeformUrlParser.extract_form_id(form_id)
        
        # Then: same string is returned
        assert result == "stu901"

    def test_extract_form_id_handles_whitespace(self):
        """Validates handling of whitespace in input."""
        # Given: URL with leading/trailing whitespace
        url = "  https://typeform.com/to/vwx234  "
        
        # When: extract form ID
        result = TypeformUrlParser.extract_form_id(url)
        
        # Then: correct form ID is returned
        assert result == "vwx234"

    def test_extract_form_id_raises_error_for_empty_input(self):
        """Validates error is raised for empty input."""
        # Given: empty string
        url = ""
        
        # When: extract form ID
        # Then: ValueError is raised
        with pytest.raises(ValueError, match="input is empty"):
            TypeformUrlParser.extract_form_id(url)

    def test_extract_form_id_raises_error_for_whitespace_only_input(self):
        """Validates error is raised for whitespace-only input."""
        # Given: whitespace-only string
        url = "   "
        
        # When: extract form ID
        # Then: ValueError is raised
        with pytest.raises(ValueError, match="input is empty"):
            TypeformUrlParser.extract_form_id(url)

    def test_extract_form_id_raises_error_for_invalid_url(self):
        """Validates error is raised for invalid URL format."""
        # Given: invalid URL
        url = "https://invalid.com/not-typeform"
        
        # When: extract form ID
        # Then: ValueError is raised
        with pytest.raises(ValueError, match="unable to extract form ID"):
            TypeformUrlParser.extract_form_id(url)

    def test_extract_form_id_raises_error_for_malicious_url_with_typeform_in_path(self):
        """Validates security: malicious URL with 'typeform.com' in path is rejected."""
        # Given: malicious URL with typeform.com in path
        url = "https://malicious-site.com/typeform.com/fake"
        
        # When: extract form ID
        # Then: ValueError is raised (security fix)
        with pytest.raises(ValueError, match="unable to extract form ID"):
            TypeformUrlParser.extract_form_id(url)

    def test_extract_form_id_raises_error_for_malicious_url_with_typeform_in_subdomain(self):
        """Validates security: malicious URL with 'typeform.com' in subdomain is rejected."""
        # Given: malicious URL with typeform.com in subdomain
        url = "https://fake-typeform.com.evil.com/to/fake123"
        
        # When: extract form ID
        # Then: ValueError is raised (security fix)
        with pytest.raises(ValueError, match="unable to extract form ID"):
            TypeformUrlParser.extract_form_id(url)


class TestTypeformUrlParserIsTypeformUrl:
    """Test Typeform URL detection."""

    def test_is_typeform_url_returns_true_for_valid_https_url(self):
        """Validates detection of valid HTTPS Typeform URL."""
        # Given: valid HTTPS Typeform URL
        url = "https://typeform.com/to/abc123"
        
        # When: check if Typeform URL
        result = TypeformUrlParser.is_typeform_url(url)
        
        # Then: returns True
        assert result is True

    def test_is_typeform_url_returns_true_for_valid_http_url(self):
        """Validates detection of valid HTTP Typeform URL."""
        # Given: valid HTTP Typeform URL
        url = "http://typeform.com/to/def456"
        
        # When: check if Typeform URL
        result = TypeformUrlParser.is_typeform_url(url)
        
        # Then: returns True
        assert result is True

    def test_is_typeform_url_returns_true_for_subdomain_url(self):
        """Validates detection of subdomain Typeform URL."""
        # Given: valid subdomain Typeform URL
        url = "https://www.typeform.com/to/ghi789"
        
        # When: check if Typeform URL
        result = TypeformUrlParser.is_typeform_url(url)
        
        # Then: returns True
        assert result is True

    def test_is_typeform_url_handles_case_insensitive(self):
        """Validates case-insensitive URL detection."""
        # Given: uppercase Typeform URL
        url = "HTTPS://TYPEFORM.COM/TO/JKL012"
        
        # When: check if Typeform URL
        result = TypeformUrlParser.is_typeform_url(url)
        
        # Then: returns True
        assert result is True

    def test_is_typeform_url_handles_whitespace(self):
        """Validates handling of whitespace in URL detection."""
        # Given: URL with whitespace
        url = "  https://typeform.com/to/mno345  "
        
        # When: check if Typeform URL
        result = TypeformUrlParser.is_typeform_url(url)
        
        # Then: returns True
        assert result is True

    def test_is_typeform_url_returns_false_for_non_url(self):
        """Validates non-URL input returns False."""
        # Given: non-URL string
        text = "just some text"
        
        # When: check if Typeform URL
        result = TypeformUrlParser.is_typeform_url(text)
        
        # Then: returns False
        assert result is False

    def test_is_typeform_url_returns_false_for_non_http_url(self):
        """Validates non-HTTP URL returns False."""
        # Given: non-HTTP URL
        url = "ftp://typeform.com/to/pqr678"
        
        # When: check if Typeform URL
        result = TypeformUrlParser.is_typeform_url(url)
        
        # Then: returns False
        assert result is False

    def test_is_typeform_url_returns_false_for_malicious_url_with_typeform_in_path(self):
        """Validates security: malicious URL with 'typeform.com' in path returns False."""
        # Given: malicious URL with typeform.com in path
        url = "https://malicious-site.com/typeform.com/fake"
        
        # When: check if Typeform URL
        result = TypeformUrlParser.is_typeform_url(url)
        
        # Then: returns False (security fix)
        assert result is False

    def test_is_typeform_url_returns_false_for_malicious_url_with_typeform_in_subdomain(self):
        """Validates security: malicious URL with 'typeform.com' in subdomain returns False."""
        # Given: malicious URL with typeform.com in subdomain
        url = "https://fake-typeform.com.evil.com/to/fake123"
        
        # When: check if Typeform URL
        result = TypeformUrlParser.is_typeform_url(url)
        
        # Then: returns False (security fix)
        assert result is False

    def test_is_typeform_url_returns_false_for_invalid_url_format(self):
        """Validates invalid URL format returns False."""
        # Given: invalid URL format
        url = "not-a-url"
        
        # When: check if Typeform URL
        result = TypeformUrlParser.is_typeform_url(url)
        
        # Then: returns False
        assert result is False


class TestTypeformUrlParserValidateFormIdFormat:
    """Test form ID format validation."""

    def test_validate_form_id_format_returns_valid_form_id(self):
        """Validates valid form ID is returned unchanged."""
        # Given: valid form ID
        form_id = "abc123"
        
        # When: validate form ID format
        result = TypeformUrlParser.validate_form_id_format(form_id)
        
        # Then: same form ID is returned
        assert result == "abc123"

    def test_validate_form_id_format_handles_whitespace(self):
        """Validates whitespace is trimmed from form ID."""
        # Given: form ID with whitespace
        form_id = "  def456  "
        
        # When: validate form ID format
        result = TypeformUrlParser.validate_form_id_format(form_id)
        
        # Then: trimmed form ID is returned
        assert result == "def456"

    def test_validate_form_id_format_accepts_underscores_and_hyphens(self):
        """Validates form ID with underscores and hyphens is accepted."""
        # Given: form ID with underscores and hyphens
        form_id = "ghi_789-jkl"
        
        # When: validate form ID format
        result = TypeformUrlParser.validate_form_id_format(form_id)
        
        # Then: form ID is returned
        assert result == "ghi_789-jkl"

    def test_validate_form_id_format_accepts_mixed_case(self):
        """Validates form ID with mixed case is accepted."""
        # Given: form ID with mixed case
        form_id = "MnoPqr123"
        
        # When: validate form ID format
        result = TypeformUrlParser.validate_form_id_format(form_id)
        
        # Then: form ID is returned
        assert result == "MnoPqr123"

    def test_validate_form_id_format_raises_error_for_empty_input(self):
        """Validates error is raised for empty form ID."""
        # Given: empty form ID
        form_id = ""
        
        # When: validate form ID format
        # Then: ValueError is raised
        with pytest.raises(ValueError, match="form ID is empty"):
            TypeformUrlParser.validate_form_id_format(form_id)

    def test_validate_form_id_format_raises_error_for_whitespace_only_input(self):
        """Validates error is raised for whitespace-only form ID."""
        # Given: whitespace-only form ID
        form_id = "   "
        
        # When: validate form ID format
        # Then: ValueError is raised
        with pytest.raises(ValueError, match="form ID is empty"):
            TypeformUrlParser.validate_form_id_format(form_id)

    def test_validate_form_id_format_raises_error_for_invalid_characters(self):
        """Validates error is raised for invalid characters."""
        # Given: form ID with invalid characters
        form_id = "stu@901#"
        
        # When: validate form ID format
        # Then: ValueError is raised
        with pytest.raises(ValueError, match="contains invalid characters"):
            TypeformUrlParser.validate_form_id_format(form_id)

    def test_validate_form_id_format_raises_error_for_too_short(self):
        """Validates error is raised for too short form ID."""
        # Given: too short form ID
        form_id = "ab"
        
        # When: validate form ID format
        # Then: ValueError is raised
        with pytest.raises(ValueError, match="length must be between 3 and 50 characters"):
            TypeformUrlParser.validate_form_id_format(form_id)

    def test_validate_form_id_format_raises_error_for_too_long(self):
        """Validates error is raised for too long form ID."""
        # Given: too long form ID
        form_id = "a" * 51
        
        # When: validate form ID format
        # Then: ValueError is raised
        with pytest.raises(ValueError, match="length must be between 3 and 50 characters"):
            TypeformUrlParser.validate_form_id_format(form_id)

    def test_validate_form_id_format_accepts_minimum_length(self):
        """Validates minimum length form ID is accepted."""
        # Given: minimum length form ID
        form_id = "abc"
        
        # When: validate form ID format
        result = TypeformUrlParser.validate_form_id_format(form_id)
        
        # Then: form ID is returned
        assert result == "abc"

    def test_validate_form_id_format_accepts_maximum_length(self):
        """Validates maximum length form ID is accepted."""
        # Given: maximum length form ID
        form_id = "a" * 50
        
        # When: validate form ID format
        result = TypeformUrlParser.validate_form_id_format(form_id)
        
        # Then: form ID is returned
        assert result == "a" * 50


class TestTypeformUrlParserSecurity:
    """Test security aspects of URL parsing."""

    def test_security_malicious_url_with_typeform_in_query_params(self):
        """Validates security: URL with 'typeform.com' in query params is rejected."""
        # Given: malicious URL with typeform.com in query params
        url = "https://evil.com/to/fake?redirect=typeform.com"
        
        # When: check if Typeform URL
        result = TypeformUrlParser.is_typeform_url(url)
        
        # Then: returns False (security fix)
        assert result is False

    def test_security_malicious_url_with_typeform_in_fragment(self):
        """Validates security: URL with 'typeform.com' in fragment is rejected."""
        # Given: malicious URL with typeform.com in fragment
        url = "https://evil.com/to/fake#typeform.com"
        
        # When: check if Typeform URL
        result = TypeformUrlParser.is_typeform_url(url)
        
        # Then: returns False (security fix)
        assert result is False

    def test_security_malicious_url_with_typeform_in_username(self):
        """Validates security: URL with 'typeform.com' in username is rejected."""
        # Given: malicious URL with typeform.com in username
        url = "https://typeform.com@evil.com/to/fake"
        
        # When: check if Typeform URL
        result = TypeformUrlParser.is_typeform_url(url)
        
        # Then: returns False (security fix)
        assert result is False

    def test_security_malicious_url_with_typeform_in_password(self):
        """Validates security: URL with 'typeform.com' in password is rejected."""
        # Given: malicious URL with typeform.com in password
        url = "https://user:typeform.com@evil.com/to/fake"
        
        # When: check if Typeform URL
        result = TypeformUrlParser.is_typeform_url(url)
        
        # Then: returns False (security fix)
        assert result is False
