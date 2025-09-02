import inspect
from collections.abc import Mapping
from typing import Any

from attrs import field, fields, frozen
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue


def _convert_to_nutri_value(nutri_fact: Any, unit: MeasureUnit) -> NutriValue:
    """Normalize inputs into a NutriValue with a concrete unit.

    Accepts existing NutriValue instances, numeric values, or mappings with
    a value key. Falls back to zero value when input is None or missing.

    Args:
        nutri_fact: Candidate value to convert.
        unit: Default unit to apply when needed.

    Returns:
        A NutriValue instance with a defined unit and value.

    Notes:
        Side-effect-free. Handles various input types consistently.
    """
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
    """Value object representing the nutritional facts of a food item.

    This class defines the default unit for each nutrient field, which should be
    used consistently across the application.

    Attributes:
        default_units: Mapping of nutrient names to their standard units.
        calories: Energy content.
        protein: Protein content.
        carbohydrate: Total carbohydrate content.
        total_fat: Total fat content.
        saturated_fat: Saturated fat content.
        trans_fat: Trans fat content.
        dietary_fiber: Dietary fiber content.
        sodium: Sodium content.
        arachidonic_acid: Arachidonic acid content.
        ashes: Ash content.
        dha: Docosahexaenoic acid content.
        epa: Eicosapentaenoic acid content.
        sugar: Sugar content.
        starch: Starch content.
        biotin: Biotin content.
        boro: Boron content.
        caffeine: Caffeine content.
        calcium: Calcium content.
        chlorine: Chlorine content.
        copper: Copper content.
        cholesterol: Cholesterol content.
        choline: Choline content.
        chrome: Chromium content.
        dextrose: Dextrose content.
        sulfur: Sulfur content.
        phenylalanine: Phenylalanine content.
        iron: Iron content.
        insoluble_fiber: Insoluble fiber content.
        soluble_fiber: Soluble fiber content.
        fluor: Fluoride content.
        phosphorus: Phosphorus content.
        fructo_oligosaccharides: Fructo-oligosaccharides content.
        fructose: Fructose content.
        galacto_oligosaccharides: Galacto-oligosaccharides content.
        galactose: Galactose content.
        glucose: Glucose content.
        glucoronolactone: Glucuronolactone content.
        monounsaturated_fat: Monounsaturated fat content.
        polyunsaturated_fat: Polyunsaturated fat content.
        guarana: Guarana content.
        inositol: Inositol content.
        inulin: Inulin content.
        iodine: Iodine content.
        l_carnitine: L-carnitine content.
        l_methionine: L-methionine content.
        lactose: Lactose content.
        magnesium: Magnesium content.
        maltose: Maltose content.
        manganese: Manganese content.
        molybdenum: Molybdenum content.
        linolenic_acid: Linolenic acid content.
        linoleic_acid: Linoleic acid content.
        omega_7: Omega-7 content.
        omega_9: Omega-9 content.
        oleic_acid: Oleic acid content.
        other_carbo: Other carbohydrate content.
        polydextrose: Polydextrose content.
        polyols: Polyols content.
        potassium: Potassium content.
        sacarose: Sucrose content.
        selenium: Selenium content.
        silicon: Silicon content.
        sorbitol: Sorbitol content.
        sucralose: Sucralose content.
        taurine: Taurine content.
        vitamin_a: Vitamin A content.
        vitamin_b1: Vitamin B1 content.
        vitamin_b2: Vitamin B2 content.
        vitamin_b3: Vitamin B3 content.
        vitamin_b5: Vitamin B5 content.
        vitamin_b6: Vitamin B6 content.
        folic_acid: Folic acid content.
        vitamin_b12: Vitamin B12 content.
        vitamin_c: Vitamin C content.
        vitamin_d: Vitamin D content.
        vitamin_e: Vitamin E content.
        vitamin_k: Vitamin K content.
        zinc: Zinc content.
        retinol: Retinol content.
        thiamine: Thiamine content.
        riboflavin: Riboflavin content.
        pyridoxine: Pyridoxine content.
        niacin: Niacin content.

    Notes:
        Immutable. Equality by value (all nutrient fields).
        Supports arithmetic operations for nutritional aggregation.
        Auto-converts inputs to NutriValue with appropriate units.
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
        """Initialize all nutrient fields with proper NutriValue instances.

        Notes:
            Auto-converts all nutrient inputs to NutriValue with appropriate units.
        """
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
        """Add nutritional facts from another NutriFacts instance.

        Args:
            other: Nutritional facts to add.

        Returns:
            New NutriFacts with summed nutritional values.

        Notes:
            Performs element-wise addition of all nutrient fields.
        """
        if isinstance(other, NutriFacts):
            params = inspect.signature(self.__class__).parameters
            self_args = {name: getattr(self, name) for name in params}
            other_args = {name: getattr(other, name) for name in params}
            return self.replace(**{k: v + other_args[k] for k, v in self_args.items()})
        return NotImplemented

    def __sub__(self, other: "NutriFacts") -> "NutriFacts":
        """Subtract nutritional facts from another NutriFacts instance.

        Args:
            other: Nutritional facts to subtract.

        Returns:
            New NutriFacts with subtracted nutritional values.

        Notes:
            Performs element-wise subtraction of all nutrient fields.
        """
        if isinstance(other, NutriFacts):
            params = inspect.signature(self.__class__).parameters
            self_args = {name: getattr(self, name) for name in params}
            other_args = {name: getattr(other, name) for name in params}
            return self.replace(**{k: v - other_args[k] for k, v in self_args.items()})
        return NotImplemented
