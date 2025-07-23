from typing import Any, Dict
from pydantic import field_validator, HttpUrl

from src.contexts.products_catalog.core.adapters.ORM.sa_models.product import ProductSaModel
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate import api_product_fields as fields
from src.contexts.products_catalog.core.adapters.api_schemas.value_objects.api_if_food_votes import (
    ApiIsFoodVotes,
)
from src.contexts.products_catalog.core.adapters.api_schemas.value_objects.api_score import (
    ApiScore,
)
from src.contexts.products_catalog.core.domain.enums import Unit
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiEntity
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UrlOptional
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import (
    ApiNutriFacts,
)
from src.logging.logger import logger


class ApiProduct(BaseApiEntity[Product, ProductSaModel]):
    """
    A pydantic model for the Product entity.

    This model is used to validate the input and output of the API endpoints.

    It is also used to convert the domain object to and from the API model.

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
        if value is None:
            return 1
        if not (0 < value <= 1):
            raise ValueError("Edible yield must be > 0 and <= 1")
        return value

    @classmethod
    def from_domain(cls, domain_obj: Product) -> "ApiProduct":
        """Creates an instance of `ApiProduct` from a domain model object."""
        try:
            return cls(
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
                image_url=HttpUrl(domain_obj.image_url) if domain_obj.image_url else None,
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
        except Exception as e:
            logger.error(f"Failed to build ApiProduct from domain instance: {e}")
            raise ValueError(f"Failed to build ApiProduct from domain instance: {e}")

    def to_domain(self) -> Product:
        """Convert the API schema instance to a domain object."""
        return Product(
            id=self.id,
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

    @classmethod
    def from_orm_model(cls, orm_model: ProductSaModel) -> "ApiProduct":
        """Convert an ORM model to an API schema instance."""
        return cls(
            id=orm_model.id,
            source_id=orm_model.source_id,
            name=orm_model.name,
            is_food=orm_model.is_food,
            shopping_name=orm_model.shopping_name,
            store_department_name=orm_model.store_department_name,
            recommended_brands_and_products=orm_model.recommended_brands_and_products,
            edible_yield=float(orm_model.edible_yield) if orm_model.edible_yield is not None else None,
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
                ) if orm_model.score else None
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

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Convert the API schema instance to ORM model kwargs."""
        return {
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
            "nutri_facts": self.nutri_facts.to_orm_kwargs() if self.nutri_facts else None,
            "ingredients": self.ingredients,
            "package_size": self.package_size,
            "package_size_unit": self.package_size_unit.value if self.package_size_unit else None,
            "image_url": str(self.image_url) if self.image_url else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "json_data": self.json_data,
            "discarded": self.discarded,
            "version": self.version,
            "is_food_houses_choice": self.is_food_houses_choice,
        }
