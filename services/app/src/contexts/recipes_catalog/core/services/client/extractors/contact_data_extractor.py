"""ContactInfo data extraction service for form response data."""

from typing import Dict, Any, Optional
import re

from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo


class ContactDataExtractor:
    """Extract ContactInfo data from form responses to create ContactInfo value objects."""
    
    def __init__(self):
        """Initialize the ContactInfo data extractor."""
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.phone_pattern = re.compile(r'^[\+]?[1-9][\d]{0,15}$')
    
    def extract_contact_info_from_form_response(self, form_response: Dict[str, Any]) -> Optional[ContactInfo]:
        """
        Extract ContactInfo information from form response data.
        
        Args:
            form_response: The form response data from client_onboarding context
            
        Returns:
            ContactInfo value object or None if no contact information found
            
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
        
        # Extract contact fields
        email = self._extract_email(extracted_data)
        phone = self._extract_phone(extracted_data)
        
        # Return None if no contact information found
        if not email and not phone:
            return None
            
        return ContactInfo(
            main_email=email,
            main_phone=phone,
            all_emails=frozenset([email]) if email else frozenset(),
            all_phones=frozenset([phone]) if phone else frozenset()
        )
    
    def _extract_answers_by_type(self, answers: list) -> Dict[str, Any]:
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
                extracted[key] = answer.get("text") or answer.get("email") or answer.get("phone_number") or answer.get("choice", {}).get("label")
                
        return extracted
    
    def _extract_email(self, extracted_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract email from form response data.
        
        Args:
            extracted_data: Processed form answers
            
        Returns:
            Email string or None if not found/invalid
        """
        # Common field references/types for email
        email_fields = [
            "email", "email_address", "contact_email", "your_email",
            "client_email", "email_contact",
            "email"  # Typeform email field type
        ]
        
        for field in email_fields:
            if field in extracted_data and extracted_data[field]:
                email = str(extracted_data[field]).strip().lower()
                if email and self.email_pattern.match(email):
                    return email
                    
        return None
    
    def _extract_phone(self, extracted_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract phone number from form response data.
        
        Args:
            extracted_data: Processed form answers
            
        Returns:
            Phone number string or None if not found/invalid
        """
        # Common field references/types for phone
        phone_fields = [
            "phone", "phone_number", "contact_phone", "your_phone",
            "client_phone", "phone_contact", "mobile", "mobile_number",
            "phone_number"  # Typeform phone number field type
        ]
        
        for field in phone_fields:
            if field in extracted_data and extracted_data[field]:
                phone = str(extracted_data[field]).strip()
                # Clean phone number (remove spaces, dashes, parentheses)
                cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
                if cleaned_phone and self._is_valid_phone(cleaned_phone):
                    return cleaned_phone
                    
        return None
    
    def _extract_preferred_contact_method(self, extracted_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract preferred contact method from form response data.
        
        Args:
            extracted_data: Processed form answers
            
        Returns:
            Preferred contact method string or None if not found
        """
        # Common field references/types for contact preference
        preference_fields = [
            "preferred_contact", "contact_preference", "preferred_contact_method",
            "how_to_contact", "contact_method", "communication_preference",
            "choice", "multiple_choice"  # Fallback field types
        ]
        
        for field in preference_fields:
            if field in extracted_data and extracted_data[field]:
                preference = str(extracted_data[field]).strip().lower()
                
                # Normalize common contact method values
                if preference in ["email", "e-mail", "electronic mail"]:
                    return "email"
                elif preference in ["phone", "telephone", "call", "phone call"]:
                    return "phone"
                elif preference in ["text", "sms", "message", "text message"]:
                    return "text"
                elif preference:
                    return preference  # Return as-is if not recognized
                    
        return None
    
    def _is_valid_phone(self, phone: str) -> bool:
        """
        Validate phone number format.
        
        Args:
            phone: Phone number string to validate
            
        Returns:
            True if phone number appears valid, False otherwise
        """
        if not phone:
            return False
            
        # Remove country code prefix if present
        if phone.startswith('+'):
            phone = phone[1:]
        elif phone.startswith('00'):
            phone = phone[2:]
            
        # Check basic length and format (7-15 digits)
        return len(phone) >= 7 and len(phone) <= 15 and phone.isdigit()