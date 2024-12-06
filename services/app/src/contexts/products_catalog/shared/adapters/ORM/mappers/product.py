import src.contexts.seedwork.shared.adapters.utils as utils
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.shared.adapters.name_search import StrProcessor
from src.contexts.products_catalog.shared.adapters.ORM.mappers.score import ScoreMapper
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.brand import (
    BrandSaModel,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.is_food_votes import (
    IsFoodVotesSaModel,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.product import (
    ProductSaModel,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.source import (
    SourceSaModel,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.category import (
    CategorySaModel,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.food_group import (
    FoodGroupSaModel,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.parent_category import (
    ParentCategorySaModel,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.process_type import (
    ProcessTypeSaModel,
)
from src.contexts.products_catalog.shared.domain.entities.product import Product
from src.contexts.products_catalog.shared.domain.value_objects.is_food_votes import (
    IsFoodVotes,
)
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.allergen import AllergenMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.nutri_facts import NutriFactsMapper


class ProductMapper(ModelMapper):

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Product
    ) -> ProductSaModel:
        # relationships ref by id in the domain object
        # are fetched here
        if domain_obj.source_id:
            source_on_db = await utils.get_sa_entity(
                session=session,
                sa_model_type=SourceSaModel,
                filter={"id": domain_obj.source_id},
            )
        else:
            source_on_db = None
        if domain_obj.brand_id:
            brand_on_db = await utils.get_sa_entity(
                session=session,
                sa_model_type=BrandSaModel,
                filter={"id": domain_obj.brand_id},
            )
        else:
            brand_on_db = None
        if domain_obj.category_id:
            category_on_db = await utils.get_sa_entity(
                session=session,
                sa_model_type=CategorySaModel,
                filter={"id": domain_obj.category_id},
            )
        else:
            category_on_db = None
        if domain_obj.parent_category_id:
            parent_category_on_db = await utils.get_sa_entity(
                session=session,
                sa_model_type=ParentCategorySaModel,
                filter={"id": domain_obj.parent_category_id},
            )
        else:
            parent_category_on_db = None
        if domain_obj.food_group_id:
            food_group_on_db = await utils.get_sa_entity(
                session=session,
                sa_model_type=FoodGroupSaModel,
                filter={"id": domain_obj.food_group_id},
            )
        else:
            food_group_on_db = None
        if domain_obj.process_type_id:
            process_type_on_db = await utils.get_sa_entity(
                session=session,
                sa_model_type=ProcessTypeSaModel,
                filter={"id": domain_obj.process_type_id},
            )
        else:
            process_type_on_db = None
        allergens_tasks = (
            [AllergenMapper.map_domain_to_sa(session, i) for i in domain_obj.allergens]
            if domain_obj.allergens
            else []
        )
        if allergens_tasks:
            allergens_on_db = await utils.gather_results_with_timeout(
                allergens_tasks,
                timeout=5,
                timeout_message="Timeout mapping allergns in ProductMapper",
            )
        else:
            allergens_on_db = []

        async def handle_is_food_votes(house_id: str, vote: bool):
            vote_on_db = await utils.get_entity_id(
                session=session,
                sa_model_type=IsFoodVotesSaModel,
                filter={"house_id": house_id, "product_id": domain_obj.id},
            )
            if vote_on_db:
                return await session.merge(
                    IsFoodVotesSaModel(
                        house_id=house_id,
                        product_id=domain_obj.id,
                        is_food=vote,
                    )
                )
            return IsFoodVotesSaModel(
                house_id=house_id,
                product_id=domain_obj.id,
                is_food=vote,
            )

        houses = [i for i in domain_obj.is_food_votes.is_food_houses].extend(
            domain_obj.is_food_votes.is_not_food_houses
        )
        is_food_votes_tasks = (
            [
                handle_is_food_votes(
                    i,
                    True if i in domain_obj.is_food_votes.is_food_houses else False,
                )
                for i in houses
            ]
            if domain_obj.is_food_votes
            else []
        )
        if is_food_votes_tasks:
            is_food_votes = await utils.gather_results_with_timeout(
                is_food_votes_tasks,
                timeout=5,
                timeout_message="Timeout mapping allergns in ProductMapper",
            )
        else:
            is_food_votes = []
        return ProductSaModel(
            id=domain_obj.id,
            source_id=domain_obj.source_id,
            name=domain_obj.name,
            preprocessed_name=StrProcessor(domain_obj.name).output,
            brand_id=domain_obj.brand_id,
            barcode=domain_obj.barcode,
            is_food=domain_obj.is_food,
            is_food_houses_choice=domain_obj.is_food_houses_choice,
            category_id=domain_obj.category_id,
            parent_category_id=domain_obj.parent_category_id,
            food_group_id=domain_obj.food_group_id,
            process_type_id=domain_obj.process_type_id,
            score=await ScoreMapper.map_domain_to_sa(session, domain_obj.score),
            ingredients=domain_obj.ingredients,
            package_size=domain_obj.package_size,
            package_size_unit=domain_obj.package_size_unit,
            image_url=domain_obj.image_url,
            nutri_facts=await NutriFactsMapper.map_domain_to_sa(
                session, domain_obj.nutri_facts
            ),
            json_data=domain_obj.json_data,
            discarded=domain_obj.discarded,
            version=domain_obj.version,
            # relationships
            source_on=source_on_db,
            brand=brand_on_db,
            category=category_on_db,
            parent_category=parent_category_on_db,
            food_group=food_group_on_db,
            process_type=process_type_on_db,
            allergens=allergens_on_db,
            is_food_votes=is_food_votes,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: ProductSaModel) -> Product:
        is_food_votes = IsFoodVotes()
        for i in sa_obj.is_food_votes:
            if i.is_food:
                is_food_votes.is_food_houses.add(i.house_id)
            else:
                is_food_votes.is_not_food_houses.add(i.house_id)

        return Product(
            id=sa_obj.id,
            name=sa_obj.name,
            barcode=sa_obj.barcode,
            is_food=sa_obj.is_food,
            score=ScoreMapper.map_sa_to_domain(sa_obj.score),
            ingredients=sa_obj.ingredients,
            package_size=sa_obj.package_size,
            package_size_unit=sa_obj.package_size_unit,
            image_url=sa_obj.image_url,
            nutri_facts=NutriFactsMapper.map_sa_to_domain(sa_obj.nutri_facts),
            json_data=sa_obj.json_data,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
            # relationships
            source_id=sa_obj.source_id,
            brand_id=sa_obj.brand_id,
            category_id=sa_obj.category_id,
            parent_category_id=sa_obj.parent_category_id,
            food_group_id=sa_obj.food_group_id,
            process_type_id=sa_obj.process_type_id,
            diet_types_ids=(
                set([i.id for i in sa_obj.diet_types]) if sa_obj.diet_types else set()
            ),
            allergens=[AllergenMapper.map_sa_to_domain(i) for i in sa_obj.allergens],
            is_food_votes=is_food_votes,
        )
