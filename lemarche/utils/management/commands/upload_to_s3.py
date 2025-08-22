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
    Upload a file to S3, primary use is to test if S3 is working correctly
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Path for file to upload on S3",
        )

    def handle(self, *args, **options):
        file = options["file"]
        self.upload_file_to_s3(file)

    def upload_file_to_s3(self, filename_with_extension):
        s3_file_key = filename_with_extension
        bucket.upload_file(
            filename_with_extension,
            s3_file_key,
            ExtraArgs={"ACL": "public-read"},
        )
        s3_file_url = build_file_url(API_CONNECTION_DICT["endpoint_url"], s3_file_key)
        self.stdout.write(f"S3 file url: {s3_file_url}")
