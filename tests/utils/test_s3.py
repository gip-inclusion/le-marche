import base64
import json

from django.test import SimpleTestCase

from lemarche.utils.s3 import S3Upload


class S3UploadTest(SimpleTestCase):
    def get_policy_conditions(self, s3_upload):
        policy = s3_upload.form_values["fields"]["policy"]
        return json.loads(base64.b64decode(policy))["conditions"]

    def test_key_path_is_random_per_policy(self):
        s3_upload_1 = S3Upload(kind="siae_logo")
        s3_upload_2 = S3Upload(kind="siae_logo")
        self.assertTrue(s3_upload_1.config["key_path"].startswith("siae_logo/"))
        self.assertTrue(s3_upload_2.config["key_path"].startswith("siae_logo/"))
        self.assertNotEqual(s3_upload_1.config["key_path"], s3_upload_2.config["key_path"])

    def test_policy_key_is_restricted_to_random_prefix(self):
        s3_upload = S3Upload(kind="siae_logo")
        conditions = self.get_policy_conditions(s3_upload)
        self.assertIn(["starts-with", "$key", f"{s3_upload.config['key_path']}/"], conditions)
        self.assertNotIn(["starts-with", "$key", "siae_logo/"], conditions)

    def test_policy_restricts_content_length(self):
        s3_upload = S3Upload(kind="siae_logo")
        conditions = self.get_policy_conditions(s3_upload)
        self.assertIn(["content-length-range", 1, s3_upload.config["max_file_size"] * 1024 * 1024], conditions)
