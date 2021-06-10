from rest_framework import serializers
from c4_directory.models import (
    Siae,
    Sector,
    SectorString,
)
from django.urls import reverse
from c4_directory import views
from hashids import Hashids

hasher = Hashids(alphabet='1234567890ABCDEF', min_length=5)

class SectorSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Sector
        fields = [
            'id',
            'parent',
        ]

    def get_id(self, obj):
        return hasher.encode(obj.id)

    def get_parent(self, obj):
        if obj.parent is None:
            return None
        return hasher.encode(obj.parent.id)


class SectorStringSerializer(serializers.ModelSerializer):
    hierarchie = SectorSerializer(many=False, read_only=True, source='translatable')

    nom = serializers.CharField(source='name')
    url = serializers.SerializerMethodField()

    class Meta:
        model = SectorString
        fields = [
            'nom',
            'slug',
            'url',
            'hierarchie',
        ]

    def get_url(self, obj):
        key =  hasher.encode(obj.id)
        return f"/secteur/{key}"

class SectorSimpleSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = Sector
        fields = [
            'id',
            'url',
        ]

    def get_id(self, obj):
        return hasher.encode(obj.id)

    def get_url(self, obj):
        key =  hasher.encode(obj.id)
        return f"/secteur/{key}"


class SiaeSerializer(serializers.ModelSerializer):
    raisonSociale = serializers.CharField(source='name')
    enseigne = serializers.CharField(source='brand')
    type = serializers.CharField(source='kind')
    telephone = serializers.CharField(source='phone')
    siteWeb = serializers.CharField(source='website')
    ville = serializers.CharField(source='city')
    departement = serializers.CharField(source='department')
    codePostal = serializers.CharField(source='post_code')
    url = serializers.SerializerMethodField()
    sectors = SectorSimpleSerializer(many=True, read_only=True)

    def get_url(self, obj):
        return f"/siae/{obj.pk}"

    class Meta:
        model = Siae
        fields = [
            'raisonSociale',
            'enseigne',
            'siret',
            'type',
            'email',
            'telephone',
            'siteWeb',
            'ville',
            'departement',
            'region',
            'codePostal',
            'createdat',
            'url',
            'sectors',
        ]

class SiaeHyperSerializer(serializers.HyperlinkedModelSerializer):
    # Tested this, but unclear error messaging
    # did not allow it to work, yet.
    raisonSociale = serializers.CharField(source='name')
    enseigne = serializers.CharField(source='brand')
    type = serializers.CharField(source='kind')
    telephone = serializers.CharField(source='phone')
    siteWeb = serializers.CharField(source='website')
    ville = serializers.CharField(source='city')
    departement = serializers.CharField(source='department')
    codePostal = serializers.CharField(source='post_code')

    target = serializers.HyperlinkedIdentityField(
        view_name="siae",
        lookup_field='siret',
        lookup_url_kwarg='key'
    )

    class Meta:
        model = Siae
        fields = [
            'raisonSociale',
            'enseigne',
            'siret',
            'type',
            'email',
            'telephone',
            'siteWeb',
            'ville',
            'departement',
            'region',
            'codePostal',
            'createdat',
            'target'
            # 'url',
        ]
        # extra_kwargs = {
        #     'url': {'view_name': 'siae-detail', 'lookup_field': 'siret'},
        # }



class SiaeLightSerializer(serializers.ModelSerializer):
    raisonSociale = serializers.CharField(source='name')
    enseigne = serializers.CharField(source='brand')
    ville = serializers.CharField(source='city')
    departement = serializers.CharField(source='department')
    codePostal = serializers.CharField(source='post_code')
    url = serializers.SerializerMethodField()

    class Meta:
        model = Siae
        fields = [
            'raisonSociale',
            'enseigne',
            'siret',
            'ville',
            'departement',
            'region',
            'codePostal',
            'createdat',
            'url',
        ]

    def get_url(self, obj):
        return f"/siae/{obj.pk}"


# class SiaeSerializer(serializers.Serializer):
# 
#     name = serializers.CharField(verbose_name="Nom", max_length=255)
#     brand = serializers.CharField(verbose_name="Enseigne", max_length=255, blank=True)
#     # kind = serializers.CharField(verbose_name="Type", max_length=6, choices=KIND_CHOICES, default=KIND_EI)
#     # siret = serializers.CharField(verbose_name="Siret", max_length=14, validators=[validate_siret], db_index=True)
#     # naf = serializers.CharField(verbose_name="Naf", max_length=5, validators=[validate_naf], blank=True)
#     # address = serializers.CharField(verbose_name="Adresse")
#     website = serializers.URLField(verbose_name="Site web", blank=True)
#     created_at = serializers.DateTimeField(verbose_name="Date de création", default=timezone.now)
# 
#     def create(self, validated_data):
#         """
#         Create and return a new `Siae` instance, given the validated data.
#         """
#         return Siae.objects.create(**validated_data)
# 
#     def update(self, instance, validated_data):
#         """
#         Update and return an existing `Snippet` instance, given the validated data.
#         """
#         instance.title = validated_data.get('title', instance.title)
#         instance.code = validated_data.get('code', instance.code)
#         instance.linenos = validated_data.get('linenos', instance.linenos)
#         instance.language = validated_data.get('language', instance.language)
#         instance.style = validated_data.get('style', instance.style)
#         instance.save()
#         return instance
