from django.core.exceptions import ValidationError


def professional_email_validator(value):
    # Skip validation for empty values or values without "@" (handled by required field validation)
    if not value or "@" not in value:
        return

    excluded_domains = [
        "gmail.com",
        "hotmail.com",
        "hotmail.fr",
        "yahoo.com",
        "yahoo.fr",
        "laposte.net",
        "live.com",
        "live.fr",
        "outlook.com",
        "outlook.fr",
        "sfr.fr",
        "free.fr",
        "orange.fr",
        "wanadoo.fr",
        "bbox.fr",
        "icloud.com",
        "aol.com",
        "msn.com",
        "gmx.com",
    ]

    domain = value.split("@")[1]

    if domain in excluded_domains:
        raise ValidationError(f"Seules les adresses professionnelles sont autorisées, {domain} n'en fait pas partie")
