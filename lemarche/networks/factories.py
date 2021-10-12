import factory
from django.utils.text import slugify
from factory.django import DjangoModelFactory

from lemarche.networks.models import Network


class NetworkFactory(DjangoModelFactory):
    class Meta:
        model = Network

    name = factory.Faker("company", locale="fr_FR")
    # slug is auto-generated
    website = "https://example.com"
