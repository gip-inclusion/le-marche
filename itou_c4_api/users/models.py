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
    username = None
    email = models.EmailField(_('email address'), unique=True)

    api_key = models.CharField(max_length=128, verbose_name="Clé API", unique=True, default='')

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    ACCOUNT_USER_MODEL_USERNAME_FIELD = None
    ACCOUNT_USERNAME_REQUIRED = False
    ACCOUNT_EMAIL_REQUIRED = True

    objects = UserManager()

    class Meta:
        unique_together = ('email', )

    def __str__(self):
        return self.email

