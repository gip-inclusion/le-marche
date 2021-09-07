from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

from lemarche.api.models import Sector, SectorString
from lemarche.api.utils import hasher


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
