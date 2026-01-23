# https://github.com/betagouv/itou/blob/master/itou/utils/validators.py
import socket
from urllib.parse import urlparse

import requests
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


class OptionalSchemeURLValidator(URLValidator):
    def __init__(self, timeout=5, *args, **kwargs):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def __call__(self, value):
        if "://" not in value:
            # Validate as if it were https://
            # https://stackoverflow.com/a/49983649/4293684
            value = "https://" + value

        # call the classic URLValidator
        super().__call__(value)

        # Validate DNS resolution
        domain = urlparse(value).netloc
        try:
            socket.gethostbyname(domain)  # DNS resolution check
        except socket.gaierror:
            raise ValidationError(
                "Le site web associé à cette adresse n'existe pas ou est inaccessible pour le moment."
            )

        # Validate HTTP response
        try:
            response = requests.get(value, timeout=5)  # Adjust timeout as needed
            if response.status_code >= 400:
                raise ValidationError(
                    """Le site web semble rencontrer un problème.
                    Êtes-vous sûr que le site existe ? Si oui, réessayez plus tard ou contactez-nous."""
                )
        except requests.RequestException:
            raise ValidationError(
                """Une erreur est survenue en essayant de vérifier cette adresse.
                Êtes-vous sûr que le site existe ? Si oui, réessayez plus tard ou contactez-nous."""
            )


def validate_post_code(post_code):
    if not post_code.isdigit() or len(post_code) != 5:
        raise ValidationError("Le code postal doit être composé de 5 chiffres.")


def validate_siren(siren):
    if not siren.isdigit() or len(siren) != 9:
        raise ValidationError("Le numéro SIREN doit être composé de 9 chiffres.")


def validate_siret(siret):
    if not siret.isdigit() or len(siret) != 14:
        raise ValidationError("Le numéro SIRET doit être composé de 14 chiffres.")


def validate_naf(naf):
    if len(naf) != 5 or not naf[:4].isdigit() or not naf[4].isalpha():
        raise ValidationError("Le code NAF doit être composé de de 4 chiffres et d'une lettre.")
