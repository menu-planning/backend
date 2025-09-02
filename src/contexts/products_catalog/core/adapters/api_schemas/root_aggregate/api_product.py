from typing import Any

from pydantic import HttpUrl, field_validator
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate import (
    api_product_fields as fields,
)
from src.contexts.products_catalog.core.adapters.api_schemas.value_objects.api_if_food_votes import (
    ApiIsFoodVotes,
)
from src.contexts.products_catalog.core.adapters.api_schemas.value_objects.api_score import (
    ApiScore,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.product import (
    ProductSaModel,
)
from src.contexts.products_catalog.core.domain.enums import Unit
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UrlOptional,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiEntity,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import (
    ApiNutriFacts,
)
from src.logging.logger import StructlogFactory

# Initialize structured logger
logger = StructlogFactory.get_logger("products_catalog.api_schemas.api_product")


class ApiProduct(BaseApiEntity[Product, ProductSaModel]):
    """API schema for Product root aggregate.
    
    Attributes:
        source_id: Source identifier for the product.
        name: Name of the product.
        is_food: Whether the product is food.
        shopping_name: Shopping name of the product.
        store_department_name: Store department name.
        recommended_brands_and_products: Recommended brands and products.
        edible_yield: Edible yield ratio (0 < value <= 1).
        kg_per_unit: Kilograms per unit.
        liters_per_kg: Liters per kilogram.
        nutrition_group: Nutrition group.
        cooking_factor: Cooking factor.
        conservation_days: Conservation days.
        substitutes: Product substitutes.
        barcode: Product barcode.
        brand_id: Brand identifier.
        category_id: Category identifier.
        parent_category_id: Parent category identifier.
        score: Product score.
        food_group_id: Food group identifier.
        process_type_id: Process type identifier.
        nutri_facts: Nutritional facts.
        ingredients: Product ingredients.
        package_size: Package size.
        package_size_unit: Package size unit.
        image_url: Product image URL.
        json_data: Additional JSON data.
        is_food_votes: Is food votes.
        is_food_houses_choice: Houses choice for is_food.
    """

    source_id: fields.ProductSourceIdRequired
    name: fields.ProductNameRequired
    is_food: fields.ProductIsFoodOptional
    shopping_name: fields.ProductShoppingNameOptional
    store_department_name: fields.ProductStoreDepartmentNameOptional
    recommended_brands_and_products: fields.ProductRecommendedBrandsOptional
    edible_yield: fields.ProductEdibleYieldOptional
    kg_per_unit: fields.ProductKgPerUnitOptional
    liters_per_kg: fields.ProductLitersPerKgOptional
    nutrition_group: fields.ProductNutritionGroupOptional
    cooking_factor: fields.ProductCookingFactorOptional
    conservation_days: fields.ProductConservationDaysOptional
    substitutes: fields.ProductSubstitutesOptional
    barcode: fields.ProductBarcodeOptional
    brand_id: fields.ProductBrandIdOptional
    category_id: fields.ProductCategoryIdOptional
    parent_category_id: fields.ProductParentCategoryIdOptional
    score: fields.ProductScoreOptional
    food_group_id: fields.ProductFoodGroupIdOptional
    process_type_id: fields.ProductProcessTypeIdOptional
    nutri_facts: fields.ProductNutriFactsOptional
    ingredients: fields.ProductIngredientsOptional
    package_size: fields.ProductPackageSizeOptional
    package_size_unit: fields.ProductPackageSizeUnitOptional
    image_url: UrlOptional
    json_data: fields.ProductJsonDataOptional
    is_food_votes: fields.ProductIsFoodVotesOptional
    is_food_houses_choice: fields.ProductIsFoodHousesChoiceOptional

    @field_validator("edible_yield")
    @classmethod
    def check_edible_yield_range(cls, value: float | None) -> float:
        """Validate edible yield is within valid range (0, 1].
        
        Args:
            value: Edible yield value to validate.
            
        Returns:
            Validated edible yield value.
            
        Raises:
            ValidationConversionError: If value is outside valid range.
        """
        logger.debug(
            "Validating edible_yield field",
            operation="validate_edible_yield",
            value=value,
            is_none=value is None
        )

        if value is None:
            logger.debug(
                "Using default edible_yield value",
                operation="validate_edible_yield_default",
                default_value=1
            )
            return 1

        if not (0 < value <= 1):
            logger.warning(
                "Invalid edible_yield value provided",
                operation="validate_edible_yield_invalid",
                value=value,
                valid_range="0 < value <= 1"
            )
            raise ValidationConversionError(
                message="Edible yield must be > 0 and <= 1",
                schema_class=cls,
                conversion_direction="field_validation",
                source_data=value,
                validation_errors=[f"Value {value} is outside valid range (0, 1]"]
            )

        logger.debug(
            "Valid edible_yield value accepted",
            operation="validate_edible_yield_valid",
            value=value
        )
        return value

    @classmethod
    def from_domain(cls, domain_obj: Product) -> "ApiProduct":
        """Create API schema instance from domain object.
        
        Args:
            domain_obj: Domain product object.
            
        Returns:
            ApiProduct instance.
            
        Raises:
            ValidationConversionError: If conversion from domain fails.
        """
        logger.debug(
            "Converting domain Product to ApiProduct",
            operation="from_domain",
            product_id=getattr(domain_obj, 'id', None),
            product_name=getattr(domain_obj, 'name', None),
            has_score=domain_obj.score is not None,
            has_nutri_facts=domain_obj.nutri_facts is not None,
            has_is_food_votes=domain_obj.is_food_votes is not None
        )

        try:
            api_product = cls(
                id=domain_obj.id,
                source_id=domain_obj.source_id,
                name=domain_obj.name,
                is_food=domain_obj.is_food,
                shopping_name=domain_obj.shopping_name,
                store_department_name=domain_obj.store_department_name,
                recommended_brands_and_products=domain_obj.recommended_brands_and_products,
                edible_yield=domain_obj.edible_yield,
                kg_per_unit=domain_obj.kg_per_unit,
                liters_per_kg=domain_obj.liters_per_kg,
                nutrition_group=domain_obj.nutrition_group,
                cooking_factor=domain_obj.cooking_factor,
                conservation_days=domain_obj.conservation_days,
                substitutes=domain_obj.substitutes,
                barcode=domain_obj.barcode,
                brand_id=domain_obj.brand_id,
                category_id=domain_obj.category_id,
                parent_category_id=domain_obj.parent_category_id,
                score=(
                    ApiScore.from_domain(domain_obj.score) if domain_obj.score else None
                ),
                food_group_id=domain_obj.food_group_id,
                process_type_id=domain_obj.process_type_id,
                nutri_facts=(
                    ApiNutriFacts.from_domain(domain_obj.nutri_facts)
                    if domain_obj.nutri_facts
                    else None
                ),
                ingredients=domain_obj.ingredients,
                package_size=domain_obj.package_size,
                package_size_unit=(
                    Unit(domain_obj.package_size_unit)
                    if domain_obj.package_size_unit
                    else None
                ),
                image_url=(
                    HttpUrl(domain_obj.image_url) if domain_obj.image_url else None
                ),
                created_at=domain_obj.created_at,
                updated_at=domain_obj.updated_at,
                json_data=domain_obj.json_data,
                discarded=domain_obj.discarded,
                version=domain_obj.version,
                is_food_votes=(
                    ApiIsFoodVotes.from_domain(domain_obj.is_food_votes)
                    if domain_obj.is_food_votes
                    else None
                ),
                is_food_houses_choice=domain_obj.is_food_houses_choice,
            )

            logger.debug(
                "Successfully converted domain Product to ApiProduct",
                operation="from_domain_success",
                product_id=api_product.id,
                product_name=api_product.name
            )

            return api_product

        except Exception as e:
            logger.error(
                "Failed to convert domain Product to ApiProduct",
                operation="from_domain_error",
                product_id=getattr(domain_obj, 'id', None),
                product_name=getattr(domain_obj, 'name', None),
                error_type=e.__class__.__name__,
                error_message=str(e),
                has_score=domain_obj.score is not None,
                has_nutri_facts=domain_obj.nutri_facts is not None,
                has_image_url=bool(getattr(domain_obj, 'image_url', None)),
                package_size_unit=getattr(domain_obj, 'package_size_unit', None)
            )
            raise ValidationConversionError(
                message=f"Failed to build ApiProduct from domain instance: {e}",
                schema_class=cls,
                conversion_direction="domain_to_api",
                source_data=domain_obj,
                validation_errors=[str(e)]
            ) from e

    def to_domain(self) -> Product:
        """Convert API schema to domain object.
        
        Returns:
            Product domain object.
            
        Raises:
            ValidationConversionError: If conversion to domain fails.
        """
        logger.debug(
            "Converting ApiProduct to domain Product",
            operation="to_domain",
            product_id=self.id,
            product_name=self.name,
            has_score=self.score is not None,
            has_nutri_facts=self.nutri_facts is not None,
            has_is_food_votes=self.is_food_votes is not None
        )

        try:
            domain_product = Product(
                entity_id=self.id,
                source_id=self.source_id,
                name=self.name,
                is_food=self.is_food,
                shopping_name=self.shopping_name,
                store_department_name=self.store_department_name,
                recommended_brands_and_products=self.recommended_brands_and_products,
                edible_yield=self.edible_yield,
                kg_per_unit=self.kg_per_unit,
                liters_per_kg=self.liters_per_kg,
                nutrition_group=self.nutrition_group,
                cooking_factor=self.cooking_factor,
                conservation_days=self.conservation_days,
                substitutes=self.substitutes,
                barcode=self.barcode,
                brand_id=self.brand_id,
                category_id=self.category_id,
                parent_category_id=self.parent_category_id,
                score=self.score.to_domain() if self.score else None,
                food_group_id=self.food_group_id,
                process_type_id=self.process_type_id,
                nutri_facts=self.nutri_facts.to_domain() if self.nutri_facts else None,
                ingredients=self.ingredients,
                package_size=self.package_size,
                package_size_unit=(
                    self.package_size_unit.value if self.package_size_unit else None
                ),
                image_url=str(self.image_url) if self.image_url else None,
                created_at=self.created_at,
                updated_at=self.updated_at,
                json_data=self.json_data,
                discarded=self.discarded,
                version=self.version,
                is_food_votes=(
                    self.is_food_votes.to_domain() if self.is_food_votes else None
                ),
            )

            logger.debug(
                "Successfully converted ApiProduct to domain Product",
                operation="to_domain_success",
                product_id=domain_product.id,
                product_name=domain_product.name
            )

            return domain_product

        except Exception as e:
            logger.error(
                "Failed to convert ApiProduct to domain Product",
                operation="to_domain_error",
                product_id=self.id,
                product_name=self.name,
                error_type=e.__class__.__name__,
                error_message=str(e),
                has_score=self.score is not None,
                has_nutri_facts=self.nutri_facts is not None,
                has_image_url=bool(self.image_url),
                package_size_unit=self.package_size_unit.value if self.package_size_unit else None
            )
            raise ValidationConversionError(
                message=f"Failed to convert ApiProduct to domain Product: {e}",
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self,
                validation_errors=[str(e)]
            ) from e

    @classmethod
    def from_orm_model(cls, orm_model: ProductSaModel) -> "ApiProduct":
        """Convert ORM model to API schema instance.
        
        Args:
            orm_model: SQLAlchemy product model.
            
        Returns:
            ApiProduct instance.
            
        Raises:
            ValidationConversionError: If conversion from ORM fails.
        """
        logger.debug(
            "Converting ORM ProductSaModel to ApiProduct",
            operation="from_orm_model",
            product_id=getattr(orm_model, 'id', None),
            product_name=getattr(orm_model, 'name', None),
            has_score=orm_model.score is not None,
            has_nutri_facts=orm_model.nutri_facts is not None,
            has_is_food_votes=orm_model.is_food_votes is not None
        )

        try:
            api_product = cls(
                id=orm_model.id,
                source_id=orm_model.source_id,
                name=orm_model.name,
                is_food=orm_model.is_food,
                shopping_name=orm_model.shopping_name,
                store_department_name=orm_model.store_department_name,
                recommended_brands_and_products=orm_model.recommended_brands_and_products,
                edible_yield=(
                    float(orm_model.edible_yield)
                    if orm_model.edible_yield is not None
                    else None
                ),
                kg_per_unit=orm_model.kg_per_unit,
                liters_per_kg=orm_model.liters_per_kg,
                nutrition_group=orm_model.nutrition_group,
                cooking_factor=orm_model.cooking_factor,
                conservation_days=orm_model.conservation_days,
                substitutes=orm_model.substitutes,
                barcode=orm_model.barcode,
                brand_id=orm_model.brand_id,
                category_id=orm_model.category_id,
                parent_category_id=orm_model.parent_category_id,
                score=(
                    ApiScore(
                        final=orm_model.score.final_score,
                        ingredients=orm_model.score.ingredients_score,
                        nutrients=orm_model.score.nutrients_score,
                    )
                    if orm_model.score
                    else None
                ),
                food_group_id=orm_model.food_group_id,
                process_type_id=orm_model.process_type_id,
                nutri_facts=(
                    ApiNutriFacts.from_orm_model(orm_model.nutri_facts)
                    if orm_model.nutri_facts
                    else None
                ),
                ingredients=orm_model.ingredients,
                package_size=orm_model.package_size,
                package_size_unit=(
                    Unit(orm_model.package_size_unit)
                    if orm_model.package_size_unit
                    else None
                ),
                image_url=HttpUrl(orm_model.image_url) if orm_model.image_url else None,
                created_at=orm_model.created_at,
                updated_at=orm_model.updated_at,
                json_data=orm_model.json_data,
                discarded=orm_model.discarded,
                version=orm_model.version,
                is_food_votes=(
                    ApiIsFoodVotes.from_orm_model(orm_model.is_food_votes)
                    if orm_model.is_food_votes
                    else None
                ),
                is_food_houses_choice=orm_model.is_food_houses_choice,
            )

            logger.debug(
                "Successfully converted ORM ProductSaModel to ApiProduct",
                operation="from_orm_model_success",
                product_id=api_product.id,
                product_name=api_product.name
            )

            return api_product

        except Exception as e:
            logger.error(
                "Failed to convert ORM ProductSaModel to ApiProduct",
                operation="from_orm_model_error",
                product_id=getattr(orm_model, 'id', None),
                product_name=getattr(orm_model, 'name', None),
                error_type=e.__class__.__name__,
                error_message=str(e),
                has_score=orm_model.score is not None,
                has_nutri_facts=orm_model.nutri_facts is not None,
                has_image_url=bool(getattr(orm_model, 'image_url', None)),
                package_size_unit=getattr(orm_model, 'package_size_unit', None)
            )
            raise ValidationConversionError(
                message=f"Failed to convert ORM ProductSaModel to ApiProduct: {e}",
                schema_class=cls,
                conversion_direction="orm_to_api",
                source_data=orm_model,
                validation_errors=[str(e)]
            ) from e

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert API schema to ORM model kwargs.
        
        Returns:
            Dictionary of kwargs for ORM model creation.
            
        Raises:
            ValidationConversionError: If conversion to ORM kwargs fails.
        """
        logger.debug(
            "Converting ApiProduct to ORM kwargs",
            operation="to_orm_kwargs",
            product_id=self.id,
            product_name=self.name,
            has_score=self.score is not None,
            has_nutri_facts=self.nutri_facts is not None
        )

        try:
            orm_kwargs = {
                "id": self.id,
                "source_id": self.source_id,
                "name": self.name,
                "is_food": self.is_food,
                "shopping_name": self.shopping_name,
                "store_department_name": self.store_department_name,
                "recommended_brands_and_products": self.recommended_brands_and_products,
                "edible_yield": self.edible_yield,
                "kg_per_unit": self.kg_per_unit,
                "liters_per_kg": self.liters_per_kg,
                "nutrition_group": self.nutrition_group,
                "cooking_factor": self.cooking_factor,
                "conservation_days": self.conservation_days,
                "substitutes": self.substitutes,
                "barcode": self.barcode,
                "brand_id": self.brand_id,
                "category_id": self.category_id,
                "parent_category_id": self.parent_category_id,
                "final_score": self.score.final if self.score else None,
                "ingredients_score": self.score.ingredients if self.score else None,
                "nutrients_score": self.score.nutrients if self.score else None,
                "food_group_id": self.food_group_id,
                "process_type_id": self.process_type_id,
                "nutri_facts": (
                    self.nutri_facts.to_orm_kwargs() if self.nutri_facts else None
                ),
                "ingredients": self.ingredients,
                "package_size": self.package_size,
                "package_size_unit": (
                    self.package_size_unit.value if self.package_size_unit else None
                ),
                "image_url": str(self.image_url) if self.image_url else None,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "json_data": self.json_data,
                "discarded": self.discarded,
                "version": self.version,
                "is_food_houses_choice": self.is_food_houses_choice,
            }

            logger.debug(
                "Successfully converted ApiProduct to ORM kwargs",
                operation="to_orm_kwargs_success",
                product_id=self.id,
                product_name=self.name,
                kwargs_count=len(orm_kwargs)
            )

            return orm_kwargs

        except Exception as e:
            logger.error(
                "Failed to convert ApiProduct to ORM kwargs",
                operation="to_orm_kwargs_error",
                product_id=self.id,
                product_name=self.name,
                error_type=e.__class__.__name__,
                error_message=str(e)
            )
            raise ValidationConversionError(
                message=f"Failed to convert ApiProduct to ORM kwargs: {e}",
                schema_class=self.__class__,
                conversion_direction="api_to_orm",
                source_data=self,
                validation_errors=[str(e)]
            ) from e
