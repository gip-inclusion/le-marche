from django.test import TestCase

from lemarche.notes.models import Note
from lemarche.users import constants as user_constants
from tests.notes.factories import NoteFactory
from tests.siaes.factories import SiaeFactory
from tests.tenders.factories import TenderFactory
from tests.users.factories import UserFactory


class NoteModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(kind=user_constants.KIND_ADMIN)
        cls.note = NoteFactory()
        cls.note_with_author = NoteFactory(author=cls.user)

    def test_count(self):
        self.assertEqual(Note.objects.count(), 2)

    def test_create_tender_note_with_generic_relation(self):
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

    def test_create_user_note_with_generic_relation(self):
        user_siae = UserFactory(kind=user_constants.KIND_SIAE)
        NoteFactory(author=self.user, content_object=user_siae)
        self.assertEqual(Note.objects.count(), 2 + 1)
        # can create multiple notes for the same object
        NoteFactory(author=self.user, content_object=user_siae)
        self.assertEqual(Note.objects.count(), 2 + 1 + 1)
        # reverse
        self.assertEqual(Note.objects.filter(user__email=user_siae.email).count(), 2)
        # self.assertEqual(user_siae.notes.count(), 2)
