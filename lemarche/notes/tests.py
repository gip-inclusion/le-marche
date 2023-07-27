from django.test import TestCase

from lemarche.notes.factories import NoteFactory
from lemarche.notes.models import Note
from lemarche.siaes.factories import SiaeFactory
from lemarche.tenders.factories import TenderFactory
from lemarche.users.factories import UserFactory
from lemarche.utils import constants


class NoteModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(kind=constants.USER_KIND_ADMIN)
        cls.note = NoteFactory()
        cls.note_with_author = NoteFactory(author=cls.user)

    def test_count(self):
        self.assertEqual(Note.objects.count(), 2)

    def test_create_note_with_generic_relation(self):
        tender = TenderFactory()
        NoteFactory(author=self.user, content_object=tender)
        self.assertEqual(Note.objects.count(), 2 + 1)
        # can create multiple notes for the same object
        NoteFactory(author=self.user, content_object=tender)
        self.assertEqual(Note.objects.count(), 2 + 1 + 1)
        # reverse
        self.assertEqual(Note.objects.filter(tender__title=tender.title).count(), 2)
        self.assertEqual(tender.notes.count(), 2)

    def test_create_siae_note_with_generic_relation(self):
        siae = SiaeFactory()
        NoteFactory(author=self.user, content_object=siae)
        self.assertEqual(Note.objects.count(), 2 + 1)
        # can create multiple notes for the same object
        NoteFactory(author=self.user, content_object=siae)
        self.assertEqual(Note.objects.count(), 2 + 1 + 1)
        # reverse
        self.assertEqual(Note.objects.filter(siae__name=siae.name).count(), 2)
        self.assertEqual(siae.notes.count(), 2)
