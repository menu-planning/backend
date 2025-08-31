import inspect
from collections.abc import Mapping
from typing import Any

from attrs import field, fields, frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue


def _convert_to_nutri_value(nutri_fact: Any, unit: MeasureUnit) -> NutriValue:
    if nutri_fact is None:
        return NutriValue(value=0, unit=unit)
    if isinstance(nutri_fact, NutriValue) and nutri_fact.value is not None:
        return nutri_fact
    if isinstance(nutri_fact, NutriValue):
        return NutriValue(value=0, unit=unit)
    if isinstance(nutri_fact, Mapping) and nutri_fact.get("value") is not None:
        return NutriValue(**nutri_fact)
    if isinstance(nutri_fact, Mapping):
        return NutriValue(value=0, unit=unit)
    return NutriValue(value=nutri_fact, unit=unit)


@frozen(kw_only=True)
class NutriFacts(ValueObject):
    """
    NutriFacts is a value object that represents the nutritional facts of a food item.

    This class defines the default unit for each nutrient field, which should be
    used consistently across the application.
    """

    default_units: dict[str, MeasureUnit] = field(default={
            "calories": MeasureUnit.ENERGY,
            "protein": MeasureUnit.GRAM,
            "carbohydrate": MeasureUnit.GRAM,
            "total_fat": MeasureUnit.GRAM,
            "saturated_fat": MeasureUnit.GRAM,
            "trans_fat": MeasureUnit.GRAM,
            "dietary_fiber": MeasureUnit.GRAM,
            "sodium": MeasureUnit.MILLIGRAM,
            "arachidonic_acid": MeasureUnit.GRAM,
            "ashes": MeasureUnit.GRAM,
            "dha": MeasureUnit.MILLIGRAM,
            "epa": MeasureUnit.MILLIGRAM,
            "sugar": MeasureUnit.GRAM,
            "starch": MeasureUnit.MICROGRAM,
            "biotin": MeasureUnit.MICROGRAM,
            "boro": MeasureUnit.MILLIGRAM,
            "caffeine": MeasureUnit.MILLIGRAM,
            "calcium": MeasureUnit.MILLIGRAM,
            "chlorine": MeasureUnit.MILLIGRAM,
            "copper": MeasureUnit.MILLIGRAM,
            "cholesterol": MeasureUnit.MILLIGRAM,
            "choline": MeasureUnit.MILLIGRAM,
            "chrome": MeasureUnit.MICROGRAM,
            "dextrose": MeasureUnit.GRAM,
            "sulfur": MeasureUnit.MILLIGRAM,
            "phenylalanine": MeasureUnit.GRAM,
            "iron": MeasureUnit.MILLIGRAM,
            "insoluble_fiber": MeasureUnit.GRAM,
            "soluble_fiber": MeasureUnit.GRAM,
            "fluor": MeasureUnit.MILLIGRAM,
            "phosphorus": MeasureUnit.MILLIGRAM,
            "fructo_oligosaccharides": MeasureUnit.MILLIGRAM,
            "fructose": MeasureUnit.GRAM,
            "galacto_oligosaccharides": MeasureUnit.GRAM,
            "galactose": MeasureUnit.MILLIGRAM,
            "glucose": MeasureUnit.GRAM,
            "glucoronolactone": MeasureUnit.MILLIGRAM,
            "monounsaturated_fat": MeasureUnit.GRAM,
            "polyunsaturated_fat": MeasureUnit.GRAM,
            "guarana": MeasureUnit.MILLIGRAM,
            "inositol": MeasureUnit.GRAM,
            "inulin": MeasureUnit.GRAM,
            "iodine": MeasureUnit.MILLIGRAM,
            "l_carnitine": MeasureUnit.MILLIGRAM,
            "l_methionine": MeasureUnit.GRAM,
            "lactose": MeasureUnit.GRAM,
            "magnesium": MeasureUnit.MILLIGRAM,
            "maltose": MeasureUnit.GRAM,
            "manganese": MeasureUnit.MILLIGRAM,
            "molybdenum": MeasureUnit.MICROGRAM,
            "linolenic_acid": MeasureUnit.GRAM,
            "linoleic_acid": MeasureUnit.GRAM,
            "omega_7": MeasureUnit.MILLIGRAM,
            "omega_9": MeasureUnit.MILLIGRAM,
            "oleic_acid": MeasureUnit.GRAM,
            "other_carbo": MeasureUnit.GRAM,
            "polydextrose": MeasureUnit.GRAM,
            "polyols": MeasureUnit.GRAM,
            "potassium": MeasureUnit.MILLIGRAM,
            "sacarose": MeasureUnit.GRAM,
            "selenium": MeasureUnit.MICROGRAM,
            "silicon": MeasureUnit.MILLIGRAM,
            "sorbitol": MeasureUnit.GRAM,
            "sucralose": MeasureUnit.GRAM,
            "taurine": MeasureUnit.MILLIGRAM,
            "vitamin_a": MeasureUnit.IU,
            "vitamin_b1": MeasureUnit.MILLIGRAM,
            "vitamin_b2": MeasureUnit.MILLIGRAM,
            "vitamin_b3": MeasureUnit.MILLIGRAM,
            "vitamin_b5": MeasureUnit.MILLIGRAM,
            "vitamin_b6": MeasureUnit.MILLIGRAM,
            "folic_acid": MeasureUnit.MICROGRAM,
            "vitamin_b12": MeasureUnit.MICROGRAM,
            "vitamin_c": MeasureUnit.MILLIGRAM,
            "vitamin_d": MeasureUnit.IU,
            "vitamin_e": MeasureUnit.MILLIGRAM,
            "vitamin_k": MeasureUnit.MICROGRAM,
            "zinc": MeasureUnit.MILLIGRAM,
            "retinol": MeasureUnit.MICROGRAM,
            "thiamine": MeasureUnit.MILLIGRAM,
            "riboflavin": MeasureUnit.MILLIGRAM,
            "pyridoxine": MeasureUnit.MILLIGRAM,
            "niacin": MeasureUnit.MILLIGRAM,
        })

    calories: NutriValue = field(default=None)
    protein: NutriValue = field(default=None)
    carbohydrate: NutriValue = field(default=None)
    total_fat: NutriValue = field(default=None)
    saturated_fat: NutriValue = field(default=None)
    trans_fat: NutriValue = field(default=None)
    dietary_fiber: NutriValue = field(default=None)
    sodium: NutriValue = field(default=None)
    arachidonic_acid: NutriValue = field(default=None)
    ashes: NutriValue = field(default=None)
    dha: NutriValue = field(default=None)
    epa: NutriValue = field(default=None)
    sugar: NutriValue = field(default=None)
    starch: NutriValue = field(default=None)
    biotin: NutriValue = field(default=None)
    boro: NutriValue = field(default=None)
    caffeine: NutriValue = field(default=None)
    calcium: NutriValue = field(default=None)
    chlorine: NutriValue = field(default=None)
    copper: NutriValue = field(default=None)
    cholesterol: NutriValue = field(default=None)
    choline: NutriValue = field(default=None)
    chrome: NutriValue = field(default=None)
    dextrose: NutriValue = field(default=None)
    sulfur: NutriValue = field(default=None)
    phenylalanine: NutriValue = field(default=None)
    iron: NutriValue = field(default=None)
    insoluble_fiber: NutriValue = field(default=None)
    soluble_fiber: NutriValue = field(default=None)
    fluor: NutriValue = field(default=None)
    phosphorus: NutriValue = field(default=None)
    fructo_oligosaccharides: NutriValue = field(default=None)
    fructose: NutriValue = field(default=None)
    galacto_oligosaccharides: NutriValue = field(default=None)
    galactose: NutriValue = field(default=None)
    glucose: NutriValue = field(default=None)
    glucoronolactone: NutriValue = field(default=None)
    monounsaturated_fat: NutriValue = field(default=None)
    polyunsaturated_fat: NutriValue = field(default=None)
    guarana: NutriValue = field(default=None)
    inositol: NutriValue = field(default=None)
    inulin: NutriValue = field(default=None)
    iodine: NutriValue = field(default=None)
    l_carnitine: NutriValue = field(default=None)
    l_methionine: NutriValue = field(default=None)
    lactose: NutriValue = field(default=None)
    magnesium: NutriValue = field(default=None)
    maltose: NutriValue = field(default=None)
    manganese: NutriValue = field(default=None)
    molybdenum: NutriValue = field(default=None)
    linolenic_acid: NutriValue = field(default=None)
    linoleic_acid: NutriValue = field(default=None)
    omega_7: NutriValue = field(default=None)
    omega_9: NutriValue = field(default=None)
    oleic_acid: NutriValue = field(default=None)
    other_carbo: NutriValue = field(default=None)
    polydextrose: NutriValue = field(default=None)
    polyols: NutriValue = field(default=None)
    potassium: NutriValue = field(default=None)
    sacarose: NutriValue = field(default=None)
    selenium: NutriValue = field(default=None)
    silicon: NutriValue = field(default=None)
    sorbitol: NutriValue = field(default=None)
    sucralose: NutriValue = field(default=None)
    taurine: NutriValue = field(default=None)
    vitamin_a: NutriValue = field(default=None)
    vitamin_b1: NutriValue = field(default=None)
    vitamin_b2: NutriValue = field(default=None)
    vitamin_b3: NutriValue = field(default=None)
    vitamin_b5: NutriValue = field(default=None)
    vitamin_b6: NutriValue = field(default=None)
    folic_acid: NutriValue = field(default=None)
    vitamin_b12: NutriValue = field(default=None)
    vitamin_c: NutriValue = field(default=None)
    vitamin_d: NutriValue = field(default=None)
    vitamin_e: NutriValue = field(default=None)
    vitamin_k: NutriValue = field(default=None)
    zinc: NutriValue = field(default=None)
    retinol: NutriValue = field(default=None)
    thiamine: NutriValue = field(default=None)
    riboflavin: NutriValue = field(default=None)
    pyridoxine: NutriValue = field(default=None)
    niacin: NutriValue = field(default=None)

    def __attrs_post_init__(self):
        for attr in fields(self.__class__):
            if attr.name == "default_units":
                continue
            attr_name = attr.name
            object.__setattr__(
                self,
                attr_name,
                _convert_to_nutri_value(
                    getattr(self, attr_name), self.default_units[attr_name]
                ),
            )

    def __add__(self, other: "NutriFacts") -> "NutriFacts":
        if isinstance(other, NutriFacts):
            params = inspect.signature(self.__class__).parameters
            self_args = {name: getattr(self, name) for name in params}
            other_args = {name: getattr(other, name) for name in params}
            return self.replace(**{k: v + other_args[k] for k, v in self_args.items()})
        return NotImplemented

    def __sub__(self, other: "NutriFacts") -> "NutriFacts":
        if isinstance(other, NutriFacts):
            params = inspect.signature(self.__class__).parameters
            self_args = {name: getattr(self, name) for name in params}
            other_args = {name: getattr(other, name) for name in params}
            return self.replace(**{k: v - other_args[k] for k, v in self_args.items()})
        return NotImplemented
