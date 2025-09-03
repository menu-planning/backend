import inspect
from collections.abc import Mapping
from typing import Any, ClassVar

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
    """Value object representing nutritional facts of a food item.

    Invariants:
        - All nutrient values must be non-negative
        - Each nutrient has a standardized unit from default_units mapping
        - Values are automatically converted to NutriValue instances

    Attributes:
        default_units: ClassVar mapping of nutrient names to standard units
        calories: Energy content in calories
        protein: Protein content in grams
        carbohydrate: Total carbohydrate content in grams
        total_fat: Total fat content in grams
        saturated_fat: Saturated fat content in grams
        trans_fat: Trans fat content in grams
        dietary_fiber: Dietary fiber content in grams
        sodium: Sodium content in milligrams
        arachidonic_acid: Arachidonic acid content in grams
        ashes: Ash content in grams
        dha: Docosahexaenoic acid content in milligrams
        epa: Eicosapentaenoic acid content in milligrams
        sugar: Sugar content in grams
        starch: Starch content in micrograms
        biotin: Biotin content in micrograms
        boro: Boron content in milligrams
        caffeine: Caffeine content in milligrams
        calcium: Calcium content in milligrams
        chlorine: Chlorine content in milligrams
        copper: Copper content in milligrams
        cholesterol: Cholesterol content in milligrams
        choline: Choline content in milligrams
        chrome: Chromium content in micrograms
        dextrose: Dextrose content in grams
        sulfur: Sulfur content in milligrams
        phenylalanine: Phenylalanine content in grams
        iron: Iron content in milligrams
        insoluble_fiber: Insoluble fiber content in grams
        soluble_fiber: Soluble fiber content in grams
        fluor: Fluoride content in milligrams
        phosphorus: Phosphorus content in milligrams
        fructo_oligosaccharides: Fructo-oligosaccharides content in milligrams
        fructose: Fructose content in grams
        galacto_oligosaccharides: Galacto-oligosaccharides content in grams
        galactose: Galactose content in milligrams
        glucose: Glucose content in grams
        glucoronolactone: Glucuronolactone content in milligrams
        monounsaturated_fat: Monounsaturated fat content in grams
        polyunsaturated_fat: Polyunsaturated fat content in grams
        guarana: Guarana content in milligrams
        inositol: Inositol content in grams
        inulin: Inulin content in grams
        iodine: Iodine content in milligrams
        l_carnitine: L-carnitine content in milligrams
        l_methionine: L-methionine content in grams
        lactose: Lactose content in grams
        magnesium: Magnesium content in milligrams
        maltose: Maltose content in grams
        manganese: Manganese content in milligrams
        molybdenum: Molybdenum content in micrograms
        linolenic_acid: Linolenic acid content in grams
        linoleic_acid: Linoleic acid content in grams
        omega_7: Omega-7 content in milligrams
        omega_9: Omega-9 content in milligrams
        oleic_acid: Oleic acid content in grams
        other_carbo: Other carbohydrate content in grams
        polydextrose: Polydextrose content in grams
        polyols: Polyols content in grams
        potassium: Potassium content in milligrams
        sacarose: Sucrose content in grams
        selenium: Selenium content in micrograms
        silicon: Silicon content in milligrams
        sorbitol: Sorbitol content in grams
        sucralose: Sucralose content in grams
        taurine: Taurine content in milligrams
        vitamin_a: Vitamin A content in IU
        vitamin_b1: Vitamin B1 content in milligrams
        vitamin_b2: Vitamin B2 content in milligrams
        vitamin_b3: Vitamin B3 content in milligrams
        vitamin_b5: Vitamin B5 content in milligrams
        vitamin_b6: Vitamin B6 content in milligrams
        folic_acid: Folic acid content in micrograms
        vitamin_b12: Vitamin B12 content in micrograms
        vitamin_c: Vitamin C content in milligrams
        vitamin_d: Vitamin D content in IU
        vitamin_e: Vitamin E content in milligrams
        vitamin_k: Vitamin K content in micrograms
        zinc: Zinc content in milligrams
        retinol: Retinol content in micrograms
        thiamine: Thiamine content in milligrams
        riboflavin: Riboflavin content in milligrams
        pyridoxine: Pyridoxine content in milligrams
        niacin: Niacin content in milligrams

    Notes:
        Immutable. Equality by value (all nutrient fields).
    """

    default_units: ClassVar[dict[str, MeasureUnit]] = {
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
            self_args = {name: getattr(self, name) for name in params if name != "default_units"}
            other_args = {name: getattr(other, name) for name in params if name != "default_units"}
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
            self_args = {name: getattr(self, name) for name in params if name != "default_units"}
            other_args = {name: getattr(other, name) for name in params if name != "default_units"}
            return self.replace(**{k: v - other_args[k] for k, v in self_args.items()})
        return NotImplemented
