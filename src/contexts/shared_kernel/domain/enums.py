"""Shared kernel enumerations for common value objects.

Includes geographic states, measurement units, privacy flags, calendar months,
diet types, allergens, cuisines, flavors, textures, and weekdays.
"""
from __future__ import annotations

from enum import Enum, unique


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

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, _o: object) -> bool:
        return isinstance(_o, State) and self.value == _o.value


@unique
class MeasureUnit(str, Enum):
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
class WeightUnit(str, Enum):
    """Weight measurement unit enumeration.

    Notes:
        Immutable. Equality by value (unit string).
    """
    KILOGRAM = "kg"
    GRAM = "g"
    MILLIGRAM = "mg"
    MICROGRAM = "mcg"


@unique
class Privacy(str, Enum):
    """Privacy level enumeration for content visibility.

    Notes:
        Immutable. Equality by value (privacy string).
    """
    PRIVATE = "private"
    PUBLIC = "public"


@unique
class Month(Enum):
    """Calendar month enumeration.

    Notes:
        Immutable. Equality by value (month number).
    """
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
    """Dietary restriction and preference enumeration.

    Notes:
        Immutable. Equality by value (diet type string).
    """
    VEGAN = "Vegana"
    VEGETARIAN = "Vegetariana"
    LOWFODMAP = "Low FODMAP"
    GLUTEN_FREE = "Sem glúten"
    LACTOSE_FREE = "Sem lactose"
    SUGAR_FREE = "Sem açúcar"
    LOW_SODIUM = "Baixa em sódio"
    LOW_FAT = "Baixa em gordura"
    LOW_SUGAR = "Baixa em açúcar"
    LOW_CALORIES = "Baixa em caloria"
    LOW_CARB = "Baixa em carboidrato"
    HIGH_PROTEIN = "Alta em proteína"
    HIGH_FIBER = "Alta em fibra"
    HIGH_CALCIUM = "Alta em cálcio"
    HIGH_IRON = "Alta em ferro"
    HIGH_POTASSIUM = "Alta em potássio"
    PALEO = "Paleo"
    KETO = "Keto"
    DAIRY_FREE = "Sem laticínios"
    PESCATARIAN = "Pescetariana"
    WHOLE30 = "Whole30"
    DASH = "DASH"
    MEDITERRANEAN = "Mediterrânea"


@unique
class Allergen(Enum):
    """Food allergen enumeration.

    Notes:
        Immutable. Equality by value (allergen string).
    """
    CELERY = "Aipo"
    GARLIC = "Alho"
    PEANUT = "Amendoim"
    BANANA = "Banana"
    CACAO = "Cacau"
    NUTS = "Castanhas"
    CITRUS_FRUITS = "Frutas cítricas"
    SEAFOOD = "Frutos do mar"
    GLUTEN = "Glúten"
    LEGUMES = "Leguminosas"
    MILK = "Leite"
    LUPIN = "Lupino"
    SHELLFISH = "Mariscos"
    CORN = "Milho"
    STRAWBERRY = "Morango"
    MUSTARD = "Mostarda"
    EGG = "Ovo"
    FISH = "Peixe"
    SESAME = "Semente de gergelim"
    SOY = "Soja"
    SULFITES = "Sulfitos"
    WHEAT = "Trigo"


@unique
class Cuisine(Enum):
    """Culinary cuisine type enumeration.

    Notes:
        Immutable. Equality by value (cuisine string).
    """
    AFRICAN = "Africana"
    GERMAN = "Alemã"
    ARABIC = "Árabe"
    ARGENTINIAN = "Argentina"
    ASIAN = "Asiática"
    BRAZILIAN = "Brasileira"
    CAPIXABA = "Capixaba"
    CARIBBEAN = "Caribenha"
    CHILEAN = "Chilena"
    CHINESE = "Chinesa"
    KOREAN = "Coreana"
    CUBAN = "Cubana"
    SPANISH = "Espanhola"
    AMERICAN = "Estado Unidense"
    EUROPEAN = "Europeia"
    FRENCH = "Francesa"
    GAUCHA = "Gaúcha"
    GREEK = "Grega"
    INDIAN = "Indiana"
    INDONESIAN = "Indonésia"
    ITALIAN = "Italiana"
    JAPANESE = "Japonesa"
    LATIN_AMERICAN = "Latino-americana"
    LEBANESE = "Libanesa"
    MEDITERRANEAN = "Mediterrânea"
    MEXICAN = "Mexicana"
    MINAS = "Mineira"
    NORTHEASTERN = "Nordestina"
    MIDDLE_EASTERN = "Oriente Médio"
    PERUVIAN = "Peruana"
    PORTUGUESE = "Portuguesa"
    RUSSIAN = "Russa"
    THAI = "Tailandesa"
    TURKISH = "Turca"
    VIETNAMESE = "Vietnamita"


@unique
class Flavor(Enum):
    """Food flavor profile enumeration.

    Notes:
        Immutable. Equality by value (flavor string).
    """
    ACIDIC = "Ácido"
    SWEET_AND_SOUR = "Agridoce"
    BITTER = "Amargo"
    ALMOND = "Amendoado"
    VELVETY = "Aveludado"
    SOUR = "Azedo"
    CARAMELIZED = "Caramelizado"
    CITRUS = "Cítrico"
    COMPLEX = "Complexo"
    SMOKY = "Defumado"
    SWEET = "Doce"
    FRESH = "Fresco"
    FRUITY = "Frutado"
    HERBACEOUS = "Herbáceo"
    BUTTERY = "Manteigoso"
    SPICY = "Picante"
    RICH = "Rico"
    SALTY = "Salgado"
    SMOOTH = "Suave"
    EARTHY = "Terroso"
    TOASTED = "Tostado"
    TROPICAL = "Tropical"
    UMAMI = "Umami"


@unique
class Texture(Enum):
    """Food texture profile enumeration.

    Notes:
        Immutable. Equality by value (texture string).
    """
    AIRY = "Aerado"
    CREAMY = "Cremoso"
    CRUNCHY = "Crocante"
    CRUSTY = "Crostinha"
    CRUMBLY = "Esfarelado"
    SPONGY = "Esponjoso"
    FIRM = "Firme"
    FLAKY = "Flocos"
    GELATINOUS = "Gelatinoso"
    GRAINY = "Granuloso"
    LIQUID = "Líquido"
    SMOOTH = "Liso"
    SOFT = "Macio"
    BUTTERY = "Manteigoso"
    OILY = "Oleoso"
    STICKY = "Pegajoso"
    SILKY = "Sedoso"


@unique
class Weekday(Enum):
    """Weekday enumeration.

    Notes:
        Immutable. Equality by value (weekday string).
    """
    MONDAY = "Segunda-feira"
    TUESDAY = "Terça-feira"
    WEDNESDAY = "Quarta-feira"
    THURSDAY = "Quinta-feira"
    FRIDAY = "Sexta-feira"
    SATURDAY = "Sábado"
    SUNDAY = "Domingo"
