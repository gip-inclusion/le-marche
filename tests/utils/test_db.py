import pytest

from blog.models import User
from lemarche.utils.db import secure_delete
from tests.tenders.factories import TenderFactory
from tests.users.factories import UserFactory


def test_secure_delete(db):
    user = UserFactory()
    TenderFactory(author=user)
    with pytest.raises(Exception) as excinfo:
        secure_delete(User.objects.all(), [])
    assert User.objects.exists()
    assert str(excinfo.value) == "Forbidden models deleted: ['tenders.Tender', 'users.User']"

    res = secure_delete(User.objects.all(), ["users.User", "tenders.Tender"])
    assert res == {"users.User": 1, "tenders.Tender": 1}
