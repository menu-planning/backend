import inspect
from collections.abc import Mapping

from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue


@frozen(kw_only=True)
class NutriFacts(ValueObject):
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
        args = {
            "calories": (
                calories
                if isinstance(calories, NutriValue)
                else (
                    NutriValue(**calories)
                    if isinstance(calories, Mapping)
                    else NutriValue(value=calories, unit=MeasureUnit.ENERGY)
                )
            ),
            "protein": (
                protein
                if isinstance(protein, NutriValue)
                else (
                    NutriValue(**protein)
                    if isinstance(protein, Mapping)
                    else NutriValue(value=protein, unit=MeasureUnit.GRAM)
                )
            ),
            "carbohydrate": (
                carbohydrate
                if isinstance(carbohydrate, NutriValue)
                else (
                    NutriValue(**carbohydrate)
                    if isinstance(carbohydrate, Mapping)
                    else NutriValue(value=carbohydrate, unit=MeasureUnit.GRAM)
                )
            ),
            "total_fat": (
                total_fat
                if isinstance(total_fat, NutriValue)
                else (
                    NutriValue(**total_fat)
                    if isinstance(total_fat, Mapping)
                    else NutriValue(value=total_fat, unit=MeasureUnit.GRAM)
                )
            ),
            "saturated_fat": (
                saturated_fat
                if isinstance(saturated_fat, NutriValue)
                else (
                    NutriValue(**saturated_fat)
                    if isinstance(saturated_fat, Mapping)
                    else NutriValue(value=saturated_fat, unit=MeasureUnit.GRAM)
                )
            ),
            "trans_fat": (
                trans_fat
                if isinstance(trans_fat, NutriValue)
                else (
                    NutriValue(**trans_fat)
                    if isinstance(trans_fat, Mapping)
                    else NutriValue(value=trans_fat, unit=MeasureUnit.GRAM)
                )
            ),
            "dietary_fiber": (
                dietary_fiber
                if isinstance(dietary_fiber, NutriValue)
                else (
                    NutriValue(**dietary_fiber)
                    if isinstance(dietary_fiber, Mapping)
                    else NutriValue(value=dietary_fiber, unit=MeasureUnit.GRAM)
                )
            ),
            "sodium": (
                sodium
                if isinstance(sodium, NutriValue)
                else (
                    NutriValue(**sodium)
                    if isinstance(sodium, Mapping)
                    else NutriValue(value=sodium, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "arachidonic_acid": (
                arachidonic_acid
                if isinstance(arachidonic_acid, NutriValue)
                else (
                    NutriValue(**arachidonic_acid)
                    if isinstance(arachidonic_acid, Mapping)
                    else NutriValue(value=arachidonic_acid, unit=MeasureUnit.GRAM)
                )
            ),
            "ashes": (
                ashes
                if isinstance(ashes, NutriValue)
                else (
                    NutriValue(**ashes)
                    if isinstance(ashes, Mapping)
                    else NutriValue(value=ashes, unit=MeasureUnit.GRAM)
                )
            ),
            "dha": (
                dha
                if isinstance(dha, NutriValue)
                else (
                    NutriValue(**dha)
                    if isinstance(dha, Mapping)
                    else NutriValue(value=dha, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "epa": (
                epa
                if isinstance(epa, NutriValue)
                else (
                    NutriValue(**epa)
                    if isinstance(epa, Mapping)
                    else NutriValue(value=epa, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "sugar": (
                sugar
                if isinstance(sugar, NutriValue)
                else (
                    NutriValue(**sugar)
                    if isinstance(sugar, Mapping)
                    else NutriValue(value=sugar, unit=MeasureUnit.GRAM)
                )
            ),
            "starch": (
                starch
                if isinstance(starch, NutriValue)
                else (
                    NutriValue(**starch)
                    if isinstance(starch, Mapping)
                    else NutriValue(value=starch, unit=MeasureUnit.MICROGRAM)
                )
            ),
            "biotin": (
                biotin
                if isinstance(biotin, NutriValue)
                else (
                    NutriValue(**biotin)
                    if isinstance(biotin, Mapping)
                    else NutriValue(value=biotin, unit=MeasureUnit.MICROGRAM)
                )
            ),
            "boro": (
                boro
                if isinstance(boro, NutriValue)
                else (
                    NutriValue(**boro)
                    if isinstance(boro, Mapping)
                    else NutriValue(value=boro, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "caffeine": (
                caffeine
                if isinstance(caffeine, NutriValue)
                else (
                    NutriValue(**caffeine)
                    if isinstance(caffeine, Mapping)
                    else NutriValue(value=caffeine, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "calcium": (
                calcium
                if isinstance(calcium, NutriValue)
                else (
                    NutriValue(**calcium)
                    if isinstance(calcium, Mapping)
                    else NutriValue(value=calcium, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "chlorine": (
                chlorine
                if isinstance(chlorine, NutriValue)
                else (
                    NutriValue(**chlorine)
                    if isinstance(chlorine, Mapping)
                    else NutriValue(value=chlorine, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "copper": (
                copper
                if isinstance(copper, NutriValue)
                else (
                    NutriValue(**copper)
                    if isinstance(copper, Mapping)
                    else NutriValue(value=copper, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "cholesterol": (
                cholesterol
                if isinstance(cholesterol, NutriValue)
                else (
                    NutriValue(**cholesterol)
                    if isinstance(cholesterol, Mapping)
                    else NutriValue(value=cholesterol, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "choline": (
                choline
                if isinstance(choline, NutriValue)
                else (
                    NutriValue(**choline)
                    if isinstance(choline, Mapping)
                    else NutriValue(value=choline, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "chrome": (
                chrome
                if isinstance(chrome, NutriValue)
                else (
                    NutriValue(**chrome)
                    if isinstance(chrome, Mapping)
                    else NutriValue(value=chrome, unit=MeasureUnit.MICROGRAM)
                )
            ),
            "dextrose": (
                dextrose
                if isinstance(dextrose, NutriValue)
                else (
                    NutriValue(**dextrose)
                    if isinstance(dextrose, Mapping)
                    else NutriValue(value=dextrose, unit=MeasureUnit.GRAM)
                )
            ),
            "sulfur": (
                sulfur
                if isinstance(sulfur, NutriValue)
                else (
                    NutriValue(**sulfur)
                    if isinstance(sulfur, Mapping)
                    else NutriValue(value=sulfur, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "phenylalanine": (
                phenylalanine
                if isinstance(phenylalanine, NutriValue)
                else (
                    NutriValue(**phenylalanine)
                    if isinstance(phenylalanine, Mapping)
                    else NutriValue(value=phenylalanine, unit=MeasureUnit.GRAM)
                )
            ),
            "iron": (
                iron
                if isinstance(iron, NutriValue)
                else (
                    NutriValue(**iron)
                    if isinstance(iron, Mapping)
                    else NutriValue(value=iron, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "insoluble_fiber": (
                insoluble_fiber
                if isinstance(insoluble_fiber, NutriValue)
                else (
                    NutriValue(**insoluble_fiber)
                    if isinstance(insoluble_fiber, Mapping)
                    else NutriValue(value=insoluble_fiber, unit=MeasureUnit.GRAM)
                )
            ),
            "soluble_fiber": (
                soluble_fiber
                if isinstance(soluble_fiber, NutriValue)
                else (
                    NutriValue(**soluble_fiber)
                    if isinstance(soluble_fiber, Mapping)
                    else NutriValue(value=soluble_fiber, unit=MeasureUnit.GRAM)
                )
            ),
            "fluor": (
                fluor
                if isinstance(fluor, NutriValue)
                else (
                    NutriValue(**fluor)
                    if isinstance(fluor, Mapping)
                    else NutriValue(value=fluor, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "phosphorus": (
                phosphorus
                if isinstance(phosphorus, NutriValue)
                else (
                    NutriValue(**phosphorus)
                    if isinstance(phosphorus, Mapping)
                    else NutriValue(value=phosphorus, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "fructo_oligosaccharides": (
                fructo_oligosaccharides
                if isinstance(fructo_oligosaccharides, NutriValue)
                else (
                    NutriValue(**fructo_oligosaccharides)
                    if isinstance(fructo_oligosaccharides, Mapping)
                    else NutriValue(
                        value=fructo_oligosaccharides, unit=MeasureUnit.MILLIGRAM.value
                    )
                )
            ),
            "fructose": (
                fructose
                if isinstance(fructose, NutriValue)
                else (
                    NutriValue(**fructose)
                    if isinstance(fructose, Mapping)
                    else NutriValue(value=fructose, unit=MeasureUnit.GRAM)
                )
            ),
            "galacto_oligosaccharides": (
                galacto_oligosaccharides
                if isinstance(galacto_oligosaccharides, NutriValue)
                else (
                    NutriValue(**galacto_oligosaccharides)
                    if isinstance(galacto_oligosaccharides, Mapping)
                    else NutriValue(
                        value=galacto_oligosaccharides, unit=MeasureUnit.GRAM.value
                    )
                )
            ),
            "galactose": (
                galactose
                if isinstance(galactose, NutriValue)
                else (
                    NutriValue(**galactose)
                    if isinstance(galactose, Mapping)
                    else NutriValue(value=galactose, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "glucose": (
                glucose
                if isinstance(glucose, NutriValue)
                else (
                    NutriValue(**glucose)
                    if isinstance(glucose, Mapping)
                    else NutriValue(value=glucose, unit=MeasureUnit.GRAM)
                )
            ),
            "glucoronolactone": (
                glucoronolactone
                if isinstance(glucoronolactone, NutriValue)
                else (
                    NutriValue(**glucoronolactone)
                    if isinstance(glucoronolactone, Mapping)
                    else NutriValue(
                        value=glucoronolactone, unit=MeasureUnit.MILLIGRAM.value
                    )
                )
            ),
            "monounsaturated_fat": (
                monounsaturated_fat
                if isinstance(monounsaturated_fat, NutriValue)
                else (
                    NutriValue(**monounsaturated_fat)
                    if isinstance(monounsaturated_fat, Mapping)
                    else NutriValue(
                        value=monounsaturated_fat, unit=MeasureUnit.GRAM.value
                    )
                )
            ),
            "polyunsaturated_fat": (
                polyunsaturated_fat
                if isinstance(polyunsaturated_fat, NutriValue)
                else (
                    NutriValue(**polyunsaturated_fat)
                    if isinstance(polyunsaturated_fat, Mapping)
                    else NutriValue(
                        value=polyunsaturated_fat, unit=MeasureUnit.GRAM.value
                    )
                )
            ),
            "guarana": (
                guarana
                if isinstance(guarana, NutriValue)
                else (
                    NutriValue(**guarana)
                    if isinstance(guarana, Mapping)
                    else NutriValue(value=guarana, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "inositol": (
                inositol
                if isinstance(inositol, NutriValue)
                else (
                    NutriValue(**inositol)
                    if isinstance(inositol, Mapping)
                    else NutriValue(value=inositol, unit=MeasureUnit.GRAM)
                )
            ),
            "inulin": (
                inulin
                if isinstance(inulin, NutriValue)
                else (
                    NutriValue(**inulin)
                    if isinstance(inulin, Mapping)
                    else NutriValue(value=inulin, unit=MeasureUnit.GRAM)
                )
            ),
            "iodine": (
                iodine
                if isinstance(iodine, NutriValue)
                else (
                    NutriValue(**iodine)
                    if isinstance(iodine, Mapping)
                    else NutriValue(value=iodine, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "l_carnitine": (
                l_carnitine
                if isinstance(l_carnitine, NutriValue)
                else (
                    NutriValue(**l_carnitine)
                    if isinstance(l_carnitine, Mapping)
                    else NutriValue(value=l_carnitine, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "l_methionine": (
                l_methionine
                if isinstance(l_methionine, NutriValue)
                else (
                    NutriValue(**l_methionine)
                    if isinstance(l_methionine, Mapping)
                    else NutriValue(value=l_methionine, unit=MeasureUnit.GRAM)
                )
            ),
            "lactose": (
                lactose
                if isinstance(lactose, NutriValue)
                else (
                    NutriValue(**lactose)
                    if isinstance(lactose, Mapping)
                    else NutriValue(value=lactose, unit=MeasureUnit.GRAM)
                )
            ),
            "magnesium": (
                magnesium
                if isinstance(magnesium, NutriValue)
                else (
                    NutriValue(**magnesium)
                    if isinstance(magnesium, Mapping)
                    else NutriValue(value=magnesium, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "maltose": (
                maltose
                if isinstance(maltose, NutriValue)
                else (
                    NutriValue(**maltose)
                    if isinstance(maltose, Mapping)
                    else NutriValue(value=maltose, unit=MeasureUnit.GRAM)
                )
            ),
            "manganese": (
                manganese
                if isinstance(manganese, NutriValue)
                else (
                    NutriValue(**manganese)
                    if isinstance(manganese, Mapping)
                    else NutriValue(value=manganese, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "molybdenum": (
                molybdenum
                if isinstance(molybdenum, NutriValue)
                else (
                    NutriValue(**molybdenum)
                    if isinstance(molybdenum, Mapping)
                    else NutriValue(value=molybdenum, unit=MeasureUnit.MICROGRAM)
                )
            ),
            "linolenic_acid": (
                linolenic_acid
                if isinstance(linolenic_acid, NutriValue)
                else (
                    NutriValue(**linolenic_acid)
                    if isinstance(linolenic_acid, Mapping)
                    else NutriValue(value=linolenic_acid, unit=MeasureUnit.GRAM)
                )
            ),
            "linoleic_acid": (
                linoleic_acid
                if isinstance(linoleic_acid, NutriValue)
                else (
                    NutriValue(**linoleic_acid)
                    if isinstance(linoleic_acid, Mapping)
                    else NutriValue(value=linoleic_acid, unit=MeasureUnit.GRAM)
                )
            ),
            "omega_7": (
                omega_7
                if isinstance(omega_7, NutriValue)
                else (
                    NutriValue(**omega_7)
                    if isinstance(omega_7, Mapping)
                    else NutriValue(value=omega_7, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "omega_9": (
                omega_9
                if isinstance(omega_9, NutriValue)
                else (
                    NutriValue(**omega_9)
                    if isinstance(omega_9, Mapping)
                    else NutriValue(value=omega_9, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "oleic_acid": (
                oleic_acid
                if isinstance(oleic_acid, NutriValue)
                else (
                    NutriValue(**oleic_acid)
                    if isinstance(oleic_acid, Mapping)
                    else NutriValue(value=oleic_acid, unit=MeasureUnit.GRAM)
                )
            ),
            "other_carbo": (
                other_carbo
                if isinstance(other_carbo, NutriValue)
                else (
                    NutriValue(**other_carbo)
                    if isinstance(other_carbo, Mapping)
                    else NutriValue(value=other_carbo, unit=MeasureUnit.GRAM)
                )
            ),
            "polydextrose": (
                polydextrose
                if isinstance(polydextrose, NutriValue)
                else (
                    NutriValue(**polydextrose)
                    if isinstance(polydextrose, Mapping)
                    else NutriValue(value=polydextrose, unit=MeasureUnit.GRAM)
                )
            ),
            "polyols": (
                polyols
                if isinstance(polyols, NutriValue)
                else (
                    NutriValue(**polyols)
                    if isinstance(polyols, Mapping)
                    else NutriValue(value=polyols, unit=MeasureUnit.GRAM)
                )
            ),
            "potassium": (
                potassium
                if isinstance(potassium, NutriValue)
                else (
                    NutriValue(**potassium)
                    if isinstance(potassium, Mapping)
                    else NutriValue(value=potassium, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "sacarose": (
                sacarose
                if isinstance(sacarose, NutriValue)
                else (
                    NutriValue(**sacarose)
                    if isinstance(sacarose, Mapping)
                    else NutriValue(value=sacarose, unit=MeasureUnit.GRAM)
                )
            ),
            "selenium": (
                selenium
                if isinstance(selenium, NutriValue)
                else (
                    NutriValue(**selenium)
                    if isinstance(selenium, Mapping)
                    else NutriValue(value=selenium, unit=MeasureUnit.MICROGRAM)
                )
            ),
            "silicon": (
                silicon
                if isinstance(silicon, NutriValue)
                else (
                    NutriValue(**silicon)
                    if isinstance(silicon, Mapping)
                    else NutriValue(value=silicon, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "sorbitol": (
                sorbitol
                if isinstance(sorbitol, NutriValue)
                else (
                    NutriValue(**sorbitol)
                    if isinstance(sorbitol, Mapping)
                    else NutriValue(value=sorbitol, unit=MeasureUnit.GRAM)
                )
            ),
            "sucralose": (
                sucralose
                if isinstance(sucralose, NutriValue)
                else (
                    NutriValue(**sucralose)
                    if isinstance(sucralose, Mapping)
                    else NutriValue(value=sucralose, unit=MeasureUnit.GRAM)
                )
            ),
            "taurine": (
                taurine
                if isinstance(taurine, NutriValue)
                else (
                    NutriValue(**taurine)
                    if isinstance(taurine, Mapping)
                    else NutriValue(value=taurine, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "vitamin_a": (
                vitamin_a
                if isinstance(vitamin_a, NutriValue)
                else (
                    NutriValue(**vitamin_a)
                    if isinstance(vitamin_a, Mapping)
                    else NutriValue(value=vitamin_a, unit=MeasureUnit.IU)
                )
            ),
            "vitamin_b1": (
                vitamin_b1
                if isinstance(vitamin_b1, NutriValue)
                else (
                    NutriValue(**vitamin_b1)
                    if isinstance(vitamin_b1, Mapping)
                    else NutriValue(value=vitamin_b1, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "vitamin_b2": (
                vitamin_b2
                if isinstance(vitamin_b2, NutriValue)
                else (
                    NutriValue(**vitamin_b2)
                    if isinstance(vitamin_b2, Mapping)
                    else NutriValue(value=vitamin_b2, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "vitamin_b3": (
                vitamin_b3
                if isinstance(vitamin_b3, NutriValue)
                else (
                    NutriValue(**vitamin_b3)
                    if isinstance(vitamin_b3, Mapping)
                    else NutriValue(value=vitamin_b3, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "vitamin_b5": (
                vitamin_b5
                if isinstance(vitamin_b5, NutriValue)
                else (
                    NutriValue(**vitamin_b5)
                    if isinstance(vitamin_b5, Mapping)
                    else NutriValue(value=vitamin_b5, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "vitamin_b6": (
                vitamin_b6
                if isinstance(vitamin_b6, NutriValue)
                else (
                    NutriValue(**vitamin_b6)
                    if isinstance(vitamin_b6, Mapping)
                    else NutriValue(value=vitamin_b6, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "folic_acid": (
                folic_acid
                if isinstance(folic_acid, NutriValue)
                else (
                    NutriValue(**folic_acid)
                    if isinstance(folic_acid, Mapping)
                    else NutriValue(value=folic_acid, unit=MeasureUnit.MICROGRAM)
                )
            ),
            "vitamin_b12": (
                vitamin_b12
                if isinstance(vitamin_b12, NutriValue)
                else (
                    NutriValue(**vitamin_b12)
                    if isinstance(vitamin_b12, Mapping)
                    else NutriValue(value=vitamin_b12, unit=MeasureUnit.MICROGRAM)
                )
            ),
            "vitamin_c": (
                vitamin_c
                if isinstance(vitamin_c, NutriValue)
                else (
                    NutriValue(**vitamin_c)
                    if isinstance(vitamin_c, Mapping)
                    else NutriValue(value=vitamin_c, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "vitamin_d": (
                vitamin_d
                if isinstance(vitamin_d, NutriValue)
                else (
                    NutriValue(**vitamin_d)
                    if isinstance(vitamin_d, Mapping)
                    else NutriValue(value=vitamin_d, unit=MeasureUnit.IU)
                )
            ),
            "vitamin_e": (
                vitamin_e
                if isinstance(vitamin_e, NutriValue)
                else (
                    NutriValue(**vitamin_e)
                    if isinstance(vitamin_e, Mapping)
                    else NutriValue(value=vitamin_e, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "vitamin_k": (
                vitamin_k
                if isinstance(vitamin_k, NutriValue)
                else (
                    NutriValue(**vitamin_k)
                    if isinstance(vitamin_k, Mapping)
                    else NutriValue(value=vitamin_k, unit=MeasureUnit.MICROGRAM)
                )
            ),
            "zinc": (
                zinc
                if isinstance(zinc, NutriValue)
                else (
                    NutriValue(**zinc)
                    if isinstance(zinc, Mapping)
                    else NutriValue(value=zinc, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "retinol": (
                retinol
                if isinstance(retinol, NutriValue)
                else (
                    NutriValue(**retinol)
                    if isinstance(retinol, Mapping)
                    else NutriValue(value=retinol, unit=MeasureUnit.MICROGRAM)
                )
            ),
            "thiamine": (
                thiamine
                if isinstance(thiamine, NutriValue)
                else (
                    NutriValue(**thiamine)
                    if isinstance(thiamine, Mapping)
                    else NutriValue(value=thiamine, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "riboflavin": (
                riboflavin
                if isinstance(riboflavin, NutriValue)
                else (
                    NutriValue(**riboflavin)
                    if isinstance(riboflavin, Mapping)
                    else NutriValue(value=riboflavin, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "pyridoxine": (
                pyridoxine
                if isinstance(pyridoxine, NutriValue)
                else (
                    NutriValue(**pyridoxine)
                    if isinstance(pyridoxine, Mapping)
                    else NutriValue(value=pyridoxine, unit=MeasureUnit.MILLIGRAM)
                )
            ),
            "niacin": (
                niacin
                if isinstance(niacin, NutriValue)
                else (
                    NutriValue(**niacin)
                    if isinstance(niacin, Mapping)
                    else NutriValue(value=niacin, unit=MeasureUnit.MILLIGRAM)
                )
            ),
        }
        self.__attrs_init__(**args)

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
