import cattrs
from attrs import asdict
from pydantic import BaseModel

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_value import (
    ApiNutriValue,
)
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


class ApiNutriFacts(BaseModel, frozen=True):
    """
    A Pydantic model representing and validating the nutritional facts
    of a food item.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Each attribute in this class represents a specific nutritional element,
    characterized by an `ApiNutriValue` object. These attributes include
    macro-nutrients like 'calories', 'protein', 'carbohydrate', and 'fats'
    (saturated, trans, mono- and polyunsaturated), as well as micro-nutrients
    like vitamins ('vitamin_a', 'vitamin_b1', etc.), minerals ('calcium',
    'iron', etc.), and other dietary components ('fiber', 'sugar', etc.).

    Attributes:
        All attributes are of type `ApiNutriValue` and include but are not
        limited to:
            - calories
            - protein
            - carbohydrate
            - total_fat
            - saturated_fat
            - ... (and so on for each nutritional element)

    Methods:
        from_domain(domain_obj: NutriFacts | None) -> "ApiNutriFacts":
            Creates an instance of `ApiNutriFacts` from a domain model object.
        to_domain() -> NutriFacts:
            Converts the instance to a domain model object.

    Raises:
        ValueError: If the instance cannot be converted to a domain model or
            if it this class cannot be instantiated from a domain model.
        ValidationError: If the instance is invalid.

    Note:
        The class handles a comprehensive list of nutritional elements.
        Consult the attribute definitions for details on each specific nutrient.
    """

    calories: ApiNutriValue
    protein: ApiNutriValue
    carbohydrate: ApiNutriValue
    total_fat: ApiNutriValue
    saturated_fat: ApiNutriValue
    trans_fat: ApiNutriValue
    dietary_fiber: ApiNutriValue
    sodium: ApiNutriValue
    arachidonic_acid: ApiNutriValue
    ashes: ApiNutriValue
    dha: ApiNutriValue
    epa: ApiNutriValue
    sugar: ApiNutriValue
    starch: ApiNutriValue
    biotin: ApiNutriValue
    boro: ApiNutriValue
    caffeine: ApiNutriValue
    calcium: ApiNutriValue
    chlorine: ApiNutriValue
    copper: ApiNutriValue
    cholesterol: ApiNutriValue
    choline: ApiNutriValue
    chrome: ApiNutriValue
    dextrose: ApiNutriValue
    sulfur: ApiNutriValue
    phenylalanine: ApiNutriValue
    iron: ApiNutriValue
    insoluble_fiber: ApiNutriValue
    soluble_fiber: ApiNutriValue
    fluor: ApiNutriValue
    phosphorus: ApiNutriValue
    fructo_oligosaccharides: ApiNutriValue
    fructose: ApiNutriValue
    galacto_oligosaccharides: ApiNutriValue
    galactose: ApiNutriValue
    glucose: ApiNutriValue
    glucoronolactone: ApiNutriValue
    monounsaturated_fat: ApiNutriValue
    polyunsaturated_fat: ApiNutriValue
    guarana: ApiNutriValue
    inositol: ApiNutriValue
    inulin: ApiNutriValue
    iodine: ApiNutriValue
    l_carnitine: ApiNutriValue
    l_methionine: ApiNutriValue
    lactose: ApiNutriValue
    magnesium: ApiNutriValue
    maltose: ApiNutriValue
    manganese: ApiNutriValue
    molybdenum: ApiNutriValue
    linolenic_acid: ApiNutriValue
    linoleic_acid: ApiNutriValue
    omega_7: ApiNutriValue
    omega_9: ApiNutriValue
    oleic_acid: ApiNutriValue
    other_carbo: ApiNutriValue
    polydextrose: ApiNutriValue
    polyols: ApiNutriValue
    potassium: ApiNutriValue
    sacarose: ApiNutriValue
    selenium: ApiNutriValue
    silicon: ApiNutriValue
    sorbitol: ApiNutriValue
    sucralose: ApiNutriValue
    taurine: ApiNutriValue
    vitamin_a: ApiNutriValue
    vitamin_b1: ApiNutriValue
    vitamin_b2: ApiNutriValue
    vitamin_b3: ApiNutriValue
    vitamin_b5: ApiNutriValue
    vitamin_b6: ApiNutriValue
    folic_acid: ApiNutriValue
    vitamin_b12: ApiNutriValue
    vitamin_c: ApiNutriValue
    vitamin_d: ApiNutriValue
    vitamin_e: ApiNutriValue
    vitamin_k: ApiNutriValue
    zinc: ApiNutriValue
    retinol: ApiNutriValue
    thiamine: ApiNutriValue
    riboflavin: ApiNutriValue
    pyridoxine: ApiNutriValue
    niacin: ApiNutriValue

    @classmethod
    def from_domain(cls, domain_obj: NutriFacts | None) -> "ApiNutriFacts":
        """Creates an instance of `ApiNutriFacts` from a domain model object."""
        try:
            return cls(**asdict(domain_obj)) if domain_obj else None
        except Exception as e:
            raise ValueError(f"Failed to build ApiNutriFacts from domain instance: {e}")

    def to_domain(self) -> NutriFacts:
        """Converts the instance to a domain model object."""
        try:
            return cattrs.structure(self.model_dump(), NutriFacts)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiNutriFacts to domain model: {e}")
