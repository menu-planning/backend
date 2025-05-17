import anyio
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.seedwork.shared.utils import get_sa_entity, gather_results_with_timeout
from src.contexts.products_catalog.core.adapters.name_search import StrProcessor
from src.contexts.products_catalog.core.adapters.ORM.mappers.score import ScoreMapper
from src.contexts.products_catalog.core.adapters.ORM.sa_models.brand import BrandSaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.category import CategorySaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.food_group import FoodGroupSaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.parent_category import ParentCategorySaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.process_type import ProcessTypeSaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.is_food_votes import IsFoodVotesSaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.product import ProductSaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.source import SourceSaModel
from src.contexts.products_catalog.core.domain.entities.product import Product
from src.contexts.products_catalog.core.domain.value_objects.is_food_votes import IsFoodVotes
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.nutri_facts import NutriFactsMapper
from src.logging.logger import logger

class ProductMapper(ModelMapper):

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession,
        domain_obj: Product,
        merge: bool = True
    ) -> ProductSaModel:
        logger.debug(f"Mapping domain Product to SA Product: {domain_obj.name}")
        product_on_db = await get_sa_entity(
            session=session, sa_model_type=ProductSaModel, filter={"id": domain_obj.id}
        )
        # 1) Prepare six “get by id” coroutines (or no-ops)
        relation_specs = [
            (SourceSaModel,         "source_id"),
            (BrandSaModel,          "brand_id"),
            (CategorySaModel,       "category_id"),
            (ParentCategorySaModel, "parent_category_id"),
            (FoodGroupSaModel,      "food_group_id"),
            (ProcessTypeSaModel,    "process_type_id"),
        ]
        relation_tasks = []
        for sa_model, attr in relation_specs:
            _id = getattr(domain_obj, attr)
            if _id:
                relation_tasks.append(
                    get_sa_entity(
                        session=session,
                        sa_model_type=sa_model,
                        filter={"id": _id},
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
            timeout_message="Timeout loading related entities in ProductMapper"
        )

        # 3) Prepare all “is_food_votes” coroutines
        async def _handle_vote(house_id: str, vote: bool):
            existing = await get_sa_entity(
                session=session,
                sa_model_type=IsFoodVotesSaModel,
                filter={"house_id": house_id, "product_id": domain_obj.id},
            )
            vote_obj = IsFoodVotesSaModel(
                house_id=house_id,
                product_id=domain_obj.id,
                is_food=vote,
            )
            return await session.merge(vote_obj) if existing else vote_obj

        vote_tasks = []
        if domain_obj.is_food_votes:
            votes = (
                list(domain_obj.is_food_votes.is_food_houses)
                + list(domain_obj.is_food_votes.is_not_food_houses)
            )
            for h in votes:
                vote_tasks.append(_handle_vote(
                    h,
                    h in domain_obj.is_food_votes.is_food_houses
                ))

        is_food_votes = await gather_results_with_timeout(
            vote_tasks,
            timeout=5,
            timeout_message="Timeout mapping is_food_votes in ProductMapper"
        ) if vote_tasks else []

        logger.debug('Start building SA Product kwargs')

        # log each argument
        logger.debug(f"id: {domain_obj.id}")
        logger.debug(f"source_id: {domain_obj.source_id}")
        logger.debug(f"name: {domain_obj.name}")
        logger.debug(f"preprocessed_name: {StrProcessor(domain_obj.name).output}")
        logger.debug(f"shopping_name: {domain_obj.shopping_name}")
        logger.debug(f"store_department_name: {domain_obj.store_department_name}")
        logger.debug(f"recommended_brands_and_products: {domain_obj.recommended_brands_and_products}")
        logger.debug(f"edible_yield: {domain_obj.edible_yield}")
        logger.debug(f"kg_per_unit: {domain_obj.kg_per_unit}")
        logger.debug(f"liters_per_kg: {domain_obj.liters_per_kg}")
        logger.debug(f"nutrition_group: {domain_obj.nutrition_group}")
        logger.debug(f"cooking_factor: {domain_obj.cooking_factor}")
        logger.debug(f"conservation_days: {domain_obj.conservation_days}")
        logger.debug(f"substitutes: {domain_obj.substitutes}")
        logger.debug(f"brand_id: {domain_obj.brand_id}")
        logger.debug(f"barcode: {domain_obj.barcode}")
        logger.debug(f"is_food: {domain_obj.is_food}")
        logger.debug(f"is_food_houses_choice: {domain_obj.is_food_houses_choice}")
        logger.debug(f"category_id: {domain_obj.category_id}")
        logger.debug(f"parent_category_id: {domain_obj.parent_category_id}")
        logger.debug(f"food_group_id: {domain_obj.food_group_id}")
        logger.debug(f"process_type_id: {domain_obj.process_type_id}")
        logger.debug(f"score: {await ScoreMapper.map_domain_to_sa(session, domain_obj.score)}")
        logger.debug(f"ingredients: {domain_obj.ingredients}")
        logger.debug(f"package_size: {domain_obj.package_size}")
        logger.debug(f"package_size_unit: {domain_obj.package_size_unit}")
        logger.debug(f"image_url: {domain_obj.image_url}")
        logger.debug(f"nutri_facts: {await NutriFactsMapper.map_domain_to_sa(
            session, domain_obj.nutri_facts
        )}")
        logger.debug(f"json_data: {domain_obj.json_data}")
        logger.debug(f"discarded: {domain_obj.discarded}")
        logger.debug(f"version: {domain_obj.version}")
        # relationships
        logger.debug(f"source: {source_on_db}")
        logger.debug(f"brand: {brand_on_db}")
        logger.debug(f"category: {category_on_db}")
        logger.debug(f"parent_category: {parent_category_on_db}")
        logger.debug(f"food_group: {food_group_on_db}")
        logger.debug(f"process_type: {process_type_on_db}")
        logger.debug(f"is_food_votes: {is_food_votes}")

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

        logger.debug(f"SA Product kwargs: {sa_kwargs}")
        sa_product = ProductSaModel(**sa_kwargs)
        if product_on_db and merge:
            return await session.merge(sa_product)
        return sa_product


    @staticmethod
    def map_sa_to_domain(sa_obj: ProductSaModel) -> Product:
        votes_vo = IsFoodVotes() # type: ignore
        for v in sa_obj.is_food_votes:
            if v.is_food:
                votes_vo.is_food_houses.add(v.house_id)
            else:
                votes_vo.is_not_food_houses.add(v.house_id)

        sa_kwargs = {
            "id": sa_obj.id,
            "source_id": sa_obj.source_id,
            "name": sa_obj.name,
            "shopping_name": sa_obj.shopping_name,
            "store_department_name": sa_obj.store_department_name,
            "recommended_brands_and_products": sa_obj.recommended_brands_and_products,
            "edible_yield": (
                float(sa_obj.edible_yield)
                if sa_obj.edible_yield is not None
                else None
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
            "is_food_votes":votes_vo,
        }

        try: 
            logger.debug(f"SA Product kwargs: {sa_kwargs}")
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
            logger.error(f"Error mapping SA Product to domain: {e}")
            raise e
