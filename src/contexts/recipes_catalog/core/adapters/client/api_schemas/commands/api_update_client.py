from typing import Any

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import (
    ApiClient,
)
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client_fields import (
    ClientAddressOptional,
    ClientContactInfoOptinal,
    ClientNotesOptional,
    ClientOnboardingDataOptional,
    ClientProfileRequired,
    ClientTagsOptionalFrozenset,
)
from src.contexts.recipes_catalog.core.domain.client.commands.update_client import (
    UpdateClient,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    FieldMappingError,
    ValidationConversionError,
)


class ApiAttributesToUpdateOnClient(BaseApiCommand[UpdateClient]):
    """
    A Pydantic model representing and validating the data required
    to update a client via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        profile (ClientProfileRequired, optional): Profile information of the client.
        contact_info (ClientContactInfoOptinal, optional): Contact information of the
        client.
        address (ClientAddressOptional, optional): Address of the client.
        tags (ClientTagsOptionalFrozenset, optional): Tags associated with the client.
        notes (ClientNotesOptional, optional): Additional notes about the client.
        onboarding_data (ClientOnboardingDataOptional, optional): Original form response
        data from client onboarding.

    Methods:
        to_domain() -> dict:
            Converts the instance to a dictionary of attributes to update.

    Raises:
        ValidationConversionError: If the instance cannot be converted to a domain model.
        FieldMappingError: If field mapping fails.
        ValidationError: If the instance is invalid.
    """

    profile: ClientProfileRequired | None = None
    contact_info: ClientContactInfoOptinal | None = None
    address: ClientAddressOptional | None = None
    tags: ClientTagsOptionalFrozenset | None = None
    notes: ClientNotesOptional | None = None
    onboarding_data: ClientOnboardingDataOptional | None = None

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            # Manual field conversion to avoid model_dump issues with complex types
            updates = {}

            # Get fields that are set (exclude_unset behavior)
            fields_set = self.__pydantic_fields_set__

            # Simple fields that can be included directly
            simple_fields = ["notes", "onboarding_data"]

            for field in simple_fields:
                if field in fields_set:
                    value = getattr(self, field)
                    updates[field] = value

            # Complex fields that need special handling
            if "profile" in fields_set and self.profile is not None:
                try:
                    updates["profile"] = self.profile.to_domain()
                except Exception as e:
                    raise FieldMappingError(
                        f"Failed to map profile field to domain: {e}",
                        schema_class=self.__class__,
                        mapping_direction="api_to_domain",
                        missing_fields=[],
                        extra_fields=[],
                        type_mismatches={"profile": (type(self.profile), "domain_profile")},
                    ) from e

            if "contact_info" in fields_set and self.contact_info is not None:
                try:
                    updates["contact_info"] = self.contact_info.to_domain()
                except Exception as e:
                    raise FieldMappingError(
                        f"Failed to map contact_info field to domain: {e}",
                        schema_class=self.__class__,
                        mapping_direction="api_to_domain",
                        missing_fields=[],
                        extra_fields=[],
                        type_mismatches={"contact_info": (type(self.contact_info), "domain_contact_info")},
                    ) from e

            if "address" in fields_set and self.address is not None:
                try:
                    updates["address"] = self.address.to_domain()
                except Exception as e:
                    raise FieldMappingError(
                        f"Failed to map address field to domain: {e}",
                        schema_class=self.__class__,
                        mapping_direction="api_to_domain",
                        missing_fields=[],
                        extra_fields=[],
                        type_mismatches={"address": (type(self.address), "domain_address")},
                    ) from e

            if "tags" in fields_set and self.tags is not None:
                try:
                    updates["tags"] = frozenset([tag.to_domain() for tag in self.tags])
                except Exception as e:
                    raise FieldMappingError(
                        f"Failed to map tags field to domain: {e}",
                        schema_class=self.__class__,
                        mapping_direction="api_to_domain",
                        missing_fields=[],
                        extra_fields=[],
                        type_mismatches={"tags": (type(self.tags), "frozenset[domain_tag]")},
                    ) from e

        except FieldMappingError:
            # Re-raise FieldMappingError as-is
            raise
        except Exception as e:
            error_msg = (
                f"Failed to convert ApiAttributesToUpdateOnClient to domain model: {e}"
            )
            raise ValidationConversionError(
                error_msg,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
        else:
            return updates


class ApiUpdateClient(BaseApiCommand[UpdateClient]):
    """
    A Pydantic model representing and validating the data required
    to update a client via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        client_id (str): ID of the client to update.
        updates (ApiAttributesToUpdateOnClient): Attributes to update.

    Methods:
        to_domain() -> UpdateClient:
            Converts the instance to a domain model object for updating a client.

    Raises:
        ValidationConversionError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    client_id: UUIDIdRequired
    updates: ApiAttributesToUpdateOnClient

    def to_domain(self) -> UpdateClient:
        """Converts the instance to a domain model object for updating a client."""
        try:
            return UpdateClient(
                client_id=self.client_id,
                updates=self.updates.to_domain(),
            )
        except Exception as e:
            error_msg = f"Failed to convert ApiUpdateClient to domain model: {e}"
            raise ValidationConversionError(
                error_msg,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e

    @classmethod
    def from_api_client(
        cls, api_client: ApiClient, old_api_client: ApiClient | None = None
    ) -> "ApiUpdateClient":
        """Creates an instance from an existing client.

        Args:
            api_client: The new/updated client data.
            old_api_client: Optional. The original client to compare against.
                           If provided, only changed fields will be included in updates.
                           If not provided, all fields will be included
                           (previous behavior).

        Returns:
            ApiUpdateClient instance with only the changed attributes
            (if old_api_client provided) or all attributes
            (if old_api_client not provided).
        """
        # Only extract fields that ApiAttributesToUpdateOnClient accepts
        allowed_fields = ApiAttributesToUpdateOnClient.model_fields.keys()
        attributes_to_update = {}

        for key in allowed_fields:
            new_value = getattr(api_client, key)

            # If no old client provided, include all fields (current behavior)
            if old_api_client is None:
                attributes_to_update[key] = new_value
            else:
                # Compare with old value and only include if changed
                old_value = getattr(old_api_client, key)
                if new_value != old_value:
                    attributes_to_update[key] = new_value

        return cls(
            client_id=api_client.id,
            updates=ApiAttributesToUpdateOnClient(**attributes_to_update),
        )
