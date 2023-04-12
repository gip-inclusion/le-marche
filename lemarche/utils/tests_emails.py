from django.test import TestCase

from lemarche.utils.emails import anonymize_email


class EmailTest(TestCase):
    def test_anonymize_email(self):
        email_1 = "bob@test.com"
        self.assertEqual(anonymize_email(email_1), "b*b@test.com")
        email_2 = "prenom.nom@test.com"
        self.assertEqual(anonymize_email(email_2), "p*****.**m@test.com")
