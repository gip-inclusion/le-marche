from lemarche.api.models import Sector, SectorString, Siae
from hashids import Hashids
from rest_framework import serializers


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

    def get_id(self, obj):
        must_hash_id = self.context.get("hashed_pk", False)
        if must_hash_id:
            return hasher.encode(obj.id)

        return obj.id

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
            "sectors",
            "zoneQPV",
        ]

    def get_url(self, obj):
        # Writing URL by hand is a hack, use hyperlinkedmodelserializer for greater good
        must_hash_id = self.context.get("hashed_pk", False)
        key = hasher.encode(obj.pk) if must_hash_id else obj.pk
        return f"/siaes/{key}"

    def get_zoneQPV(self, obj):
        # Impossible to make the Boolean field serializer return false if value is null.
        return obj.is_qpv == 1


class SiaeLightSerializer(SiaeSerializer):
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
