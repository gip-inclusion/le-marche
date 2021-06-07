from django.db import models
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _

from users.managers import UserManager
#
# Create your models here.


class User(AbstractUser):
    """
    C4 Custom User Model
    """
    email = models.EmailField(_('email address'), unique=True)

    api_key = models.CharField(max_length=128, verbose_name="Clé API", default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

