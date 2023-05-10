import factory
from factory.django import DjangoModelFactory

from lemarche.labels.models import Label


class LabelFactory(DjangoModelFactory):
    class Meta:
        model = Label

    name = factory.Faker("company", locale="fr_FR")
    # slug: auto-generated
    website = "https://example.com"
