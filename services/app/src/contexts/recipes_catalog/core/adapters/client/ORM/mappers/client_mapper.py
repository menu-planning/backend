from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.recipes_catalog.core.adapters.client.ORM.mappers.menu_mapper import MenuMapper
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.client_sa_model import ClientSaModel
from src.contexts.recipes_catalog.core.domain.client.root_aggregate.client import Client
import src.contexts.seedwork.shared.utils as utils
from src.contexts.seedwork.shared.adapters.ORM.mappers.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.tag.tag_mapper import TagMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.address import AddressSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.contact_info import ContactInfoSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.profile import ProfileSaModel
from src.contexts.shared_kernel.domain.value_objects.address import Address
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.logging.logger import logger
from dataclasses import asdict as data_class_asdict
from attrs import asdict

class ClientMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Client, merge: bool = True
    ) -> ClientSaModel:
        logger.debug(f"Mapping domain client to sa: {domain_obj}")
        # is_domain_obj_discarded = False
        # if domain_obj.discarded:
        #     is_domain_obj_discarded = True
        #     domain_obj._discarded = False
        merge_children = False
        client_on_db: ClientSaModel = await utils.get_sa_entity(
            session=session, sa_model_type=ClientSaModel, filter={"id": domain_obj.id}
        )
        if not client_on_db and merge:
            merge_children = True

        ids_of_menus_on_domain_client = [menu.id for menu in domain_obj.menus]
        if client_on_db:
            for menu in client_on_db.menus:
                if menu.id not in ids_of_menus_on_domain_client:
                    menu.discarded = True

        menus_tasks = (
            [MenuMapper.map_domain_to_sa(session, i, merge=merge_children)
             for i in domain_obj.menus]
            if domain_obj.menus
            else []
        )
        tags_tasks = (
            [TagMapper.map_domain_to_sa(session, i)
             for i in domain_obj.tags]
            if domain_obj.tags
            else []
        )

        # Combine both lists of awaitables into one list
        combined_tasks = menus_tasks + tags_tasks

        # If we have any tasks, gather them in one call.
        if combined_tasks: # and not is_domain_obj_discarded:
            combined_results = await utils.gather_results_with_timeout(
                combined_tasks,
                timeout=5,
                timeout_message="Timeout mapping recipes and tags in ClientMapper",
            )
            # Split the combined results back into recipes and tags.
            menus = combined_results[: len(menus_tasks)]
            tags = combined_results[len(menus_tasks):]

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
            "created_at": domain_obj.created_at if domain_obj.created_at else datetime.now(),
            "updated_at": domain_obj.updated_at if domain_obj.created_at else datetime.now(),
            "discarded": domain_obj.discarded, # is_domain_obj_discarded,
            "version": domain_obj.version,
            # relationships
            "menus": menus,
            "tags": tags,
        }
        # domain_obj._discarded = is_domain_obj_discarded
        logger.debug(f"SA Client kwargs: {sa_client_kwargs}")
        sa_client = ClientSaModel(**sa_client_kwargs)
        if client_on_db and merge:
            return await session.merge(sa_client)
        return sa_client

    @staticmethod
    def map_sa_to_domain(sa_obj: ClientSaModel) -> Client:
        return Client(
            id=sa_obj.id,
            profile=Profile(**data_class_asdict(sa_obj.profile)),
            contact_info=ContactInfo(**data_class_asdict(sa_obj.contact_info)),
            address=Address(**data_class_asdict(sa_obj.address)),
            menus=[MenuMapper.map_sa_to_domain(i) for i in sa_obj.menus],
            tags=set([TagMapper.map_sa_to_domain(i) for i in sa_obj.tags]),
            author_id=sa_obj.author_id,
            notes=sa_obj.notes,
            created_at=sa_obj.created_at,
            updated_at=sa_obj.updated_at,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )