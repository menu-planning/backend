"""Mappers between domain `Product` and SQLAlchemy `ProductSaModel`."""
import anyio
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.mappers.score_mapper import (
    ScoreMapper,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.brand import BrandSaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.category_sa_model import (
    CategorySaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.food_group_sa_model import (
    FoodGroupSaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.parent_categorysa_model import (
    ParentCategorySaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.process_type_sa_model import (
    ProcessTypeSaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.is_food_votes import (
    IsFoodVotesSaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.product import (
    ProductSaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.source import (
    SourceSaModel,
)
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.products_catalog.core.domain.value_objects.is_food_votes import (
    IsFoodVotes,
)
from src.contexts.seedwork.adapters.ORM.mappers.helpers import (
    gather_results_with_timeout,
    get_sa_entity,
)
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.name_search import StrProcessor
from src.contexts.shared_kernel.adapters.ORM.mappers.nutri_facts_mapper import (
    NutriFactsMapper,
)
from src.logging.logger import StructlogFactory

logger = StructlogFactory.get_logger(__name__)


class ProductMapper(ModelMapper):
    """Map Product between domain and ORM, handling related entities and votes."""

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Product, merge: bool = True
    ) -> ProductSaModel:
        logger.debug(
            "Mapping domain Product to SA Product",
            product_name=domain_obj.name,
            product_id=domain_obj.id,
            operation="domain_to_sa"
        )
        product_on_db = await get_sa_entity(
            session=session, sa_model_type=ProductSaModel, filters={"id": domain_obj.id}
        )
        # 1) Prepare six “get by id” coroutines (or no-ops)
        relation_specs = [
            (SourceSaModel, "source_id"),
            (BrandSaModel, "brand_id"),
            (CategorySaModel, "category_id"),
            (ParentCategorySaModel, "parent_category_id"),
            (FoodGroupSaModel, "food_group_id"),
            (ProcessTypeSaModel, "process_type_id"),
        ]
        relation_tasks = []
        for sa_model, attr in relation_specs:
            _id = getattr(domain_obj, attr)
            if _id:
                relation_tasks.append(
                    get_sa_entity(
                        session=session,
                        sa_model_type=sa_model,
                        filters={"id": _id},
                    )
                )
            else:
                # immediate None
                relation_tasks.append(anyio.sleep(0))

        # 2) Run them with timeout
        (
            source_on_db,
            brand_on_db,
            category_on_db,
            parent_category_on_db,
            food_group_on_db,
            process_type_on_db,
        ) = await gather_results_with_timeout(
            relation_tasks,
            timeout=5,
            timeout_message="Timeout loading related entities in ProductMapper",
        )

        # 3) Prepare all “is_food_votes” coroutines
        async def _handle_vote(house_id: str, vote: bool):
            existing = await get_sa_entity(
                session=session,
                sa_model_type=IsFoodVotesSaModel,
                filters={"house_id": house_id, "product_id": domain_obj.id},
            )
            vote_obj = IsFoodVotesSaModel(
                house_id=house_id,
                product_id=domain_obj.id,
                is_food=vote,
            )
            return await session.merge(vote_obj) if existing else vote_obj

        vote_tasks = []
        if domain_obj.is_food_votes:
            votes = list(domain_obj.is_food_votes.is_food_houses) + list(
                domain_obj.is_food_votes.is_not_food_houses
            )
            for h in votes:
                vote_tasks.append(
                    _handle_vote(h, h in domain_obj.is_food_votes.is_food_houses)
                )

        is_food_votes = (
            await gather_results_with_timeout(
                vote_tasks,
                timeout=5,
                timeout_message="Timeout mapping is_food_votes in ProductMapper",
            )
            if vote_tasks
            else []
        )

                # Build SA Product kwargs with structured logging for key fields only
        logger.debug(
            "Building SA Product kwargs",
            product_id=domain_obj.id,
            has_brand=bool(domain_obj.brand_id),
            has_category=bool(domain_obj.category_id),
            is_food=domain_obj.is_food,
            operation="build_kwargs"
        )

        # 4) Build kwargs and return the SA model
        sa_kwargs = {
            "id": domain_obj.id,
            "source_id": domain_obj.source_id,
            "name": domain_obj.name,
            "preprocessed_name": StrProcessor(domain_obj.name).output,
            "shopping_name": domain_obj.shopping_name,
            "store_department_name": domain_obj.store_department_name,
            "recommended_brands_and_products": domain_obj.recommended_brands_and_products,
            "edible_yield": domain_obj.edible_yield,
            "kg_per_unit": domain_obj.kg_per_unit,
            "liters_per_kg": domain_obj.liters_per_kg,
            "nutrition_group": domain_obj.nutrition_group,
            "cooking_factor": domain_obj.cooking_factor,
            "conservation_days": domain_obj.conservation_days,
            "substitutes": domain_obj.substitutes,
            "brand_id": domain_obj.brand_id,
            "barcode": domain_obj.barcode,
            "is_food": domain_obj.is_food,
            "is_food_houses_choice": domain_obj.is_food_houses_choice,
            "category_id": domain_obj.category_id,
            "parent_category_id": domain_obj.parent_category_id,
            "food_group_id": domain_obj.food_group_id,
            "process_type_id": domain_obj.process_type_id,
            "score": await ScoreMapper.map_domain_to_sa(session, domain_obj.score),
            "ingredients": domain_obj.ingredients,
            "package_size": domain_obj.package_size,
            "package_size_unit": domain_obj.package_size_unit,
            "image_url": domain_obj.image_url,
            "nutri_facts": await NutriFactsMapper.map_domain_to_sa(
                session, domain_obj.nutri_facts
            ),
            "json_data": domain_obj.json_data,
            "discarded": domain_obj.discarded,
            "version": domain_obj.version,
            # relationships
            "source": source_on_db,
            "brand": brand_on_db,
            "category": category_on_db,
            "parent_category": parent_category_on_db,
            "food_group": food_group_on_db,
            "process_type": process_type_on_db,
            "is_food_votes": is_food_votes,
        }

        logger.debug(
            "SA Product mapping completed",
            product_id=domain_obj.id,
            kwargs_count=len(sa_kwargs),
            operation="sa_product_created"
        )
        sa_product = ProductSaModel(**sa_kwargs)
        if product_on_db and merge:
            return await session.merge(sa_product)
        return sa_product

    @staticmethod
    def map_sa_to_domain(sa_obj: ProductSaModel) -> Product:
        is_food_houses = set()
        is_not_food_houses = set()
        for v in sa_obj.is_food_votes:
            if v.is_food:
                is_food_houses.add(v.house_id)
            else:
                is_not_food_houses.add(v.house_id)
        votes_vo = IsFoodVotes(
            is_food_houses=frozenset(is_food_houses),
            is_not_food_houses=frozenset(is_not_food_houses),
        )  # type: ignore

        sa_kwargs = {
            "id": sa_obj.id,
            "source_id": sa_obj.source_id,
            "name": sa_obj.name,
            "shopping_name": sa_obj.shopping_name,
            "store_department_name": sa_obj.store_department_name,
            "recommended_brands_and_products": sa_obj.recommended_brands_and_products,
            "edible_yield": (
                float(sa_obj.edible_yield) if sa_obj.edible_yield is not None else None
            ),
            "kg_per_unit": sa_obj.kg_per_unit,
            "liters_per_kg": sa_obj.liters_per_kg,
            "nutrition_group": sa_obj.nutrition_group,
            "cooking_factor": sa_obj.cooking_factor,
            "conservation_days": sa_obj.conservation_days,
            "substitutes": sa_obj.substitutes,
            "brand_id": sa_obj.brand_id,
            "barcode": sa_obj.barcode,
            "is_food": sa_obj.is_food,
            "category_id": sa_obj.category_id,
            "parent_category_id": sa_obj.parent_category_id,
            "food_group_id": sa_obj.food_group_id,
            "process_type_id": sa_obj.process_type_id,
            "score": ScoreMapper.map_sa_to_domain(sa_obj.score),
            "ingredients": sa_obj.ingredients,
            "package_size": sa_obj.package_size,
            "package_size_unit": sa_obj.package_size_unit,
            "image_url": sa_obj.image_url,
            "nutri_facts": NutriFactsMapper.map_sa_to_domain(sa_obj.nutri_facts),
            "json_data": sa_obj.json_data,
            "discarded": sa_obj.discarded,
            "version": sa_obj.version,
            "is_food_votes": votes_vo,
        }

        try:
            logger.debug(
                "Creating domain Product from SA kwargs",
                product_id=sa_kwargs.get("id"),
                kwargs_count=len(sa_kwargs),
                operation="sa_to_domain"
            )
            return Product(**sa_kwargs)
        #     return Product(
        #     id=sa_obj.id,
        #     name=sa_obj.name,
        #     barcode=sa_obj.barcode,
        #     is_food=sa_obj.is_food,
        #     shopping_name=sa_obj.shopping_name,
        #     store_department_name=sa_obj.store_department_name,
        #     recommended_brands_and_products=sa_obj.recommended_brands_and_products,
        #     edible_yield=(
        #         float(sa_obj.edible_yield)
        #         if sa_obj.edible_yield is not None
        #         else None
        #     ),
        #     kg_per_unit=sa_obj.kg_per_unit,
        #     liters_per_kg=sa_obj.liters_per_kg,
        #     nutrition_group=sa_obj.nutrition_group,
        #     cooking_factor=sa_obj.cooking_factor,
        #     conservation_days=sa_obj.conservation_days,
        #     substitutes=sa_obj.substitutes,
        #     score=ScoreMapper.map_sa_to_domain(sa_obj.score),
        #     ingredients=sa_obj.ingredients,
        #     package_size=sa_obj.package_size,
        #     package_size_unit=sa_obj.package_size_unit,
        #     image_url=sa_obj.image_url,
        #     nutri_facts=NutriFactsMapper.map_sa_to_domain(sa_obj.nutri_facts),
        #     json_data=sa_obj.json_data,
        #     discarded=sa_obj.discarded,
        #     version=sa_obj.version,
        #     # relationships by id
        #     source_id=sa_obj.source_id,
        #     brand_id=sa_obj.brand_id,
        #     category_id=sa_obj.category_id,
        #     parent_category_id=sa_obj.parent_category_id,
        #     food_group_id=sa_obj.food_group_id,
        #     process_type_id=sa_obj.process_type_id,
        #     is_food_votes=votes_vo,
        # )
        except Exception as e:
            logger.error(
                "Error mapping SA Product to domain",
                product_id=sa_kwargs.get("id"),
                error_type=type(e).__name__,
                error_message=str(e),
                operation="sa_to_domain_error",
                exc_info=True
            )
            raise
