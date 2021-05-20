from rest_framework import serializers
from c4_directory.models import (
    Siae,
    Sector,
)

class SiaeSerializer(serializers.ModelSerializer):
    raisonSociale = serializers.CharField(source='name')
    enseigne = serializers.CharField(source='brand')
    type = serializers.CharField(source='kind')
    telephone = serializers.CharField(source='phone')
    siteWeb = serializers.CharField(source='website')
    ville = serializers.CharField(source='city')
    departement = serializers.CharField(source='department')
    codePostal = serializers.CharField(source='post_code')

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
                'createdat'
        ]

class SectorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sector


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
