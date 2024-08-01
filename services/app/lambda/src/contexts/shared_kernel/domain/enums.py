from __future__ import annotations

from enum import Enum, unique


class State(Enum):
    AC = "AC"
    AL = "AL"
    AP = "AP"
    AM = "AM"
    BA = "BA"
    CE = "CE"
    DF = "DF"
    ES = "ES"
    GO = "GO"
    MA = "MA"
    MT = "MT"
    MS = "MS"
    MG = "MG"
    PA = "PA"
    PB = "PB"
    PR = "PR"
    PE = "PE"
    PI = "PI"
    RJ = "RJ"
    RN = "RN"
    RS = "RS"
    RO = "RO"
    RR = "RR"
    SC = "SC"
    SP = "SP"
    SE = "SE"
    TO = "TO"

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, State) and self.value == __o.value


@unique
class MeasureUnit(str, Enum):
    UNIT = "un"
    KILOGRAM = "kg"
    GRAM = "g"
    MILLIGRAM = "mg"
    MICROGRAM = "mcg"
    LITER = "l"
    MILLILITER = "ml"
    PERCENT = "percent"
    ENERGY = "kcal"
    IU = "IU"
    TABLESPOON = "tbsp"
    TEASPOON = "tsp"
    CUP = "cup"


@unique
class WeightUnit(str, Enum):
    KILOGRAM = "kg"
    GRAM = "g"
    MILLIGRAM = "mg"
    MICROGRAM = "mcg"


@unique
class Privacy(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"


@unique
class Month(Enum):
    JAN = 1
    FEB = 2
    MAR = 3
    APR = 4
    MAY = 5
    JUN = 6
    JUL = 7
    AUG = 8
    SEP = 9
    OCT = 10
    NOV = 11
    DEC = 12


@unique
class DietType(Enum):
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    LOWFODMAP = "lowfodmap"
    GLUTEN_FREE = "gluten_free"
    LACTOSE_FREE = "lactose_free"
    SUGAR_FREE = "sugar_free"
    LOW_SODIUM = "low_sodium"
    LOW_FAT = "low_fat"
    LOW_SUGAR = "low_sugar"
    LOW_CALORIES = "low_calories"
    LOW_CARB = "low_carb"
    HIGH_PROTEIN = "high_protein"
    HIGH_FIBER = "high_fiber"
    HIGH_CALCIUM = "high_calcium"
    HIGH_IRON = "high_iron"
    HIGH_POTASSIUM = "high_potassium"
