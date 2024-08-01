from pydantic import UUID4, BaseModel, Field, field_serializer
from src.contexts.products_catalog.shared.adapters.api_schemas.value_objects.score import (
    ApiScore,
)
from src.contexts.products_catalog.shared.domain.entities import Product
from src.contexts.products_catalog.shared.domain.enums import Unit
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.nutri_facts import (
    ApiNutriFacts,
)


class ApiProduct(BaseModel):
    """
    A pydantic model for the Product entity.

    This model is used to validate the input and output of the API endpoints.

    It is also used to convert the domain object to and from the API model.

    """

    id: str
    source_id: str
    name: str
    is_food: bool
    barcode: str | None = None
    brand_id: str | None = None
    category_id: str | None = None
    parent_category_id: str | None = None
    score: ApiScore | None = None
    food_group_id: str | None = None
    process_type_id: str | None = None
    diet_types_ids: list[str] = Field(default_factory=list)
    nutri_facts: ApiNutriFacts | None = None
    ingredients: str | None = None
    package_size: float | None = None
    package_size_unit: Unit | None = None
    image_url: str | None = None
    is_food_houses_choice: bool | None = None

    @field_serializer("package_size_unit")
    def serialize_package_size_unit(self, unit: Unit, _info):
        return unit.value if unit else None

    @classmethod
    def from_domain(cls, domain_obj: Product) -> "ApiProduct":
        return cls(
            id=domain_obj.id,
            source_id=domain_obj.source_id,
            name=domain_obj.name,
            is_food=domain_obj.is_food,
            barcode=domain_obj.barcode,
            brand_id=domain_obj.brand_id,
            category_id=domain_obj.category_id,
            parent_category_id=domain_obj.parent_category_id,
            score=ApiScore.from_domain(domain_obj.score) if domain_obj.score else None,
            food_group_id=domain_obj.food_group_id,
            process_type_id=domain_obj.process_type_id,
            diet_types_ids=domain_obj.diet_types_ids,
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
            is_food_houses_choice=domain_obj.is_food_houses_choice,
        )

    def to_domain(self) -> Product:
        return Product(
            id=self.id,
            source_id=self.source_id,
            name=self.name,
            is_food=self.is_food,
            barcode=self.barcode,
            brand_id=self.brand_id,
            category_id=self.category_id,
            parent_category_id=self.parent_category_id,
            score=self.score.to_domain() if self.score else None,
            food_group_id=self.food_group_id,
            process_type_id=self.process_type_id,
            diet_types_ids=self.diet_types_ids,
            nutri_facts=self.nutri_facts.to_domain() if self.nutri_facts else None,
            ingredients=self.ingredients,
            package_size=self.package_size,
            package_size_unit=(
                self.package_size_unit.value if self.package_size_unit else None
            ),
            image_url=self.image_url,
        )
