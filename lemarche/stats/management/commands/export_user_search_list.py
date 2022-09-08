import csv
import glob
import os
from datetime import date, timedelta

import boto3
from django.conf import settings
from django.db.models import Count

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
FILENAME = f"liste_recherches_{date.today()}"
FILENAME_PREVIOUS = f"liste_recherches_{date.today() - timedelta(days=1)}"


def build_file_url(endpoint, bucket_name, file_key):
    return f"{endpoint}/{bucket_name}/{file_key}"


class Command(BaseCommand):
    """
    Export all search events to a file (XLS or CSV)

    Steps:
    1. Query the stats DB to get all the search events
    2. Enrich with the user details
    3. Generate the file (.xls or .csv or both)
    4. Upload to S3
    5. Cleanup

    Usage:
    poetry run python manage.py export_user_search_list
    poetry run python manage.py export_user_search_list --start_date 2022-03-01
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

    def handle(self, *args, **options):
        self.stdout_info("-" * 80)
        self.stdout_info("Step 1: fetching search list from stats DB")
        search_list = self.fetch_search_list(options["start_date"])
        self.stdout_info(f"Found {len(search_list)} items")

        self.stdout_info("-" * 80)
        self.stdout_info("Step 2: enrich search list")
        search_list_enriched = self.enrich_search_list(search_list)

        self.stdout_info("-" * 80)
        self.stdout_info("Step 3: export search list to csv")  # + Step 4
        self.generate_search_list_file(search_list_enriched, "csv")

        self.stdout_info("-" * 80)
        self.stdout_info("Step 5: cleanup")
        self.cleanup()

    def fetch_search_list(self, start_date):
        response = Tracker.objects.filter(
            env="prod", action="directory_search", date_created__gte=start_date
        ).order_by("date_created")
        search_list_temp = list()
        for row in response:
            search_list_temp.append(row)

        return search_list_temp

    def enrich_search_list(self, search_list):
        # init
        search_list_enriched = list()
        # we store the users in a list to avoid querying the DB on every iteration
        user_list = User.objects.prefetch_related("siaes").annotate(siae_count=Count("siaes")).values()

        for item in search_list:
            search_item = {}
            # search
            tracker_meta_data = item.data.get("meta")
            search_item.update(
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
            user_id = tracker_meta_data["user_id"]
            user_dict = next((user for user in user_list if user["id"] == user_id), {})
            search_item.update(
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
            search_item.update(
                {
                    "cmp": tracker_meta_data["cmp"],
                    "timestamp": item.date_created,
                    "stats_id": item.id_internal,
                }
            )
            search_list_enriched.append(search_item)

        return search_list_enriched

    def generate_search_list_file(self, search_list_enriched, format):
        if format in ["csv", "all"]:
            self.stdout_info("Generating the CSV file")
            filename_with_extension = f"{FILENAME}.csv"
            file = open(filename_with_extension, "w")
            writer = csv.DictWriter(file, fieldnames=list(search_list_enriched[0].keys()))
            writer.writeheader()
            for item in search_list_enriched:
                writer.writerow(item)
            file.close()
            self.stdout_success(f"Generated {filename_with_extension}")

            self.stdout_info("-" * 80)
            self.stdout_info("Step 4: uploading the CSV file to S3")
            self.upload_file_to_s3(filename_with_extension)

        # if format in ["xls", "all"]:
        #     self.stdout_info("Generating the XLS file")
        #     filename_with_extension = f"{FILENAME}.xls"
        #     wb = export_siae_to_excel(siae_list)
        #     wb.save(filename_with_extension)
        #     self.stdout_info(f"Generated {filename_with_extension}")

        #     self.stdout_info("-" * 80)
        #     self.stdout_info("Step 4: uploading the XLS file to S3")
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
