from django.test import TestCase

from lemarche.labels.factories import LabelFactory


class LabelModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.label = LabelFactory(name="Un label")

    def test_slug_field(self):
        self.assertEqual(self.label.slug, "un-label")

    def test_str(self):
        self.assertEqual(str(self.label), "Un label")
