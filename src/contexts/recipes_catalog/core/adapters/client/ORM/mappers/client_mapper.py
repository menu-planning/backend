from dataclasses import asdict as data_class_asdict
from datetime import datetime

from attrs import asdict
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.recipes_catalog.core.adapters.client.ORM.mappers.menu_mapper import (
    MenuMapper,
)
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.client_sa_model import (
    ClientSaModel,
)
from src.contexts.recipes_catalog.core.domain.client.root_aggregate.client import Client
from src.contexts.seedwork.shared import utils
from src.contexts.seedwork.shared.adapters.ORM.mappers.mapper import ModelMapper
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
from src.contexts.shared_kernel.domain.value_objects.address import Address
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.logging.logger import structlog_logger


class ClientMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Client, merge: bool = True
    ) -> ClientSaModel:
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
        # is_domain_obj_discarded = False
        # if domain_obj.discarded:
        #     is_domain_obj_discarded = True
        #     domain_obj._discarded = False
        merge_children = False
        client_on_db: ClientSaModel = await utils.get_sa_entity(
            session=session, sa_model_type=ClientSaModel, filters={"id": domain_obj.id}
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
        if combined_tasks:  # and not is_domain_obj_discarded:
            log.debug(
                "Starting concurrent mapping of menus and tags",
                menu_tasks=len(menus_tasks),
                tag_tasks=len(tags_tasks),
                total_tasks=len(combined_tasks),
            )
            combined_results = await utils.gather_results_with_timeout(
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
            "profile": ProfileSaModel(**asdict(domain_obj.profile)),
            "contact_info": ContactInfoSaModel(**asdict(domain_obj.contact_info)),
            "address": AddressSaModel(**asdict(domain_obj.address)),
            "notes": domain_obj.notes,
            "onboarding_data": domain_obj.onboarding_data,
            "created_at": (
                domain_obj.created_at if domain_obj.created_at else datetime.now()
            ),
            "updated_at": (
                domain_obj.updated_at if domain_obj.created_at else datetime.now()
            ),
            "discarded": domain_obj.discarded,  # is_domain_obj_discarded,
            "version": domain_obj.version,
            # relationships
            "menus": menus,
            "tags": tags,
        }
        # domain_obj._discarded = is_domain_obj_discarded
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
        log = structlog_logger("ClientMapper")
        log.info(
            "Starting SA to domain client mapping",
            client_id=sa_obj.id,
            author_id=sa_obj.author_id,
            menu_count=len(sa_obj.menus),
            tag_count=len(sa_obj.tags),
            is_discarded=sa_obj.discarded,
        )
        
        client = Client(
            entity_id=sa_obj.id,
            profile=Profile(**data_class_asdict(sa_obj.profile)),
            contact_info=ContactInfo(**data_class_asdict(sa_obj.contact_info)),
            address=Address(**data_class_asdict(sa_obj.address)),
            menus=[MenuMapper.map_sa_to_domain(i) for i in sa_obj.menus],
            tags=set([TagMapper.map_sa_to_domain(i) for i in sa_obj.tags]),
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
