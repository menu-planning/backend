from typing import Any

from sqlalchemy import Select, case, desc, func, inspect, nulls_last, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from src.contexts.products_catalog.core.adapters.name_search import SimilarityRanking
from src.contexts.products_catalog.core.adapters.ORM.mappers.product_mapper import (
    ProductMapper,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models import (
    BrandSaModel,
    CategorySaModel,
    FoodGroupSaModel,
    ParentCategorySaModel,
    ProcessTypeSaModel,
    ProductSaModel,
    SourceSaModel,
)
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.products_catalog.core.domain.enums import FrontendFilterTypes
from src.contexts.seedwork.shared.adapters.seedwork_repository import (
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

    async def list_filter_options(
        self,
        *,
        filter: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        limit: int | None = None,
    ) -> dict[str, dict[str, str | list[str]]]:
        levels = ["parent_category", "category", "brand"]
        filter = filter or {}

        # 1) Extract any pre-selection on those three levels
        selected: dict[str, str | list[str]] = {
            lvl: filter.pop(lvl)
            for lvl in levels
            if lvl in filter
        }

        # 2) Your guard: category without parent is invalid
        if "category" in selected and "parent_category" not in selected:
            raise BadRequestException(
                f"Category selected without parent category. "
                f"Category={selected['category']}"
            )

        # 3) Build the base SELECT with one labeled column per level
        cols = [getattr(self.sa_model_type, lvl).label(lvl) for lvl in levels]
        stmt = select(*cols) if starting_stmt is None else starting_stmt

        # 4) Apply all the other (non-hierarchy) filters + paging
        stmt = self._generic_repo.setup_skip_and_limit(stmt, filter, limit)
        # reuse your existing join+filter logic:
        stmt = self._apply_join_and_filters(stmt, filter)

        # helper to get distinct values for any single level,
        # applying any upstream selections
        async def distinct_for(level_idx: int) -> list[str]:
            lvl = levels[level_idx]
            alias = stmt.alias()
            col = getattr(alias.c, lvl)
            q = select(col).where(col.is_not(None))

            # if there's a selected parent or category, apply it
            for parent_lvl in levels[:level_idx]:
                val = selected.get(parent_lvl)
                parent_col = getattr(alias.c, parent_lvl)
                if val is None:
                    continue
                if isinstance(val, (list, set)):
                    q = q.where(parent_col.in_(val))
                else:
                    q = q.where(parent_col == val)

            q = q.distinct().order_by(nulls_last(col))
            rows = await self._session.execute(q)
            return [r[0] for r in rows.scalars().all()]

        # 5) Build your outputs, respecting your "only if" rules
        parent_opts = await distinct_for(0)
        if "parent_category" in selected:
            category_opts = await distinct_for(1)
        else:
            category_opts: list[str] = []

        # brands are always shown, but filtered by parent→category if given
        brand_opts = await distinct_for(2)

        return {
            "sort": {
                "type": FrontendFilterTypes.SORT.value,
                "options": list(self._generic_repo.inspector.columns.keys()),
            },
            "parent-category": {
                "type": FrontendFilterTypes.MULTI_SELECTION.value,
                "options": parent_opts,
            },
            "category": {
                "type": FrontendFilterTypes.MULTI_SELECTION.value,
                "options": category_opts,
            },
            "brand": {
                "type": FrontendFilterTypes.MULTI_SELECTION.value,
                "options": brand_opts,
            },
        }
    
    def _apply_join_and_filters(
        self,
        stmt: Select,
        filter: dict[str, Any]
    ) -> Select:
        """
        Apply the joins and WHERE filters defined by filter_to_column_mappers.
        """
        already_joined: set[type] = set()

        for mapper in self.filter_to_column_mappers or []:
            # 1) pull out just the filters meant for this mapper's SA model
            sa_filters = self._generic_repo.get_filters_for_sa_model_type(
                filter=filter, 
                sa_model_type=mapper.sa_model_type
            )

            # 2) if there are any filters and join instructions, join once
            if sa_filters and mapper.join_target_and_on_clause:
                for join_target, on_clause in mapper.join_target_and_on_clause:
                    if join_target not in already_joined:
                        stmt = stmt.join(join_target, on_clause)
                        already_joined.add(join_target)

            # 3) apply all the WHERE clauses for this model
            stmt = self._generic_repo.filter_stmt(
                stmt=stmt,
                filter=sa_filters,
                sa_model_type=mapper.sa_model_type,
                mapping=mapper.filter_key_to_column_name,
            )

        return stmt

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
