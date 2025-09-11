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

from datetime import date, datetime, timedelta
from typing import Any

from src.contexts.recipes_catalog.core.domain.client.root_aggregate.client import Client
from src.contexts.shared_kernel.domain.value_objects.address import Address
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.shared_domain_factories import (
    create_client_tag,
)
from tests.utils.counter_manager import get_next_client_id

# =============================================================================
# CLIENT DATA FACTORIES (DOMAIN)
# =============================================================================


def create_client_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create client kwargs with deterministic values and validation.

    Following seedwork pattern with static counters for consistent test behavior.
    All required entity attributes are guaranteed to be present.

    Args:
        **kwargs: Override any default values

    Returns:
        Dict with all required client creation parameters
    """
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    client_counter = get_next_client_id()

    # Create default Profile with correct parameters
    default_profile = Profile(
        name=kwargs.get("name", f"Test Client {client_counter}"),
        sex=kwargs.get("sex", "M" if client_counter % 2 == 0 else "F"),
        birthday=kwargs.get("birthday", date(1980 + (client_counter % 40), 1, 1)),
    )

    # Create default ContactInfo with correct parameters
    default_contact_info = ContactInfo(
        main_phone=f"+1555{client_counter:04d}",
        main_email=f"client{client_counter}@example.com",
        all_phones=frozenset({f"+1555{client_counter:04d}"}),
        all_emails=frozenset({f"client{client_counter}@example.com"}),
    )

    # Create default Address with correct parameters
    default_address = Address(
        street=f"{client_counter} Test Street",
        city="Test City",
        zip_code=f"{10000 + client_counter}",
    )

    final_kwargs = {
        "id": kwargs.get("id", f"client_{client_counter:03d}"),
        "author_id": kwargs.get(
            "author_id", f"author_{(client_counter % 5) + 1}"
        ),  # Cycle through 5 authors
        "profile": kwargs.get("profile", default_profile),
        "contact_info": kwargs.get("contact_info", default_contact_info),
        "address": kwargs.get("address", default_address),
        "tags": kwargs.get("tags", set()),  # Will be populated separately if needed
        "menus": kwargs.get("menus", []),  # Will be populated separately if needed
        "notes": kwargs.get("notes", f"Test notes for client {client_counter}"),
        "created_at": kwargs.get(
            "created_at", base_time + timedelta(hours=client_counter)
        ),
        "updated_at": kwargs.get(
            "updated_at", base_time + timedelta(hours=client_counter, minutes=30)
        ),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
    }

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
            birthday=date(1970, 1, 1),
        ),
        "contact_info": ContactInfo(
            main_phone="+1555PIZZA1",
            main_email="info@giuseppes.com",
            all_phones=frozenset({"+1555PIZZA1"}),
            all_emails=frozenset({"info@giuseppes.com"}),
        ),
        "tags": kwargs.get(
            "tags",
            {
                create_client_tag(key="category", value="restaurant", type="client"),
                create_client_tag(key="industry", value="hospitality", type="client"),
                create_client_tag(key="size", value="medium", type="client"),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k not in ["profile", "contact_info", "tags"]
        },
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
            birthday=date(1975, 1, 1),
        ),
        "contact_info": ContactInfo(
            main_phone="+1555CATER1",
            main_email="events@elitecatering.com",
            all_phones=frozenset({"+1555CATER1"}),
            all_emails=frozenset({"events@elitecatering.com"}),
        ),
        "tags": kwargs.get(
            "tags",
            {
                create_client_tag(key="category", value="catering", type="client"),
                create_client_tag(key="industry", value="hospitality", type="client"),
                create_client_tag(key="size", value="large", type="client"),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k not in ["profile", "contact_info", "tags"]
        },
    }
    return create_client(**final_kwargs)


# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP
# =============================================================================


def create_clients_with_tags(count: int = 3, tags_per_client: int = 2) -> list[Client]:
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
        "priority": ["high", "medium", "low", "urgent"],
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

                author_idx = (
                    total_tag_index
                    // (len(tag_keys) * max(len(v) for v in values_by_key.values()))
                ) % max_authors
                author_id = f"author_{author_idx + 1}"

                tag_key = (key, value, author_id, "client")

                if tag_key not in unique_tags:
                    tag = create_client_tag(
                        key=key, value=value, author_id=author_id, type="client"
                    )
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
