from dataclasses import dataclass


@dataclass
class NutriFactsSaModel:
    """SQLAlchemy composite dataclass for nutritional facts fields.

    Attributes:
        calories: Caloric content.
        protein: Protein content.
        carbohydrate: Carbohydrate content.
        total_fat: Total fat content.
        saturated_fat: Saturated fat content.
        trans_fat: Trans fat content.
        dietary_fiber: Dietary fiber content.
        sodium: Sodium content.
        arachidonic_acid: Arachidonic acid content.
        ashes: Ash content.
        dha: DHA content.
        epa: EPA content.
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
        other_carbo: Other carbohydrates content.
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
        Dataclass storing raw numeric nutrition fields for ORM persistence.
        All fields are optional to support partial nutritional data.
    """
    calories: float | None = None
    protein: float | None = None
    carbohydrate: float | None = None
    total_fat: float | None = None
    saturated_fat: float | None = None
    trans_fat: float | None = None
    dietary_fiber: float | None = None
    sodium: float | None = None
    arachidonic_acid: float | None = None
    ashes: float | None = None
    dha: float | None = None
    epa: float | None = None
    sugar: float | None = None
    starch: float | None = None
    biotin: float | None = None
    boro: float | None = None
    caffeine: float | None = None
    calcium: float | None = None
    chlorine: float | None = None
    copper: float | None = None
    cholesterol: float | None = None
    choline: float | None = None
    chrome: float | None = None
    dextrose: float | None = None
    sulfur: float | None = None
    phenylalanine: float | None = None
    iron: float | None = None
    insoluble_fiber: float | None = None
    soluble_fiber: float | None = None
    fluor: float | None = None
    phosphorus: float | None = None
    fructo_oligosaccharides: float | None = None
    fructose: float | None = None
    galacto_oligosaccharides: float | None = None
    galactose: float | None = None
    glucose: float | None = None
    glucoronolactone: float | None = None
    monounsaturated_fat: float | None = None
    polyunsaturated_fat: float | None = None
    guarana: float | None = None
    inositol: float | None = None
    inulin: float | None = None
    iodine: float | None = None
    l_carnitine: float | None = None
    l_methionine: float | None = None
    lactose: float | None = None
    magnesium: float | None = None
    maltose: float | None = None
    manganese: float | None = None
    molybdenum: float | None = None
    linolenic_acid: float | None = None
    linoleic_acid: float | None = None
    omega_7: float | None = None
    omega_9: float | None = None
    oleic_acid: float | None = None
    other_carbo: float | None = None
    polydextrose: float | None = None
    polyols: float | None = None
    potassium: float | None = None
    sacarose: float | None = None
    selenium: float | None = None
    silicon: float | None = None
    sorbitol: float | None = None
    sucralose: float | None = None
    taurine: float | None = None
    vitamin_a: float | None = None
    vitamin_b1: float | None = None
    vitamin_b2: float | None = None
    vitamin_b3: float | None = None
    vitamin_b5: float | None = None
    vitamin_b6: float | None = None
    folic_acid: float | None = None
    vitamin_b12: float | None = None
    vitamin_c: float | None = None
    vitamin_d: float | None = None
    vitamin_e: float | None = None
    vitamin_k: float | None = None
    zinc: float | None = None
    retinol: float | None = None
    thiamine: float | None = None
    riboflavin: float | None = None
    pyridoxine: float | None = None
    niacin: float | None = None
