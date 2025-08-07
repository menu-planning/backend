"""
Client Onboarding Provider Schemas

Pydantic models for client_onboarding data used in recipes_catalog context.
These schemas define the structure for cross-context communication.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ClientOnboardingFormResponse(BaseModel):
    """
    Schema for form response data from client_onboarding context.
    
    Used by recipes_catalog to consume form response data for client creation.
    """
    
    id: int = Field(..., description="Internal form response ID")
    form_id: int = Field(..., description="Associated onboarding form ID")
    response_id: str = Field(..., description="TypeForm response ID")
    submission_id: Optional[str] = Field(None, description="TypeForm submission ID")
    
    # Core data fields
    response_data: Dict[str, Any] = Field(..., description="Raw TypeForm response data")
    client_identifiers: Optional[Dict[str, Any]] = Field(
        None, 
        description="Extracted client identification data (email, phone, etc.)"
    )
    
    # Timestamps
    submitted_at: Optional[str] = Field(None, description="When form was submitted (ISO format)")
    processed_at: Optional[str] = Field(None, description="When response was processed (ISO format)")
    created_at: Optional[str] = Field(None, description="When record was created (ISO format)")
    updated_at: Optional[str] = Field(None, description="When record was last updated (ISO format)")
    
    class Config:
        """Pydantic configuration"""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def get_client_email(self) -> Optional[str]:
        """Extract client email from client identifiers."""
        return self.client_identifiers.get("email") if self.client_identifiers else None
    
    def get_client_phone(self) -> Optional[str]:
        """Extract client phone from client identifiers."""
        return self.client_identifiers.get("phone") if self.client_identifiers else None
    
    def get_client_name(self) -> tuple[Optional[str], Optional[str]]:
        """Extract client first and last name from client identifiers."""
        if not self.client_identifiers:
            return None, None
        return (
            self.client_identifiers.get("first_name"),
            self.client_identifiers.get("last_name")
        )
    
    def has_sufficient_client_data(self) -> bool:
        """Check if this response has sufficient data for client creation."""
        if not self.client_identifiers:
            return False
        
        # At minimum, we need email or phone for client creation
        has_email = bool(self.client_identifiers.get("email"))
        has_phone = bool(self.client_identifiers.get("phone"))
        
        return has_email or has_phone


class ClientOnboardingFormResponseList(BaseModel):
    """
    Schema for multiple form responses from client_onboarding context.
    """
    
    responses: List[ClientOnboardingFormResponse] = Field(..., description="List of form responses")
    count: int = Field(..., description="Total number of responses")
    context: str = Field(..., description="Requesting context name")
    
    # Optional pagination metadata
    offset: Optional[int] = Field(None, description="Pagination offset")
    limit: Optional[int] = Field(None, description="Pagination limit")
    total_available: Optional[int] = Field(None, description="Total responses available")
    
    class Config:
        """Pydantic configuration"""
        from_attributes = True
    
    def get_responses_with_sufficient_data(self) -> List[ClientOnboardingFormResponse]:
        """Filter responses that have sufficient data for client creation."""
        return [
            response for response in self.responses 
            if response.has_sufficient_client_data()
        ]


class ClientOnboardingClientData(BaseModel):
    """
    Schema for extracted client data ready for Client entity creation.
    
    This schema formats form response data specifically for recipes_catalog
    Client creation workflows.
    """
    
    # Core client identification
    email: Optional[str] = Field(None, description="Client email address")
    phone: Optional[str] = Field(None, description="Client phone number")
    first_name: Optional[str] = Field(None, description="Client first name")
    last_name: Optional[str] = Field(None, description="Client last name")
    company: Optional[str] = Field(None, description="Client company")
    
    # Original form response metadata
    form_response_data: Dict[str, Any] = Field(..., description="Original form response data and metadata")
    
    class Config:
        """Pydantic configuration"""
        from_attributes = True
    
    def has_email(self) -> bool:
        """Check if client data includes email."""
        return bool(self.email)
    
    def has_phone(self) -> bool:
        """Check if client data includes phone."""
        return bool(self.phone)
    
    def has_name(self) -> bool:
        """Check if client data includes first or last name."""
        return bool(self.first_name or self.last_name)
    
    def get_full_name(self) -> Optional[str]:
        """Get full name if available."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return None