from rest_framework import serializers

from lemarche.sectors.models import Sector, SectorGroup


class SectorGroupSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectorGroup
        fields = [
            "name",
            "slug",
        ]


class SectorSerializer(serializers.ModelSerializer):
    group = SectorGroupSimpleSerializer()

    class Meta:
        model = Sector
        fields = [
            "name",
            "slug",
            "group",
        ]


class SectorSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = [
            "name",
            "slug",
        ]
