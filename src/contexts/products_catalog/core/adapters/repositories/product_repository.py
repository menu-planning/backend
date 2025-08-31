from typing import Any, ClassVar

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
from src.contexts.products_catalog.core.domain.enums import FrontendFilterTypes
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.seedwork.shared.adapters.repositories.repository_logger import (
    RepositoryLogger,
)
from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestError


_source_sort_order = ["manual", "tbca", "taco", "private", "gs1", "auto"]


class ProductRepo(CompositeRepository[Product, ProductSaModel]):
    filter_to_column_mappers: ClassVar[list[FilterColumnMapper]] = [
        FilterColumnMapper(
            sa_model_type=ProductSaModel,
            filter_key_to_column_name={
                "id": "id",
                "name": "name",
                "barcode": "barcode",
                "is_food": "is_food",
                "created_at": "created_at",
                "updated_at": "updated_at",
                "discarded": "discarded",
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
        repository_logger: RepositoryLogger | None = None,
    ):
        self._session = db_session

        # Create default logger if none provided
        if repository_logger is None:
            repository_logger = RepositoryLogger.create_logger("ProductRepository")

        self._repository_logger = repository_logger

        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=ProductMapper,
            domain_model_type=Product,
            sa_model_type=ProductSaModel,
            filter_to_column_mappers=ProductRepo.filter_to_column_mappers,
            repository_logger=self._repository_logger,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Product):
        await self._generic_repo.add(entity)

    async def get(self, entity_id: str) -> Product:
        return await self._generic_repo.get(entity_id)

    async def get_sa_instance(self, entity_id: str) -> ProductSaModel:
        return await self._generic_repo.get_sa_instance(entity_id)

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
            and clean_sort_name in inspector.columns
            and "source" not in sort  # source is a enum
        ):
            source_alias = aliased(SourceSaModel)
            try:
                # Tries to sort by source in the case of equality on other fields
                source_order = case(
                    {
                        entity_id: number
                        for number, entity_id in enumerate(_source_sort_order)
                    },
                    value=source_alias.name,
                )
                stmt = stmt.join(source_alias, sa_model_type.source).order_by(
                    nulls_last(source_order)
                )
            except Exception:
                pass
        elif "source" in sort and "source" in inspector.columns:
            source_alias = aliased(SourceSaModel)
            try:
                if sort.startswith("-"):
                    _whens = {
                        entity_id: number
                        for number, entity_id in enumerate(_source_sort_order[::-1])
                    }
                else:
                    _whens = {
                        entity_id: number
                        for number, entity_id in enumerate(_source_sort_order)
                    }
                source_order = case(_whens, value=source_alias.name)
                stmt = stmt.join(source_alias, sa_model_type.source).order_by(
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
        *,
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
            stmt.where(
                ProductSaModel.is_food == True, ProductSaModel.discarded == False
            )
            .order_by(nulls_last(desc("sim_score")))
            .limit(limit)
        )

        sa_objs = await self._session.execute(stmt)
        rows = sa_objs.all()

        self._repository_logger.debug_query_step(
            "similarity_raw_results",
            f"Retrieved {len(rows)} similarity matches from database",
            result_count=len(rows),
            search_term=description,
            include_barcode=include_product_with_barcode,
        )
        
        out = []
        mapping_errors = 0

        for idx, (sa, score) in enumerate(rows, start=1):
            # Map to domain with error tracking
            try:
                prod = self.data_mapper.map_sa_to_domain(sa)
                out.append((prod, score))
                
                # Only log individual mapping success in very verbose mode
                if self._repository_logger.verbose_performance:
                    self._repository_logger.debug_query_step(
                        "similarity_mapping_success",
                        f"Mapped product {idx}/{len(rows)}",
                        product_id=sa.id,
                        similarity_score=round(score, 3),
                    )
            except Exception as e:
                mapping_errors += 1
                self._repository_logger.logger.error(
                    "Failed to map similarity search result to domain model",
                    product_id=sa.id,
                    product_name=getattr(sa, 'name', 'unknown'),
                    row_index=idx,
                    total_rows=len(rows),
                    error_type=type(e).__name__,
                    error_message=str(e),
                    exc_info=True,
                )
                continue

        if mapping_errors > 0:
            self._repository_logger.warn_performance_issue(
                "similarity_mapping_errors",
                f"Encountered {mapping_errors} mapping errors during similarity search",
                mapping_errors=mapping_errors,
                total_results=len(rows),
                success_rate=round((len(rows) - mapping_errors) / len(rows) * 100, 1) if rows else 0,
            )

        return out

    async def list_top_similar_names(
        self,
        description: str,
        *,
        limit: int = 20,
        include_product_with_barcode: bool = False,
        filter_by_first_word_partial_match: bool = False,
    ) -> list[Product]:
        # Use the track_query context manager for structured logging
        async with self._repository_logger.track_query(
            operation="similarity_search",
            entity_type="Product",
            search_term=description,
            include_barcode=include_product_with_barcode,
            limit=limit,
            filter_first_word=filter_by_first_word_partial_match,
        ) as query_context:

            # Perform full name similarity search
            full_name_matches: list[tuple[Product, float]] = (
                await self._list_similar_names_using_pg_similarity(
                    description=description,
                    include_product_with_barcode=include_product_with_barcode,
                    limit=limit,
                )
            )

            # Perform first word similarity search
            first_word_matches: list[tuple[Product, float]] = (
                await self._list_similar_names_using_pg_similarity(
                    description=description.split()[0],
                    include_product_with_barcode=include_product_with_barcode,
                    limit=limit,
                )
            )

            # Combine and deduplicate results
            similars = list(set(full_name_matches + first_word_matches))

            query_context["raw_matches"] = {
                "full_name_matches": len(full_name_matches),
                "first_word_matches": len(first_word_matches),
                "combined_unique": len(similars),
            }

            self._repository_logger.debug_query_step(
                "similarity_ranking",
                f"Found {len(similars)} unique matches, applying ranking",
                raw_results=query_context["raw_matches"],
            )

            # Apply similarity ranking
            ranking = SimilarityRanking(
                description, [(i[0].name, i[1]) for i in similars]
            ).ranking

            if len(ranking) == 0:
                query_context["result_count"] = 0
                self._repository_logger.debug_query_step(
                    "no_results",
                    "No matches found after ranking",
                )
                return []

            # Apply filtering logic
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

            # Order products based on ranking
            ordered_products: list[Product] = []
            for description_name in result[:limit]:
                for product in [i[0] for i in similars]:
                    if product.name == description_name:
                        ordered_products.append(product)
                        break  # Stop once you find the match to avoid duplicates

            query_context["result_count"] = len(ordered_products)
            query_context["ranking_stats"] = {
                "total_ranked": len(ranking),
                "after_filtering": len(result),
                "final_results": len(ordered_products),
            }

            self._repository_logger.debug_query_step(
                "similarity_search_complete",
                f"Similarity search completed: {len(ordered_products)} results",
                ranking_stats=query_context["ranking_stats"],
            )

            return ordered_products

    async def list_filter_options(
        self,
        *,
        filters: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        limit: int | None = None,
    ) -> dict[str, dict[str, str | list[str]]]:
        filters = filters or {}
        # Use the track_query context manager for structured logging
        async with self._repository_logger.track_query(
            operation="list_filter_options",
            entity_type="Product",
            filter_count=len(filters or {}),
            has_starting_stmt=starting_stmt is not None,
            limit=limit,
        ) as query_context:

            levels = ["parent_category", "category", "brand"]
            filters = filters or {}

            # 1) Extract any pre-selection on those three levels
            selected: dict[str, str | list[str]] = {
                lvl: filters.pop(lvl) for lvl in levels if lvl in filters
            }

            query_context["selected_filters"] = {
                level: len(value) if isinstance(value, list | set) else 1
                for level, value in selected.items()
            }

            # 2) Your guard: category without parent is invalid
            if "category" in selected and "parent_category" not in selected:
                self._repository_logger.warn_performance_issue(
                    "invalid_filter_combination",
                    "Category selected without parent category - this is invalid",
                    category=selected["category"],
                )
                error_msg = (
                    f"Category selected without parent category. "
                    f"Category={selected['category']}"
                )
                raise BadRequestError(error_msg)

            # 3) Build the base SELECT with one labeled column per level
            cols = [getattr(self.sa_model_type, lvl).label(lvl) for lvl in levels]
            stmt = select(*cols) if starting_stmt is None else starting_stmt

            # 4) Apply all the other (non-hierarchy) filters + paging
            stmt = self._generic_repo.setup_skip_and_limit(stmt, filters, limit)
            # reuse your existing join+filter logic:
            stmt = self._apply_join_and_filters(stmt, filters)

            self._repository_logger.debug_filter_operation(
                "Applied base filters and joins for filter options query",
                remaining_filters=len(filters),
                selected_hierarchy=selected,
            )

            # helper to get distinct values for any single level,
            # applying any upstream selections
            async def distinct_for(level_idx: int) -> list[str]:
                lvl = levels[level_idx]
                alias = stmt.alias()
                col = getattr(alias.c, lvl)
                q = select(col).where(col.is_not(None))

                # if there's a selected parent or category, apply it
                applied_filters = 0
                for parent_lvl in levels[:level_idx]:
                    val = selected.get(parent_lvl)
                    parent_col = getattr(alias.c, parent_lvl)
                    if val is None:
                        continue
                    if isinstance(val, list | set):
                        q = q.where(parent_col.in_(val))
                        applied_filters += len(val)
                    else:
                        q = q.where(parent_col == val)
                        applied_filters += 1

                q = q.distinct().order_by(nulls_last(col))

                # Only log individual distinct queries in verbose mode
                if self._repository_logger.verbose_performance:
                    self._repository_logger.debug_query_step(
                        f"distinct_query_{lvl}",
                        f"Executing distinct query for {lvl}",
                        level=lvl,
                        applied_filters=applied_filters,
                    )

                rows = await self._session.execute(q)
                results = [r[0] for r in rows.scalars().all()]

                # Always log results count as it's useful for debugging filter issues
                self._repository_logger.debug_query_step(
                    f"distinct_results_{lvl}",
                    f"Found {len(results)} distinct values for {lvl}",
                    level=lvl,
                    result_count=len(results),
                )

                return results

            # 5) Build your outputs, respecting your "only if" rules
            parent_opts = await distinct_for(0)
            if "parent_category" in selected:
                category_opts = await distinct_for(1)
            else:
                category_opts: list[str] = []

            # brands are always shown, but filtered by parent→category if given
            brand_opts = await distinct_for(2)

            query_context["aggregation_results"] = {
                "parent_categories": len(parent_opts),
                "categories": len(category_opts),
                "brands": len(brand_opts),
                "categories_skipped": "parent_category" not in selected,
            }

            self._repository_logger.debug_query_step(
                "filter_options_complete",
                "Filter options aggregation completed",
                results=query_context["aggregation_results"],
            )

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

    def _apply_join_and_filters(self, stmt: Select, filters: dict[str, Any]) -> Select:
        """
        Apply the joins and WHERE filters defined by filter_to_column_mappers.
        """
        already_joined: set[type] = set()

        for mapper in self.filter_to_column_mappers or []:
            # 1) pull out just the filters meant for this mapper's SA model
            sa_filters = self._generic_repo.get_filters_for_sa_model_type(
                filters=filters, sa_model_type=mapper.sa_model_type
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
                filters=sa_filters,
                sa_model_type=mapper.sa_model_type,
                mapping=mapper.filter_key_to_column_name,
            )

        return stmt

    async def query(
        self,
        *,
        filters: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        hide_undefined_auto_products: bool = True,
        _return_sa_instance: bool = False,
    ) -> list[Product]:
        filters = filters or {}
        async with self._repository_logger.track_query(
            operation="query",
            entity_type="Product",
            filter_count=len(filters),
            has_starting_stmt=starting_stmt is not None,
            hide_undefined_auto_products=hide_undefined_auto_products,
        ) as query_context:

            if starting_stmt is None:
                starting_stmt = select(ProductSaModel)

            if hide_undefined_auto_products and filters.get("source") is None:
                starting_stmt = starting_stmt.join(
                    SourceSaModel, ProductSaModel.source
                ).where(
                    or_(
                        SourceSaModel.name != "auto",
                        ProductSaModel.is_food_houses_choice.is_not(None),
                    )
                )
                query_context["auto_products_filter_applied"] = True

                self._repository_logger.debug_filter_operation(
                    "Applied auto products filter - hiding undefined auto products",
                    auto_filter_applied=True,
                )

            model_objs: list[Product] = await self._generic_repo.query(
                filters=filters,
                starting_stmt=starting_stmt,
                # TODO: Uncomment sort_stmt to enable custom source sorting logic
                # The ProductRepo.sort_stmt method contains important business logic for
                # sorting by "source" with priority order: ["manual", "tbca", "taco", "private", "gs1", "auto"]
                # Currently this custom sorting is not being applied.
                # sort_stmt=self.sort_stmt,
                _return_sa_instance=_return_sa_instance,
            )

            query_context["result_count"] = len(model_objs)

            self._repository_logger.debug_query_step(
                "product_query_complete",
                f"Product query completed: {len(model_objs)} results",
                result_summary={
                    "count": len(model_objs),
                    "return_type": "SqlAlchemy" if _return_sa_instance else "Domain",
                },
            )

            return model_objs

    async def persist(self, domain_obj: Product) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[Product] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
