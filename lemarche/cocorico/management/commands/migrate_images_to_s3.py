import os
from ftplib import FTP

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand

from lemarche.siaes.models import Siae, SiaeClientReference
from lemarche.users.models import User
from lemarche.utils.s3 import API_CONNECTION_DICT


# init FTP config
ftp = FTP(
    host=os.environ.get("COCORICO_FTP_HOST"),
    user=os.environ.get("COCORICO_FTP_USER"),
    passwd=os.environ.get("COCORICO_FTP_PASSWORD"),
)

# init S3 config
bucket_name = settings.S3_STORAGE_BUCKET_NAME
resource = boto3.resource("s3", **API_CONNECTION_DICT)
bucket = resource.Bucket(bucket_name)
USER_IMAGE_FOLDER_NAME = "user_image"
SIAE_LOGO_FOLDER_NAME = "siae_logo"
SIAE_CLIENT_REFERENCE_LOGO_FOLDER_NAME = "client_reference_logo"

# Content-Type file mapping
CONTENT_TYPE_MAPPING = {
    "png": "image/png",
    "PNG": "image/png",
    "svg": "image/svg+xml",
    "gif": "image/gif",
    "jpg": "image/jpg",
    "JPG": "image/jpg",
    "jpeg": "image/jpeg",
}  # "jfif"


def build_image_url(endpoint, bucket_name, image_key):
    return f"{endpoint}/{bucket_name}/{image_key}"


class Command(BaseCommand):
    def handle(self, *args, **options):
        # self.clean_bucket()
        # self.migrate_user_images()
        # self.migrate_siae_logos()
        # self.migrate_siae_client_reference_logos()
        self.migrate_siae_images()

    def clean_bucket(self):
        bucket.objects.delete()

    def migrate_user_images(self):
        """ """
        print("-" * 80)
        print("Migrating User images...")

        # reconnect just to be sure
        ftp = FTP(
            host=os.environ.get("COCORICO_FTP_HOST"),
            user=os.environ.get("COCORICO_FTP_USER"),
            passwd=os.environ.get("COCORICO_FTP_PASSWORD"),
        )
        ftp.cwd("users/images")

        users_with_images = User.objects.exclude(image_name="").exclude(image_name__isnull=True)
        progress = 0

        for user in users_with_images:
            # Step 1: download image from FTP
            with open(user.image_name, "wb") as f:
                ftp.retrbinary("RETR " + user.image_name, f.write)

            image_extension = user.image_name.split(".")[1]
            if image_extension in CONTENT_TYPE_MAPPING:
                # Step 2: upload image to S3
                s3_image_key = USER_IMAGE_FOLDER_NAME + "/" + user.image_name
                bucket.upload_file(
                    user.image_name,
                    s3_image_key,
                    ExtraArgs={"ACL": "public-read", "ContentType": CONTENT_TYPE_MAPPING[image_extension]},
                )

                # Step 3: update object
                user.image_url = build_image_url(API_CONNECTION_DICT["endpoint_url"], bucket_name, s3_image_key)
                user.save()
            else:
                print(f"Image extension error / User {user.id} / Image name {user.image_name}")

            # Step 4: delete local image
            os.remove(user.image_name)

            progress += 1
            if (progress % 500) == 0:
                print(f"{progress}...")

        print(f"Migrated {users_with_images.count()} user images !")

    def migrate_siae_logos(self):
        """ """
        print("-" * 80)
        print("Migrating Siae logos...")

        ftp = FTP(
            host=os.environ.get("COCORICO_FTP_HOST"),
            user=os.environ.get("COCORICO_FTP_USER"),
            passwd=os.environ.get("COCORICO_FTP_PASSWORD"),
        )
        ftp.cwd("listings/images")

        siaes_with_logos = Siae.objects.exclude(image_name="").exclude(image_name__isnull=True)
        progress = 0

        for siae in siaes_with_logos:
            # Step 1: download image from FTP
            with open(siae.image_name, "wb") as f:
                ftp.retrbinary("RETR " + siae.image_name, f.write)

            image_extension = siae.image_name.split(".")[1]
            if image_extension in CONTENT_TYPE_MAPPING:
                # Step 2: upload image to S3
                s3_image_key = SIAE_LOGO_FOLDER_NAME + "/" + siae.image_name
                bucket.upload_file(
                    siae.image_name,
                    s3_image_key,
                    ExtraArgs={"ACL": "public-read", "ContentType": CONTENT_TYPE_MAPPING[image_extension]},
                )

                # Step 3: update object
                siae.logo_url = build_image_url(API_CONNECTION_DICT["endpoint_url"], bucket_name, s3_image_key)
                siae.save()
            else:
                print(f"Image extension error / Siae {siae.id} / Image name {siae.image_name}")

            # Step 4: delete local image
            os.remove(siae.image_name)

            progress += 1
            if (progress % 500) == 0:
                print(f"{progress}...")

        print(f"Migrated {siaes_with_logos.count()} siae images !")

    def migrate_siae_client_reference_logos(self):
        """ """
        print("-" * 80)
        print("Migrating Siae Client Reference logos...")

        ftp = FTP(
            host=os.environ.get("COCORICO_FTP_HOST"),
            user=os.environ.get("COCORICO_FTP_USER"),
            passwd=os.environ.get("COCORICO_FTP_PASSWORD"),
        )
        ftp.cwd("listings/images")

        client_references_with_logos = SiaeClientReference.objects.exclude(image_name="").exclude(
            image_name__isnull=True
        )
        progress = 0

        for client_reference in client_references_with_logos:
            # Step 1: download image from FTP
            with open(client_reference.image_name, "wb") as f:
                ftp.retrbinary("RETR " + client_reference.image_name, f.write)

            image_extension = client_reference.image_name.split(".")[1]
            if image_extension in CONTENT_TYPE_MAPPING:
                # Step 2: upload image to S3
                s3_image_key = SIAE_CLIENT_REFERENCE_LOGO_FOLDER_NAME + "/" + client_reference.image_name
                bucket.upload_file(
                    client_reference.image_name,
                    s3_image_key,
                    ExtraArgs={"ACL": "public-read", "ContentType": CONTENT_TYPE_MAPPING[image_extension]},
                )

                # Step 3: update object
                client_reference.logo_url = build_image_url(
                    API_CONNECTION_DICT["endpoint_url"], bucket_name, s3_image_key
                )
                client_reference.save()
            else:
                print(
                    f"Image extension error / Client reference {client_reference.id} / Image name {client_reference.image_name}"  # noqa
                )

            # Step 4: delete local image
            os.remove(client_reference.image_name)

            progress += 1
            if (progress % 500) == 0:
                print(f"{progress}...")

        print(f"Migrated {client_references_with_logos.count()} client reference images !")

    def migrate_siae_images(self):
        """ """
        print("-" * 80)
        print("Migrating Siae images...")
