from django.db import models
from django.db import models
from django.contrib.auth.models import AbstractUser

#
# Create your models here.


class User(AbstractUser):
    """
    C4 Custom User Model
    """

    api_key = models.BooleanField(verbose_name="Clé API", default=False)

