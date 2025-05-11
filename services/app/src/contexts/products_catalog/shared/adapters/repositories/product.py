from typing import Any

from sqlalchemy import Select, case, desc, func, inspect, nulls_last, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from src.contexts.products_catalog.shared.adapters.name_search import SimilarityRanking
from src.contexts.products_catalog.shared.adapters.ORM.mappers.product import (
    ProductMapper,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models import (
    BrandSaModel,
    CategorySaModel,
    FoodGroupSaModel,
    ParentCategorySaModel,
    ProcessTypeSaModel,
    ProductSaModel,
    SourceSaModel,
)
from src.contexts.products_catalog.shared.domain.entities.product import Product
from src.contexts.products_catalog.shared.domain.enums import FrontendFilterTypes
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.logging.logger import logger

_source_sort_order = ["manual", "tbca", "taco", "private", "gs1", "auto"]


class ProductRepo(CompositeRepository[Product, ProductSaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=ProductSaModel,
            filter_key_to_column_name={
                "id": "id",
                "name": "name",
                "barcode": "barcode",
                "is_food": "is_food",
            },
        ),
        FilterColumnMapper(
            sa_model_type=SourceSaModel,
            filter_key_to_column_name={"source": "name"},
            join_target_and_on_clause=[(SourceSaModel, ProductSaModel.source)],
        ),
        FilterColumnMapper(
            sa_model_type=BrandSaModel,
            filter_key_to_column_name={"brand": "name"},
            join_target_and_on_clause=[(BrandSaModel, ProductSaModel.brand)],
        ),
        FilterColumnMapper(
            sa_model_type=CategorySaModel,
            filter_key_to_column_name={"category": "name"},
            join_target_and_on_clause=[(CategorySaModel, ProductSaModel.category)],
        ),
        FilterColumnMapper(
            sa_model_type=ParentCategorySaModel,
            filter_key_to_column_name={"parent_category": "name"},
            join_target_and_on_clause=[
                (ParentCategorySaModel, ProductSaModel.parent_category)
            ],
        ),
        FilterColumnMapper(
            sa_model_type=FoodGroupSaModel,
            filter_key_to_column_name={"food_group": "name"},
            join_target_and_on_clause=[(FoodGroupSaModel, ProductSaModel.food_group)],
        ),
        FilterColumnMapper(
            sa_model_type=ProcessTypeSaModel,
            filter_key_to_column_name={"process_type": "name"},
            join_target_and_on_clause=[
                (ProcessTypeSaModel, ProductSaModel.process_type)
            ],
        ),
    ]

    def __init__(
        self,
        db_session: AsyncSession,
    ):
        self._session = db_session
        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=ProductMapper,
            domain_model_type=Product,
            sa_model_type=ProductSaModel,
            filter_to_column_mappers=ProductRepo.filter_to_column_mappers,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Product):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Product:
        model_obj = await self._generic_repo.get(id)
        return model_obj # type: ignore

    async def get_sa_instance(self, id: str) -> ProductSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj # type: ignore

    def sort_stmt(
        self,
        stmt: Select,
        sort: str | None,
    ) -> Select:
        stmt = self._generic_repo.sort_stmt(stmt, sort)
        if not sort:
            return stmt
        sa_model_type = (
            self._generic_repo.get_sa_model_type_by_filter_key(
                self._generic_repo.remove_desc_prefix(sort)
            )
            or self.sa_model_type
        )
        inspector = inspect(sa_model_type)
        filter_key_to_column_name = (
            self._generic_repo.get_filter_key_to_column_name_for_sa_model_type(
                sa_model_type
            )
        )
        if filter_key_to_column_name:
            clean_sort_name = filter_key_to_column_name.get(
                self._generic_repo.remove_desc_prefix(sort), None
            ) or self._generic_repo.remove_desc_prefix(sort)
        else:
            clean_sort_name = self._generic_repo.remove_desc_prefix(sort)
        if (
            sort
            and clean_sort_name in inspector.columns.keys()
            and "source" not in sort  # source is a enum
        ):
            SourceAlias = aliased(SourceSaModel)
            try:
                # Tries to sort by source in the case of equality on other fields
                source_order = case(
                    {id: number for number, id in enumerate(_source_sort_order)},
                    value=SourceAlias.name,
                )
                stmt = stmt.join(SourceAlias, sa_model_type.source).order_by(
                    nulls_last(source_order)
                )
            except Exception:
                pass
        elif "source" in sort and "source" in inspector.columns.keys():
            SourceAlias = aliased(SourceSaModel)
            try:
                if sort.startswith("-"):
                    _whens = {
                        id: number for number, id in enumerate(_source_sort_order[::-1])
                    }
                else:
                    _whens = {
                        id: number for number, id in enumerate(_source_sort_order)
                    }
                source_order = case(_whens,value=SourceAlias.name)
                stmt = stmt.join(SourceAlias, sa_model_type.source).order_by(
                    nulls_last(source_order)
                )
            except Exception:
                pass
        return stmt

    # TODO: move to tag repo
    async def list_all_brand_names(
        self,
    ) -> list[str]:
        stmt = (
            select(ProductSaModel.brand)
            .distinct(ProductSaModel.brand)
            .where(ProductSaModel.brand != None)
            .order_by(nulls_last(ProductSaModel.brand))
        )
        return await self._generic_repo.execute_stmt(stmt)

    async def _list_similar_names_using_pg_similarity(
        self,
        description: str,
        include_product_with_barcode: bool = False,
        limit: int = 10,
    ) -> list[tuple[Product, float]]:
        stmt = select(
            ProductSaModel,
            func.similarity(ProductSaModel.preprocessed_name, description).label(
                "sim_score"
            ),
        ).where(func.similarity(ProductSaModel.preprocessed_name, description) > 0)
        if not include_product_with_barcode:
            stmt = stmt.where(
                (ProductSaModel.barcode == None) | (ProductSaModel.barcode == "")
            )
        stmt = (
            stmt.where(ProductSaModel.is_food == True, ProductSaModel.discarded == False)
            .order_by(nulls_last(desc("sim_score")))
            .limit(limit)
        )
        sa_objs = await self._session.execute(stmt)
        rows = sa_objs.all()
        out = []
        for idx, (sa, score) in enumerate(rows, start=1):
            # log minimal info about the SA model
            logger.debug(
                "Row %d: id=%s name=%s score=%.3f",
                idx,
                sa.id,
                sa.name,
                score,
            )

            # 3) map to domain in its own try/except so we see failures
            try:
                prod = self.data_mapper.map_sa_to_domain(sa)
            except Exception:
                logger.exception("❌ map_sa_to_domain failed for %s", sa.id)
                continue

            # 4) log the small repr of your Product entity
            logger.debug("  → domain product: %r", prod)
            out.append((prod, score))

        return out

    async def list_top_similar_names(
        self,
        description: str,
        include_product_with_barcode: bool = False,
        limit: int = 20,
        filter_by_first_word_partial_match: bool = False,
    ) -> list[Product]:
        logger.debug(f"Searching for similar names to {description}")
        full_name_matches: list[tuple[Product,float]] = await self._list_similar_names_using_pg_similarity(
            description, include_product_with_barcode, limit
        )
        first_word_matches: list[tuple[Product,float]] = await self._list_similar_names_using_pg_similarity(
            description.split()[0], include_product_with_barcode, limit
        )
        similars = list(set(full_name_matches + first_word_matches))
        ranking = SimilarityRanking(
            description, [(i[0].name, i[1]) for i in similars]
        ).ranking
        if len(ranking) == 0:
            return []
        # if ranking[0].partial_word == 0:
        #     return []
        if filter_by_first_word_partial_match:
            result = []
            for i in ranking:
                if i.has_first_word_partial_match and i.description not in result:
                    result.append(i.description)
        else:
            result = []
            for i in ranking:
                if i.description not in result:
                    result.append(i.description)

        ordered_products: list[Product] = []
        for description in result[:limit]:
            for product in [i[0] for i in similars]:
                if product.name == description:
                    ordered_products.append(product)
                    break  # Stop once you find the match to avoid duplicates

        # logger.debug(f"Returning similar names: {[i.name for i in ordered_products]}")
        return ordered_products

    # TODO: refactor this frankenstein
    async def list_filter_options(
        self,
        *,
        filter: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        limit: int | None = None,
    ) -> dict[str, dict[str, str | list[str]]]:
        target_columns = ["brand", "category", "parent_category"]
        if filter:
            target_columns_filter = {
                i: filter.pop(i) for i in target_columns if i in filter
            }
        else:
            target_columns_filter = {}
        if starting_stmt is not None:
            stmt = starting_stmt
        else:
            for column in target_columns:
                if column == target_columns[0]:
                    stmt = select(getattr(self.sa_model_type, column).label(column))
                else:
                    stmt = stmt.add_columns(
                        getattr(self.sa_model_type, column).label(column)
                    )
        if not filter:
            stmt = self._generic_repo.setup_skip_and_limit(stmt, {}, limit)
        else:
            stmt = self._generic_repo.setup_skip_and_limit(stmt, filter, limit)
            already_joined = set()
            if self.filter_to_column_mappers:
                for mapper in self.filter_to_column_mappers:
                    sa_model_type_filter = (
                        self._generic_repo.get_filters_for_sa_model_type(
                            filter=filter, sa_model_type=mapper.sa_model_type
                        )
                    )
                    if sa_model_type_filter and mapper.join_target_and_on_clause:
                        for join_target, on_clause in mapper.join_target_and_on_clause:
                            if join_target not in already_joined:
                                stmt = stmt.join(join_target, on_clause)
                                already_joined.add(join_target)
                    stmt = self._generic_repo.filter_stmt(
                        stmt=stmt,
                        filter=sa_model_type_filter,
                        sa_model_type=mapper.sa_model_type,
                        mapping=mapper.filter_key_to_column_name,
                    )
            # stmt = self._generic_repo.filter_stmt(stmt, filter)

        result = {}
        stmt_alias = stmt.alias()
        parent_category_stmt = (
            select(stmt_alias.c.parent_category)
            .where(stmt_alias.c.parent_category != None)
            .distinct(stmt_alias.c.parent_category)
            .order_by(nulls_last(stmt_alias.c.parent_category))
        )
        parent_categories = await self._session.execute(parent_category_stmt)
        result["parent_category"] = [i[0] for i in parent_categories.all()]

        if (
            "parent_category" in target_columns_filter
            and "category" not in target_columns_filter
        ):
            if isinstance(target_columns_filter["parent_category"], str):
                stmt = stmt.where(
                    ProductSaModel.parent_category
                    == target_columns_filter["parent_category"]
                )
            else:
                stmt = stmt.where(
                    ProductSaModel.parent_category.in_(
                        target_columns_filter["parent_category"]
                    )
                )
            stmt_alias = stmt.alias()
            categories_stmt = (
                select(stmt_alias.c.category)
                .where(stmt_alias.c.category != None)
                .distinct(stmt_alias.c.category)
                .order_by(nulls_last(stmt_alias.c.category))
            )
            categories = await self._session.execute(categories_stmt)
            result["category"] = [i[0] for i in categories.all()]

            brands_stmt = (
                select(stmt_alias.c.brand)
                .where(stmt_alias.c.brand != None)
                .distinct(stmt_alias.c.brand)
                .order_by(nulls_last(stmt_alias.c.brand))
            )
            brands = await self._session.execute(brands_stmt)
            result["brand"] = [i[0] for i in brands.all()]
        elif (
            "parent_category" in target_columns_filter
            and "category" in target_columns_filter
        ):
            if isinstance(target_columns_filter["parent_category"], str):
                stmt = stmt.where(
                    ProductSaModel.parent_category
                    == target_columns_filter["parent_category"]
                )
            else:
                stmt = stmt.where(
                    ProductSaModel.parent_category.in_(
                        target_columns_filter["parent_category"]
                    )
                )
            stmt_alias = stmt.alias()
            categories_stmt = (
                select(stmt_alias.c.category)
                .where(stmt_alias.c.category != None)
                .distinct(stmt_alias.c.category)
                .order_by(nulls_last(stmt_alias.c.category))
            )
            categories = await self._session.execute(categories_stmt)
            result["category"] = [i[0] for i in categories.all()]

            if isinstance(target_columns_filter["category"], str):
                assert target_columns_filter["category"] in result["category"]
                stmt = stmt.where(
                    ProductSaModel.category == target_columns_filter["category"]
                )
            else:
                for i in target_columns_filter["category"]:
                    assert i in result["category"]
                stmt = stmt.where(
                    ProductSaModel.category.in_(target_columns_filter["category"])
                )
            stmt_alias = stmt.alias()
            brands_stmt = (
                select(stmt_alias.c.brand)
                .where(stmt_alias.c.brand != None)
                .distinct(stmt_alias.c.brand)
                .order_by(nulls_last(stmt_alias.c.brand))
            )
            brands = await self._session.execute(brands_stmt)
            result["brand"] = [i[0] for i in brands.all()]
        elif (
            "parent_category" not in target_columns_filter
            and "category" in target_columns_filter
        ):
            raise BadRequestException(
                f"Category selected without parent category. Category={target_columns_filter['category']}"
            )
        elif (
            "parent_category" not in target_columns_filter
            and "category" not in target_columns_filter
        ):
            result["category"] = []

            stmt_alias = stmt.alias()
            brands_stmt = (
                select(stmt_alias.c.brand)
                .where(stmt_alias.c.brand != None)
                .distinct(stmt_alias.c.brand)
                .order_by(nulls_last(stmt_alias.c.brand))
            )
            brands = await self._session.execute(brands_stmt)
            result["brand"] = [i[0] for i in brands.all()]

        final_filters = {
            "sort": {
                "type": FrontendFilterTypes.SORT.value,
                "options": self._generic_repo.inspector.columns.keys(),
                # "options": [
                #     i
                #     for i in self.filter_to_column_mappers.keys()
                #     if i in self._generic_repo.inspector.columns.keys()
                # ],
            },
            "category": {
                "type": FrontendFilterTypes.MULTI_SELECTION.value,
                "options": result.get("category", []),
            },
            "parent-category": {
                "type": FrontendFilterTypes.MULTI_SELECTION.value,
                "options": result.get("parent_category", []),
            },
            "food-group": {
                "type": FrontendFilterTypes.MULTI_SELECTION.value,
                "options": [i.value for i in FoodGroup],
            },
            "brand": {
                "type": FrontendFilterTypes.MULTI_SELECTION.value,
                "options": result.get("brand", []),
            },
            "process-type": {
                "type": FrontendFilterTypes.MULTI_SELECTION.value,
                "options": [i.value for i in ProcessType],
            },
            "source": {
                "type": FrontendFilterTypes.SINGLE_SELECTION.value,
                "options": [i.value for i in Source],
            },
        }

        return final_filters

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
        hide_undefined_auto_products: bool = True,
        _return_sa_instance: bool = False,
    ) -> list[Product]:
        if starting_stmt is None:
            starting_stmt = select(ProductSaModel)
        if hide_undefined_auto_products and filter.get("source") is None:
            starting_stmt = starting_stmt.join(
                SourceSaModel, ProductSaModel.source
            ).where(
                or_(
                    SourceSaModel.name != "auto",
                    ProductSaModel.is_food_houses_choice.is_not(None),
                )
            )
        model_objs: list[Product] = await self._generic_repo.query(
            filter=filter,
            starting_stmt=starting_stmt,
            # sort_stmt=self.sort_stmt,
            _return_sa_instance=_return_sa_instance,
        )
        return model_objs

    async def persist(self, domain_obj: Product) -> None:
        await self._generic_repo.persist(
            domain_obj,
        )

    async def persist_all(self, domain_entities: list[Product] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
