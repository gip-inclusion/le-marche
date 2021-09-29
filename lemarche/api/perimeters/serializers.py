from rest_framework import serializers

from lemarche.perimeters.models import Perimeter


class PerimeterSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perimeter
        fields = [
            "name",
            "slug",
            "kind",
        ]


class PerimeterChoiceSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
