from pydantic import BaseModel, field_serializer
from src.contexts.products_catalog.core.domain.commands.products.add_food_product import (
    AddFoodProduct,
)
from src.contexts.products_catalog.core.domain.enums import Unit
from src.contexts.products_catalog.core.domain.value_objects.score import Score
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_facts import (
    ApiNutriFacts,
)
from src.logging.logger import logger


class ApiAddFoodProduct(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to add a new food product via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        source_id (str): The source of the information about product.
        name (str): The name of the product.
        nutri_facts (ApiNutriFacts): The nutritional facts of the product.
        category_id (str): The id of the category the product id part of.
        parent_category_id (str): The id of the parent category the product is part of.
        ingredients (str): The ingredients of the product.
        food_group_id (str): The id of the food group the product is part of.
        process_type_id (str): The id of the process type the product is part of.
        package_size (float): The size of the package the product comes in.
        package_size_unit (ApiUnit): The unit of the package size.
        score (dict): The score of the product.
        brand_id (str): The id of the brand the product is part of.
        barcode (str): The barcode of the product.
        image_url (str): The url of the image of the product.
        json_data (str): The json data of the product.

        Raises:
            ValueError: If the conversion to domain model fails.

    """

    source_id: str
    name: str
    nutri_facts: ApiNutriFacts
    category_id: str | None = None
    parent_category_id: str | None = None
    ingredients: str | None = None
    food_group_id: str | None = None
    process_type_id: str | None = None
    package_size: float | None = None
    package_size_unit: Unit | None = None
    score: dict | None = None
    brand_id: str | None = None
    barcode: str | None = None
    image_url: str | None = None
    json_data: str | None = None

    @field_serializer("package_size_unit")
    def serialize_package_size_unit(self, unit: Unit, _info):
        return unit.value if unit else None

    def to_domain(self) -> AddFoodProduct:
        """Converts the instance to a domain model object for adding a food product."""
        try:
            cmd = AddFoodProduct(
                source_id=self.source_id,
                name=self.name,
                nutri_facts=self.nutri_facts.to_domain(),
                category_id=self.category_id,
                parent_category_id=self.parent_category_id,
                ingredients=self.ingredients,
                food_group_id=self.food_group_id,
                process_type_id=self.process_type_id,
                package_size=self.package_size,
                package_size_unit=self.package_size_unit,
                score=Score(**self.score) if self.score else None,
                brand_id=self.brand_id,
                barcode=self.barcode,
                image_url=self.image_url,
                json_data=self.json_data,
            )
            return cmd
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiAddFoodProduct to domain model: {e}"
            )
