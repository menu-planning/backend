from enum import Enum, unique

from src.contexts.shared_kernel.domain.enums import State


class CfeStateCodes(Enum):
    AC = 12
    AL = 27
    AP = 16
    AM = 13
    BA = 29
    CE = 23
    DF = 53
    ES = 32
    GO = 52
    MA = 21
    MT = 51
    MS = 50
    MG = 31
    PA = 15
    PB = 25
    PR = 41
    PE = 26
    PI = 22
    RJ = 33
    RN = 24
    RS = 43
    RO = 11
    RR = 14
    SC = 42
    SP = 35
    SE = 28
    TO = 17

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, State) and self.value == __o.value


@unique
class Unit(str, Enum):
    unit = "un"
    kilogram = "kg"
    gram = "g"
    milligram = "mg"
    microgram = "mcg"
    liter = "l"
    milliliter = "ml"
    percent = "percent"
    energy = "kcal"
    IU = "IU"

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Unit) and self.value == __o.value
