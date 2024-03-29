from django.test import TestCase

from lemarche.siaes.models import Siae
from lemarche.utils.models import get_object_by_id_or_none


class ModelsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae = Siae.objects.create()

    def test_get_object_by_id_or_none(self):
        # None
        result = get_object_by_id_or_none(Siae, None)
        self.assertIsNone(result)
        # wrong id
        result = get_object_by_id_or_none(Siae, self.siae.id + 1)
        self.assertIsNone(result)
        # id exists (but string)
        result = get_object_by_id_or_none(Siae, str(self.siae.id))
        self.assertEqual(result, self.siae)
        # id exists
        result = get_object_by_id_or_none(Siae, self.siae.id)
        self.assertEqual(result, self.siae)
