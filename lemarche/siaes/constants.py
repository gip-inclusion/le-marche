# https://github.com/betagouv/itou/blob/master/itou/common_apps/address/departments.py

REGIONS = {
    "01": "Guadeloupe",
    "02": "Martinique",
    "03": "Guyane",
    "04": "La Réunion",
    "06": "Mayotte",
    "11": "Île-de-France",
    "24": "Centre-Val de Loire",
    "27": "Bourgogne-Franche-Comté",
    "28": "Normandie",
    "32": "Hauts-de-France",
    "44": "Grand Est",
    "52": "Pays de la Loire",
    "53": "Bretagne",
    "75": "Nouvelle-Aquitaine",
    "76": "Occitanie",
    "84": "Auvergne-Rhône-Alpes",
    "93": "Provence-Alpes-Côte d'Azur",
    "94": "Corse",
    "97": "Collectivités d'outre-mer",
}

REGIONS_WITH_DEPARTMENTS = {
    "Auvergne-Rhône-Alpes": ["01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"],
    "Bourgogne-Franche-Comté": ["21", "25", "39", "58", "70", "71", "89", "90"],
    "Bretagne": ["35", "22", "56", "29"],
    "Centre-Val de Loire": ["18", "28", "36", "37", "41", "45"],
    "Corse": ["2A", "2B"],
    "Grand Est": ["08", "10", "51", "52", "54", "55", "57", "67", "68", "88"],
    "Guadeloupe": ["971"],
    "Guyane": ["973"],
    "Hauts-de-France": ["02", "59", "60", "62", "80"],
    "Île-de-France": ["75", "77", "78", "91", "92", "93", "94", "95"],
    "La Réunion": ["974"],
    "Martinique": ["972"],
    "Mayotte": ["976"],
    "Normandie": ["14", "27", "50", "61", "76"],
    "Nouvelle-Aquitaine": ["16", "17", "19", "23", "24", "33", "40", "47", "64", "79", "86", "87"],
    "Occitanie": ["09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"],
    "Pays de la Loire": ["44", "49", "53", "72", "85"],
    "Provence-Alpes-Côte d'Azur": ["04", "05", "06", "13", "83", "84"],
    "Collectivités d'outre-mer": ["975", "977", "978", "984", "986", "987", "988", "989"],  # updated
    # "Anciens territoires d'outre-mer": ["986", "987", "988"],  # moved above
}

# difference: ordered by name
REGIONS_PRETTY = dict((name, name) for (name, list) in REGIONS_WITH_DEPARTMENTS.items())

REGIONS_WITH_IDENTICAL_DEPARTMENT_NAME = ["Guadeloupe", "Martinique", "Guyane", "La Réunion", "Mayotte"]


def get_region_code_from_name(region_name):
    return next((code for code, name in REGIONS.items() if name == region_name), None)


def get_department_to_region():
    department_to_region = {}
    for region, dpts in REGIONS_WITH_DEPARTMENTS.items():
        for dpt in dpts:
            department_to_region[dpt] = region
    return department_to_region


DEPARTMENT_TO_REGION = get_department_to_region()

DEPARTMENTS = {
    "01": "Ain",
    "02": "Aisne",
    "03": "Allier",
    "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes",
    "06": "Alpes-Maritimes",
    "07": "Ardèche",
    "08": "Ardennes",
    "09": "Ariège",
    "10": "Aube",
    "11": "Aude",
    "12": "Aveyron",
    "13": "Bouches-du-Rhône",
    "14": "Calvados",
    "15": "Cantal",
    "16": "Charente",
    "17": "Charente-Maritime",
    "18": "Cher",
    "19": "Corrèze",
    "2A": "Corse-du-Sud",
    "2B": "Haute-Corse",
    "21": "Côte-d'Or",
    "22": "Côtes-d'Armor",
    "23": "Creuse",
    "24": "Dordogne",
    "25": "Doubs",
    "26": "Drôme",
    "27": "Eure",
    "28": "Eure-et-Loir",
    "29": "Finistère",
    "30": "Gard",
    "31": "Haute-Garonne",
    "32": "Gers",
    "33": "Gironde",
    "34": "Hérault",
    "35": "Ille-et-Vilaine",
    "36": "Indre",
    "37": "Indre-et-Loire",
    "38": "Isère",
    "39": "Jura",
    "40": "Landes",
    "41": "Loir-et-Cher",
    "42": "Loire",
    "43": "Haute-Loire",
    "44": "Loire-Atlantique",
    "45": "Loiret",
    "46": "Lot",
    "47": "Lot-et-Garonne",
    "48": "Lozère",
    "49": "Maine-et-Loire",
    "50": "Manche",
    "51": "Marne",
    "52": "Haute-Marne",
    "53": "Mayenne",
    "54": "Meurthe-et-Moselle",
    "55": "Meuse",
    "56": "Morbihan",
    "57": "Moselle",
    "58": "Nièvre",
    "59": "Nord",
    "60": "Oise",
    "61": "Orne",
    "62": "Pas-de-Calais",
    "63": "Puy-de-Dôme",
    "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées",
    "66": "Pyrénées-Orientales",
    "67": "Bas-Rhin",
    "68": "Haut-Rhin",
    "69": "Rhône",
    "70": "Haute-Saône",
    "71": "Saône-et-Loire",
    "72": "Sarthe",
    "73": "Savoie",
    "74": "Haute-Savoie",
    "75": "Paris",
    "76": "Seine-Maritime",
    "77": "Seine-et-Marne",
    "78": "Yvelines",
    "79": "Deux-Sèvres",
    "80": "Somme",
    "81": "Tarn",
    "82": "Tarn-et-Garonne",
    "83": "Var",
    "84": "Vaucluse",
    "85": "Vendée",
    "86": "Vienne",
    "87": "Haute-Vienne",
    "88": "Vosges",
    "89": "Yonne",
    "90": "Territoire de Belfort",
    "91": "Essonne",
    "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne",
    "95": "Val-d'Oise",
    "971": "Guadeloupe",
    "972": "Martinique",
    "973": "Guyane",
    "974": "La Réunion",
    "975": "Saint-Pierre-et-Miquelon",
    "976": "Mayotte",
    "977": "Saint-Barthélémy",
    "978": "Saint-Martin",
    "984": "Terres australes et antarctiques françaises",  # added
    "986": "Wallis-et-Futuna",
    "987": "Polynésie française",
    "988": "Nouvelle-Calédonie",
    "989": "Île de Clipperton",  # added
}

# Marseille, Lyon and Paris
# The "max" value is the maximum postal code of the districts of the department
DEPARTMENTS_WITH_DISTRICTS = {
    "13": {"city": "Marseille", "max": 13016},
    "69": {"city": "Lyon", "max": 69009},
    "75": {"city": "Paris", "max": 75020},
}

# difference: {"01": "01 - Ain"}
DEPARTMENTS_PRETTY = dict((code, code + " - " + name) for (code, name) in DEPARTMENTS.items())


def get_department_code_from_name(department_name):
    return next((code for code, name in DEPARTMENTS.items() if name == department_name), None)


def department_from_postcode(post_code):
    """
    Extract the department from the postal code (if possible)
    """
    department = ""
    if post_code:
        if post_code.startswith("20"):
            a_post_codes = ("200", "201", "207")
            b_post_codes = ("202", "204", "206")
            if post_code.startswith(a_post_codes):
                department = "2A"
            elif post_code.startswith(b_post_codes):
                department = "2B"
        elif post_code.startswith("97") or post_code.startswith("98"):
            department = post_code[:3]
        else:
            department = post_code[:2]

    return department


def format_district(post_code, department):
    # Could use ordinal from humanize but it would be overkill
    number = int(post_code) - (int(department) * 1000)
    return "1er" if number == 1 else f"{number}e"


PRESTA_DISP = "DISP"
PRESTA_PREST = "PREST"
PRESTA_BUILD = "BUILD"

PRESTA_CHOICES = (
    (PRESTA_DISP, "Mise à disposition - Interim"),  # 0010
    (PRESTA_PREST, "Prestation de service"),  # 0100
    (PRESTA_BUILD, "Fabrication et commercialisation de biens"),  # 1000
)


COMPLETION_KIND_KEY = "kind"
COMPLETION_SCORE_KEY = "score"
COMPLETION_COMPARE_TO_KEY = "compare_to"

COMPLETION_KIND_NOT_EMPTY_OR_FALSE = "NOT_EMPTY_OR_FALSE"
COMPLETION_KIND_GREATER_THAN = "GREATER_THAN"

SIAE_COMPLETION_SCORE_GRID = {
    "logo_url": {
        COMPLETION_SCORE_KEY: 5,
        COMPLETION_KIND_KEY: COMPLETION_KIND_NOT_EMPTY_OR_FALSE,
    },
    "contact_email": {
        COMPLETION_SCORE_KEY: 5,
        COMPLETION_KIND_KEY: COMPLETION_KIND_NOT_EMPTY_OR_FALSE,
    },
    "contact_phone": {
        COMPLETION_SCORE_KEY: 5,
        COMPLETION_KIND_KEY: COMPLETION_KIND_NOT_EMPTY_OR_FALSE,
    },
    "presta_type": {
        COMPLETION_SCORE_KEY: 5,
        COMPLETION_KIND_KEY: COMPLETION_KIND_NOT_EMPTY_OR_FALSE,
    },
    "geo_range": {
        COMPLETION_SCORE_KEY: 5,
        COMPLETION_KIND_KEY: COMPLETION_KIND_NOT_EMPTY_OR_FALSE,
    },
    "sector_count": {
        COMPLETION_SCORE_KEY: 5,
        COMPLETION_KIND_KEY: COMPLETION_KIND_GREATER_THAN,
        COMPLETION_COMPARE_TO_KEY: 1,
    },
    "description": {
        COMPLETION_SCORE_KEY: 4,
        COMPLETION_KIND_KEY: COMPLETION_KIND_NOT_EMPTY_OR_FALSE,
    },
    "offer_count": {
        COMPLETION_SCORE_KEY: 4,
        COMPLETION_KIND_KEY: COMPLETION_KIND_GREATER_THAN,
        COMPLETION_COMPARE_TO_KEY: 1,
    },
    "client_reference_count": {
        COMPLETION_SCORE_KEY: 3,
        COMPLETION_KIND_KEY: COMPLETION_KIND_GREATER_THAN,
        COMPLETION_COMPARE_TO_KEY: 2,
    },
    "ca": {
        COMPLETION_SCORE_KEY: 3,
        COMPLETION_KIND_KEY: COMPLETION_KIND_NOT_EMPTY_OR_FALSE,
    },
    "employees_insertion_count": {
        COMPLETION_SCORE_KEY: 3,
        COMPLETION_KIND_KEY: COMPLETION_KIND_GREATER_THAN,
        COMPLETION_COMPARE_TO_KEY: 0,
    },
    "label_count": {
        COMPLETION_SCORE_KEY: 3,
        COMPLETION_KIND_KEY: COMPLETION_KIND_GREATER_THAN,
        COMPLETION_COMPARE_TO_KEY: 0,
    },
    "is_cocontracting": {
        COMPLETION_SCORE_KEY: 2,
        COMPLETION_KIND_KEY: COMPLETION_KIND_NOT_EMPTY_OR_FALSE,
    },
    "image_count": {
        COMPLETION_SCORE_KEY: 2,
        COMPLETION_KIND_KEY: COMPLETION_KIND_GREATER_THAN,
        COMPLETION_COMPARE_TO_KEY: 2,
    },
    "employees_permanent_count": {
        COMPLETION_SCORE_KEY: 2,
        COMPLETION_KIND_KEY: COMPLETION_KIND_GREATER_THAN,
        COMPLETION_COMPARE_TO_KEY: 2,
    },
    "network_count": {
        COMPLETION_SCORE_KEY: 1,
        COMPLETION_KIND_KEY: COMPLETION_KIND_GREATER_THAN,
        COMPLETION_COMPARE_TO_KEY: 2,
    },
    "year_constitution": {
        COMPLETION_SCORE_KEY: 1,
        COMPLETION_KIND_KEY: COMPLETION_KIND_NOT_EMPTY_OR_FALSE,
    },
    # groupements 1
}
