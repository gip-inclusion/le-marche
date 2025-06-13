"""
Enums fields used in Tender models.
"""

from django.db import models


class SurveyScaleQuestionChoices(models.TextChoices):
    NON = "0", "Non"
    PEU_PROBABLE = "1", "Peu probablement"
    TRES_PROBABLE = "2", "Très probablement"
    OUI = "3", "Oui"


class SurveyDoesNotExistQuestionChoices(models.TextChoices):
    DONT_KNOW = "DK", "Je ne sais pas"
    INTERNET_SEARCH = "IS", "Recherche sur Internet (Google, page jaune, recherche sur le web)"
    NETWORKS = "NW", "Réseaux professionnels et partenariats"
    DIRECTORY = "DI", "Annuaire spécialisé (GESAT, UNEA, Handeco)"
    RECOMMENDATIONS = (
        "RC",
        "Recommandations et bouche-à-oreille (Réseaux sociaux, recommandations personnelles, collègues)",
    )
    KNOWN_PROVIDERS = "KP", "Prestataires connus et habituels (Fournisseurs actuels)"
    PUBLIC_TENDERS = "PT", "Appel d'offres et consultations publiques (BOAMP, JOUE, AWS, appels d'offres)"
    FACILITATORS = "FA", "Facilitateurs de clauses sociales"
    LOCAL_SOURCING = (
        "LS",
        "Sourcing local et salons professionnels (Recherche locale, salons, événements professionnels)",
    )


class TenderSourcesChoices(models.TextChoices):
    SOURCE_FORM = "FORM", "Formulaire"
    SOURCE_STAFF_C4_CREATED = "STAFF_C4_CREATED", "Staff Marché (via l'Admin)"
    SOURCE_API = "API", "API"
    SOURCE_TALLY = "TALLY", "TALLY"
