"""Mapper to convert between Client domain objects and SQLAlchemy models."""

from dataclasses import asdict as data_class_asdict
from datetime import UTC, datetime
from enum import Enum

from attrs import asdict
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.recipes_catalog.core.adapters.client.ORM.mappers.menu_mapper import (
    MenuMapper,
)
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.client_sa_model import (
    ClientSaModel,
)
from src.contexts.recipes_catalog.core.domain.client.root_aggregate.client import Client
from src.contexts.seedwork.adapters.ORM.mappers import helpers
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_address import (
    ApiAddress,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_contact_info import (
    ApiContactInfo,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_profile import (
    ApiProfile,
)
from src.contexts.shared_kernel.adapters.ORM.mappers.tag.tag_mapper import TagMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.address_sa_model import (
    AddressSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.contact_info_sa_model import (
    ContactInfoSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.profile_sa_model import (
    ProfileSaModel,
)
from src.contexts.shared_kernel.domain.enums import State
from src.contexts.shared_kernel.domain.value_objects.address import Address
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.logging.logger import structlog_logger


class ClientMapper(ModelMapper):
    """Mapper for converting between Client domain objects and SQLAlchemy models.

    Handles complex mapping including nested menus, tags, profile, contact info,
    and address. Performs concurrent mapping of child entities with timeout
    protection and tag deduplication across menus.

    Notes:
        Lossless: Yes. Timezone: local assumption. Currency: N/A.
        Handles async operations with 5-second timeout for child entity mapping.
        Performs global tag deduplication across all client menus.
    """

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Client, merge: bool = True
    ) -> ClientSaModel:
        """Map domain client to SQLAlchemy model.

        Args:
            session: Database session for operations.
            domain_obj: Client domain object to map.
            merge: Whether to merge with existing database entity.

        Returns:
            SQLAlchemy client model ready for persistence.

        Notes:
            Maps child entities (menus, tags) concurrently with 5-second timeout.
            Handles existing client merging and child entity updates.
            Performs global tag deduplication across all client menus.
            Marks discarded menus that are no longer in domain object.
        """
        log = structlog_logger("ClientMapper")
        log.info(
            "Starting client domain to SA mapping",
            client_id=domain_obj.id,
            author_id=domain_obj.author_id,
            has_menus=len(domain_obj.menus) > 0,
            menu_count=len(domain_obj.menus),
            has_tags=len(domain_obj.tags) > 0,
            tag_count=len(domain_obj.tags),
            merge_requested=merge,
        )
        merge_children = False
        client_on_db: ClientSaModel = await helpers.get_sa_entity(
            session=session,
            sa_model_type=ClientSaModel,
            filters={"id": domain_obj.id},
        )
        if not client_on_db and merge:
            merge_children = True
            log.debug(
                "Client not found in database, will merge children",
                client_id=domain_obj.id,
            )
        elif client_on_db:
            log.debug(
                "Found existing client in database",
                client_id=domain_obj.id,
                existing_menu_count=len(client_on_db.menus),
            )

        ids_of_menus_on_domain_client = [menu.id for menu in domain_obj.menus]
        if client_on_db:
            for menu in client_on_db.menus:
                if menu.id not in ids_of_menus_on_domain_client:
                    menu.discarded = True

        menus_tasks = (
            [
                MenuMapper.map_domain_to_sa(session, i, merge=merge_children)
                for i in domain_obj.menus
            ]
            if domain_obj.menus
            else []
        )
        tags_tasks = (
            [TagMapper.map_domain_to_sa(session, i) for i in domain_obj.tags]
            if domain_obj.tags
            else []
        )

        # Combine both lists of awaitables into one list
        combined_tasks = menus_tasks + tags_tasks

        # If we have any tasks, gather them in one call.
        if combined_tasks:
            log.debug(
                "Starting concurrent mapping of menus and tags",
                menu_tasks=len(menus_tasks),
                tag_tasks=len(tags_tasks),
                total_tasks=len(combined_tasks),
            )
            combined_results = await helpers.gather_results_with_timeout(
                combined_tasks,
                timeout=5,
                timeout_message="Timeout mapping recipes and tags in ClientMapper",
            )
            log.info(
                "Completed concurrent mapping of menus and tags",
                results_count=len(combined_results),
                menus_mapped=len(menus_tasks),
                tags_mapped=len(tags_tasks),
            )
            # Split the combined results back into recipes and tags.
            menus = combined_results[: len(menus_tasks)]
            tags = combined_results[len(menus_tasks) :]

            # Global deduplication of tags across all recipes.
            all_tags = {}
            for menu in menus:
                current_menu_tags = {}
                for tag in menu.tags:
                    key = (tag.key, tag.value, tag.author_id, tag.type)
                    if key in all_tags:
                        current_menu_tags[key] = all_tags[key]
                    else:
                        current_menu_tags[key] = tag
                        all_tags[key] = tag
                menu.tags = list(current_menu_tags.values())
        else:
            menus = []
            tags = []
        sa_client_kwargs = {
            "id": domain_obj.id,
            "author_id": domain_obj.author_id,
            "profile": (
                ApiProfile.from_domain(domain_obj.profile).to_orm_kwargs()
                if domain_obj.profile
                else None
            ),
            "contact_info": (
                ApiContactInfo.from_domain(domain_obj.contact_info).to_orm_kwargs()
                if domain_obj.contact_info
                else None
            ),
            "address": (
                ApiAddress.from_domain(domain_obj.address).to_orm_kwargs()
                if domain_obj.address
                else None
            ),
            "notes": domain_obj.notes,
            "onboarding_data": domain_obj.onboarding_data,
            "created_at": (
                domain_obj.created_at if domain_obj.created_at else datetime.now(UTC)
            ),
            "updated_at": (
                domain_obj.updated_at if domain_obj.created_at else datetime.now(UTC)
            ),
            "discarded": domain_obj.discarded,
            "version": domain_obj.version,
            # relationships
            "menus": menus,
            "tags": tags,
        }
        sa_client = ClientSaModel(**sa_client_kwargs)
        log.info(
            "Created SA client model",
            client_id=domain_obj.id,
            menus_mapped=len(menus),
            tags_mapped=len(tags),
            will_merge=client_on_db is not None and merge,
        )
        if client_on_db and merge:
            log.info(
                "Merging client with existing database record",
                client_id=domain_obj.id,
            )
            return await session.merge(sa_client)

        log.info(
            "Returning new SA client model",
            client_id=domain_obj.id,
            is_new_client=client_on_db is None,
        )
        return sa_client

    @staticmethod
    def map_sa_to_domain(sa_obj: ClientSaModel) -> Client:
        """Map SQLAlchemy client model to domain object.

        Args:
            sa_obj: SQLAlchemy client model to convert.

        Returns:
            Client domain object with all relationships mapped.

        Notes:
            Maps nested menus and tags using their respective mappers.
            Converts profile, contact info, and address using data class conversion.
            Logs mapping progress and completion status.
        """
        log = structlog_logger("ClientMapper")
        log.info(
            "Starting SA to domain client mapping",
            client_id=sa_obj.id,
            author_id=sa_obj.author_id,
            menu_count=len(sa_obj.menus),
            tag_count=len(sa_obj.tags),
            is_discarded=sa_obj.discarded,
        )

        address_kwargs = data_class_asdict(sa_obj.address)
        address_kwargs["state"] = State(address_kwargs["state"])

        client = Client(
            id=sa_obj.id,
            profile=Profile(**data_class_asdict(sa_obj.profile)),
            contact_info=ContactInfo(**data_class_asdict(sa_obj.contact_info)),
            address=Address(**address_kwargs),
            menus=[MenuMapper.map_sa_to_domain(i) for i in sa_obj.menus],
            tags={TagMapper.map_sa_to_domain(i) for i in sa_obj.tags},
            author_id=sa_obj.author_id,
            notes=sa_obj.notes,
            onboarding_data=sa_obj.onboarding_data,
            created_at=sa_obj.created_at,
            updated_at=sa_obj.updated_at,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )

        log.info(
            "Completed SA to domain client mapping",
            client_id=client.id,
            menus_mapped=len(client.menus),
            tags_mapped=len(client.tags),
        )

        return client
