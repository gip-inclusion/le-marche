import factory
from factory.django import DjangoModelFactory

from lemarche.networks.models import Network


class NetworkFactory(DjangoModelFactory):
    class Meta:
        model = Network
        skip_postgeneration_save = True  # Prevents unnecessary save

    name = factory.Faker("company", locale="fr_FR")
    # slug: auto-generated
    website = "https://example.com"

    @factory.post_generation
    def siaes(self, create, extracted, **kwargs):
        if extracted:
            self.siaes.add(*extracted)
