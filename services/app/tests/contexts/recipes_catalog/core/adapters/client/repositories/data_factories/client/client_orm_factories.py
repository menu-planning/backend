"""
Data factories for ClientRepository testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- Validation logic for entity completeness
- Parametrized test scenarios for filtering
- Performance test scenarios with dataset expectations
- Specialized factory functions for different client types
- ORM equivalents for all domain factory methods

All data follows the exact structure of Client domain entities and their relationships.
Both domain and ORM variants are provided for comprehensive testing scenarios.
"""

from datetime import datetime, timedelta, date
from typing import Any

# ORM model imports
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.client_sa_model import ClientSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import TagSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.profile_sa_model import ProfileSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.contact_info_sa_model import ContactInfoSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.address_sa_model import AddressSaModel
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.shared_orm_factories import create_client_tag_orm

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC IDS
# =============================================================================

_CLIENT_COUNTER = 1


def reset_client_orm_counters() -> None:
    """Reset all counters for test isolation"""
    global _CLIENT_COUNTER
    _CLIENT_COUNTER = 1


# =============================================================================
# CLIENT DATA FACTORIES (ORM)
# =============================================================================

def create_client_orm_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create client ORM kwargs with deterministic values.
    
    Similar to create_client_kwargs but includes ORM-specific composite fields.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required ORM client creation parameters
    """
    global _CLIENT_COUNTER
    
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    # Create default ProfileSaModel with correct parameters
    default_profile = ProfileSaModel(
        name=kwargs.get("name", f"Test Client {_CLIENT_COUNTER}"),
        sex=kwargs.get("sex", "M" if _CLIENT_COUNTER % 2 == 0 else "F"),
        birthday=kwargs.get("birthday", date(1980 + (_CLIENT_COUNTER % 40), 1, 1))
    )
    
    # Create default ContactInfoSaModel with correct parameters
    default_contact_info = ContactInfoSaModel(
        main_phone=f"+1555{_CLIENT_COUNTER:04d}",
        main_email=f"client{_CLIENT_COUNTER}@example.com",
        all_phones=[f"+1555{_CLIENT_COUNTER:04d}"],
        all_emails=[f"client{_CLIENT_COUNTER}@example.com"]
    )
    
    # Create default AddressSaModel with correct parameters
    default_address = AddressSaModel(
        street=f"{_CLIENT_COUNTER} Test Street",
        city="Test City",
        zip_code=f"{10000 + _CLIENT_COUNTER}"
    )
    
    final_kwargs = {
        "id": kwargs.get("id", f"client_{_CLIENT_COUNTER:03d}"),
        "author_id": kwargs.get("author_id", f"author_{(_CLIENT_COUNTER % 5) + 1}"),
        "profile": kwargs.get("profile", default_profile),
        "contact_info": kwargs.get("contact_info", default_contact_info),
        "address": kwargs.get("address", default_address),
        "tags": kwargs.get("tags", []),  # List for ORM relationships
        "menus": kwargs.get("menus", []),  # List for ORM relationships
        "notes": kwargs.get("notes", f"Test notes for client {_CLIENT_COUNTER}"),
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=_CLIENT_COUNTER)),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(hours=_CLIENT_COUNTER, minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
    }
    
    # Increment counter for next call
    _CLIENT_COUNTER += 1
    
    return final_kwargs


def create_client_orm(**kwargs) -> ClientSaModel:
    """
    Create a ClientSaModel ORM instance with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ClientSaModel ORM instance
    """
    client_kwargs = create_client_orm_kwargs(**kwargs)
    return ClientSaModel(**client_kwargs)

# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP
# =============================================================================


def create_clients_with_tags_orm(count: int = 3, tags_per_client: int = 2) -> list[ClientSaModel]:
    """Create multiple ORM clients with various tag combinations for testing"""
    clients = []
    
    # Similar logic as domain version but for ORM
    unique_tags = {}
    
    tag_keys = ["category", "industry", "size", "region", "priority"]
    values_by_key = {
        "category": ["restaurant", "catering", "hotel", "healthcare", "school"],
        "industry": ["hospitality", "healthcare", "education", "retail", "corporate"],
        "size": ["small", "medium", "large", "enterprise"],
        "region": ["north", "south", "east", "west", "central"],
        "priority": ["high", "medium", "low", "urgent"]
    }
    max_authors = 5
    
    if tags_per_client > 0:
        for client_idx in range(count):
            for tag_idx in range(tags_per_client):
                total_tag_index = client_idx * tags_per_client + tag_idx
                
                key_idx = total_tag_index % len(tag_keys)
                key = tag_keys[key_idx]
                
                value_idx = (total_tag_index // len(tag_keys)) % len(values_by_key[key])
                value = values_by_key[key][value_idx]
                
                author_idx = (total_tag_index // (len(tag_keys) * max(len(v) for v in values_by_key.values()))) % max_authors
                author_id = f"author_{author_idx + 1}"
                
                tag_key = (key, value, author_id, "client")
                
                if tag_key not in unique_tags:
                    tag = create_client_tag_orm(key=key, value=value, author_id=author_id, type="client")
                    unique_tags[tag_key] = tag
    
    unique_tag_list = list(unique_tags.values())
    
    for i in range(count):
        tags = []
        if tags_per_client > 0 and unique_tag_list:
            start_idx = (i * tags_per_client) % len(unique_tag_list)
            for j in range(min(tags_per_client, len(unique_tag_list))):
                tag_idx = (start_idx + j) % len(unique_tag_list)
                tags.append(unique_tag_list[tag_idx])
        
        client_kwargs = create_client_orm_kwargs()
        client_kwargs["tags"] = tags
        client = create_client_orm(**client_kwargs)
        clients.append(client)
    
    return clients 