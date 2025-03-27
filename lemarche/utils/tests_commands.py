from unittest.mock import patch

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TransactionTestCase

from lemarche.tenders.factories import TenderFactory


class AntivirusScanCommandTest(TransactionTestCase):

    def setUp(self):
        # create a tender with an attachment
        self.tender = TenderFactory.create()
        self.tender.attachment_one = SimpleUploadedFile(
            name="document.pdf", content=b"file_content", content_type="application/pdf"
        )
        self.tender.save()

    @patch("lemarche.utils.management.commands.antivirus_scan.shutil.chown")
    @patch("lemarche.utils.management.commands.antivirus_scan.os.chmod")
    @patch("lemarche.utils.management.commands.antivirus_scan.subprocess.run")
    def test_antivirus_scan_command_with_no_virus(self, mock_subprocess_run, mock_os_chmod, mock_shutil_chown):
        mock_subprocess_run.return_value.returncode = 0
        mock_shutil_chown.return_value = None
        mock_os_chmod.return_value = None

        call_command("antivirus_scan")

        # Check that the scan command was called
        self.assertEqual(mock_subprocess_run.call_count, 1)

        # Check that the attachment was not deleted on DB
        self.tender.refresh_from_db()
        self.assertTrue(self.tender.attachment_one)

        # Check file was not deleted on storage
        self.assertTrue(default_storage.exists(self.tender.attachment_one.name))

    @patch("lemarche.utils.management.commands.antivirus_scan.shutil.chown")
    @patch("lemarche.utils.management.commands.antivirus_scan.os.chmod")
    @patch("lemarche.utils.management.commands.antivirus_scan.subprocess.run")
    def test_antivirus_scan_command_with_virus(self, mock_subprocess_run, mock_os_chmod, mock_shutil_chown):
        mock_subprocess_run.return_value.returncode = 1
        mock_shutil_chown.return_value = None
        mock_os_chmod.return_value = None

        attachment = self.tender.attachment_one

        call_command("antivirus_scan")

        # Check that the scan command was called
        self.assertEqual(mock_subprocess_run.call_count, 1)

        # Check that the attachment was deleted on DB
        self.tender.refresh_from_db()
        self.assertFalse(self.tender.attachment_one)

        # Check file was deleted on storage
        self.assertFalse(default_storage.exists(attachment.name))
