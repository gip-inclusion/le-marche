from rest_framework import serializers

from lemarche.api.sectors.serializers import SectorSimpleSerializer
from lemarche.siaes.models import Siae


class SiaeSerializer(serializers.ModelSerializer):
    sectors = SectorSimpleSerializer(many=True)

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
            "city",
            "post_code",
            "department",
            "region",
            "is_qpv",
            "is_cocontracting",
            "sectors",
            "created_at",
            "updated_at",
        ]


class SiaeAnonSerializer(SiaeSerializer):
    class Meta:
        model = Siae
        fields = [
            "name",
            "brand",
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
            "department",
            "created_at",
            "updated_at",
        ]


class SiaeChoiceSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
