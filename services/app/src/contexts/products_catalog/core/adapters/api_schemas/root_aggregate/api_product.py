from pydantic import BaseModel, field_serializer, field_validator

from src.contexts.products_catalog.core.adapters.api_schemas.value_objects.api_if_food_votes import (
    ApiIsFoodVotes,
)
from src.contexts.products_catalog.core.adapters.api_schemas.value_objects.api_score import (
    ApiScore,
)
from src.contexts.products_catalog.core.domain.enums import Unit
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.seedwork.shared.adapters.api_schemas.fields import CreatedAtValue
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_facts import (
    ApiNutriFacts,
)
from src.logging.logger import logger


class ApiProduct(BaseModel):
    """
    A pydantic model for the Product entity.

    This model is used to validate the input and output of the API endpoints.

    It is also used to convert the domain object to and from the API model.

    """

    id: str
    source_id: str
    name: str
    is_food: bool | None = None
    shopping_name: str | None = None
    store_department_name: str | None = None
    recommended_brands_and_products: str | None = None
    edible_yield: float | None = None
    kg_per_unit: float | None = None
    liters_per_kg: float | None = None
    nutrition_group: str | None = None
    cooking_factor: float | None = None
    conservation_days: int | None = None
    substitutes: str | None = None
    barcode: str | None = None
    brand_id: str | None = None
    category_id: str | None = None
    parent_category_id: str | None = None
    score: ApiScore | None = None
    food_group_id: str | None = None
    process_type_id: str | None = None
    nutri_facts: ApiNutriFacts | None = None
    ingredients: str | None = None
    package_size: float | None = None
    package_size_unit: Unit | None = None
    image_url: str | None = None
    created_at: CreatedAtValue | None = None
    updated_at: CreatedAtValue | None = None
    json_data: str | None = None
    discarded: bool = False
    version: int = 1
    is_food_votes: ApiIsFoodVotes | None = None
    is_food_houses_choice: bool | None = None

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        for key, value in data.items():
            if isinstance(value, set):
                data[key] = list(value)
        return data
    
    @field_validator("edible_yield")
    def check_edible_yield_range(cls, value: float | None) -> float:
        if value is None:
            return 1
        if not (0 < value <= 1):
            raise ValueError("Edible yield must be > 0 and <= 1")
        return value

    @field_serializer("package_size_unit")
    def serialize_package_size_unit(self, unit: Unit, _info):
        return unit.value if unit else None

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
                image_url=domain_obj.image_url,
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
            image_url=self.image_url,
            created_at=self.created_at,
            updated_at=self.updated_at,
            json_data=self.json_data,
            discarded=self.discarded,
            version=self.version,
            is_food_votes=(
                self.is_food_votes.to_domain() if self.is_food_votes else None
            ),
        )
