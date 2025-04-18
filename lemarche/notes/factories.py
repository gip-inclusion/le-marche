from factory.django import DjangoModelFactory

from lemarche.notes.models import Note


class NoteFactory(DjangoModelFactory):
    class Meta:
        model = Note

    text = "Ceci est une note de test"
