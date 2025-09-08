"""Shared kernel enumerations for common value objects.

Includes geographic states, measurement units, privacy flags, calendar months,
diet types, allergens, cuisines, flavors, textures, and weekdays.
"""

from __future__ import annotations

from enum import Enum, unique


@unique
class State(Enum):
    """Geographic state enumeration for Brazilian states.

    Notes:
        Immutable. Equality by value (state code).
    """

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


@unique
class MeasureUnit(Enum):
    """Measurement unit enumeration for nutritional and ingredient values.

    Notes:
        Immutable. Equality by value (unit string).
    """

    UNIT = "un"
    KILOGRAM = "kg"
    GRAM = "g"
    MILLIGRAM = "mg"
    MICROGRAM = "mcg"
    LITER = "l"
    MILLILITER = "ml"
    PERCENT = "percentual"
    ENERGY = "kcal"
    IU = "IU"
    TABLESPOON = "colher de sopa"
    TEASPOON = "colher de chá"
    CUP = "xícara"
    PINCH = "pitada"
    HANDFUL = "mão cheia"
    SLICE = "fatia"
    PIECE = "pedaço"


@unique
class Privacy(Enum):
    """Privacy level enumeration for content visibility.

    Notes:
        Immutable. Equality by value (privacy string).
    """

    PRIVATE = "private"
    PUBLIC = "public"


@unique
class Weekday(Enum):
    """Weekday enumeration.

    Notes:
        Immutable. Equality by value (weekday string).
    """

    MONDAY = "Segunda"
    TUESDAY = "Terça"
    WEDNESDAY = "Quarta"
    THURSDAY = "Quinta"
    FRIDAY = "Sexta"
    SATURDAY = "Sábado"
    SUNDAY = "Domingo"
