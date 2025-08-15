import factory
from factory.django import DjangoModelFactory

from lemarche.companies.models import Company


class CompanyFactory(DjangoModelFactory):
    class Meta:
        model = Company
        skip_postgeneration_save = True  # Prevents unnecessary save

    name = factory.Sequence("Some Company N°:{0}".format)
    # slug: auto-generated
    website = "https://example.com"

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        if extracted:
            self.users.add(*extracted)

    @factory.post_generation
    def labels(self, create, extracted, **kwargs):
        if extracted:
            self.labels.add(*extracted)
