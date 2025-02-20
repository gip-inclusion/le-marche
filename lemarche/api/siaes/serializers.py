from rest_framework import serializers

from lemarche.api.networks.serializers import NetworkSimpleSerializer
from lemarche.api.sectors.serializers import SectorSimpleSerializer
from lemarche.siaes import constants
from lemarche.siaes.models import Siae, SiaeClientReference, SiaeLabelOld, SiaeOffer


class SiaeOfferSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiaeOffer
        fields = [
            "name",
            "description",
        ]


class SiaeClientReferenceSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiaeClientReference
        fields = [
            "name",
            "description",
            "logo_url",
        ]


class SiaeLabelOldSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiaeLabelOld
        fields = [
            "name",
        ]


class SiaeDetailSerializer(serializers.ModelSerializer):
    kind_parent = serializers.ReadOnlyField()
    sectors = SectorSimpleSerializer(many=True, source="get_sectors")
    presta_types = serializers.MultipleChoiceField(choices=constants.PRESTA_CHOICES, source="presta_types_annotated")
    networks = NetworkSimpleSerializer(many=True)
    offers = SiaeOfferSimpleSerializer(many=True)
    client_references = SiaeClientReferenceSimpleSerializer(many=True)
    labels_old = SiaeLabelOldSimpleSerializer(many=True)

    class Meta:
        model = Siae
        fields = [
            "id",
            "name",
            "brand",
            "slug",
            "siret",
            "nature",
            "kind",
            "kind_parent",
            "contact_website",
            "contact_email",
            "contact_phone",
            "contact_social_website",
            "logo_url",
            "address",
            "city",
            "post_code",
            "department",
            "region",
            "is_qpv",
            "is_active",
            "sectors",
            "presta_types",
            "networks",
            "offers",
            "client_references",
            "labels_old",
            "created_at",
            "updated_at",
        ]


class SiaeListSerializer(SiaeDetailSerializer):
    class Meta:
        model = Siae
        fields = [
            "id",
            "name",
            "brand",
            "slug",
            "siret",
            "nature",
            "kind",
            "kind_parent",
            "contact_website",
            "logo_url",
            # additional contact_ fields available in detail
            "address",
            "city",
            "post_code",
            "department",
            "region",
            "is_active",
            # is_ boolean fields available in detail
            # M2M fields available in detail
            "created_at",
            "updated_at",
        ]
