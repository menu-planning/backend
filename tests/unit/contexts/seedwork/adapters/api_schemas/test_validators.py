"""Unit tests for API schema validators.

Tests input validation, sanitization, and security pattern detection.
Follows testing principles: no I/O, fakes only, behavior-focused assertions.
"""
import pytest

from src.contexts.seedwork.adapters.api_schemas.validators import (
    sanitize_text_input,
    validate_email_format,
    validate_phone_format,
    validate_uuid_format,
    validate_url_optinal,
)


class TestSanitizeTextInput:
    """Test text sanitization with security focus."""

    def test_sanitize_text_input_returns_none_for_none_input(self):
        """Validates None input returns None."""
        # Given: None input
        # When: sanitize text input
        result = sanitize_text_input(None)
        
        # Then: None is returned
        assert result is None

    def test_sanitize_text_input_returns_none_for_empty_string(self):
        """Validates empty string returns None."""
        # Given: empty string
        # When: sanitize text input
        result = sanitize_text_input("")
        
        # Then: None is returned
        assert result is None

    def test_sanitize_text_input_returns_none_for_whitespace_only(self):
        """Validates whitespace-only string returns None."""
        # Given: whitespace-only string
        # When: sanitize text input
        result = sanitize_text_input("   ")
        
        # Then: None is returned
        assert result is None

    def test_sanitize_text_input_returns_trimmed_text(self):
        """Validates text is trimmed of leading/trailing whitespace."""
        # Given: text with whitespace
        # When: sanitize text input
        result = sanitize_text_input("  Hello World  ")
        
        # Then: trimmed text is returned
        assert result == "Hello World"

    def test_sanitize_text_input_preserves_legitimate_content(self):
        """Validates legitimate content is preserved."""
        # Given: legitimate text content
        # When: sanitize text input
        result = sanitize_text_input("This is legitimate content with apostrophes and quotes.")
        
        # Then: content is preserved
        assert result == "This is legitimate content with apostrophes and quotes."

    def test_sanitize_text_input_removes_script_tags(self):
        """Validates script tags are removed."""
        # Given: text with script tags
        # When: sanitize text input
        result = sanitize_text_input("Hello <script>alert('xss')</script> World")
        
        # Then: script tags are removed
        assert result == "Hello  World"

    def test_sanitize_text_input_removes_script_tags_with_spaces(self):
        """Validates script tags with spaces before closing > are removed."""
        # Given: text with script tags containing spaces
        # When: sanitize text input
        result = sanitize_text_input("Hello <script>alert('xss')</script > World")
        
        # Then: script tags are removed (security fix)
        assert result == "Hello  World"

    def test_sanitize_text_input_removes_script_tags_multiline(self):
        """Validates multiline script tags are removed."""
        # Given: text with multiline script tags
        # When: sanitize text input
        result = sanitize_text_input("Hello <script>\nalert('xss')\n</script> World")
        
        # Then: script tags are removed
        assert result == "Hello  World"

    def test_sanitize_text_input_removes_iframe_tags(self):
        """Validates iframe tags are removed."""
        # Given: text with iframe tags
        # When: sanitize text input
        result = sanitize_text_input("Hello <iframe src='evil.com'></iframe> World")
        
        # Then: iframe tags are removed
        assert result == "Hello  World"

    def test_sanitize_text_input_removes_object_tags(self):
        """Validates object tags are removed."""
        # Given: text with object tags
        # When: sanitize text input
        result = sanitize_text_input("Hello <object data='evil.swf'></object> World")
        
        # Then: object tags are removed
        assert result == "Hello  World"

    def test_sanitize_text_input_removes_embed_tags(self):
        """Validates embed tags are removed."""
        # Given: text with embed tags
        # When: sanitize text input
        result = sanitize_text_input("Hello <embed src='evil.swf'></embed> World")
        
        # Then: embed tags are removed
        assert result == "Hello  World"

    def test_sanitize_text_input_removes_form_tags(self):
        """Validates form tags are removed."""
        # Given: text with form tags
        # When: sanitize text input
        result = sanitize_text_input("Hello <form action='evil.com'></form> World")
        
        # Then: form tags are removed
        assert result == "Hello  World"

    def test_sanitize_text_input_removes_input_tags(self):
        """Validates input tags are removed."""
        # Given: text with input tags
        # When: sanitize text input
        result = sanitize_text_input("Hello <input type='text'></input> World")
        
        # Then: input tags are removed
        assert result == "Hello  World"

    def test_sanitize_text_input_removes_textarea_tags(self):
        """Validates textarea tags are removed."""
        # Given: text with textarea tags
        # When: sanitize text input
        result = sanitize_text_input("Hello <textarea></textarea> World")
        
        # Then: textarea tags are removed
        assert result == "Hello  World"

    def test_sanitize_text_input_removes_select_tags(self):
        """Validates select tags are removed."""
        # Given: text with select tags
        # When: sanitize text input
        result = sanitize_text_input("Hello <select><option>1</option></select> World")
        
        # Then: select tags are removed
        assert result == "Hello  World"

    def test_sanitize_text_input_removes_event_handlers(self):
        """Validates event handlers are removed."""
        # Given: text with event handlers
        # When: sanitize text input
        result = sanitize_text_input("Hello <div onclick='alert(1)' onload='evil()'>World</div>")
        
        # Then: event handlers are removed
        assert result == "Hello <div>World</div>"

    def test_sanitize_text_input_removes_javascript_urls(self):
        """Validates javascript: URLs are removed."""
        # Given: text with javascript: URLs
        # When: sanitize text input
        result = sanitize_text_input("Hello <a href='javascript:alert(1)'>Link</a> World")
        
        # Then: javascript: URLs are removed
        assert result == "Hello <a href=''>Link</a> World"

    def test_sanitize_text_input_removes_data_urls(self):
        """Validates data: URLs are removed."""
        # Given: text with data: URLs
        # When: sanitize text input
        result = sanitize_text_input("Hello <a href='data:text/html,<script>alert(1)</script>'>Link</a> World")
        
        # Then: data: URLs are removed
        assert result == "Hello <a href=''>Link</a> World"

    def test_sanitize_text_input_removes_vbscript_urls(self):
        """Validates vbscript: URLs are removed."""
        # Given: text with vbscript: URLs
        # When: sanitize text input
        result = sanitize_text_input("Hello <a href='vbscript:msgbox(1)'>Link</a> World")
        
        # Then: vbscript: URLs are removed
        assert result == "Hello <a href=''>Link</a> World"

    def test_sanitize_text_input_removes_style_attributes(self):
        """Validates style attributes are removed."""
        # Given: text with style attributes
        # When: sanitize text input
        result = sanitize_text_input("Hello <div style='color: red; background: url(javascript:alert(1))'>World</div>")
        
        # Then: style attributes are removed
        assert result == "Hello <World</div>"

    def test_sanitize_text_input_removes_sql_injection_patterns(self):
        """Validates SQL injection patterns are removed."""
        # Given: text with SQL injection patterns
        # When: sanitize text input
        result = sanitize_text_input("Hello '; DROP TABLE users; -- World")
        
        # Then: SQL injection patterns are removed (dangerous parts removed)
        assert result == "Hello 'TABLE users; World"

    def test_sanitize_text_input_removes_sql_comments(self):
        """Validates SQL comment patterns are removed."""
        # Given: text with SQL comment patterns
        # When: sanitize text input
        result = sanitize_text_input("Hello /* comment */ World")
        
        # Then: SQL comment patterns are removed
        assert result == "Hello  World"

    def test_sanitize_text_input_removes_execution_attempts(self):
        """Validates execution attempt patterns are removed."""
        # Given: text with execution attempt patterns
        # When: sanitize text input
        result = sanitize_text_input("Hello exec('evil') World")
        
        # Then: execution attempt patterns are removed (dangerous parts removed)
        assert result == "Hello 'evil') World"

    def test_sanitize_text_input_handles_complex_xss_attempts(self):
        """Validates complex XSS attempts are properly sanitized."""
        # Given: complex XSS attempt
        # When: sanitize text input
        result = sanitize_text_input(
            "Hello <script>alert('xss')</script> <iframe src='evil.com'></iframe> "
            "<div onclick='alert(1)' style='color: red'>World</div>"
        )
        
        # Then: all dangerous elements are removed
        assert result == "Hello   <div>World</div>"

    def test_sanitize_text_input_preserves_legitimate_html(self):
        """Validates legitimate HTML is preserved (except dangerous elements)."""
        # Given: legitimate HTML content
        # When: sanitize text input
        result = sanitize_text_input("Hello <strong>Bold</strong> <em>Italic</em> World")
        
        # Then: legitimate HTML is preserved
        assert result == "Hello <strong>Bold</strong> <em>Italic</em> World"

    def test_sanitize_text_input_handles_nested_dangerous_tags(self):
        """Validates nested dangerous tags are properly handled."""
        # Given: text with nested dangerous tags
        # When: sanitize text input
        result = sanitize_text_input("Hello <div><script>alert('xss')</script></div> World")
        
        # Then: dangerous tags are removed
        assert result == "Hello <div></div> World"

    def test_sanitize_text_input_handles_case_insensitive_tags(self):
        """Validates case-insensitive dangerous tags are removed."""
        # Given: text with case-insensitive dangerous tags
        # When: sanitize text input
        result = sanitize_text_input("Hello <SCRIPT>alert('xss')</SCRIPT> World")
        
        # Then: dangerous tags are removed
        assert result == "Hello  World"

    def test_sanitize_text_input_handles_mixed_case_tags(self):
        """Validates mixed case dangerous tags are removed."""
        # Given: text with mixed case dangerous tags
        # When: sanitize text input
        result = sanitize_text_input("Hello <ScRiPt>alert('xss')</ScRiPt> World")
        
        # Then: dangerous tags are removed
        assert result == "Hello  World"


class TestEmailValidation:
    """Test email format validation."""

    def test_validate_email_format_returns_none_for_none_input(self):
        """Validates None input returns None."""
        # Given: None input
        # When: validate email format
        result = validate_email_format(None)
        
        # Then: None is returned
        assert result is None

    def test_validate_email_format_returns_none_for_empty_string(self):
        """Validates empty string returns None."""
        # Given: empty string
        # When: validate email format
        result = validate_email_format("")
        
        # Then: None is returned
        assert result is None

    def test_validate_email_format_returns_none_for_whitespace_only(self):
        """Validates whitespace-only string returns None."""
        # Given: whitespace-only string
        # When: validate email format
        result = validate_email_format("   ")
        
        # Then: None is returned
        assert result is None

    def test_validate_email_format_accepts_valid_email(self):
        """Validates valid email is accepted."""
        # Given: valid email
        # When: validate email format
        result = validate_email_format("test@example.com")
        
        # Then: email is normalized and returned
        assert result == "test@example.com"

    def test_validate_email_format_normalizes_case(self):
        """Validates email case is normalized to lowercase."""
        # Given: email with mixed case
        # When: validate email format
        result = validate_email_format("TEST@EXAMPLE.COM")
        
        # Then: email is normalized to lowercase
        assert result == "test@example.com"

    def test_validate_email_format_trims_whitespace(self):
        """Validates email whitespace is trimmed."""
        # Given: email with whitespace
        # When: validate email format
        result = validate_email_format("  test@example.com  ")
        
        # Then: email is trimmed and normalized
        assert result == "test@example.com"

    def test_validate_email_format_rejects_invalid_format(self):
        """Validates invalid email format is rejected."""
        # Given: invalid email format
        # When: validate email format
        # Then: ValueError is raised
        with pytest.raises(ValueError, match="Invalid email format"):
            validate_email_format("invalid-email")

    def test_validate_email_format_rejects_email_with_script_tags(self):
        """Validates email with script tags is rejected."""
        # Given: email with script tags
        # When: validate email format
        # Then: ValueError is raised
        with pytest.raises(ValueError, match="Invalid email format"):
            validate_email_format("test<script>alert('xss')</script>@example.com")

    def test_validate_email_format_rejects_too_long_email(self):
        """Validates email exceeding length limit is rejected."""
        # Given: email exceeding 254 character limit
        # When: validate email format
        # Then: ValueError is raised
        long_email = "a" * 250 + "@example.com"  # 264 characters total
        with pytest.raises(ValueError, match="Email address too long"):
            validate_email_format(long_email)

    def test_validate_email_format_rejects_too_long_local_part(self):
        """Validates email with local part exceeding 64 character limit is rejected."""
        # Given: email with local part exceeding 64 character limit
        # When: validate email format
        # Then: ValueError is raised
        long_local_part = "a" * 65 + "@example.com"
        with pytest.raises(ValueError, match="Email local part too long"):
            validate_email_format(long_local_part)


class TestPhoneValidation:
    """Test phone number format validation."""

    def test_validate_phone_format_returns_none_for_none_input(self):
        """Validates None input returns None."""
        # Given: None input
        # When: validate phone format
        result = validate_phone_format(None)
        
        # Then: None is returned
        assert result is None

    def test_validate_phone_format_returns_none_for_empty_string(self):
        """Validates empty string returns None."""
        # Given: empty string
        # When: validate phone format
        result = validate_phone_format("")
        
        # Then: None is returned
        assert result is None

    def test_validate_phone_format_returns_none_for_whitespace_only(self):
        """Validates whitespace-only string returns None."""
        # Given: whitespace-only string
        # When: validate phone format
        result = validate_phone_format("   ")
        
        # Then: None is returned
        assert result is None

    def test_validate_phone_format_accepts_valid_phone(self):
        """Validates valid phone number is accepted."""
        # Given: valid phone number
        # When: validate phone format
        result = validate_phone_format("+1234567890")
        
        # Then: phone number is returned
        assert result == "+1234567890"

    def test_validate_phone_format_accepts_formatted_phone(self):
        """Validates formatted phone number is accepted."""
        # Given: formatted phone number
        # When: validate phone format
        result = validate_phone_format("(123) 456-7890")
        
        # Then: phone number is returned
        assert result == "(123) 456-7890"

    def test_validate_phone_format_trims_whitespace(self):
        """Validates phone number whitespace is trimmed."""
        # Given: phone number with whitespace
        # When: validate phone format
        result = validate_phone_format("  +1234567890  ")
        
        # Then: phone number is trimmed
        assert result == "+1234567890"

    def test_validate_phone_format_rejects_too_short_phone(self):
        """Validates phone number that is too short is rejected."""
        # Given: phone number that is too short
        # When: validate phone format
        # Then: ValueError is raised
        with pytest.raises(ValueError, match="Phone number too short"):
            validate_phone_format("123456")

    def test_validate_phone_format_rejects_too_long_phone(self):
        """Validates phone number that is too long is rejected."""
        # Given: phone number that is too long
        # When: validate phone format
        # Then: ValueError is raised
        long_phone = "1" * 16  # 16 digits, exceeds 15 limit
        with pytest.raises(ValueError, match="Phone number too long"):
            validate_phone_format(long_phone)

    def test_validate_phone_format_rejects_invalid_format(self):
        """Validates invalid phone format is rejected."""
        # Given: invalid phone format
        # When: validate phone format
        # Then: ValueError is raised
        with pytest.raises(ValueError, match="Phone number too short"):
            validate_phone_format("abc-def-ghij")

    def test_validate_phone_format_rejects_phone_with_script_tags(self):
        """Validates phone with script tags is rejected."""
        # Given: phone with script tags
        # When: validate phone format
        # Then: ValueError is raised
        with pytest.raises(ValueError, match="Phone number too short"):
            validate_phone_format("123<script>alert('xss')</script>456")


class TestUuidValidation:
    """Test UUID format validation."""

    def test_validate_uuid_format_accepts_valid_uuid(self):
        """Validates valid UUID is accepted."""
        # Given: valid UUID
        # When: validate UUID format
        result = validate_uuid_format("550e8400-e29b-41d4-a716-446655440000")
        
        # Then: UUID is returned
        assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_validate_uuid_format_rejects_invalid_uuid(self):
        """Validates invalid UUID is rejected."""
        # Given: invalid UUID
        # When: validate UUID format
        # Then: ValueError is raised
        with pytest.raises(ValueError, match="Invalid UUID4 format"):
            validate_uuid_format("invalid-uuid")


class TestUrlValidation:
    """Test URL format validation."""

    def test_validate_url_optional_returns_none_for_none_input(self):
        """Validates None input returns None."""
        # Given: None input
        # When: validate URL optional
        result = validate_url_optinal(None)
        
        # Then: None is returned
        assert result is None

    def test_validate_url_optional_returns_none_for_empty_string(self):
        """Validates empty string returns None."""
        # Given: empty string
        # When: validate URL optional
        result = validate_url_optinal("")
        
        # Then: None is returned
        assert result is None

    def test_validate_url_optional_returns_none_for_whitespace_only(self):
        """Validates whitespace-only string returns None."""
        # Given: whitespace-only string
        # When: validate URL optional
        result = validate_url_optinal("   ")
        
        # Then: None is returned
        assert result is None

    def test_validate_url_optional_accepts_valid_url(self):
        """Validates valid URL is accepted."""
        # Given: valid URL
        # When: validate URL optional
        result = validate_url_optinal("https://example.com")
        
        # Then: URL is returned (HttpUrl normalizes URLs)
        assert str(result) == "https://example.com/"

    def test_validate_url_optional_rejects_invalid_url(self):
        """Validates invalid URL is rejected."""
        # Given: invalid URL
        # When: validate URL optional
        # Then: ValueError is raised
        with pytest.raises(ValueError, match="Invalid URL format"):
            validate_url_optinal("not-a-url")
