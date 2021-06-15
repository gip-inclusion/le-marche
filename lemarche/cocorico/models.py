# Generated table models from the cocorico database
# /!\ DO NOT make them managed by django : Management is done by Doctrine, the symfony ORM
# This API is only a mere client to these data, a coy reader.

from django.db import models
from django.conf import settings


# QuerySets, allowing for easier future migration to managed
# database (just rewrite query)
class SectorQuerySet(models.QuerySet):

    START_IDS_AT = 10

    def get_all_active_sectors(self):
        return self.filter(translatable__gte=self.START_IDS_AT).select_related("translatable").all()

    def get_sector(self, pk):
        return SectorString.objects.select_related("translatable").get(translatable=pk)



# class ListingCategory(models.Model):
class Sector(models.Model):
    id = models.IntegerField(primary_key=True)
    parent = models.ForeignKey("self", models.DO_NOTHING, blank=True, null=True)
    lft = models.IntegerField()
    lvl = models.IntegerField()
    rgt = models.IntegerField()
    root = models.IntegerField(blank=True, null=True)

    class Meta:
        # managed = False
        managed = getattr(settings, "MANAGE_COCORICO_DATABASE", False)
        db_table = "listing_category"


# class ListingCategoryTranslation(models.Model):
class SectorString(models.Model):
    id = models.IntegerField(primary_key=True)
    translatable = models.ForeignKey(Sector, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=100)
    locale = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, blank=True, null=True)

    objects = models.Manager.from_queryset(SectorQuerySet)()

    class Meta:
        # managed = False
        managed = getattr(settings, "MANAGE_COCORICO_DATABASE", False)
        db_table = "listing_category_translation"


class Directory(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    siret = models.CharField(max_length=14, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    kind = models.CharField(max_length=255)
    website = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    post_code = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    presta_type = models.CharField(max_length=255, blank=True, null=True)
    # sector = models.TextField(blank=True, null=True)
    naf = models.CharField(max_length=5, blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    brand = models.CharField(max_length=255, blank=True, null=True)
    createdat = models.DateTimeField(db_column="createdAt", blank=True, null=True)  # Field name made lowercase.
    updatedat = models.DateTimeField(db_column="updatedAt", blank=True, null=True)  # Field name made lowercase.
    c1_id = models.IntegerField(blank=True, null=True)
    c4_id = models.IntegerField(blank=True, null=True)
    is_delisted = models.IntegerField(blank=True, null=True)
    c1_source = models.CharField(max_length=255, blank=True, null=True)
    last_sync_date = models.DateTimeField(blank=True, null=True)
    nature = models.CharField(max_length=255, blank=True, null=True)
    siret_is_valid = models.IntegerField(blank=True, null=True)
    ig_employees = models.CharField(max_length=255, blank=True, null=True)
    ig_ca = models.IntegerField(blank=True, null=True)
    ig_date_constitution = models.DateTimeField(blank=True, null=True)
    admin_email = models.CharField(max_length=255, blank=True, null=True)
    admin_name = models.CharField(max_length=255, blank=True, null=True)
    geo_range = models.IntegerField(blank=True, null=True)
    pol_range = models.IntegerField(blank=True, null=True)
    description = models.TextField()
    sectors = models.ManyToManyField(Sector, through="DirectorySector")

    class Meta:
        # managed = False
        managed = getattr(settings, "MANAGE_COCORICO_DATABASE", False)
        db_table = "directory"


class DirectorySector(models.Model):
    # id = models.IntegerField(primary_key=True)

    source = models.CharField(max_length=255, blank=True, null=True)
    directory = models.ForeignKey(Directory, models.DO_NOTHING, db_column="directory_id")
    sector = models.ForeignKey(Sector, models.DO_NOTHING, db_column="listing_category_id")

    class Meta:
        # managed = False
        managed = getattr(settings, "MANAGE_COCORICO_DATABASE", False)
        db_table = "directory_listing_category"
        unique_together = (("directory", "sector"),)


class DirectoryClientImage(models.Model):
    id = models.IntegerField(primary_key=True)
    directory = models.ForeignKey(Directory, models.DO_NOTHING)
    name = models.CharField(max_length=255)
    position = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = "directory_client_image"


class DirectoryImage(models.Model):
    id = models.IntegerField(primary_key=True)
    directory = models.ForeignKey(Directory, models.DO_NOTHING)
    name = models.CharField(max_length=255)
    position = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = "directory_image"


# class DirectoryListingCategory(models.Model):
#     id = models.IntegerField(primary_key=True)
#     directory = models.ForeignKey(Directory, models.DO_NOTHING)
#     listing_category = models.ForeignKey('Sector', models.DO_NOTHING)
#     source = models.CharField(max_length=255, blank=True, null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'directory_listing_category'
#         unique_together = (('directory', 'listing_category'),)


class DirectoryCategory(models.Model):
    class Meta:
        managed = False
        db_table = "directory_category"


class DirectoryUser(models.Model):
    class Meta:
        managed = False
        db_table = "directory_user"


class Booking(models.Model):
    class Meta:
        managed = False
        db_table = "booking"


class BookingBankWire(models.Model):
    class Meta:
        managed = False
        db_table = "booking_bank_wire"


class BookingPayinRefund(models.Model):
    class Meta:
        managed = False
        db_table = "booking_payin_refund"


class BookingUserAddress(models.Model):
    class Meta:
        managed = False
        db_table = "booking_user_address"


class Contact(models.Model):
    class Meta:
        managed = False
        db_table = "contact"


class Footer(models.Model):
    class Meta:
        managed = False
        db_table = "footer"


class FooterTranslation(models.Model):
    class Meta:
        managed = False
        db_table = "footer_translation"


class GeoArea(models.Model):
    class Meta:
        managed = False
        db_table = "geo_area"


class GeoAreaTranslation(models.Model):
    class Meta:
        managed = False
        db_table = "geo_area_translation"


class GeoCity(models.Model):
    class Meta:
        managed = False
        db_table = "geo_city"


class GeoCityTranslation(models.Model):
    class Meta:
        managed = False
        db_table = "geo_city_translation"


class GeoCoordinate(models.Model):
    class Meta:
        managed = False
        db_table = "geo_coordinate"


class GeoCountry(models.Model):
    class Meta:
        managed = False
        db_table = "geo_country"


class GeoCountryTranslation(models.Model):
    class Meta:
        managed = False
        db_table = "geo_country_translation"


class GeoDepartment(models.Model):
    class Meta:
        managed = False
        db_table = "geo_department"


class GeoDepartmentTranslation(models.Model):
    class Meta:
        managed = False
        db_table = "geo_department_translation"


class GeoGeocoding(models.Model):
    class Meta:
        managed = False
        db_table = "geo_geocoding"


class Group(models.Model):
    class Meta:
        managed = False
        db_table = "group"


class LexikCurrency(models.Model):
    class Meta:
        managed = False
        db_table = "lexik_currency"


class Listing(models.Model):
    class Meta:
        managed = False
        db_table = "listing"


class ListingCharacteristic(models.Model):
    class Meta:
        managed = False
        db_table = "listing_characteristic"


class ListingCharacteristicGroup(models.Model):
    class Meta:
        managed = False
        db_table = "listing_characteristic_group"


class ListingCharacteristicGroupTranslation(models.Model):
    class Meta:
        managed = False
        db_table = "listing_characteristic_group_translation"


class ListingCharacteristicTranslation(models.Model):
    class Meta:
        managed = False
        db_table = "listing_characteristic_translation"


class ListingCharacteristicType(models.Model):
    class Meta:
        managed = False
        db_table = "listing_characteristic_type"


class ListingCharacteristicValue(models.Model):
    class Meta:
        managed = False
        db_table = "listing_characteristic_value"


class ListingCharacteristicValueTranslation(models.Model):
    class Meta:
        managed = False
        db_table = "listing_characteristic_value_translation"


class ListingClientImage(models.Model):
    class Meta:
        managed = False
        db_table = "listing_client_image"


class ListingDiscount(models.Model):
    class Meta:
        managed = False
        db_table = "listing_discount"


class ListingImage(models.Model):
    class Meta:
        managed = False
        db_table = "listing_image"


class ListingListingCategory(models.Model):
    class Meta:
        managed = False
        db_table = "listing_listing_category"


class ListingListingCharacteristic(models.Model):
    class Meta:
        managed = False
        db_table = "listing_listing_characteristic"


class ListingLocation(models.Model):
    class Meta:
        managed = False
        db_table = "listing_location"


class ListingTranslation(models.Model):
    class Meta:
        managed = False
        db_table = "listing_translation"


class Message(models.Model):
    class Meta:
        managed = False
        db_table = "message"


class MessageMetadata(models.Model):
    class Meta:
        managed = False
        db_table = "message_metadata"


class MessageThread(models.Model):
    class Meta:
        managed = False
        db_table = "message_thread"


class MessageThreadMetadata(models.Model):
    class Meta:
        managed = False
        db_table = "message_thread_metadata"


class Page(models.Model):
    class Meta:
        managed = False
        db_table = "page"


class PageTranslation(models.Model):
    class Meta:
        managed = False
        db_table = "page_translation"


class Parameter(models.Model):
    class Meta:
        managed = False
        db_table = "parameter"


class ParameterAudit(models.Model):
    class Meta:
        managed = False
        db_table = "parameter_audit"


class Quote(models.Model):
    class Meta:
        managed = False
        db_table = "quote"


class QuoteUserAddress(models.Model):
    class Meta:
        managed = False
        db_table = "quote_user_address"


class Review(models.Model):
    class Meta:
        managed = False
        db_table = "review"


class Revisions(models.Model):
    class Meta:
        managed = False
        db_table = "revisions"


class User(models.Model):
    class Meta:
        managed = False
        db_table = "user"


class UserAddress(models.Model):
    class Meta:
        managed = False
        db_table = "user_address"


class UserFacebook(models.Model):
    class Meta:
        managed = False
        db_table = "user_facebook"


class UserGroup(models.Model):
    class Meta:
        managed = False
        db_table = "user_group"


class UserImage(models.Model):
    class Meta:
        managed = False
        db_table = "user_image"


class UserLanguage(models.Model):
    class Meta:
        managed = False
        db_table = "user_language"


class UserTranslation(models.Model):
    class Meta:
        managed = False
        db_table = "user_translation"
