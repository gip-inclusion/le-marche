"""
Centralized constants for Brevo attributes.

This module contains all attributes used in the Brevo API to avoid
naming errors and facilitate maintenance.

Attribute names correspond exactly to those defined in Brevo.
"""

# ============================================================================
# BREVO CONTACT ATTRIBUTES
# ============================================================================

CONTACT_ATTRIBUTES = {
    # Default Brevo attributes
    "EMAIL": "EMAIL",
    # Custom contact attributes
    "NOM": "NOM",
    "PRENOM": "PRENOM",
    "DATE_INSCRIPTION": "DATE_INSCRIPTION",
    "TYPE_ORGANISATION": "TYPE_ORGANISATION",
    "NOM_ENTREPRISE": "NOM_ENTREPRISE",
    "SMS": "SMS",
    "MONTANT_BESOIN_ACHETEUR": "MONTANT_BESOIN_ACHETEUR",
    "TYPE_BESOIN_ACHETEUR": "TYPE_BESOIN_ACHETEUR",
    "TYPE_VERTICALE_ACHETEUR": "TYPE_VERTICALE_ACHETEUR",
}


# ============================================================================
# BREVO COMPANY ATTRIBUTES (COMMON)
# ============================================================================

# Common attributes for all companies (SIAE and buyers)
COMMON_COMPANY_ATTRIBUTES = {
    # Default Brevo attributes
    "name": "name",
    "owner": "owner",
    "linked_contacts": "linked_contacts",
    "revenue": "revenue",
    "number_of_employees": "number_of_employees",
    "created_at": "created_at",
    "last_updated_at": "last_updated_at",
    "next_activity_date": "next_activity_date",
    "owner_assign_date": "owner_assign_date",
    "number_of_contacts": "number_of_contacts",
    "number_of_activities": "number_of_activities",
    "industry": "industry",
    "domain": "domain",
    "phone_number": "phone_number",
    # Common custom attributes
    "app_id": "app_id",
    "siae": "siae",
    "description": "description",
    "kind": "kind",
    "app_admin_url": "app_admin_url",
}

# SIAE-specific attributes
SIAE_SPECIFIC_ATTRIBUTES = {
    "active": "active",
    "address_street": "address_street",
    "postal_code": "postal_code",  # Fixed: was "address_post_code"
    "address_city": "address_city",
    "contact_email": "contact_email",
    "logo_url": "logo_url",
    "app_url": "app_url",
    "taux_de_completion": "taux_de_completion",
    "nombre_de_besoins_recus": "nombre_de_besoins_recus",
    "nombre_de_besoins_interesses": "nombre_de_besoins_interesses",
}

# Buyer company-specific attributes
BUYER_SPECIFIC_ATTRIBUTES = {
    "siret": "siret",
    "nombre_d_utilisateurs": "nombre_d_utilisateurs",
    "nombre_besoins": "nombre_besoins",
    "domaines_email": "domaines_email",
}


# ============================================================================
# COMPLETE ATTRIBUTES BY COMPANY TYPE
# ============================================================================

# All SIAE attributes (common + specific)
SIAE_COMPANY_ATTRIBUTES = {**COMMON_COMPANY_ATTRIBUTES, **SIAE_SPECIFIC_ATTRIBUTES}

# All buyer company attributes (common + specific)
BUYER_COMPANY_ATTRIBUTES = {**COMMON_COMPANY_ATTRIBUTES, **BUYER_SPECIFIC_ATTRIBUTES}


# ============================================================================
# ALL ATTRIBUTES LISTS BY TYPE
# ============================================================================

ALL_CONTACT_ATTRIBUTES = list(CONTACT_ATTRIBUTES.values())

ALL_SIAE_COMPANY_ATTRIBUTES = list(SIAE_COMPANY_ATTRIBUTES.values())

ALL_BUYER_COMPANY_ATTRIBUTES = list(BUYER_COMPANY_ATTRIBUTES.values())

# All company attributes (SIAE + Buyers)
ALL_COMPANY_ATTRIBUTES = list(set(ALL_SIAE_COMPANY_ATTRIBUTES + ALL_BUYER_COMPANY_ATTRIBUTES))
