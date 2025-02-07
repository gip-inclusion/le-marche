import factory
from factory.django import DjangoModelFactory

from lemarche.labels.models import Label


class LabelFactory(DjangoModelFactory):
    class Meta:
        model = Label
        skip_postgeneration_save = True  # Prevents unnecessary save

    name = factory.Faker("company", locale="fr_FR")
    # slug: auto-generated
    website = "https://example.com"

    @factory.post_generation
    def siaes(self, create, extracted, **kwargs):
        if extracted:
            # Add the iterable of groups using bulk addition
            self.siaes.add(*extracted)
