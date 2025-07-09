import inspect
from collections.abc import Mapping
from typing import Any

from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue

def _convert_to_nutri_value(nutri_fact: Any, unit: MeasureUnit) -> NutriValue:
        if nutri_fact is None:
            return NutriValue(value=0, unit=unit)
        if isinstance(nutri_fact, NutriValue) and nutri_fact.value is not None:
            return nutri_fact
        elif isinstance(nutri_fact, NutriValue):
            return NutriValue(value=0, unit=unit)
        if isinstance(nutri_fact, Mapping) and nutri_fact.get("value") is not None:
            return NutriValue(**nutri_fact)
        elif isinstance(nutri_fact, Mapping):
            return NutriValue(value=0, unit=unit)
        return NutriValue(value=nutri_fact, unit=unit)

@frozen(kw_only=True)
class NutriFacts(ValueObject):
    """
    NutriFacts is a value object that represents the nutritional facts of a food item.
    
    This class defines the default unit for each nutrient field, which should be 
    used consistently across the application.
    """
    
    # Default units for each nutrient field
    _DEFAULT_UNITS = {
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
    }
    
    calories: NutriValue
    protein: NutriValue
    carbohydrate: NutriValue
    total_fat: NutriValue
    saturated_fat: NutriValue
    trans_fat: NutriValue
    dietary_fiber: NutriValue
    sodium: NutriValue
    arachidonic_acid: NutriValue
    ashes: NutriValue
    dha: NutriValue
    epa: NutriValue
    sugar: NutriValue
    starch: NutriValue
    biotin: NutriValue
    boro: NutriValue
    caffeine: NutriValue
    calcium: NutriValue
    chlorine: NutriValue
    copper: NutriValue
    cholesterol: NutriValue
    choline: NutriValue
    chrome: NutriValue
    dextrose: NutriValue
    sulfur: NutriValue
    phenylalanine: NutriValue
    iron: NutriValue
    insoluble_fiber: NutriValue
    soluble_fiber: NutriValue
    fluor: NutriValue
    phosphorus: NutriValue
    fructo_oligosaccharides: NutriValue
    fructose: NutriValue
    galacto_oligosaccharides: NutriValue
    galactose: NutriValue
    glucose: NutriValue
    glucoronolactone: NutriValue
    monounsaturated_fat: NutriValue
    polyunsaturated_fat: NutriValue
    guarana: NutriValue
    inositol: NutriValue
    inulin: NutriValue
    iodine: NutriValue
    l_carnitine: NutriValue
    l_methionine: NutriValue
    lactose: NutriValue
    magnesium: NutriValue
    maltose: NutriValue
    manganese: NutriValue
    molybdenum: NutriValue
    linolenic_acid: NutriValue
    linoleic_acid: NutriValue
    omega_7: NutriValue
    omega_9: NutriValue
    oleic_acid: NutriValue
    other_carbo: NutriValue
    polydextrose: NutriValue
    polyols: NutriValue
    potassium: NutriValue
    sacarose: NutriValue
    selenium: NutriValue
    silicon: NutriValue
    sorbitol: NutriValue
    sucralose: NutriValue
    taurine: NutriValue
    vitamin_a: NutriValue
    vitamin_b1: NutriValue
    vitamin_b2: NutriValue
    vitamin_b3: NutriValue
    vitamin_b5: NutriValue
    vitamin_b6: NutriValue
    folic_acid: NutriValue
    vitamin_b12: NutriValue
    vitamin_c: NutriValue
    vitamin_d: NutriValue
    vitamin_e: NutriValue
    vitamin_k: NutriValue
    zinc: NutriValue
    retinol: NutriValue
    thiamine: NutriValue
    riboflavin: NutriValue
    pyridoxine: NutriValue
    niacin: NutriValue

    def __init__(
        self,
        calories: float | NutriValue | Mapping = 0,
        protein: float | NutriValue | Mapping = 0,
        carbohydrate: float | NutriValue | Mapping = 0,
        total_fat: float | NutriValue | Mapping = 0,
        saturated_fat: float | NutriValue | Mapping = 0,
        trans_fat: float | NutriValue | Mapping = 0,
        dietary_fiber: float | NutriValue | Mapping = 0,
        sodium: float | NutriValue | Mapping = 0,
        arachidonic_acid: float | NutriValue | Mapping = 0,
        ashes: float | NutriValue | Mapping = 0,
        dha: float | NutriValue | Mapping = 0,
        epa: float | NutriValue | Mapping = 0,
        sugar: float | NutriValue | Mapping = 0,
        starch: float | NutriValue | Mapping = 0,
        biotin: float | NutriValue | Mapping = 0,
        boro: float | NutriValue | Mapping = 0,
        caffeine: float | NutriValue | Mapping = 0,
        calcium: float | NutriValue | Mapping = 0,
        chlorine: float | NutriValue | Mapping = 0,
        copper: float | NutriValue | Mapping = 0,
        cholesterol: float | NutriValue | Mapping = 0,
        choline: float | NutriValue | Mapping = 0,
        chrome: float | NutriValue | Mapping = 0,
        dextrose: float | NutriValue | Mapping = 0,
        sulfur: float | NutriValue | Mapping = 0,
        phenylalanine: float | NutriValue | Mapping = 0,
        iron: float | NutriValue | Mapping = 0,
        insoluble_fiber: float | NutriValue | Mapping = 0,
        soluble_fiber: float | NutriValue | Mapping = 0,
        fluor: float | NutriValue | Mapping = 0,
        phosphorus: float | NutriValue | Mapping = 0,
        fructo_oligosaccharides: float | NutriValue | Mapping = 0,
        fructose: float | NutriValue | Mapping = 0,
        galacto_oligosaccharides: float | NutriValue | Mapping = 0,
        galactose: float | NutriValue | Mapping = 0,
        glucose: float | NutriValue | Mapping = 0,
        glucoronolactone: float | NutriValue | Mapping = 0,
        monounsaturated_fat: float | NutriValue | Mapping = 0,
        polyunsaturated_fat: float | NutriValue | Mapping = 0,
        guarana: float | NutriValue | Mapping = 0,
        inositol: float | NutriValue | Mapping = 0,
        inulin: float | NutriValue | Mapping = 0,
        iodine: float | NutriValue | Mapping = 0,
        l_carnitine: float | NutriValue | Mapping = 0,
        l_methionine: float | NutriValue | Mapping = 0,
        lactose: float | NutriValue | Mapping = 0,
        magnesium: float | NutriValue | Mapping = 0,
        maltose: float | NutriValue | Mapping = 0,
        manganese: float | NutriValue | Mapping = 0,
        molybdenum: float | NutriValue | Mapping = 0,
        linolenic_acid: float | NutriValue | Mapping = 0,
        linoleic_acid: float | NutriValue | Mapping = 0,
        omega_7: float | NutriValue | Mapping = 0,
        omega_9: float | NutriValue | Mapping = 0,
        oleic_acid: float | NutriValue | Mapping = 0,
        other_carbo: float | NutriValue | Mapping = 0,
        polydextrose: float | NutriValue | Mapping = 0,
        polyols: float | NutriValue | Mapping = 0,
        potassium: float | NutriValue | Mapping = 0,
        sacarose: float | NutriValue | Mapping = 0,
        selenium: float | NutriValue | Mapping = 0,
        silicon: float | NutriValue | Mapping = 0,
        sorbitol: float | NutriValue | Mapping = 0,
        sucralose: float | NutriValue | Mapping = 0,
        taurine: float | NutriValue | Mapping = 0,
        vitamin_a: float | NutriValue | Mapping = 0,
        vitamin_b1: float | NutriValue | Mapping = 0,
        vitamin_b2: float | NutriValue | Mapping = 0,
        vitamin_b3: float | NutriValue | Mapping = 0,
        vitamin_b5: float | NutriValue | Mapping = 0,
        vitamin_b6: float | NutriValue | Mapping = 0,
        folic_acid: float | NutriValue | Mapping = 0,
        vitamin_b12: float | NutriValue | Mapping = 0,
        vitamin_c: float | NutriValue | Mapping = 0,
        vitamin_d: float | NutriValue | Mapping = 0,
        vitamin_e: float | NutriValue | Mapping = 0,
        vitamin_k: float | NutriValue | Mapping = 0,
        zinc: float | NutriValue | Mapping = 0,
        retinol: float | NutriValue | Mapping = 0,
        thiamine: float | NutriValue | Mapping = 0,
        riboflavin: float | NutriValue | Mapping = 0,
        pyridoxine: float | NutriValue | Mapping = 0,
        niacin: float | NutriValue | Mapping = 0,
    ):
        # Use the class-level _DEFAULT_UNITS mapping to construct args
        args = {
            field_name: _convert_to_nutri_value(locals()[field_name], default_unit)
            for field_name, default_unit in self.__class__._DEFAULT_UNITS.items()
        }
        self.__attrs_init__(**args) # type: ignore
        

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
