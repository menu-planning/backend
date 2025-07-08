from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiValueObject
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import NutriFactsSaModel
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_value import ApiNutriValue
from src.db.base import SaBase
from typing import Annotated
from pydantic import BeforeValidator, Field
from src.contexts.shared_kernel.domain.enums import MeasureUnit

def convert_to_api_nutri_value_or_float(value: float | int | ApiNutriValue | dict | None) -> float | ApiNutriValue:
    """Convert a float or ApiNutriValue to a NutriValue."""
    if isinstance(value, int):
        return float(value)
    elif isinstance(value, ApiNutriValue):
        return value
    elif isinstance(value, dict):
        if value.get("value") is not None and value.get("unit") is not None:
            return ApiNutriValue(value=value["value"], unit= MeasureUnit(value["unit"]))
        elif value.get("value") is not None and value.get("unit") is None:
            return float(value.get("value")) # type: ignore
        else:
            return 0.0
    elif isinstance(value, float):
        return value
    return 0.0

NutriValueAnnotation = Annotated[
    float | ApiNutriValue,
    Field(default=0.0),
    BeforeValidator(convert_to_api_nutri_value_or_float),
]

class ApiNutriFacts(BaseApiValueObject[NutriFacts, SaBase]):
    """
    A Pydantic model representing and validating the nutritional facts
    of a food item.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Each nutrient is represented by an ApiNutriValue instance that contains
    both the value and the appropriate unit for that nutrient.
    """

    calories: NutriValueAnnotation
    protein: NutriValueAnnotation
    carbohydrate: NutriValueAnnotation
    total_fat: NutriValueAnnotation
    saturated_fat: NutriValueAnnotation
    trans_fat: NutriValueAnnotation
    dietary_fiber: NutriValueAnnotation
    sodium: NutriValueAnnotation
    arachidonic_acid: NutriValueAnnotation
    ashes: NutriValueAnnotation
    dha: NutriValueAnnotation
    epa: NutriValueAnnotation
    sugar: NutriValueAnnotation
    starch: NutriValueAnnotation
    biotin: NutriValueAnnotation
    boro: NutriValueAnnotation
    caffeine: NutriValueAnnotation
    calcium: NutriValueAnnotation
    chlorine: NutriValueAnnotation
    copper: NutriValueAnnotation
    cholesterol: NutriValueAnnotation
    choline: NutriValueAnnotation
    chrome: NutriValueAnnotation
    dextrose: NutriValueAnnotation
    sulfur: NutriValueAnnotation
    phenylalanine: NutriValueAnnotation
    iron: NutriValueAnnotation
    insoluble_fiber: NutriValueAnnotation
    soluble_fiber: NutriValueAnnotation
    fluor: NutriValueAnnotation
    phosphorus: NutriValueAnnotation
    fructo_oligosaccharides: NutriValueAnnotation
    fructose: NutriValueAnnotation
    galacto_oligosaccharides: NutriValueAnnotation
    galactose: NutriValueAnnotation
    glucose: NutriValueAnnotation
    glucoronolactone: NutriValueAnnotation
    monounsaturated_fat: NutriValueAnnotation
    polyunsaturated_fat: NutriValueAnnotation
    guarana: NutriValueAnnotation
    inositol: NutriValueAnnotation
    inulin: NutriValueAnnotation
    iodine: NutriValueAnnotation
    l_carnitine: NutriValueAnnotation
    l_methionine: NutriValueAnnotation
    lactose: NutriValueAnnotation
    magnesium: NutriValueAnnotation
    maltose: NutriValueAnnotation
    manganese: NutriValueAnnotation
    molybdenum: NutriValueAnnotation
    linolenic_acid: NutriValueAnnotation
    linoleic_acid: NutriValueAnnotation
    omega_7: NutriValueAnnotation
    omega_9: NutriValueAnnotation
    oleic_acid: NutriValueAnnotation
    other_carbo: NutriValueAnnotation
    polydextrose: NutriValueAnnotation
    polyols: NutriValueAnnotation
    potassium: NutriValueAnnotation
    sacarose: NutriValueAnnotation
    selenium: NutriValueAnnotation
    silicon: NutriValueAnnotation
    sorbitol: NutriValueAnnotation
    sucralose: NutriValueAnnotation
    taurine: NutriValueAnnotation
    vitamin_a: NutriValueAnnotation
    vitamin_b1: NutriValueAnnotation
    vitamin_b2: NutriValueAnnotation
    vitamin_b3: NutriValueAnnotation
    vitamin_b5: NutriValueAnnotation
    vitamin_b6: NutriValueAnnotation
    folic_acid: NutriValueAnnotation
    vitamin_b12: NutriValueAnnotation
    vitamin_c: NutriValueAnnotation
    vitamin_d: NutriValueAnnotation
    vitamin_e: NutriValueAnnotation
    vitamin_k: NutriValueAnnotation
    zinc: NutriValueAnnotation
    retinol: NutriValueAnnotation
    thiamine: NutriValueAnnotation
    riboflavin: NutriValueAnnotation
    pyridoxine: NutriValueAnnotation
    niacin: NutriValueAnnotation

    @classmethod
    def from_domain(cls, domain_obj: NutriFacts) -> "ApiNutriFacts":
        """Creates an instance of `ApiNutriFacts` from a domain model object."""
        kwargs = {}
        for name in cls.model_fields.keys():
            value = getattr(domain_obj, name)
            if value is not None:
                if isinstance(value, NutriValue):
                    kwargs[name] = ApiNutriValue.from_domain(value)
                else:
                    kwargs[name] = value
        return cls(**kwargs)

    def to_domain(self) -> NutriFacts:
        """Converts the instance to a domain model object."""
        kwargs = {}
        for name in self.__class__.model_fields.keys():
            value = getattr(self, name)
            if value is not None:
                if isinstance(value, ApiNutriValue):
                    kwargs[name] = value.to_domain()
                else:
                    kwargs[name] = value
        return NutriFacts(**kwargs)

    @classmethod
    def from_orm_model(cls, orm_model: NutriFactsSaModel):
        """
        Can't be implemented because ORM model stores only the value.
        """
        kwargs = {}
        for name in cls.model_fields.keys():
            value = getattr(orm_model, name)
            if value is not None:
                kwargs[name] = value
        return cls(**kwargs)
        

    def to_orm_kwargs(self) -> dict:
        """Convert to ORM model kwargs."""
        kwargs = {}
        for name in self.__class__.model_fields.keys():
            value = getattr(self, name)
            if isinstance(value, ApiNutriValue):
                kwargs[name] = value.value
            elif isinstance(value, float):
                kwargs[name] = value
            else:
                kwargs[name] = None
        return kwargs

