import os
import shutil
import stat
import subprocess
import tempfile

from django.core.files.storage import default_storage
from django.core.management.base import CommandError
from django.db.models import Q

from lemarche.tenders.models import Tender
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    help = "Scan S3 files uploaded in tender form for viruses"

    def handle(self, *args, **options):
        self.stdout_info("Scanning S3 files attachments for viruses...")
        temp_dir = tempfile.mkdtemp()
        shutil.chown(temp_dir, group="clamav")
        attachments_count = 0
        attachments_not_found_count = 0
        virus_detected_count = 0
        for tender in Tender.objects.filter(
            Q(attachment_one__isnull=False) | Q(attachment_two__isnull=False) | Q(attachment_three__isnull=False)
        ):
            self.stdout_info(f"Tender {tender.id} has {len(tender.attachments)} attachments")
            for attachment in tender.attachments:
                try:
                    self.stdout_info(f"Scanning attachment {attachment}")
                    if default_storage.exists(attachment.file.name):
                        attachments_count += 1
                        local_file_path = f"{temp_dir}/{attachment.file.name.split('/')[-1]}"
                        with default_storage.open(attachment.file.name) as remote_file:
                            with open(local_file_path, "wb") as local_file:
                                local_file.write(remote_file.read())

                        shutil.chown(local_file_path, group="clamav")
                        os.chmod(local_file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)

                        result = self.scan(local_file_path)
                        if result is not None:
                            self.stdout_error(f"Virus detected in {attachment}")
                            self.stdout_messages_info(result)
                            virus_detected_count += 1
                            default_storage.delete(attachment.file.name)
                            match attachment:
                                case tender.attachment_one:
                                    tender.attachment_one = None
                                case tender.attachment_two:
                                    tender.attachment_two = None
                                case tender.attachment_three:
                                    tender.attachment_three = None
                            tender.save()
                            self.stdout_error(f"Attachment {attachment} deleted")
                            # TODO: send slack notification to admin

                except FileNotFoundError:
                    self.stdout_error("File not found!")
                    attachments_not_found_count += 1

        shutil.rmtree(temp_dir)
        if attachments_not_found_count > 0:
            self.stdout_error(f"{attachments_not_found_count} attachments not found")

        if virus_detected_count > 0:
            self.stdout_error(f"Virus detected in {virus_detected_count} attachments out of {attachments_count}")
        else:
            self.stdout_success(f"No virus detected in {attachments_count} attachments")

    @staticmethod
    def scan(path):
        try:
            result = subprocess.run(
                ["clamdscan", "--no-summary", "--infected", path],
                capture_output=True,
                text=True,
                check=True,  # Raises CalledProcessError if return code is non-zero
            )
        except FileNotFoundError:
            raise Exception("Command 'clamdscan' not found.")
        match result.returncode:
            case 0:
                return None
            case 1:
                return result.stdout
            case _:
                raise CommandError(result.stderr)
