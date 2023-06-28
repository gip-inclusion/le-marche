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

KIND_CHOICES = (
    (KIND_EI, "Entreprise d'insertion"),  # Regroupées au sein de la fédération des entreprises d'insertion.
    (KIND_AI, "Association intermédiaire"),
    (KIND_ACI, "Atelier chantier d'insertion"),
    # (KIND_ACIPHC, "Atelier chantier d'insertion premières heures en chantier"),
    (KIND_ETTI, "Entreprise de travail temporaire d'insertion"),
    (KIND_EITI, "Entreprise d'insertion par le travail indépendant"),
    (KIND_GEIQ, "Groupement d'employeurs pour l'insertion et la qualification"),
    (KIND_EA, "Entreprise adaptée"),
    (KIND_EATT, "Entreprise adaptée de travail temporaire"),
    (KIND_ESAT, "Etablissement et service d'aide par le travail"),
    (KIND_SEP, "Produits et services réalisés en prison"),
)
# KIND_CHOICES_WITH_EXTRA = ((key, f"{value} ({key})") for (key, value) in KIND_CHOICES)
KIND_CHOICES_WITH_EXTRA_INSERTION = (
    (KIND_EI, "Entreprise d'insertion (EI)"),  # Regroupées au sein de la fédération des entreprises d'insertion.
    (KIND_AI, "Association intermédiaire (AI)"),
    (KIND_ACI, "Atelier chantier d'insertion (ACI)"),
    # (KIND_ACIPHC, "Atelier chantier d'insertion premières heures en chantier (ACIPHC)"),
    (KIND_ETTI, "Entreprise de travail temporaire d'insertion (ETTI)"),
    (KIND_EITI, "Entreprise d'insertion par le travail indépendant (EITI)"),
    (KIND_GEIQ, "Groupement d'employeurs pour l'insertion et la qualification (GEIQ)"),
    (KIND_SEP, "Produits et services réalisés en prison"),  # (SEP) ne s'applique pas à toutes les structures
)
KIND_CHOICES_WITH_EXTRA_HANDICAP = (
    (KIND_EA, "Entreprise adaptée (EA)"),
    (KIND_EATT, "Entreprise adaptée de travail temporaire (EATT)"),
    (KIND_ESAT, "Etablissement et service d'aide par le travail (ESAT)"),
)
KIND_CHOICES_WITH_EXTRA = KIND_CHOICES_WITH_EXTRA_INSERTION + KIND_CHOICES_WITH_EXTRA_HANDICAP


PRESTA_DISP = "DISP"
PRESTA_PREST = "PREST"
PRESTA_BUILD = "BUILD"

PRESTA_CHOICES = (
    (PRESTA_DISP, "Mise à disposition - Interim"),  # 0010
    (PRESTA_PREST, "Prestation de service"),  # 0100
    (PRESTA_BUILD, "Fabrication et commercialisation de biens"),  # 1000
)

LEGAL_FORM_ASSOCIATION = "ASSOCIATION"
LEGAL_FORM_SARL = "SARL"
LEGAL_FORM_SARL_COOP = "SARL_COOP"
LEGAL_FORM_SAS = "SAS"
LEGAL_FORM_SA = "SA"
LEGAL_FORM_SA_COOP = "SA_COOP"
LEGAL_FORM_SNC = "SNC"
LEGAL_FORM_FONDATION = "FONDATION"
LEGAL_FORM_AUTRE = "AUTRE"

LEGAL_FORM_CHOICES = (
    (LEGAL_FORM_ASSOCIATION, "Association"),
    (LEGAL_FORM_SARL, "SARL"),
    (LEGAL_FORM_SARL_COOP, "SARL coopérative"),
    (LEGAL_FORM_SAS, "SAS (Société par actions simplifiée)"),
    (LEGAL_FORM_SA, "SA (Société anonyme)"),
    (LEGAL_FORM_SA_COOP, "SA coopérative"),
    (LEGAL_FORM_SNC, "SNC (Société en nom collectif)"),
    (LEGAL_FORM_FONDATION, "Fondation"),
    (LEGAL_FORM_AUTRE, "Autre"),
)

GEO_RANGE_DEPARTMENT = "DEPARTMENT"
GEO_RANGE_REGION = "REGION"
GEO_RANGE_CUSTOM = "CUSTOM"
GEO_RANGE_COUNTRY = "COUNTRY"

GEO_RANGE_CHOICES = (
    (GEO_RANGE_COUNTRY, "France entière"),
    (GEO_RANGE_REGION, "Région"),
    (GEO_RANGE_DEPARTMENT, "Département"),
    (GEO_RANGE_CUSTOM, "Distance en kilomètres"),
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
