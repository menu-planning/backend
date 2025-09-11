from enum import Enum, unique


@unique
class SourceTestEnum(Enum):
    PRIVATE = "private"
    MANUAL = "manual"
    TACO = "taco"
    GS1 = "gs1"
    AUTO = "auto"


@unique
class FoodGroupTestEnum(Enum):
    ENERGY = "Energéticos"
    BUILDERS = "Construtores"
    REGULATORS = "Reguladores"


@unique
class ProcessTypeTestEnum(Enum):
    UNPROCESSED = "In natura"
    MIN_PROCCESSED = "Minimante processados"
    PROCESSED = "Processados"
    ULTRA_PROCESSED = "Ultra processados"
    OILS_FAT_SALT_SUGAR = "Óleos, gorduras, sal e açúcar"


@unique
class CategoryTestEnum(Enum):
    ARROZ = "Arroz"
    FEIJAO = "Feijão"
    LEITE = "Leite"
    QUEIJO = "Queijo"
    FRUTAS = "Frutas"
    VERDURAS = "Verduras"
    CARNES = "Carnes"
    MASSAS = "Massas"
    PAES = "Pães"
    DOCES = "Doces"


@unique
class ParentCategoryTestEnum(Enum):
    GRAOS_CEREAIS = "Grãos e Cereais"
    LATICINIOS = "Laticínios"
    HORTALICAS = "Hortaliças"
    BEBIDAS = "Bebidas"
    DOCES_SOBREMESAS = "Doces e Sobremesas"
    CARNES_DERIVADOS = "Carnes e Derivados"
    PEIXES_MAR = "Peixes e Frutos do Mar"
    OLEOS_GORDURAS = "Óleos e Gorduras"
    SEMENTES_OLEAGINOSAS = "Sementes e Oleaginosas"
    ALIMENTOS_PROCESSADOS = "Alimentos Processados"
