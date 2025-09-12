"""Sensitive data redaction utilities for logging.

This module provides utilities to redact sensitive information from log events
to prevent accidental exposure of personal data, tokens, and other sensitive
information in logs.

The redaction follows a conservative approach where sensitive fields are either
completely removed or replaced with masked values that indicate the presence
of data without exposing the actual values.
"""

import re
from typing import Any, ClassVar


class SensitiveDataRedactor:
    """Redacts sensitive information from data structures for safe logging.

    This class provides methods to recursively traverse data structures and
    redact sensitive information such as JWT tokens, email addresses, user IDs,
    IP addresses, and other personally identifiable information.

    Attributes:
        REDACTION_MASK: The string used to replace sensitive values.
        SENSITIVE_HEADERS: Set of HTTP headers that typically contain sensitive data.
        SENSITIVE_KEYS: Set of dictionary keys that typically contain sensitive data.
        EMAIL_PATTERN: Regex pattern to identify email addresses.
        IP_PATTERN: Regex pattern to identify IP addresses.
        JWT_PATTERN: Regex pattern to identify JWT tokens.
    """

    REDACTION_MASK = "[REDACTED]"

    # Headers that typically contain sensitive information
    SENSITIVE_HEADERS: ClassVar[set[str]] = {
        "authorization",
        "x-api-key",
        "x-auth-token",
        "cookie",
        "set-cookie",
        "x-forwarded-for",
        "x-real-ip",
        "x-client-ip",
        "x-forwarded-proto",
        "x-amzn-trace-id",
    }

    # Dictionary keys that typically contain sensitive information
    SENSITIVE_KEYS: ClassVar[set[str]] = {
        "authorization",
        "password",
        "token",
        "secret",
        "key",
        "email",
        "sub",
        "user_id",
        "userid",
        "account_id",
        "accountid",
        "cognito_username",
        "cognito:username",
        "jti",
        "origin_jti",
        "aud",
        "iss",
        "sourceIp",
        "source_ip",
        "userArn",
        "user_arn",
        "caller",
        "principalOrgId",
        "principal_org_id",
        "cognitoIdentityId",
        "cognito_identity_id",
        "cognitoIdentityPoolId",
        "cognito_identity_pool_id",
        "accessKey",
        "access_key",
        "userAgent",
        "user_agent",
        "domainName",
        "domain_name",
        "deploymentId",
        "deployment_id",
        "apiId",
        "api_id",
        "requestId",
        "request_id",
        "extendedRequestId",
        "extended_request_id",
    }

    # Regex patterns for identifying sensitive data
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    IP_PATTERN = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
    JWT_PATTERN = re.compile(r"eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*")

    def redact_data(self, data: Any) -> Any:
        """Recursively redact sensitive information from data structures.

        Args:
            data: The data structure to redact sensitive information from.

        Returns:
            A copy of the data structure with sensitive information redacted.
        """
        if isinstance(data, dict):
            return self._redact_dict(data)
        elif isinstance(data, list):
            return self._redact_list(data)
        elif isinstance(data, str):
            return self._redact_string(data)
        else:
            return data

    def _redact_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive information from a dictionary.

        Args:
            data: The dictionary to redact.

        Returns:
            A new dictionary with sensitive information redacted.
        """
        redacted = {}

        for key, value in data.items():
            # Check if the key itself is sensitive
            if self._is_sensitive_key(key):
                redacted[key] = self.REDACTION_MASK
            else:
                # Recursively redact the value
                redacted[key] = self.redact_data(value)

        return redacted

    def _redact_list(self, data: list[Any]) -> list[Any]:
        """Redact sensitive information from a list.

        Args:
            data: The list to redact.

        Returns:
            A new list with sensitive information redacted.
        """
        return [self.redact_data(item) for item in data]

    def _redact_string(self, data: str) -> str:
        """Redact sensitive information from a string.

        Args:
            data: The string to redact.

        Returns:
            A new string with sensitive information redacted.
        """
        # Redact JWT tokens
        data = self.JWT_PATTERN.sub(self.REDACTION_MASK, data)

        # Redact email addresses
        data = self.EMAIL_PATTERN.sub(self.REDACTION_MASK, data)

        # Redact IP addresses
        data = self.IP_PATTERN.sub(self.REDACTION_MASK, data)

        return data

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a dictionary key is considered sensitive.

        Args:
            key: The key to check.

        Returns:
            True if the key is considered sensitive, False otherwise.
        """
        key_lower = key.lower()

        # Check exact matches
        if key_lower in self.SENSITIVE_KEYS:
            return True

        # Check if key contains sensitive patterns
        for sensitive_key in self.SENSITIVE_KEYS:
            return sensitive_key in key_lower

        return False

    def redact_lambda_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive information from AWS Lambda event data.

        This method provides specialized redaction for AWS Lambda events,
        handling nested structures like headers, requestContext, and authorizer claims.

        Args:
            event: The AWS Lambda event dictionary.

        Returns:
            A new event dictionary with sensitive information redacted.
        """
        redacted_event = self.redact_data(event)

        # Additional specialized redaction for Lambda events
        if "headers" in redacted_event:
            redacted_event["headers"] = self._redact_headers(redacted_event["headers"])

        if "multiValueHeaders" in redacted_event:
            redacted_event["multiValueHeaders"] = self._redact_headers(
                redacted_event["multiValueHeaders"]
            )

        # Redact requestContext authorizer claims
        if "requestContext" in redacted_event:
            request_context = redacted_event["requestContext"]
            if (
                "authorizer" in request_context
                and "claims" in request_context["authorizer"]
            ):
                request_context["authorizer"]["claims"] = (
                    self._redact_authorizer_claims(
                        request_context["authorizer"]["claims"]
                    )
                )

        return redacted_event

    def _redact_headers(self, headers: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive information from HTTP headers.

        Args:
            headers: The headers dictionary to redact.

        Returns:
            A new headers dictionary with sensitive information redacted.
        """
        redacted_headers = {}

        for key, value in headers.items():
            key_lower = key.lower()

            # Check if this is a sensitive header
            if key_lower in self.SENSITIVE_HEADERS:
                redacted_headers[key] = self.REDACTION_MASK
            else:
                # For non-sensitive headers, still redact any sensitive content in the value
                if isinstance(value, str):
                    redacted_headers[key] = self._redact_string(value)
                else:
                    redacted_headers[key] = value

        return redacted_headers

    def _redact_authorizer_claims(self, claims: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive information from authorizer claims.

        Args:
            claims: The authorizer claims dictionary to redact.

        Returns:
            A new claims dictionary with sensitive information redacted.
        """
        redacted_claims = {}

        for key, value in claims.items():
            if self._is_sensitive_key(key):
                redacted_claims[key] = self.REDACTION_MASK
            else:
                redacted_claims[key] = (
                    self._redact_string(str(value)) if isinstance(value, str) else value
                )

        return redacted_claims


# Global instance for easy access
sensitive_data_redactor = SensitiveDataRedactor()
