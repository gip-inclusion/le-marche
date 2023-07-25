import factory
from factory.django import DjangoModelFactory

from lemarche.notes.models import Note


class NoteFactory(DjangoModelFactory):
    class Meta:
        model = Note

    text = factory.Faker("paragraph", nb_sentences=2, locale="fr_FR")
