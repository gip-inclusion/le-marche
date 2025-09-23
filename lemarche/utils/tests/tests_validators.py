from django.core.exceptions import ValidationError
from django.test import TestCase

from lemarche.utils.validators import validate_naf, validate_post_code, validate_siret


class ValidatorsTest(TestCase):

    def test_post_code_validator(self):
        validator = validate_post_code
        POST_CODE_OK = ["00000", "12345", "38000"]
        for item in POST_CODE_OK:
            validator(item)
        POST_CODE_NOT_OK = ["0", "1234"]
        for item in POST_CODE_NOT_OK:
            self.assertRaises(ValidationError, validator, item)

    def test_siret_validator(self):
        validator = validate_siret
        SIRET_OK = ["12312312312345"]
        for item in SIRET_OK:
            validator(item)
        SIRET_NOT_OK = ["123123123"]
        for item in SIRET_NOT_OK:
            self.assertRaises(ValidationError, validator, item)

    def test_naf_validator(self):
        validator = validate_naf
        NAF_OK = ["1234A"]
        for item in NAF_OK:
            validator(item)
        NAF_NOT_OK = ["1234", "12345", "ABCDE"]
        for item in NAF_NOT_OK:
            self.assertRaises(ValidationError, validator, item)
