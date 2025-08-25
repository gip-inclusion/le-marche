from pathlib import Path

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand

from lemarche.utils.s3 import API_CONNECTION_DICT


# init S3 config
bucket_name = settings.S3_STORAGE_BUCKET_NAME
resource = boto3.resource("s3", **API_CONNECTION_DICT)
bucket = resource.Bucket(bucket_name)


def build_file_url(endpoint, file_key):
    return f"{endpoint}/{bucket_name}/{file_key}"


class Command(BaseCommand):
    """
    Upload a file to S3, primary use is to test if S3 is working correctly.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Path for file to upload on S3",
            required=True,
        )
        parser.add_argument(
            "--bucket-path",
            dest="bucket_path",
            type=str,
            help="Path of the file on S3",
            required=False,
            default="",
        )

    def handle(self, *args, **options):
        file = options["file"]
        bucket_path = options["bucket_path"]
        self.upload_file_to_s3(file, bucket_path)

    def upload_file_to_s3(self, file_path, bucket_path):
        """Upload on the same path as local path if no bucket_path is provided, else use the provided bucket path"""
        if bucket_path:
            file_name = Path(file_path).name
            s3_file_key = f"{bucket_path}/{file_name}"
        else:
            s3_file_key = file_path
        bucket.upload_file(
            file_path,
            s3_file_key,
            ExtraArgs={"ACL": "public-read"},
        )
        s3_file_url = build_file_url(API_CONNECTION_DICT["endpoint_url"], s3_file_key)
        self.stdout.write(f"S3 file url: {s3_file_url}")
