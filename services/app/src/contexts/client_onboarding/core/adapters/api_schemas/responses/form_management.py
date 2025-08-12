"""
Form Management Command Schemas

Pydantic models for form setup, update, and management API requests.
Handles CRUD operations and webhook configuration for onboarding forms.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

class FormOperationType(str, Enum):
    """Types of form operations."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ACTIVATE = "activate"
    PAUSE = "pause"
    COMPLETE = "complete"
    CONFIGURE_WEBHOOK = "configure_webhook"

class FormManagementResponse(BaseModel):
    """Response for form management operations."""
    
    success: bool = Field(..., description="Whether the operation succeeded")
    operation: FormOperationType = Field(..., description="Operation that was performed")
    form_id: Optional[int] = Field(None, description="ID of the affected form")
    message: str = Field(..., description="Human-readable result message")
    
    # Operation results
    created_form_id: Optional[int] = Field(None, description="ID of newly created form")
    updated_fields: List[str] = Field(default=[], description="Fields that were updated")
    webhook_status: Optional[str] = Field(None, description="Webhook configuration status")
    
    # Metadata
    operation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the operation was performed"
    )
    execution_time_ms: Optional[int] = Field(
        None,
        description="Operation execution time in milliseconds"
    )
    
    # Error information
    error_code: Optional[str] = Field(None, description="Error code if operation failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")
    warnings: List[str] = Field(default=[], description="Non-fatal warnings from the operation")


