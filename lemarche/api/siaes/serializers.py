from lemarche.api.models import Sector, SectorString, Siae
from hashids import Hashids
from rest_framework import serializers


# TODO: implement hashid as shared object
hasher = Hashids(alphabet="1234567890ABCDEF", min_length=5)


class SectorSerializer(serializers.ModelSerializer):
    # TODO : Use hyperlinkedmodelserializer
    id = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Sector
        fields = [
            "id",
            "parent",
        ]

    def get_id(self, obj):
        return hasher.encode(obj.id)

    def get_parent(self, obj):
        if obj.parent is None:
            return None
        return hasher.encode(obj.parent.id)


class SectorSimpleSerializer(SectorSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Sector
        fields = [
            "id",
            "url",
        ]

    def get_url(self, obj):
        key = hasher.encode(obj.id)
        return f"/secteurs/{key}"


class SectorStringSerializer(serializers.ModelSerializer):
    # TODO : Use hyperlinkedmodelserializer
    # FIXME : Code repetition
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
        key = hasher.encode(obj.id)
        return f"/secteur/{key}"


class SiaeSerializer(serializers.ModelSerializer):
    # TODO : Use hyperlinkedmodelserializer
    # FIXME : Code repetition
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

    def get_url(self, obj):
        return f"/siaes/{obj.pk}"

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
        ]


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
