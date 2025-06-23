from typing import Any, Optional

from sqlalchemy import Select, case, desc, func, inspect, nulls_last, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
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
from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)
from src.contexts.seedwork.shared.adapters.repositories.repository_logger import RepositoryLogger
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
        repository_logger: Optional[RepositoryLogger] = None,
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
        logger.info(f"rows: {rows}")
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
        # Use the track_query context manager for structured logging
        async with self._repository_logger.track_query(
            operation="similarity_search", 
            entity_type="Product",
            search_term=description,
            include_barcode=include_product_with_barcode,
            limit=limit,
            filter_first_word=filter_by_first_word_partial_match
        ) as query_context:
            
            self._repository_logger.debug_query_step(
                "start_similarity_search",
                f"Starting similarity search for '{description}'",
                search_params={
                    "description": description,
                    "include_barcode": include_product_with_barcode,
                    "limit": limit,
                    "filter_first_word": filter_by_first_word_partial_match
                }
            )
            
            # Perform full name similarity search
            full_name_matches: list[tuple[Product,float]] = await self._list_similar_names_using_pg_similarity(
                description, include_product_with_barcode, limit
            )
            
            # Perform first word similarity search
            first_word_matches: list[tuple[Product,float]] = await self._list_similar_names_using_pg_similarity(
                description.split()[0], include_product_with_barcode, limit
            )
            
            # Combine and deduplicate results
            similars = list(set(full_name_matches + first_word_matches))
            
            query_context["raw_matches"] = {
                "full_name_matches": len(full_name_matches),
                "first_word_matches": len(first_word_matches),
                "combined_unique": len(similars)
            }
            
            self._repository_logger.debug_query_step(
                "similarity_ranking",
                f"Found {len(similars)} unique matches, applying ranking",
                raw_results=query_context["raw_matches"]
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
                "final_results": len(ordered_products)
            }
            
            self._repository_logger.debug_query_step(
                "similarity_search_complete",
                f"Similarity search completed: {len(ordered_products)} results",
                ranking_stats=query_context["ranking_stats"]
            )
            
            return ordered_products

    async def list_filter_options(
        self,
        *,
        filter: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        limit: int | None = None,
    ) -> dict[str, dict[str, str | list[str]]]:
        # Use the track_query context manager for structured logging
        async with self._repository_logger.track_query(
            operation="list_filter_options", 
            entity_type="Product",
            filter_count=len(filter or {}),
            has_starting_stmt=starting_stmt is not None,
            limit=limit
        ) as query_context:
            
            levels = ["parent_category", "category", "brand"]
            filter = filter or {}
            
            self._repository_logger.debug_query_step(
                "filter_options_start",
                "Starting filter options aggregation",
                levels=levels,
                initial_filter=filter
            )

            # 1) Extract any pre-selection on those three levels
            selected: dict[str, str | list[str]] = {
                lvl: filter.pop(lvl)
                for lvl in levels
                if lvl in filter
            }
            
            query_context["selected_filters"] = {
                level: len(value) if isinstance(value, (list, set)) else 1 
                for level, value in selected.items()
            }

            # 2) Your guard: category without parent is invalid
            if "category" in selected and "parent_category" not in selected:
                self._repository_logger.warn_performance_issue(
                    "invalid_filter_combination",
                    "Category selected without parent category - this is invalid",
                    category=selected['category']
                )
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
            
            self._repository_logger.debug_filter_operation(
                "Applied base filters and joins for filter options query",
                remaining_filters=len(filter),
                selected_hierarchy=selected
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
                    if isinstance(val, (list, set)):
                        q = q.where(parent_col.in_(val))
                        applied_filters += len(val)
                    else:
                        q = q.where(parent_col == val)
                        applied_filters += 1

                q = q.distinct().order_by(nulls_last(col))
                
                self._repository_logger.debug_query_step(
                    f"distinct_query_{lvl}",
                    f"Executing distinct query for {lvl}",
                    level=lvl,
                    level_index=level_idx,
                    applied_filters=applied_filters
                )
                
                rows = await self._session.execute(q)
                results = [r[0] for r in rows.scalars().all()]
                
                self._repository_logger.debug_query_step(
                    f"distinct_results_{lvl}",
                    f"Found {len(results)} distinct values for {lvl}",
                    level=lvl,
                    result_count=len(results)
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
                "categories_skipped": "parent_category" not in selected
            }
            
            self._repository_logger.debug_query_step(
                "filter_options_complete",
                "Filter options aggregation completed",
                results=query_context["aggregation_results"]
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
    ) -> list[Product] | list[ProductSaModel]:
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

    def _enhance_sqlalchemy_error(self, error: SQLAlchemyError, operation: str, product_id: Optional[str] = None) -> Exception:
        """
        Enhance SQLAlchemy errors with meaningful messages and structured logging.
        
        Args:
            error: The original SQLAlchemy error
            operation: The operation being performed (e.g., "persist", "add")
            product_id: Optional product ID for context
            
        Returns:
            Enhanced exception with better error messages
        """
        error_msg = str(error).lower()
        
        # Log the original error for debugging
        self._repository_logger.debug_conditional(
            f"SQLAlchemy error during {operation}",
            context="sql_errors",
            original_error=str(error),
            operation=operation,
            product_id=product_id
        )
        
        if isinstance(error, IntegrityError):
            if "null value in column \"source_id\"" in error_msg:
                enhanced_msg = (
                    f"Product validation failed: source_id is required but was null. "
                    f"Every product must have a valid source (manual, auto, etc.). "
                    f"Original error: {error}"
                )
                self._repository_logger.warn_performance_issue(
                    "missing_source_id",
                    "Product missing required source_id",
                    product_id=product_id,
                    operation=operation
                )
                return BadRequestException(enhanced_msg)
            
            elif "violates foreign key constraint" in error_msg:
                if "fk_products_source_id" in error_msg or "source_id" in error_msg:
                    enhanced_msg = (
                        f"Product validation failed: Invalid source_id reference. "
                        f"The specified source does not exist in the system. "
                        f"Please ensure the source exists before creating the product. "
                        f"Original error: {error}"
                    )
                    self._repository_logger.warn_performance_issue(
                        "invalid_source_reference",
                        "Product references non-existent source",
                        product_id=product_id,
                        operation=operation
                    )
                    return BadRequestException(enhanced_msg)
                    
                elif "fk_products_brand_id" in error_msg or "brand_id" in error_msg:
                    enhanced_msg = (
                        f"Product validation failed: Invalid brand_id reference. "
                        f"The specified brand does not exist in the system. "
                        f"Please ensure the brand exists before creating the product. "
                        f"Original error: {error}"
                    )
                    self._repository_logger.warn_performance_issue(
                        "invalid_brand_reference",
                        "Product references non-existent brand",
                        product_id=product_id,
                        operation=operation
                    )
                    return BadRequestException(enhanced_msg)
                    
                elif "fk_products_category_id" in error_msg or "category_id" in error_msg:
                    enhanced_msg = (
                        f"Product validation failed: Invalid category_id reference. "
                        f"The specified category does not exist in the system. "
                        f"Please ensure the category exists before creating the product. "
                        f"Original error: {error}"
                    )
                    self._repository_logger.warn_performance_issue(
                        "invalid_category_reference",
                        "Product references non-existent category",
                        product_id=product_id,
                        operation=operation
                    )
                    return BadRequestException(enhanced_msg)
                else:
                    enhanced_msg = (
                        f"Product validation failed: Invalid foreign key reference. "
                        f"One of the referenced entities (source, brand, category, etc.) does not exist. "
                        f"Original error: {error}"
                    )
                    self._repository_logger.warn_performance_issue(
                        "invalid_foreign_key",
                        "Product references non-existent entity",
                        product_id=product_id,
                        operation=operation
                    )
                    return BadRequestException(enhanced_msg)
            
            elif "duplicate key value violates unique constraint" in error_msg:
                enhanced_msg = (
                    f"Product creation failed: A product with this ID already exists. "
                    f"Product IDs must be unique. "
                    f"Original error: {error}"
                )
                self._repository_logger.warn_performance_issue(
                    "duplicate_product_id",
                    "Attempt to create product with duplicate ID",
                    product_id=product_id,
                    operation=operation
                )
                return BadRequestException(enhanced_msg)
            
            else:
                # Generic integrity error
                enhanced_msg = (
                    f"Product validation failed: Database constraint violation. "
                    f"Please check that all required fields are provided and references are valid. "
                    f"Original error: {error}"
                )
                self._repository_logger.warn_performance_issue(
                    "generic_constraint_violation",
                    "Generic database constraint violation",
                    product_id=product_id,
                    operation=operation
                )
                return BadRequestException(enhanced_msg)
        
        # For non-IntegrityError SQLAlchemy errors, log and re-raise
        self._repository_logger.warn_performance_issue(
            "sqlalchemy_error",
            f"Unexpected SQLAlchemy error during {operation}",
            error_type=type(error).__name__,
            product_id=product_id,
            operation=operation
        )
        return error

    async def persist(self, domain_obj: Product) -> None:
        """
        Persist a single product with enhanced error handling.
        
        Args:
            domain_obj: Product domain object to persist
            
        Raises:
            BadRequestException: For constraint violations with enhanced error messages
            SQLAlchemyError: For other database errors
        """
        try:
            await self._generic_repo.persist(domain_obj)
        except SQLAlchemyError as e:
            enhanced_error = self._enhance_sqlalchemy_error(e, "persist", domain_obj.id)
            raise enhanced_error

    async def persist_all(self, domain_entities: list[Product] | None = None) -> None:
        """
        Persist multiple products with enhanced error handling.
        
        Args:
            domain_entities: List of Product domain objects to persist
            
        Raises:
            BadRequestException: For constraint violations with enhanced error messages
            SQLAlchemyError: For other database errors
        """
        try:
            await self._generic_repo.persist_all(domain_entities)
        except SQLAlchemyError as e:
            # For bulk operations, we may not have a specific product ID
            product_ids = [entity.id for entity in (domain_entities or [])] if domain_entities else []
            enhanced_error = self._enhance_sqlalchemy_error(
                e, 
                "persist_all", 
                f"bulk_operation_with_{len(product_ids)}_products" if product_ids else "unknown"
            )
            raise enhanced_error
