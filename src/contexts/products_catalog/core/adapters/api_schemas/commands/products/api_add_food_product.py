from pydantic import BaseModel, field_serializer
from src.contexts.products_catalog.core.domain.commands.products import (
    AddFoodProduct,
)
from src.contexts.products_catalog.core.domain.enums import Unit
from src.contexts.products_catalog.core.domain.value_objects.score import Score
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import (
    ApiNutriFacts,
)


class ApiAddFoodProduct(BaseModel):
    """API schema for adding a new food product.

    Attributes:
        source_id: The source of the information about product.
        name: The name of the product.
        nutri_facts: The nutritional facts of the product.
        category_id: The id of the category the product is part of.
        parent_category_id: The id of the parent category the product is part of.
        ingredients: The ingredients of the product.
        food_group_id: The id of the food group the product is part of.
        process_type_id: The id of the process type the product is part of.
        package_size: The size of the package the product comes in.
        package_size_unit: The unit of the package size.
        score: The score of the product.
        brand_id: The id of the brand the product is part of.
        barcode: The barcode of the product.
        image_url: The url of the image of the product.
        json_data: The json data of the product.
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
        """Serialize package size unit to its string value.

        Args:
            unit: Unit enum to serialize.
            _info: Pydantic serialization info (unused).

        Returns:
            String value of the unit or None.
        """
        return unit.value if unit else None

    def to_domain(self) -> AddFoodProduct:
        """Convert API schema to domain command.

        Returns:
            AddFoodProduct domain command.

        Raises:
            ValidationConversionError: If conversion to domain model fails.
        """
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
        except Exception as e:
            error_msg = f"Failed to convert ApiAddFoodProduct to domain model: {e}"
            raise ValidationConversionError(
                error_msg,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
        else:
            return cmd
