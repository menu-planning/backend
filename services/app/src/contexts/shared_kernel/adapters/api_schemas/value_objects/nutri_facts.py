from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseValueObject
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_value import ApiNutriValue
from src.db.base import SaBase


class ApiNutriFacts(BaseValueObject[NutriFacts, SaBase]):
    """
    A Pydantic model representing and validating the nutritional facts
    of a food item.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Each nutrient is represented by an ApiNutriValue instance that contains
    both the value and the appropriate unit for that nutrient.
    """

    calories: float | ApiNutriValue | None = None
    protein: float | ApiNutriValue | None = None
    carbohydrate: float | ApiNutriValue | None = None
    total_fat: float | ApiNutriValue | None = None
    saturated_fat: float | ApiNutriValue | None = None
    trans_fat: float | ApiNutriValue | None = None
    dietary_fiber: float | ApiNutriValue | None = None
    sodium: float | ApiNutriValue | None = None
    arachidonic_acid: float | ApiNutriValue | None = None
    ashes: float | ApiNutriValue | None = None
    dha: float | ApiNutriValue | None = None
    epa: float | ApiNutriValue | None = None
    sugar: float | ApiNutriValue | None = None
    starch: float | ApiNutriValue | None = None
    biotin: float | ApiNutriValue | None = None
    boro: float | ApiNutriValue | None = None
    caffeine: float | ApiNutriValue | None = None
    calcium: float | ApiNutriValue | None = None
    chlorine: float | ApiNutriValue | None = None
    copper: float | ApiNutriValue | None = None
    cholesterol: float | ApiNutriValue | None = None
    choline: float | ApiNutriValue | None = None
    chrome: float | ApiNutriValue | None = None
    dextrose: float | ApiNutriValue | None = None
    sulfur: float | ApiNutriValue | None = None
    phenylalanine: float | ApiNutriValue | None = None
    iron: float | ApiNutriValue | None = None
    insoluble_fiber: float | ApiNutriValue | None = None
    soluble_fiber: float | ApiNutriValue | None = None
    fluor: float | ApiNutriValue | None = None
    phosphorus: float | ApiNutriValue | None = None
    fructo_oligosaccharides: float | ApiNutriValue | None = None
    fructose: float | ApiNutriValue | None = None
    galacto_oligosaccharides: float | ApiNutriValue | None = None
    galactose: float | ApiNutriValue | None = None
    glucose: float | ApiNutriValue | None = None
    glucoronolactone: float | ApiNutriValue | None = None
    monounsaturated_fat: float | ApiNutriValue | None = None
    polyunsaturated_fat: float | ApiNutriValue | None = None
    guarana: float | ApiNutriValue | None = None
    inositol: float | ApiNutriValue | None = None
    inulin: float | ApiNutriValue | None = None
    iodine: float | ApiNutriValue | None = None
    l_carnitine: float | ApiNutriValue | None = None
    l_methionine: float | ApiNutriValue | None = None
    lactose: float | ApiNutriValue | None = None
    magnesium: float | ApiNutriValue | None = None
    maltose: float | ApiNutriValue | None = None
    manganese: float | ApiNutriValue | None = None
    molybdenum: float | ApiNutriValue | None = None
    linolenic_acid: float | ApiNutriValue | None = None
    linoleic_acid: float | ApiNutriValue | None = None
    omega_7: float | ApiNutriValue | None = None
    omega_9: float | ApiNutriValue | None = None
    oleic_acid: float | ApiNutriValue | None = None
    other_carbo: float | ApiNutriValue | None = None
    polydextrose: float | ApiNutriValue | None = None
    polyols: float | ApiNutriValue | None = None
    potassium: float | ApiNutriValue | None = None
    sacarose: float | ApiNutriValue | None = None
    selenium: float | ApiNutriValue | None = None
    silicon: float | ApiNutriValue | None = None
    sorbitol: float | ApiNutriValue | None = None
    sucralose: float | ApiNutriValue | None = None
    taurine: float | ApiNutriValue | None = None
    vitamin_a: float | ApiNutriValue | None = None
    vitamin_b1: float | ApiNutriValue | None = None
    vitamin_b2: float | ApiNutriValue | None = None
    vitamin_b3: float | ApiNutriValue | None = None
    vitamin_b5: float | ApiNutriValue | None = None
    vitamin_b6: float | ApiNutriValue | None = None
    folic_acid: float | ApiNutriValue | None = None
    vitamin_b12: float | ApiNutriValue | None = None
    vitamin_c: float | ApiNutriValue | None = None
    vitamin_d: float | ApiNutriValue | None = None
    vitamin_e: float | ApiNutriValue | None = None
    vitamin_k: float | ApiNutriValue | None = None
    zinc: float | ApiNutriValue | None = None
    retinol: float | ApiNutriValue | None = None
    thiamine: float | ApiNutriValue | None = None
    riboflavin: float | ApiNutriValue | None = None
    pyridoxine: float | ApiNutriValue | None = None
    niacin: float | ApiNutriValue | None = None

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

    def to_orm_kwargs(self) -> dict:
        """Convert to ORM model kwargs."""
        kwargs = {}
        for name in self.__class__.model_fields.keys():
            value = getattr(self, name)
            if value is not None:
                if isinstance(value, ApiNutriValue):
                    kwargs[name] = value.value
                else:
                    kwargs[name] = value
        return kwargs

