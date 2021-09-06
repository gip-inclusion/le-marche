from rest_framework import serializers

from lemarche.sectors.models import SectorGroup, Sector


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


class SectorSimpleSerializer(SectorSerializer):

    class Meta:
        model = Sector
        fields = [
            "name",
            "slug",
        ]
