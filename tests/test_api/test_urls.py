import json

import pytest

from tests import data_setup


pytestmark = pytest.mark.django_db


class TestApiEndpoints:

    endpoint = '/siaes'

    def setUp(self):
        data_setup.basic_setup(self)

    def test_list(self, api_client):
        response = api_client().get(
            self.endpoint
        )

        assert response.status_code == 200
        # By default, non-authenticated connections return
        # 10 structures
        assert len(json.loads(response.content)) == 10
