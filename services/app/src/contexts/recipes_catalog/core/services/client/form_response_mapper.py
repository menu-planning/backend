"""Form response mapper service that orchestrates all extractors."""

from typing import Dict, Any, Optional, Tuple

from src.contexts.recipes_catalog.core.services.client.extractors.profile_data_extractor import ProfileDataExtractor
from src.contexts.recipes_catalog.core.services.client.extractors.contact_data_extractor import ContactDataExtractor
from src.contexts.recipes_catalog.core.services.client.extractors.address_data_extractor import AddressDataExtractor


class FormResponseMapper:
    """Main service that orchestrates all extractors to map raw form response data to Client creation parameters."""
    
    def __init__(self):
        """Initialize the form response mapper with all extractors."""
        self.profile_extractor = ProfileDataExtractor()
        self.contact_extractor = ContactDataExtractor()
        self.address_extractor = AddressDataExtractor()
    
    def map_form_response_to_client_data(
        self, 
        form_response: Dict[str, Any], 
        author_id: str
    ) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """
        Map form response data to Client creation parameters.
        
        Args:
            form_response: The form response data from client_onboarding context
            author_id: The ID of the user creating the client
            
        Returns:
            Tuple of (client_creation_params, extraction_warnings)
            - client_creation_params: Dictionary suitable for CreateClient command
            - extraction_warnings: Dictionary of field -> warning message for partial extractions
            
        Raises:
            ValueError: If form response data is invalid or missing required fields
        """
        if not form_response:
            raise ValueError("Form response data cannot be empty")
            
        if not author_id:
            raise ValueError("Author ID is required")
            
        extraction_warnings = {}
        
        # Extract Profile (required)
        try:
            profile = self.profile_extractor.extract_profile_from_form_response(form_response)
            if not profile:
                raise ValueError("Profile data is required but could not be extracted from form response")
        except Exception as e:
            raise ValueError(f"Failed to extract profile data: {str(e)}")
        
        # Extract ContactInfo (optional)
        contact_info = None
        try:
            contact_info = self.contact_extractor.extract_contact_info_from_form_response(form_response)
        except Exception as e:
            extraction_warnings["contact_info"] = f"Could not extract contact information: {str(e)}"
        
        # Extract Address (optional)
        address = None
        try:
            address = self.address_extractor.extract_address_from_form_response(form_response)
        except Exception as e:
            extraction_warnings["address"] = f"Could not extract address information: {str(e)}"
        
        # Build client creation parameters
        client_params = {
            "author_id": author_id,
            "profile": profile,
            "contact_info": contact_info,
            "address": address,
            "onboarding_data": form_response,
            "notes": self._generate_extraction_notes(form_response, extraction_warnings),
            "tags": None  # Could be enhanced later to extract tags from form responses
        }
        
        return client_params, extraction_warnings
    
    def preview_client_data_from_form_response(
        self, 
        form_response: Dict[str, Any], 
        author_id: str
    ) -> Dict[str, Any]:
        """
        Preview what client data would look like before actual creation.
        
        Args:
            form_response: The form response data from client_onboarding context
            author_id: The ID of the user creating the client
            
        Returns:
            Dictionary with preview data including extracted fields and warnings
            
        Raises:
            ValueError: If form response data is invalid
        """
        try:
            client_params, warnings = self.map_form_response_to_client_data(form_response, author_id)
            
            return {
                "preview": {
                    "profile": {
                        "name": client_params["profile"].name if client_params["profile"] else None,
                        "age": client_params["profile"].age if client_params["profile"] else None,
                        "dietary_preferences": client_params["profile"].dietary_preferences if client_params["profile"] else None,
                    },
                    "contact_info": {
                        "email": client_params["contact_info"].email if client_params["contact_info"] else None,
                        "phone": client_params["contact_info"].phone if client_params["contact_info"] else None,
                        "preferred_contact_method": client_params["contact_info"].preferred_contact_method if client_params["contact_info"] else None,
                    } if client_params["contact_info"] else None,
                    "address": {
                        "street": client_params["address"].street if client_params["address"] else None,
                        "city": client_params["address"].city if client_params["address"] else None,
                        "state": client_params["address"].state if client_params["address"] else None,
                        "country": client_params["address"].country if client_params["address"] else None,
                        "zip_code": client_params["address"].zip_code if client_params["address"] else None,
                    } if client_params["address"] else None,
                    "notes": client_params["notes"],
                },
                "warnings": warnings,
                "form_response_id": form_response.get("response_id"),
                "form_id": form_response.get("form_id"),
                "extraction_success": len(warnings) == 0,
                "required_fields_present": bool(client_params["profile"]),
            }
        except Exception as e:
            return {
                "preview": None,
                "warnings": {"extraction_error": str(e)},
                "form_response_id": form_response.get("response_id"),
                "form_id": form_response.get("form_id"),
                "extraction_success": False,
                "required_fields_present": False,
            }
    
    def validate_form_response_completeness(self, form_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate completeness of form response for client creation.
        
        Args:
            form_response: The form response data to validate
            
        Returns:
            Dictionary with validation results and completeness score
        """
        if not form_response:
            return {
                "is_complete": False,
                "completeness_score": 0.0,
                "missing_fields": ["form_response"],
                "extractable_fields": [],
                "validation_errors": ["Form response data is empty"]
            }
            
        missing_fields = []
        extractable_fields = []
        validation_errors = []
        
        # Check Profile extraction (required)
        try:
            profile = self.profile_extractor.extract_profile_from_form_response(form_response)
            if profile:
                extractable_fields.append("profile")
            else:
                missing_fields.append("profile")
        except Exception as e:
            missing_fields.append("profile")
            validation_errors.append(f"Profile extraction failed: {str(e)}")
        
        # Check ContactInfo extraction (optional but valuable)
        try:
            contact_info = self.contact_extractor.extract_contact_info_from_form_response(form_response)
            if contact_info:
                extractable_fields.append("contact_info")
            else:
                missing_fields.append("contact_info")
        except Exception:
            missing_fields.append("contact_info")
        
        # Check Address extraction (optional but valuable)
        try:
            address = self.address_extractor.extract_address_from_form_response(form_response)
            if address:
                extractable_fields.append("address")
            else:
                missing_fields.append("address")
        except Exception:
            missing_fields.append("address")
        
        # Calculate completeness score
        total_possible_fields = 3  # profile, contact_info, address
        extractable_count = len(extractable_fields)
        
        # Base score on extractable fields vs total, with required field weight
        if "profile" in extractable_fields:
            completeness_score = (extractable_count / total_possible_fields) * 100
        else:
            completeness_score = 0.0
        
        is_complete = "profile" in extractable_fields and len(validation_errors) == 0
        
        return {
            "is_complete": is_complete,
            "completeness_score": completeness_score,
            "missing_fields": missing_fields,
            "extractable_fields": extractable_fields,
            "validation_errors": validation_errors,
            "has_required_fields": "profile" in extractable_fields,
            "optional_fields_available": extractable_count - (1 if "profile" in extractable_fields else 0)
        }
    
    def _generate_extraction_notes(self, form_response: Dict[str, Any], warnings: Dict[str, str]) -> Optional[str]:
        """
        Generate notes about the extraction process for audit purposes.
        
        Args:
            form_response: The original form response data
            warnings: Dictionary of extraction warnings
            
        Returns:
            Notes string or None if no notable information
        """
        notes_parts = []
        
        # Add form metadata
        form_id = form_response.get("form_id")
        response_id = form_response.get("response_id")
        if form_id:
            notes_parts.append(f"Created from form {form_id}")
        if response_id:
            notes_parts.append(f"Response ID: {response_id}")
        
        # Add warnings if any
        if warnings:
            notes_parts.append("Extraction warnings:")
            for field, warning in warnings.items():
                notes_parts.append(f"- {field}: {warning}")
        
        return "; ".join(notes_parts) if notes_parts else None