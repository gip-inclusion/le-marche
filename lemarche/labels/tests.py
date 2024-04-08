from django.test import TestCase

from lemarche.labels.factories import LabelFactory
from lemarche.labels.models import Label
from lemarche.siaes.factories import SiaeFactory


class LabelModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.label = LabelFactory(name="Un label")

    def test_slug_field(self):
        self.assertEqual(self.label.slug, "un-label")

    def test_str(self):
        self.assertEqual(str(self.label), "Un label")


class LabelQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_1 = SiaeFactory()
        cls.siae_2 = SiaeFactory()
        cls.label = LabelFactory(name="Un label")
        cls.label_with_siaes = LabelFactory(name="Un autre label", siaes=[cls.siae_1, cls.siae_2])

    def test_with_siae_stats(self):
        label_queryset = Label.objects.with_siae_stats()
        self.assertEqual(label_queryset.get(id=self.label.id).siae_count_annotated, 0)
        self.assertEqual(label_queryset.get(id=self.label_with_siaes.id).siae_count_annotated, 2)
