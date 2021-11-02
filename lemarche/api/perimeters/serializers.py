from rest_framework import serializers

from lemarche.perimeters.models import Perimeter


class PerimeterSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perimeter
        fields = [
            "name",
            "slug",
            "kind",
            # only for CITY
            "insee_code",
            "post_codes",
            "department_code",
            # only for CITY & DEPARTMENT
            "region_code",
        ]


class PerimeterChoiceSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
