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
from typing import Dict, Any, List

from src.contexts.recipes_catalog.core.domain.client.root_aggregate.client import Client
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.domain.value_objects.address import Address

# ORM model imports
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.client_sa_model import ClientSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import TagSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.profile_sa_model import ProfileSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.contact_info_sa_model import ContactInfoSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.address_sa_model import AddressSaModel

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC IDS
# =============================================================================

_CLIENT_COUNTER = 1
_TAG_COUNTER = 1


def reset_counters() -> None:
    """Reset all counters for test isolation"""
    global _CLIENT_COUNTER, _TAG_COUNTER
    _CLIENT_COUNTER = 1
    _TAG_COUNTER = 1


# =============================================================================
# CLIENT DATA FACTORIES (DOMAIN)
# =============================================================================

def create_client_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create client kwargs with deterministic values and validation.
    
    Following seedwork pattern with static counters for consistent test behavior.
    All required entity attributes are guaranteed to be present.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required client creation parameters
    """
    global _CLIENT_COUNTER
    
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    # Create default Profile with correct parameters
    default_profile = Profile(
        name=kwargs.get("name", f"Test Client {_CLIENT_COUNTER}"),
        sex=kwargs.get("sex", "M" if _CLIENT_COUNTER % 2 == 0 else "F"),
        birthday=kwargs.get("birthday", date(1980 + (_CLIENT_COUNTER % 40), 1, 1))
    )
    
    # Create default ContactInfo with correct parameters
    default_contact_info = ContactInfo(
        main_phone=f"+1555{_CLIENT_COUNTER:04d}",
        main_email=f"client{_CLIENT_COUNTER}@example.com",
        all_phones={f"+1555{_CLIENT_COUNTER:04d}"},
        all_emails={f"client{_CLIENT_COUNTER}@example.com"}
    )
    
    # Create default Address with correct parameters
    default_address = Address(
        street=f"{_CLIENT_COUNTER} Test Street",
        city="Test City",
        zip_code=f"{10000 + _CLIENT_COUNTER}"
    )
    
    final_kwargs = {
        "id": kwargs.get("id", f"client_{_CLIENT_COUNTER:03d}"),
        "author_id": kwargs.get("author_id", f"author_{(_CLIENT_COUNTER % 5) + 1}"),  # Cycle through 5 authors
        "profile": kwargs.get("profile", default_profile),
        "contact_info": kwargs.get("contact_info", default_contact_info),
        "address": kwargs.get("address", default_address),
        "tags": kwargs.get("tags", set()),  # Will be populated separately if needed
        "menus": kwargs.get("menus", []),  # Will be populated separately if needed
        "notes": kwargs.get("notes", f"Test notes for client {_CLIENT_COUNTER}"),
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=_CLIENT_COUNTER)),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(hours=_CLIENT_COUNTER, minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
    }
    
    # Increment counter for next call
    _CLIENT_COUNTER += 1
    
    return final_kwargs


def create_client(**kwargs) -> Client:
    """
    Create a Client domain entity with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Client domain entity
    """
    client_kwargs = create_client_kwargs(**kwargs)
    return Client(**client_kwargs)


# =============================================================================
# CLIENT DATA FACTORIES (ORM)
# =============================================================================

def create_client_orm_kwargs(**kwargs) -> Dict[str, Any]:
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
# TAG DATA FACTORIES (SHARED)
# =============================================================================

def create_tag_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create tag kwargs with deterministic values for client tags.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with tag creation parameters
    """
    global _TAG_COUNTER
    
    # Predefined tag types for realistic test data
    keys = ["category", "industry", "size", "region", "priority"]
    values_by_key = {
        "category": ["restaurant", "catering", "hotel", "healthcare", "school"],
        "industry": ["hospitality", "healthcare", "education", "retail", "corporate"],
        "size": ["small", "medium", "large", "enterprise"],
        "region": ["north", "south", "east", "west", "central"],
        "priority": ["high", "medium", "low", "urgent"]
    }
    
    key = keys[(_TAG_COUNTER - 1) % len(keys)]
    value = values_by_key[key][(_TAG_COUNTER - 1) % len(values_by_key[key])]
    
    final_kwargs = {
        "key": kwargs.get("key", key),
        "value": kwargs.get("value", value),
        "author_id": kwargs.get("author_id", f"author_{((_TAG_COUNTER - 1) % 5) + 1}"),
        "type": kwargs.get("type", "client"),
    }
    
    _TAG_COUNTER += 1
    return final_kwargs


def create_tag(**kwargs) -> Tag:
    """
    Create a Tag value object with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Tag value object
    """
    tag_kwargs = create_tag_kwargs(**kwargs)
    return Tag(**tag_kwargs)


def create_tag_orm(**kwargs) -> TagSaModel:
    """
    Create a TagSaModel ORM instance with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        TagSaModel ORM instance
    """
    tag_kwargs = create_tag_kwargs(**kwargs)
    return TagSaModel(**tag_kwargs)


# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS (DOMAIN)
# =============================================================================

def create_restaurant_client(**kwargs) -> Client:
    """
    Create a client representing a restaurant business.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Client with restaurant characteristics and tags
    """
    final_kwargs = {
        "profile": Profile(
            name=kwargs.get("name", "Giuseppe's Italian Restaurant"),
            sex="M",
            birthday=date(1970, 1, 1)
        ),
        "contact_info": ContactInfo(
            main_phone="+1555PIZZA1",
            main_email="info@giuseppes.com",
            all_phones={"+1555PIZZA1"},
            all_emails={"info@giuseppes.com"}
        ),
        "tags": kwargs.get("tags", {
            create_tag(key="category", value="restaurant", type="client"),
            create_tag(key="industry", value="hospitality", type="client"),
            create_tag(key="size", value="medium", type="client")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["profile", "contact_info", "tags"]}
    }
    return create_client(**final_kwargs)


def create_catering_client(**kwargs) -> Client:
    """
    Create a client representing a catering business.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Client with catering characteristics and tags
    """
    final_kwargs = {
        "profile": Profile(
            name=kwargs.get("name", "Elite Catering Services"),
            sex="F",
            birthday=date(1975, 1, 1)
        ),
        "contact_info": ContactInfo(
            main_phone="+1555CATER1",
            main_email="events@elitecatering.com",
            all_phones={"+1555CATER1"},
            all_emails={"events@elitecatering.com"}
        ),
        "tags": kwargs.get("tags", {
            create_tag(key="category", value="catering", type="client"),
            create_tag(key="industry", value="hospitality", type="client"),
            create_tag(key="size", value="large", type="client")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["profile", "contact_info", "tags"]}
    }
    return create_client(**final_kwargs)


# =============================================================================
# PARAMETRIZED TEST SCENARIOS
# =============================================================================

def get_client_filter_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for testing client filtering.
    
    Returns:
        List of test scenarios with client_kwargs, filter, and expected outcome
    """
    return [
        {
            "scenario_id": "author_id_match",
            "client_kwargs": {"author_id": "test_author_123"},
            "filter": {"author_id": "test_author_123"},
            "should_match": True,
            "description": "Client should match author_id filter"
        },
        {
            "scenario_id": "author_id_no_match",
            "client_kwargs": {"author_id": "test_author_123"},
            "filter": {"author_id": "different_author"},
            "should_match": False,
            "description": "Client should not match different author_id"
        },
        {
            "scenario_id": "created_at_gte_match",
            "client_kwargs": {"created_at": datetime(2024, 6, 1)},
            "filter": {"created_at_gte": datetime(2024, 5, 1)},
            "should_match": True,
            "description": "Client created after filter date should match"
        },
        {
            "scenario_id": "created_at_gte_no_match",
            "client_kwargs": {"created_at": datetime(2024, 4, 1)},
            "filter": {"created_at_gte": datetime(2024, 5, 1)},
            "should_match": False,
            "description": "Client created before filter date should not match"
        },
        {
            "scenario_id": "discarded_filter_false",
            "client_kwargs": {"discarded": False},
            "filter": {"discarded": False},
            "should_match": True,
            "description": "Non-discarded client should match discarded=False filter"
        },
        {
            "scenario_id": "discarded_filter_true",
            "client_kwargs": {"discarded": True},
            "filter": {"discarded": False},
            "should_match": False,
            "description": "Discarded client should not match discarded=False filter"
        }
    ]


def get_client_tag_filtering_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for testing complex client tag filtering logic.
    
    Returns:
        List of tag filtering test scenarios
    """
    return [
        {
            "scenario_id": "single_client_tag_match",
            "client_tags": [
                {"key": "category", "value": "restaurant", "author_id": "author_1", "type": "client"}
            ],
            "filter_tags": [("category", "restaurant", "author_1")],
            "should_match": True,
            "description": "Single client tag exact match should work"
        },
        {
            "scenario_id": "multiple_client_tags_and_logic",
            "client_tags": [
                {"key": "category", "value": "restaurant", "author_id": "author_1", "type": "client"},
                {"key": "size", "value": "large", "author_id": "author_1", "type": "client"}
            ],
            "filter_tags": [
                ("category", "restaurant", "author_1"),
                ("size", "large", "author_1")
            ],
            "should_match": True,
            "description": "Multiple different keys should use AND logic (all must match)"
        },
        {
            "scenario_id": "client_tags_or_logic",
            "client_tags": [
                {"key": "industry", "value": "hospitality", "author_id": "author_1", "type": "client"}
            ],
            "filter_tags": [
                ("industry", "hospitality", "author_1"),
                ("industry", "healthcare", "author_1")  # OR with hospitality
            ],
            "should_match": True,
            "description": "Multiple values for same key should use OR logic"
        }
    ]


# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP
# =============================================================================

def create_clients_with_tags(count: int = 3, tags_per_client: int = 2) -> List[Client]:
    """Create multiple clients with various tag combinations for testing"""
    clients = []
    
    # Create a pool of unique tags first
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
    
    # Pre-create unique tags if needed
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
                    tag = create_tag(key=key, value=value, author_id=author_id, type="client")
                    unique_tags[tag_key] = tag
    
    unique_tag_list = list(unique_tags.values())
    
    for i in range(count):
        tags = set()
        if tags_per_client > 0 and unique_tag_list:
            start_idx = (i * tags_per_client) % len(unique_tag_list)
            for j in range(min(tags_per_client, len(unique_tag_list))):
                tag_idx = (start_idx + j) % len(unique_tag_list)
                tags.add(unique_tag_list[tag_idx])
        
        client_kwargs = create_client_kwargs()
        client_kwargs["tags"] = tags
        client = create_client(**client_kwargs)
        clients.append(client)
    
    return clients


def create_clients_with_tags_orm(count: int = 3, tags_per_client: int = 2) -> List[ClientSaModel]:
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
                    tag = create_tag_orm(key=key, value=value, author_id=author_id, type="client")
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