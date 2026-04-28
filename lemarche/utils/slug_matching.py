"""
Résolution de valeurs texte libre vers des slugs internes (secteurs, périmètres).

Architecture en 4 couches, appliquées dans l'ordre :
  1. Exact match sur le slug lui-même
  2. Base de matching validée (SlugMappingCache, admin_validated)
  3. Trigram PostgreSQL sur le nom (résolution auto si score ≥ CONFIDENCE_AUTO)
  4. Trigram sur le titre/description du projet (toujours en validation manuelle)

Statuts retournés :
  RESOLVED   → slug trouvé avec confiance suffisante, passe direct à l'analyse
  AMBIGUOUS  → correspondances trouvées mais score insuffisant, validation requise
  ERROR      → aucune correspondance acceptable, ligne ignorée de l'analyse
"""

import unicodedata

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F

from lemarche.perimeters.models import Perimeter
from lemarche.purchases import constants as purchases_constants
from lemarche.purchases.models import SlugMappingCache
from lemarche.sectors.models import Sector


FRANCE_ENTIERE_VARIANTS = {"france_entiere", "france entiere", "france entière", "france", "national", "nationale"}

RESOLUTION_STATUS_RESOLVED = "resolved"
RESOLUTION_STATUS_AMBIGUOUS = "ambiguous"
RESOLUTION_STATUS_ERROR = "error"

COLUMN_HEADER_ALIASES = {
    "secteur": ["secteur", "secteur d'activité", "secteur activite", "categorie", "catégorie"],
    "perimetre_geographique": [
        "perimetre_geographique",
        "perimetre geographique",
        "périmètre géographique",
        "perimetre",
        "périmètre",
        "zone géographique",
        "zone geographique",
        "localisation",
        "collectivité concernée",
        "collectivite concernee",
        "collectivité",
        "collectivite",
    ],
    "titre": [
        "titre",
        "titre du projet",
        "intitulé",
        "intitule",
        "nom du projet",
        "objet",
        "objet du marché",
        "objet du marche",
        "libellé",
        "libelle",
    ],
    "description": ["description", "detail", "détail", "commentaire"],
    "montant": ["montant", "budget", "montant €", "montant eur", "valeur"],
}


def normalize(text: str) -> str:
    """
    Normalise une chaîne pour comparaison : minuscules, sans accents, sans tirets superflus.
    Retourne "" si text est None ou vide.
    """
    if not text:
        return ""
    text = str(text).strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode()
    return text


def is_france_entiere(raw_value: str) -> bool:
    """Retourne True si la valeur correspond à une variante de 'france_entiere'."""
    return normalize(raw_value) in FRANCE_ENTIERE_VARIANTS


def resolve_column_header(raw_header: str) -> str | None:
    """
    Résout un en-tête de colonne Excel vers le nom de colonne interne.
    Retourne le nom interne si trouvé, None sinon.
    Cas insensible à la casse et aux accents.
    """
    normalized = normalize(raw_header)
    for internal_name, aliases in COLUMN_HEADER_ALIASES.items():
        if normalized in [normalize(a) for a in aliases]:
            return internal_name
    return None


def _get_validated_cache(raw_value: str, kind: str) -> SlugMappingCache | None:
    """Cherche une entrée admin_validated dans le cache pour cette valeur."""
    normalized = normalize(raw_value)
    return SlugMappingCache.objects.filter(
        raw_value__iexact=normalized,
        kind=kind,
        source=purchases_constants.SLUG_MAPPING_SOURCE_ADMIN_VALIDATED,
    ).first()


def _increment_cache_usage(cache: SlugMappingCache) -> None:
    """Incrémente le compteur d'usage de manière atomique."""
    SlugMappingCache.objects.filter(pk=cache.pk).update(usage_count=F("usage_count") + 1)


def _save_to_cache(raw_value: str, kind: str, resolved_slug: str, source: str, confidence: float, user) -> None:
    """
    Enregistre ou met à jour une correspondance dans le cache.
    Utilise get_or_create pour éviter les IntegrityError en concurrence.
    """
    normalized = normalize(raw_value)
    cache, created = SlugMappingCache.objects.get_or_create(
        raw_value=normalized,
        kind=kind,
        defaults={
            "resolved_slug": resolved_slug,
            "source": source,
            "confidence": confidence,
            "proposed_by": user,
            "usage_count": 1,
        },
    )
    if not created:
        SlugMappingCache.objects.filter(pk=cache.pk).update(usage_count=F("usage_count") + 1)


def resolve_sector(raw_value: str, user=None) -> dict:
    """
    Résout une valeur texte libre vers un slug de secteur.

    Retourne un dict :
      {"status": RESOLUTION_STATUS_*, "slug": str|None, "candidates": list, "source": str}

    candidates est une liste de {"slug", "name", "score"} pour la page de validation.
    """
    if not raw_value or not raw_value.strip():
        return {"status": RESOLUTION_STATUS_ERROR, "slug": None, "candidates": [], "source": ""}

    # Couche 1 — exact match slug
    if Sector.objects.filter(slug=raw_value.strip()).exists():
        return {"status": RESOLUTION_STATUS_RESOLVED, "slug": raw_value.strip(), "candidates": [], "source": "exact"}

    normalized = normalize(raw_value)

    # Couche 2 — cache validé par admin
    cache = _get_validated_cache(normalized, purchases_constants.SLUG_MAPPING_KIND_SECTOR)
    if cache:
        _increment_cache_usage(cache)
        return {"status": RESOLUTION_STATUS_RESOLVED, "slug": cache.resolved_slug, "candidates": [], "source": "cache"}

    # Couche 3 — trigram sur Sector.name
    candidates = (
        Sector.objects.annotate(score=TrigramSimilarity("name", normalized))
        .filter(score__gte=purchases_constants.SLUG_MAPPING_CONFIDENCE_MIN)
        .order_by("-score")
        .values("slug", "name", "score")[:5]
    )
    candidates = list(candidates)

    if not candidates:
        return {"status": RESOLUTION_STATUS_ERROR, "slug": None, "candidates": [], "source": ""}

    best = candidates[0]

    if best["score"] >= purchases_constants.SLUG_MAPPING_CONFIDENCE_AUTO:
        _save_to_cache(
            normalized,
            purchases_constants.SLUG_MAPPING_KIND_SECTOR,
            best["slug"],
            purchases_constants.SLUG_MAPPING_SOURCE_AUTO_TRIGRAM,
            best["score"],
            user,
        )
        return {"status": RESOLUTION_STATUS_RESOLVED, "slug": best["slug"], "candidates": [], "source": "trigram_auto"}

    return {"status": RESOLUTION_STATUS_AMBIGUOUS, "slug": None, "candidates": candidates, "source": "trigram"}


def resolve_perimeter(raw_value: str, user=None) -> dict:
    """
    Résout une valeur texte libre vers un slug de périmètre.
    Gère le cas spécial 'france_entiere'.

    Retourne un dict :
      {"status": RESOLUTION_STATUS_*, "slug": str|None, "france_entiere": bool, "candidates": list, "source": str}
    """
    if not raw_value or not raw_value.strip():
        return {
            "status": RESOLUTION_STATUS_ERROR,
            "slug": None,
            "france_entiere": False,
            "candidates": [],
            "source": "",
        }

    # Interception france_entiere avant toute recherche
    if is_france_entiere(raw_value):
        return {
            "status": RESOLUTION_STATUS_RESOLVED,
            "slug": None,
            "france_entiere": True,
            "candidates": [],
            "source": "france_entiere",
        }

    # Couche 1 — exact match slug
    if Perimeter.objects.filter(slug=raw_value.strip()).exists():
        return {
            "status": RESOLUTION_STATUS_RESOLVED,
            "slug": raw_value.strip(),
            "france_entiere": False,
            "candidates": [],
            "source": "exact",
        }

    normalized = normalize(raw_value)

    # Couche 2 — cache validé par admin
    cache = _get_validated_cache(normalized, purchases_constants.SLUG_MAPPING_KIND_PERIMETER)
    if cache:
        _increment_cache_usage(cache)
        return {
            "status": RESOLUTION_STATUS_RESOLVED,
            "slug": cache.resolved_slug,
            "france_entiere": False,
            "candidates": [],
            "source": "cache",
        }

    # Couche 3 — trigram sur Perimeter.name (toutes mailles)
    candidates = (
        Perimeter.objects.annotate(score=TrigramSimilarity("name", normalized))
        .filter(score__gte=purchases_constants.SLUG_MAPPING_CONFIDENCE_MIN)
        .order_by("-score")
        .values("slug", "name", "kind", "score")[:5]
    )
    candidates = list(candidates)

    if not candidates:
        return {
            "status": RESOLUTION_STATUS_ERROR,
            "slug": None,
            "france_entiere": False,
            "candidates": [],
            "source": "",
        }

    best = candidates[0]

    if best["score"] >= purchases_constants.SLUG_MAPPING_CONFIDENCE_AUTO:
        _save_to_cache(
            normalized,
            purchases_constants.SLUG_MAPPING_KIND_PERIMETER,
            best["slug"],
            purchases_constants.SLUG_MAPPING_SOURCE_AUTO_TRIGRAM,
            best["score"],
            user,
        )
        return {
            "status": RESOLUTION_STATUS_RESOLVED,
            "slug": best["slug"],
            "france_entiere": False,
            "candidates": [],
            "source": "trigram_auto",
        }

    return {
        "status": RESOLUTION_STATUS_AMBIGUOUS,
        "slug": None,
        "france_entiere": False,
        "candidates": candidates,
        "source": "trigram",
    }


def resolve_sector_from_title(title: str, description: str = "") -> dict:
    """
    Tente d'inférer un secteur depuis le titre et/ou la description du projet.
    Toujours retourné comme AMBIGUOUS (jamais résolu automatiquement).

    Retourne un dict identique à resolve_sector, avec source='title_inference'.
    """
    text = normalize(f"{title} {description}".strip())
    if not text:
        return {"status": RESOLUTION_STATUS_ERROR, "slug": None, "candidates": [], "source": ""}

    candidates = (
        Sector.objects.annotate(score=TrigramSimilarity("name", text))
        .filter(score__gte=purchases_constants.SLUG_MAPPING_CONFIDENCE_TITLE_MIN)
        .order_by("-score")
        .values("slug", "name", "score")[:3]
    )
    candidates = list(candidates)

    if not candidates:
        return {"status": RESOLUTION_STATUS_ERROR, "slug": None, "candidates": [], "source": ""}

    return {"status": RESOLUTION_STATUS_AMBIGUOUS, "slug": None, "candidates": candidates, "source": "title_inference"}


def record_user_choices(choices: list[dict], user) -> None:
    """
    Enregistre les choix de l'utilisateur depuis la page de validation en base.
    Chaque choix est enregistré en 'user_proposed' pour modération admin.

    choices est une liste de {"raw_value", "kind", "resolved_slug", "confidence"}.
    """
    for choice in choices:
        _save_to_cache(
            choice["raw_value"],
            choice["kind"],
            choice["resolved_slug"],
            purchases_constants.SLUG_MAPPING_SOURCE_USER_PROPOSED,
            choice.get("confidence", 1.0),
            user,
        )
