"""
API Schema: Form Response

Pydantic models for form response data used in internal provider endpoints.
These schemas define the structure for cross-context communication.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ApiFormResponse(BaseModel):
    """
    API schema for form response data.
    
    Used for serializing FormResponse data for internal provider endpoints
    and cross-context communication.
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
    
    @classmethod
    def from_domain(cls, form_response) -> "ApiFormResponse":
        """
        Create ApiFormResponse from domain FormResponse object.
        
        Args:
            form_response: FormResponse domain object
            
        Returns:
            ApiFormResponse instance
        """
        return cls(
            id=form_response.id,
            form_id=form_response.form_id,
            response_id=form_response.response_id,
            submission_id=form_response.submission_id,
            response_data=form_response.response_data,
            client_identifiers=form_response.client_identifiers,
            submitted_at=form_response.submitted_at.isoformat() if form_response.submitted_at else None,
            processed_at=form_response.processed_at.isoformat() if form_response.processed_at else None,
            created_at=form_response.created_at.isoformat() if form_response.created_at else None,
            updated_at=form_response.updated_at.isoformat() if form_response.updated_at else None,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the form response
        """
        return self.model_dump()


class ApiFormResponseList(BaseModel):
    """
    API schema for multiple form responses.
    
    Used for listing multiple form responses with metadata.
    """
    
    responses: List[ApiFormResponse] = Field(..., description="List of form responses")
    count: int = Field(..., description="Total number of responses")
    context: str = Field(..., description="Requesting context name")
    
    # Optional pagination metadata
    offset: Optional[int] = Field(None, description="Pagination offset")
    limit: Optional[int] = Field(None, description="Pagination limit")
    total_available: Optional[int] = Field(None, description="Total responses available")
    
    class Config:
        """Pydantic configuration"""
        from_attributes = True
    
    @classmethod
    def from_domain_list(
        cls, 
        form_responses: List, 
        caller_context: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        total_available: Optional[int] = None
    ) -> "ApiFormResponseList":
        """
        Create ApiFormResponseList from list of domain FormResponse objects.
        
        Args:
            form_responses: List of FormResponse domain objects
            caller_context: The context making the request
            offset: Optional pagination offset
            limit: Optional pagination limit
            total_available: Optional total available count
            
        Returns:
            ApiFormResponseList instance
        """
        api_responses = [ApiFormResponse.from_domain(response) for response in form_responses]
        
        return cls(
            responses=api_responses,
            count=len(api_responses),
            context=caller_context,
            offset=offset,
            limit=limit,
            total_available=total_available,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the form response list
        """
        return self.model_dump()


class ApiClientIdentifiers(BaseModel):
    """
    API schema for client identifier data extracted from form responses.
    
    Used for standardizing client identification data across contexts.
    """
    
    email: Optional[str] = Field(None, description="Client email address")
    phone: Optional[str] = Field(None, description="Client phone number")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    first_name: Optional[str] = Field(None, description="Client first name")
    last_name: Optional[str] = Field(None, description="Client last name")
    company: Optional[str] = Field(None, description="Client company")
    
    # Additional identifier fields
    custom_identifiers: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional custom identifier fields"
    )
    
    class Config:
        """Pydantic configuration"""
        from_attributes = True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of client identifiers
        """
        return self.model_dump(exclude_none=True)