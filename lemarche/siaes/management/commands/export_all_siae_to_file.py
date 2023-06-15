import csv
import glob
import os
from datetime import date, timedelta

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand

from lemarche.utils.export import export_siae_to_csv, export_siae_to_excel
from lemarche.utils.s3 import API_CONNECTION_DICT
from lemarche.www.siaes.forms import SiaeFilterForm


# init S3 config
bucket_name = settings.S3_STORAGE_BUCKET_NAME
resource = boto3.resource("s3", **API_CONNECTION_DICT)
bucket = resource.Bucket(bucket_name)

# Content-Type file mapping
CONTENT_TYPE_MAPPING = {
    "xls": "application/ms-excel",
    "csv": "text/csv",
}

FILENAME = f"liste_structures_{date.today()}"
FILENAME_PREVIOUS = f"liste_structures_{date.today() - timedelta(days=1)}"


def build_file_url(endpoint, bucket_name, file_key):
    return f"{endpoint}/{bucket_name}/{file_key}"


class Command(BaseCommand):
    """
    Export all Siae to a file (XLS or CSV)

    Steps:
    1. Use the SiaeFilterForm to get the list of all the Siae available for the user
    2. Generate the file (.xls or .csv or both)
    3. Upload to S3
    4. Cleanup

    Usage:
    poetry run python manage.py export_all_siae_to_file
    poetry run python manage.py export_all_siae_to_file  --format csv
    poetry run python manage.py export_all_siae_to_file  --format all
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            type=str,
            choices=["xls", "csv", "all"],
            default="xls",
            help="Options are 'xls' (default), 'csv' or 'all'",
        )

    def handle(self, *args, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Task: export Siae list...")

        self.stdout.write("Step 1: fetching Siae list")
        filter_form = SiaeFilterForm({})
        siae_list = filter_form.filter_queryset()
        self.stdout.write(f"Found {len(siae_list)} Siae")

        if options["format"] in ["csv", "all"]:
            self.stdout.write("Step 2: generating the CSV file")
            filename_with_extension = f"{FILENAME}.csv"
            file = open(filename_with_extension, "w")
            writer = csv.writer(file)
            export_siae_to_csv(writer, siae_list)
            file.close()
            self.stdout.write(f"Generated {filename_with_extension}")

            self.stdout.write("Step 3: uploading the CSV file to S3")
            self.upload_file_to_s3(filename_with_extension)

        if options["format"] in ["xls", "all"]:
            self.stdout.write("Step 2: generating the XLS file")
            filename_with_extension = f"{FILENAME}.xls"
            wb = export_siae_to_excel(siae_list)
            wb.save(filename_with_extension)
            self.stdout.write(f"Generated {filename_with_extension}")

            self.stdout.write("Step 3: uploading the XLS file to S3")
            self.upload_file_to_s3(filename_with_extension)

        # Step 4: delete local file(s) & previous S3 file(s)
        files_to_remove = glob.glob(f"{FILENAME}.*")
        for file_path in files_to_remove:
            os.remove(file_path)
        bucket.objects.filter(Prefix=f"{settings.SIAE_EXPORT_FOLDER_NAME}/{FILENAME_PREVIOUS}").delete()

    def upload_file_to_s3(self, filename_with_extension):
        file_extension = filename_with_extension.split(".")[1]
        s3_file_key = settings.SIAE_EXPORT_FOLDER_NAME + "/" + filename_with_extension
        bucket.upload_file(
            filename_with_extension,
            s3_file_key,
            ExtraArgs={"ACL": "public-read", "ContentType": CONTENT_TYPE_MAPPING[file_extension]},
        )
        s3_file_url = build_file_url(API_CONNECTION_DICT["endpoint_url"], bucket_name, s3_file_key)
        self.stdout.write(f"S3 file url: {s3_file_url}")
