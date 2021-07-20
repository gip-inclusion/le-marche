from lemarche.api.models import Sector, SectorString, Siae
from hashids import Hashids
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, OpenApiTypes


# TODO: implement hashid as shared object
hasher = Hashids(alphabet="1234567890ABCDEF", min_length=5)


class SectorSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Sector
        fields = [
            "id",
            "parent",
        ]

    @extend_schema_field(OpenApiTypes.STR)
    def get_id(self, obj):
        must_hash_id = self.context.get("hashed_pk", False)
        if must_hash_id:
            return hasher.encode(obj.id)

        return obj.id

    @extend_schema_field(OpenApiTypes.STR)
    def get_parent(self, obj):
        if obj.parent is None:
            return None

        must_hash_id = self.context.get("hashed_pk", False)
        return hasher.encode(obj.parent.id) if must_hash_id else obj.parent.id


class SectorSimpleSerializer(SectorSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Sector
        fields = [
            "id",
            "url",
        ]

    @extend_schema_field(OpenApiTypes.STR)
    def get_url(self, obj):
        # Writing URL by hand is a hack, use hyperlinkedmodelserializer for greater good
        must_hash_id = self.context.get("hashed_pk", False)
        key = hasher.encode(obj.id) if must_hash_id else obj.id
        return f"/secteurs/{key}"


class SectorStringSerializer(serializers.ModelSerializer):
    # TODO : Use hyperlinkedmodelserializer
    hierarchie = SectorSerializer(many=False, read_only=True, source="translatable")

    nom = serializers.CharField(source="name")
    url = serializers.SerializerMethodField()

    class Meta:
        model = SectorString
        fields = [
            "nom",
            "slug",
            "url",
            "hierarchie",
        ]

    @extend_schema_field(OpenApiTypes.STR)
    def get_url(self, obj):
        # Writing URL by hand is a hack, use hyperlinkedmodelserializer for greater good
        must_hash_id = self.context.get("hashed_pk", False)
        key = hasher.encode(obj.translatable.id) if must_hash_id else obj.translatable.id
        return f"/secteurs/{key}"


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
            "createdat",
            "url",
            "siretUrl",
            "sectors",
            "zoneQPV",
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
