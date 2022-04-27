import csv
import glob
import os
from datetime import date, timedelta

import boto3
import psycopg2
import psycopg2.extras
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from lemarche.users.models import User
from lemarche.utils.s3 import API_CONNECTION_DICT


# init S3 config
bucket_name = settings.S3_STORAGE_BUCKET_NAME
resource = boto3.resource("s3", **API_CONNECTION_DICT)
bucket = resource.Bucket(bucket_name)

# Content-Type file mapping
CONTENT_TYPE_MAPPING = {
    "xls": "application/ms-excel",
    "csv": "text/csv",
}
FILENAME = f"liste_telechargements_{date.today()}"
FILENAME_PREVIOUS = f"liste_telechargements_{date.today() - timedelta(days=1)}"


def build_file_url(endpoint, bucket_name, file_key):
    return f"{endpoint}/{bucket_name}/{file_key}"


class Command(BaseCommand):
    """
    Export all download events to a file (XLS or CSV)

    Steps:
    1. Query the stats DB to get all the download events
    2. Enrich with the user details
    3. Generate the file (.xls or .csv or both)
    4. Upload to S3
    5. Cleanup

    Usage:
    poetry run python manage.py export_user_download_list
    """

    # def add_arguments(self, parser):
    #     parser.add_argument(
    #         "--format",
    #         type=str,
    #         choices=["xls", "csv", "all"],
    #         default="xls",
    #         help="Options are 'xls' (default), 'csv' or 'all'",
    #     )

    def handle(self, *args, **options):
        if not os.environ.get("STATS_DSN"):
            raise CommandError("Missing STATS_DSN in env")

        self.stdout.write("-" * 80)
        self.stdout.write("Step 1: fetching download list from stats DB")
        download_list = self.fetch_download_list()

        self.stdout.write("-" * 80)
        self.stdout.write("Step 2: enrich download list")
        download_list_enriched = self.enrich_download_list(download_list)

        self.stdout.write("-" * 80)
        self.stdout.write("Step 3: export download list to csv")  # + Step 4
        self.generate_download_list_file(download_list_enriched, "csv")

        self.stdout.write("-" * 80)
        self.stdout.write("Step 5: cleanup")
        self.cleanup()

    def fetch_download_list(self):
        sql = """
        SELECT *
        FROM trackers
        WHERE env = 'prod'
        AND action = 'directory_csv'
        AND date_created >= '2022-01-01'
        ORDER BY date_created DESC;
        """
        connection = psycopg2.connect(os.environ.get("STATS_DSN"))
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(sql)
        response = cursor.fetchall()

        download_list_temp = list()
        for row in response:
            download_list_temp.append(dict(row))

        return download_list_temp

    def enrich_download_list(self, download_list):
        download_list_enriched = list()

        for item in download_list:
            download_item = {}
            # search
            download_item.update(
                {
                    "search_sectors": ", ".join(item["data"]["meta"].get("sectors", [])),
                    # "search_perimeter": ", ".join(item["data"]["meta"].get("perimeter", [])),
                    "search_perimeter_name": ", ".join(item["data"]["meta"].get("perimeter_name", [])),
                    "search_kind": ", ".join(item["data"]["meta"].get("kind", [])),
                    "search_presta_type": ", ".join(item["data"]["meta"].get("presta_type", [])),
                    "search_territory": ", ".join(item["data"]["meta"].get("territory", [])),
                    "search_networks": ", ".join(item["data"]["meta"].get("networks", [])),
                    "search_results_count": item["data"]["meta"].get("results_count", None),
                }
            )
            # user
            try:
                user_id = item["data"]["meta"]["user_id"]
                user = User.objects.get(id=user_id)
            except:  # noqa
                user = {}
            download_item.update(
                {
                    "user_first_name": user.first_name if user else "",
                    "user_last_name": user.last_name if user else "",
                    "user_kind": user.kind if user else "",
                    "user_email": user.email if user else "",
                    "user_phone": user.phone if user else "",
                    "user_company_name": user.company_name if user else "",
                    "user_siae_count": user.siaes.count() if user else "",
                    "user_created_at": user.created_at if user else "",
                }
            )
            # other
            download_item.update(
                {
                    "cmp": item["data"]["meta"]["cmp"],
                    "timestamp": item["date_created"],
                    "stats_id": item["id_internal"],
                }
            )
            download_list_enriched.append(download_item)

        return download_list_enriched

    def generate_download_list_file(self, download_list_enriched, format):
        if format in ["csv", "all"]:
            self.stdout.write("Generating the CSV file")
            filename_with_extension = f"{FILENAME}.csv"
            file = open(filename_with_extension, "w")
            writer = csv.DictWriter(file, fieldnames=list(download_list_enriched[0].keys()))
            writer.writeheader()
            for item in download_list_enriched:
                writer.writerow(item)
            file.close()
            self.stdout.write(f"Generated {filename_with_extension}")

            self.stdout.write("-" * 80)
            self.stdout.write("Step 4: uploading the CSV file to S3")
            self.upload_file_to_s3(filename_with_extension)

        # if format in ["xls", "all"]:
        #     self.stdout.write("Generating the XLS file")
        #     filename_with_extension = f"{FILENAME}.xls"
        #     wb = export_siae_to_excel(siae_list)
        #     wb.save(filename_with_extension)
        #     self.stdout.write(f"Generated {filename_with_extension}")

        #     self.stdout.write("-" * 80)
        #     self.stdout.write("Step 4: uploading the XLS file to S3")
        #     self.upload_file_to_s3(filename_with_extension)

    def upload_file_to_s3(self, filename_with_extension):
        file_extension = filename_with_extension.split(".")[1]
        s3_file_key = settings.STAT_EXPORT_FOLDER_NAME + "/" + filename_with_extension
        bucket.upload_file(
            filename_with_extension,
            s3_file_key,
            ExtraArgs={"ACL": "public-read", "ContentType": CONTENT_TYPE_MAPPING[file_extension]},
        )
        s3_file_url = build_file_url(API_CONNECTION_DICT["endpoint_url"], bucket_name, s3_file_key)
        self.stdout.write(f"S3 file url: {s3_file_url}")

    def cleanup(self):
        files_to_remove = glob.glob(f"{FILENAME}.*")
        for file_path in files_to_remove:
            os.remove(file_path)
        bucket.objects.filter(Prefix=f"{settings.STAT_EXPORT_FOLDER_NAME}/{FILENAME_PREVIOUS}").delete()
