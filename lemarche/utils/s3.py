"""
Useful functions to interact with an S3 bucket.
https://github.com/betagouv/itou/blob/master/itou/utils/storage/s3.py
"""

import boto3
from botocore.client import Config
from django.conf import settings


SCHEME = "https://" if settings.AWS_S3_USE_SSL else "http://"

API_CONNECTION_DICT = {
    "endpoint_url": f"{SCHEME}{settings.S3_STORAGE_ENDPOINT_DOMAIN}",
    "aws_access_key_id": settings.S3_STORAGE_ACCESS_KEY_ID,
    "aws_secret_access_key": settings.S3_STORAGE_SECRET_ACCESS_KEY,
    "region_name": settings.S3_STORAGE_BUCKET_REGION,
    "config": Config(
        signature_version="s3v4",
        # CleverCloud S3 implementation does not support recent data integrity features from AWS.
        # https://github.com/boto/boto3/issues/4392
        # https://github.com/boto/boto3/issues/4398#issuecomment-2619946229
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    ),
}


class S3Upload:
    def __init__(self, kind="default"):
        self.config = self.get_config(kind)

    @property
    def form_values(self):
        """
        Returns a dict like this:
        {
            "url": "https://cellar-c2.services.clever-cloud.com/bucket_name",
            "fields": {
                'key': 'key_path',
                'x-amz-algorithm': 'AWS4-HMAC-SHA256',
                'x-amz-credential': '',
                'x-amz-date': '',
                'policy': '',
                'x-amz-signature': '',
            }
        }
        """
        client = boto3.client("s3", **API_CONNECTION_DICT)
        key_path = self.config["key_path"] + "/${filename}"
        expiration = self.config["upload_expiration"]
        values_dict = client.generate_presigned_post(
            settings.S3_STORAGE_BUCKET_NAME,
            key_path,
            ExpiresIn=expiration,
            Conditions=[["starts-with", "$Content-Type", "image/"]],
        )
        values_dict["fields"].pop("key")
        return values_dict

    @staticmethod
    def get_config(kind):
        config = settings.STORAGE_UPLOAD_KINDS[kind]
        default_options = settings.STORAGE_UPLOAD_KINDS["default"]
        config = default_options | config

        key_path = config["key_path"]
        if key_path.startswith("/") or key_path.endswith("/"):
            raise ValueError("key_path should not begin or end with a slash")

        config["allowed_mime_types"] = ",".join(config["allowed_mime_types"])

        return config
