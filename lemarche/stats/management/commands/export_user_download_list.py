import csv
import glob
import os
from datetime import date, timedelta

import boto3
from django.conf import settings
from sentry_sdk.crons import monitor

from lemarche.stats.models import Tracker
from lemarche.users.models import User
from lemarche.utils.commands import BaseCommand
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
    poetry run python manage.py export_user_download_list --start_date 2022-03-01
    """

    def add_arguments(self, parser):
        parser.add_argument("--start_date", type=str, default="2022-01-01")

    #     parser.add_argument(
    #         "--format",
    #         type=str,
    #         choices=["xls", "csv", "all"],
    #         default="xls",
    #         help="Options are 'xls' (default), 'csv' or 'all'",
    #     )

    @monitor(monitor_slug="export_user_download_list")
    def handle(self, *args, **options):
        self.stdout_info("-" * 80)
        self.stdout_info("Step 1: fetching download list from stats DB")
        download_list = self.fetch_download_list(options["start_date"])
        self.stdout_info(f"Found {len(download_list)} items")

        self.stdout_info("-" * 80)
        self.stdout_info("Step 2: enrich download list")
        download_list_enriched = self.enrich_download_list(download_list)

        self.stdout_info("-" * 80)
        self.stdout_info("Step 3: export download list to csv")  # + Step 4
        self.generate_download_list_file(download_list_enriched, "csv")

        self.stdout_info("-" * 80)
        self.stdout_info("Step 5: cleanup")
        self.cleanup()

    def fetch_download_list(self, start_date):
        response = Tracker.objects.filter(env="prod", action="directory_csv", date_created__gte=start_date).order_by(
            "date_created"
        )
        download_list_temp = list()
        for row in response:
            download_list_temp.append(row)

        return download_list_temp

    def enrich_download_list(self, download_list):
        # init
        download_list_enriched = list()
        # we store the users in a list to avoid querying the DB on every iteration
        user_list = User.objects.with_siae_stats().values()

        for item in download_list:
            download_item = {}
            # search
            tracker_meta_data = item.data.get("meta")
            download_item.update(
                {
                    "search_sectors": ", ".join(tracker_meta_data.get("sectors", [])),
                    # "search_perimeter": ", ".join(tracker_meta_data.get("perimeter", [])),
                    "search_perimeter_name": ", ".join(tracker_meta_data.get("perimeter_name", [])),
                    "search_kind": ", ".join(tracker_meta_data.get("kind", [])),
                    "search_presta_type": ", ".join(tracker_meta_data.get("presta_type", [])),
                    "search_territory": ", ".join(tracker_meta_data.get("territory", [])),
                    "search_networks": ", ".join(tracker_meta_data.get("networks", [])),
                    "search_results_count": tracker_meta_data.get("results_count", None),
                    "search_page": ", ".join(tracker_meta_data.get("page", [])),
                }
            )
            # user
            user_id = tracker_meta_data.get("user_id")
            user_dict = next((user for user in user_list if user["id"] == user_id), {})
            download_item.update(
                {
                    "user_first_name": user_dict.get("first_name", ""),
                    "user_last_name": user_dict.get("last_name", ""),
                    "user_kind": user_dict.get("kind", ""),
                    "user_email": user_dict.get("email", ""),
                    "user_phone": user_dict.get("phone", ""),
                    "user_company_name": user_dict.get("company_name", ""),
                    "user_siae_count": user_dict.get("siae_count", ""),
                    "user_created_at": user_dict.get("created_at", ""),
                }
            )
            # other
            download_item.update(
                {
                    "cmp": tracker_meta_data.get("cmp", ""),
                    "timestamp": item.date_created,
                    "stats_id": item.id_internal,
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
            self.stdout_success(f"Generated {filename_with_extension}")

            self.stdout_info("-" * 80)
            self.stdout_info("Step 4: uploading the CSV file to S3")
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
        self.stdout_success(f"S3 file url: {s3_file_url}")

    def cleanup(self):
        files_to_remove = glob.glob(f"{FILENAME}.*")
        for file_path in files_to_remove:
            os.remove(file_path)
        bucket.objects.filter(Prefix=f"{settings.STAT_EXPORT_FOLDER_NAME}/{FILENAME_PREVIOUS}").delete()
