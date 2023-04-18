from django.test import TestCase

from lemarche.utils.emails import anonymize_email, whitelist_recipient_list


class EmailTest(TestCase):
    def test_anonymize_email(self):
        email_1 = "bob@test.com"
        self.assertEqual(anonymize_email(email_1), "b*b@test.com")
        email_2 = "prenom.nom@test.com"
        self.assertEqual(anonymize_email(email_2), "p*****.**m@test.com")

    def test_whitelist_recipient_list(self):
        email_list_1 = ["bob@test.com"]
        self.assertEqual(whitelist_recipient_list(email_list_1), [])
        email_list_2 = ["bob@test.com", "prenom.nom@beta.gouv.fr"]
        self.assertEqual(whitelist_recipient_list(email_list_2), ["prenom.nom@beta.gouv.fr"])
