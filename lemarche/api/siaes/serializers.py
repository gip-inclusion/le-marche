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


class SiaeSerializer(serializers.ModelSerializer):
    sectors = SectorSimpleSerializer(many=True)
    networks = NetworkSimpleSerializer(many=True)
    offers = SiaeOfferSimpleSerializer(many=True)
    client_references = SiaeClientReferenceSimpleSerializer(many=True)
    labels = SiaeLabelSimpleSerializer(many=True)

    class Meta:
        model = Siae
        fields = [
            "name",
            "brand",
            "slug",
            "siret",
            "kind",
            "presta_type",
            "contact_email",
            "contact_phone",
            "contact_website",
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
            "created_at",
            "updated_at",
        ]


class SiaeAnonSerializer(SiaeSerializer):
    class Meta:
        model = Siae
        fields = [
            "name",
            "brand",
            # "slug"
            "siret",
            "city",
            "post_code",
            "department",
            "region",
            "created_at",
        ]


class SiaeListSerializer(SiaeSerializer):
    class Meta:
        model = Siae
        fields = [
            "name",
            "brand",
            "slug",
            "siret",
            "kind",
            "presta_type",
            # contact stuff available in detail
            "city",
            "post_code",
            "department",
            "region",
            # boolean stuff available in detail
            # M2M stuff available in detail
            "created_at",
            "updated_at",
        ]


class SiaeChoiceSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
