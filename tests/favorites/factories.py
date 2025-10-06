import factory
from factory.django import DjangoModelFactory

from lemarche.favorites.models import FavoriteList


class FavoriteListFactory(DjangoModelFactory):
    class Meta:
        model = FavoriteList
        skip_postgeneration_save = True  # Prevents unnecessary save

    name = "Some FavoriteList"
    # slug: auto-generated

    @factory.post_generation
    def siaes(self, create, extracted, **kwargs):
        if extracted:
            self.siaes.add(*extracted)
