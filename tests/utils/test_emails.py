from django.test import TestCase

from lemarche.utils.emails import anonymize_email, whitelist_recipient_list


class EmailTest(TestCase):
    def test_anonymize_email(self):
        email_1 = "bob@test.com"
        self.assertEqual(anonymize_email(email_1), "b***@test.com")
        email_2 = "prenom.nom@test.com"
        self.assertEqual(anonymize_email(email_2), "p***@test.com")

    def test_anonymize_email_masks_any_character(self):
        for email, expected in [
            ("BBTEST12@test.com", "B***@test.com"),
            ("j0hn.d03-42+tag@test.com", "j***@test.com"),
            ("élodie.müller@test.com", "é***@test.com"),
            ("ab@test.com", "a***@test.com"),
            ("a@test.com", "a***@test.com"),
        ]:
            with self.subTest(email=email):
                self.assertEqual(anonymize_email(email), expected)

    def test_whitelist_recipient_list(self):
        email_list_1 = ["bob@test.com"]
        self.assertEqual(whitelist_recipient_list(email_list_1), [])
        email_list_2 = ["bob@test.com", "prenom.nom@inclusion.gouv.fr"]
        self.assertEqual(whitelist_recipient_list(email_list_2), ["prenom.nom@inclusion.gouv.fr"])
