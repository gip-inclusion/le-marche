## Temporary code
## FIXME : move elsewhere
from django.db import models


## End of temporary code


class Sector(models.Model):
    id = models.IntegerField(primary_key=True)
    parent = models.ForeignKey("self", models.DO_NOTHING, blank=True, null=True)
    lft = models.IntegerField()
    lvl = models.IntegerField()
    rgt = models.IntegerField()
    root = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ["id"]


class SectorString(models.Model):
    id = models.IntegerField(primary_key=True)
    translatable = models.ForeignKey(Sector, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=100)
    locale = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["id"]


# class SiaeSector(models.Model):
#     id = models.IntegerField(primary_key=True)
#     directory = models.ForeignKey(Directory, models.DO_NOTHING)
#     listing_category = models.ForeignKey('Sector', models.DO_NOTHING)
#     source = models.CharField(max_length=255, blank=True, null=True)
#
#     class Meta:
#         ordering = ['id']
