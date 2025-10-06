from django.test import TestCase

from lemarche.utils.data import phone_number_display
from tests.users.factories import UserFactory


class UtilsDataTest(TestCase):
    def test_phone_number_display(self):
        user_with_phone_1 = UserFactory(phone="0612345678")
        self.assertEqual(phone_number_display(user_with_phone_1.phone_display), "+33612345678")
        user_with_phone_2 = UserFactory(phone="+33612345678")
        self.assertEqual(phone_number_display(user_with_phone_2.phone_display), "+33612345678")
        user_without_phone = UserFactory(phone="")
        self.assertEqual(phone_number_display(user_without_phone.phone_display), "")
