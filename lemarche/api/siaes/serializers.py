from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

from lemarche.siaes.models import Siae
from lemarche.api.sectors.serializers import SectorSimpleSerializer
from lemarche.api.utils import hasher


class SiaeSerializer(serializers.ModelSerializer):
    # TODO : Use hyperlinkedmodelserializer
    raisonSociale = serializers.CharField(source="name")
    enseigne = serializers.CharField(source="brand")
    type = serializers.CharField(source="kind")
    telephone = serializers.CharField(source="phone")
    siteWeb = serializers.CharField(source="website")
    ville = serializers.CharField(source="city")
    departement = serializers.CharField(source="department")
    codePostal = serializers.CharField(source="post_code")
    url = serializers.SerializerMethodField()
    siretUrl = serializers.SerializerMethodField()
    sectors = SectorSimpleSerializer(many=True, read_only=True)
    # zoneQPV = serializers.BooleanField(source="is_qpv", default=False)
    zoneQPV = serializers.SerializerMethodField()

    class Meta:
        model = Siae
        fields = [
            "raisonSociale",
            "enseigne",
            "siret",
            "type",
            "email",
            "telephone",
            "siteWeb",
            "ville",
            "departement",
            "region",
            "codePostal",
            "zoneQPV",
            "createdat",
            "updatedat",
            "url",
            "siretUrl",
            "sectors",
        ]

    @extend_schema_field(OpenApiTypes.STR)
    def get_url(self, obj):
        # Writing URL by hand is a hack, use hyperlinkedmodelserializer for
        # greater good
        must_hash_id = self.context.get("hashed_pk", False)
        key = hasher.encode(obj.pk) if must_hash_id else obj.pk
        return f"/siae/id/{key}"

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
            "enseigne",
            "siret",
            "ville",
            "departement",
            "region",
            "codePostal",
            "createdat",
            "url",
        ]


class SiaeListSerializer(SiaeSerializer):
    # TODO : Use hyperlinkedmodelserializer

    class Meta:
        model = Siae
        fields = [
            "raisonSociale",
            "siret",
            "type",
            "departement",
            "createdat",
            "updatedat",
            "url",
        ]


class SiaeListAnonSerializer(SiaeSerializer):
    # TODO : Use hyperlinkedmodelserializer

    class Meta:
        model = Siae
        fields = [
            "raisonSociale",
            "siret",
            "url",
        ]


class SiaeHyperSerializer(serializers.HyperlinkedModelSerializer):
    # Tested this, bur error messages are very confusing.
    # Should replace all manually generated URLS, so
    # I keep it here as a reminder

    raisonSociale = serializers.CharField(source="name")
    enseigne = serializers.CharField(source="brand")
    type = serializers.CharField(source="kind")
    telephone = serializers.CharField(source="phone")
    siteWeb = serializers.CharField(source="website")
    ville = serializers.CharField(source="city")
    departement = serializers.CharField(source="department")
    codePostal = serializers.CharField(source="post_code")

    target = serializers.HyperlinkedIdentityField(
        view_name="siae-detail", lookup_field="siret", lookup_url_kwarg="key"
    )

    class Meta:
        model = Siae
        fields = [
            "raisonSociale",
            "enseigne",
            "siret",
            "type",
            "email",
            "telephone",
            "siteWeb",
            "ville",
            "departement",
            "region",
            "codePostal",
            "createdat",
            "target",
            # 'url',
        ]
        # extra_kwargs = {
        #     'url': {'view_name': 'siae-detail', 'lookup_field': 'siret'},
        # }
