import factory
from factory.django import DjangoModelFactory

from lemarche.networks.models import Network


class NetworkFactory(DjangoModelFactory):
    class Meta:
        model = Network

    name = factory.Faker("company", locale="fr_FR")
    website = "https://example.com"
