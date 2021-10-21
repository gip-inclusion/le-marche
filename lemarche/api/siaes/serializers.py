from drf_spectacular.utils import OpenApiTypes, extend_schema_field
from rest_framework import serializers

from lemarche.api.sectors.serializers import SectorSimpleSerializer
from lemarche.siaes.models import Siae


class SiaeSerializer(serializers.ModelSerializer):
    # TODO : Use hyperlinkedmodelserializer
    raisonSociale = serializers.CharField(source="name")
    enseigne = serializers.CharField(source="brand")
    type = serializers.CharField(source="kind")
    # presta_type =
    telephone = serializers.CharField(source="phone")
    siteWeb = serializers.CharField(source="website")
    ville = serializers.CharField(source="city")
    departement = serializers.CharField(source="department")
    codePostal = serializers.CharField(source="post_code")
    siretUrl = serializers.SerializerMethodField()
    sectors = SectorSimpleSerializer(many=True)
    # zoneQPV = serializers.BooleanField(source="is_qpv", default=False)
    zoneQPV = serializers.SerializerMethodField()

    class Meta:
        model = Siae
        fields = [
            "raisonSociale",
            "slug",
            "enseigne",
            "siret",
            "type",
            "presta_type",
            "email",
            "telephone",
            "siteWeb",
            "ville",
            "departement",
            "region",
            "codePostal",
            "zoneQPV",
            "created_at",
            "updated_at",
            "siretUrl",
            "sectors",
        ]

    @extend_schema_field(OpenApiTypes.STR)
    def get_siretUrl(self, obj):
        return f"/siae/siret/{obj.siret}"

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_zoneQPV(self, obj):
        # Impossible to make the Boolean field serializer return false if
        # value is null.
        return obj.is_qpv == 1


class SiaeAnonSerializer(SiaeSerializer):
    # TODO : Use hyperlinkedmodelserializer

    class Meta:
        model = Siae
        fields = [
            "raisonSociale",
            # "slug",
            "enseigne",
            "siret",
            "ville",
            "departement",
            "region",
            "codePostal",
            "created_at",
        ]


class SiaeListSerializer(SiaeSerializer):
    # TODO : Use hyperlinkedmodelserializer

    class Meta:
        model = Siae
        fields = [
            "raisonSociale",
            "siret",
            "type",
            "presta_type",
            "departement",
            "created_at",
            "updated_at",
        ]


class SiaeListAnonSerializer(SiaeSerializer):
    # TODO : Use hyperlinkedmodelserializer

    class Meta:
        model = Siae
        fields = [
            "raisonSociale",
            "siret",
        ]


class SiaeChoiceSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
