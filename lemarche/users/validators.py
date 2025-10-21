from django.core.exceptions import ValidationError


def professional_email_validator(value):
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
