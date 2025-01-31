KIND_EI = "EI"
KIND_AI = "AI"
KIND_ACI = "ACI"
KIND_ETTI = "ETTI"
KIND_EITI = "EITI"
KIND_GEIQ = "GEIQ"
KIND_EA = "EA"
KIND_EATT = "EATT"
KIND_ESAT = "ESAT"
KIND_SEP = "SEP"

KIND_PARENT_INSERTION_NAME = "Insertion"
KIND_INSERTION_CHOICES = (
    (KIND_EI, "Entreprise d'insertion"),  # Regroupées au sein de la fédération des entreprises d'insertion.
    (KIND_AI, "Association intermédiaire"),
    (KIND_ACI, "Atelier chantier d'insertion"),
    # (KIND_ACIPHC, "Atelier chantier d'insertion premières heures en chantier"),
    (KIND_ETTI, "Entreprise de travail temporaire d'insertion"),
    (KIND_EITI, "Entreprise d'insertion par le travail indépendant"),
    (KIND_GEIQ, "Groupement d'employeurs pour l'insertion et la qualification"),
    (KIND_SEP, "Produits et services réalisés en prison"),
)
KIND_INSERTION_CHOICES_WITH_EXTRA = [(key, f"{value} ({key})") for (key, value) in KIND_INSERTION_CHOICES]
KIND_INSERTION_LIST = [k[0] for k in KIND_INSERTION_CHOICES]

KIND_PARENT_HANDICAP_NAME = "Handicap"
KIND_HANDICAP_CHOICES = (
    (KIND_EA, "Entreprise adaptée"),
    (KIND_EATT, "Entreprise adaptée de travail temporaire"),
    (KIND_ESAT, "Etablissement et service d'aide par le travail"),
)
KIND_HANDICAP_CHOICES_WITH_EXTRA = [(key, f"{value} ({key})") for (key, value) in KIND_HANDICAP_CHOICES]
KIND_HANDICAP_LIST = [k[0] for k in KIND_HANDICAP_CHOICES]

KIND_CHOICES = KIND_INSERTION_CHOICES + KIND_HANDICAP_CHOICES
KIND_CHOICES_WITH_EXTRA = KIND_INSERTION_CHOICES_WITH_EXTRA + KIND_HANDICAP_CHOICES_WITH_EXTRA

PRESTA_DISP = "DISP"
PRESTA_PREST = "PREST"
PRESTA_BUILD = "BUILD"

PRESTA_CHOICES = (
    (PRESTA_DISP, "Mise à disposition - Interim"),  # 0010
    (PRESTA_PREST, "Prestation de service"),  # 0100
    (PRESTA_BUILD, "Fabrication et commercialisation de biens"),  # 1000
)

LEGAL_FORM_SARL = "SARL"
LEGAL_FORM_SARL_COOP = "SARL_COOP"
LEGAL_FORM_SAS = "SAS"
LEGAL_FORM_SA = "SA"
LEGAL_FORM_SA_COOP = "SA_COOP"
LEGAL_FORM_SNC = "SNC"
LEGAL_FORM_ASSOCIATION = "ASSOCIATION"
LEGAL_FORM_GROUPEMENT_EMPLOYEUR = "GROUPEMENT_EMPLOYEUR"
LEGAL_FORM_COLLECTIVITE = "COLLECTIVITE"
LEGAL_FORM_CCAS = "CCAS"
LEGAL_FORM_EPSMS = "EPSMS"
LEGAL_FORM_FONDATION = "FONDATION"
LEGAL_FORM_AUTRE = "AUTRE"

LEGAL_FORM_CHOICES = (
    (LEGAL_FORM_SARL, "SARL"),
    (LEGAL_FORM_SARL_COOP, "SARL coopérative"),
    (LEGAL_FORM_SAS, "SAS (Société par actions simplifiée)"),
    (LEGAL_FORM_SA, "SA (Société anonyme)"),
    (LEGAL_FORM_SA_COOP, "SA coopérative"),
    (LEGAL_FORM_SNC, "SNC (Société en nom collectif)"),
    (LEGAL_FORM_ASSOCIATION, "Association"),
    (LEGAL_FORM_GROUPEMENT_EMPLOYEUR, "Groupement d'employeurs"),
    (LEGAL_FORM_COLLECTIVITE, "Collectivité"),
    (LEGAL_FORM_CCAS, "CCAS (Centre (inter)communal d'action sociale)"),
    (LEGAL_FORM_EPSMS, "EPSMS (Établissement public social ou médico-social)"),
    (LEGAL_FORM_FONDATION, "Fondation"),
    (LEGAL_FORM_AUTRE, "Autre"),
)
SIAE_LEGAL_FORM_CHOICE_LIST = [lf[0] for lf in LEGAL_FORM_CHOICES]

GEO_RANGE_DEPARTMENT = "DEPARTMENT"
GEO_RANGE_REGION = "REGION"
GEO_RANGE_CUSTOM = "CUSTOM"
GEO_RANGE_COUNTRY = "COUNTRY"
GEO_RANGE_ZONES = "ZONES"

GEO_RANGE_CHOICES = (
    (GEO_RANGE_COUNTRY, "France entière"),
    (GEO_RANGE_REGION, "Région"),
    (GEO_RANGE_DEPARTMENT, "Département"),
    (GEO_RANGE_CUSTOM, "Distance en kilomètres"),
)

ACTIVITIES_GEO_RANGE_CHOICES = (
    (GEO_RANGE_COUNTRY, "France entière"),
    (GEO_RANGE_CUSTOM, "Distance en kilomètres"),
    (GEO_RANGE_ZONES, "Zone(s) d'intervention personnalisée(s)"),
)

SOURCE_ASP = "ASP"
SOURCE_GEIQ = "GEIQ"
SOURCE_EA_EATT = "EA_EATT"
SOURCE_USER_CREATED = "USER_CREATED"
SOURCE_STAFF_C1_CREATED = "STAFF_C1_CREATED"
SOURCE_STAFF_C4_CREATED = "STAFF_C4_CREATED"
SOURCE_ESAT = "ESAT"
SOURCE_SEP = "SEP"

SOURCE_CHOICES = (
    (SOURCE_ASP, "Export ASP"),
    (SOURCE_GEIQ, "Export GEIQ"),
    (SOURCE_EA_EATT, "Export EA+EATT"),
    (SOURCE_USER_CREATED, "Utilisateur (Antenne)"),
    (SOURCE_STAFF_C1_CREATED, "Staff C1"),
    (SOURCE_STAFF_C4_CREATED, "Staff C4"),
    (SOURCE_ESAT, "Import ESAT (GSAT, Handeco)"),
    (SOURCE_SEP, "Import SEP"),
)

NATURE_HEAD_OFFICE = "HEAD_OFFICE"
NATURE_ANTENNA = "ANTENNA"

NATURE_CHOICES = (
    (NATURE_HEAD_OFFICE, "Conventionné par la DREETS"),
    (NATURE_ANTENNA, "Rattaché à un autre conventionnement"),
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
    "sector_count": {
        COMPLETION_SCORE_KEY: 15,
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
