import factory
from factory.django import DjangoModelFactory

from lemarche.favorites.models import FavoriteList


class FavoriteListFactory(DjangoModelFactory):
    class Meta:
        model = FavoriteList

    name = factory.Faker("company", locale="fr_FR")
    # slug: auto-generated
