from rest_framework import serializers

from lemarche.api.networks.serializers import NetworkSimpleSerializer
from lemarche.api.sectors.serializers import SectorSimpleSerializer
from lemarche.siaes.models import Siae, SiaeClientReference, SiaeLabel, SiaeOffer


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


class SiaeLabelSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiaeLabel
        fields = [
            "name",
        ]


class SiaeDetailSerializer(serializers.ModelSerializer):
    sectors = SectorSimpleSerializer(many=True)
    networks = NetworkSimpleSerializer(many=True)
    offers = SiaeOfferSimpleSerializer(many=True)
    client_references = SiaeClientReferenceSimpleSerializer(many=True)
    labels = SiaeLabelSimpleSerializer(many=True)

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
            "presta_type",
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
            "is_cocontracting",
            "is_active",
            "sectors",
            "networks",
            "offers",
            "client_references",
            "labels",
            # "images",
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
            "presta_type",
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


class SiaeChoiceSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
