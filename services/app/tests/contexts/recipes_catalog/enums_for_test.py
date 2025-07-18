from enum import Enum, unique


@unique
class MealTypeTestEnum(str, Enum):
    PRE_WORKOUT = "pré treino"
    POST_WORKOUT = "pós treino"
    BREAKFAST = "breakfast"
    MORNING_SNACK = "lanche da manhã"
    LUNCH = "almoço"
    AFTERNOON_SNACK = "lanche da tarde"
    DINNER = "jantar"
    SUPPER = "ceia"
    DESSERT = "sobremesa"
    DRINK = "bebida"
    OTHER = "outro"


@unique
class MealPlanningTestEnum(str, Enum):
    QUICK = "rápido"
    SLOW = "lento"
    MAKE_AHEAD = "preparar com antecedência"
    ONE_POT = "travessa"
    FREEZER_FRIENDLY = "pode congelar"
    KID_FRIENDLY = "menu kids"
    BUDGET_FRIENDLY = "econômico"
    LEFTOVERS = "restos"
    ENTERTAINING = "divertido"
